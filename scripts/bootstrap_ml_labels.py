#!/usr/bin/env python3
"""
Bootstrap ML Labels — brise la circularite de l'entrainement.

Probleme initial :
  - Le modele fine-tune a appris sur des labels LEXICAUX (moteur de mots-cles).
  - Le moteur lexical est son propre oracle de verite terrain.
  - Le modele ne peut pas depasser le plafond du lexique.

Solution : self-training iteratif
  1. Charger les predictions du modele fine-tune sur GOLD_APP_INPUT
     (ou en lancer une si absentes).
  2. Selectionner les predictions a haute confiance (seuil configurable).
  3. Reconstruire gold_ia_labelled.parquet avec ces nouveaux labels ML
     a la place des labels lexicaux.
  4. Regenerer les splits train/val/test.
  5. Le prochain fine-tuning utilisera ces labels de meilleure qualite.

Iteration suivante : relancer ce script apres chaque fine-tuning.

Usage :
  python scripts/bootstrap_ml_labels.py
  python scripts/bootstrap_ml_labels.py --confidence-min 0.75 --run-inference
  python scripts/bootstrap_ml_labels.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import pandas as pd

from src.config import get_settings
from src.datasets.gold_branches import normalize_sentiment_label

settings = get_settings()


def _find_latest_predictions(goldai_base: Path) -> Path | None:
    """Retourne le predictions.parquet le plus recent."""
    pred_root = goldai_base / "predictions"
    if not pred_root.exists():
        return None
    candidates = sorted(
        pred_root.glob("date=*/run=*/predictions.parquet"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap ML labels pour briser la circularite lexicale."
    )
    parser.add_argument(
        "--confidence-min",
        type=float,
        default=0.70,
        help="Seuil de confiance minimum pour accepter un label ML (defaut 0.70)",
    )
    parser.add_argument(
        "--run-inference",
        action="store_true",
        help="Lancer l'inference ML si aucune prediction recente n'est disponible",
    )
    parser.add_argument(
        "--inference-limit",
        type=int,
        default=0,
        help="Limit pour l'inference si --run-inference (0 = tout)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher les statistiques sans ecrire les fichiers",
    )
    args = parser.parse_args()

    goldai_base = Path(settings.goldai_base_path)
    if not goldai_base.is_absolute():
        goldai_base = project_root / goldai_base

    print("\n" + "=" * 60)
    print("BOOTSTRAP ML LABELS")
    print("=" * 60)
    print(f"  confidence_min={args.confidence_min}  dry_run={args.dry_run}")

    # 1. Trouver ou generer les predictions ML
    pred_path = _find_latest_predictions(goldai_base)

    if pred_path is None:
        if args.run_inference:
            print("\nAucune prediction trouvee. Lancement de l'inference ML...")
            from scripts.run_inference_pipeline import main as run_infer
            sys.argv = ["run_inference_pipeline.py", "--limit", str(args.inference_limit or 0)]
            ret = run_infer()
            if ret != 0:
                print("ERREUR: inference echouee.")
                return 1
            pred_path = _find_latest_predictions(goldai_base)
        else:
            print(
                "\nERREUR: Aucune prediction ML disponible.\n"
                "Lancez d'abord: python scripts/run_inference_pipeline.py --limit 0 --run-id bootstrap_v1\n"
                "Ou utilisez --run-inference pour lancer automatiquement."
            )
            return 1

    print(f"\n  Predictions ML: {pred_path}")
    pred_df = pd.read_parquet(pred_path)
    print(f"  {len(pred_df):,} predictions chargees")
    print(f"  Colonnes: {list(pred_df.columns)}")

    # Distribution des predictions brutes
    pred_dist = pred_df["predicted_sentiment"].value_counts().to_dict()
    print(f"\n  Distribution predictions (toutes confiances): {pred_dist}")

    conf_dist = pred_df["confidence"].describe()
    print(f"  Confiance — min:{conf_dist['min']:.3f} mean:{conf_dist['mean']:.3f} max:{conf_dist['max']:.3f}")

    # 2. Filtrer sur la confiance
    high_conf = pred_df[pred_df["confidence"] >= args.confidence_min].copy()
    low_conf = pred_df[pred_df["confidence"] < args.confidence_min]
    print(f"\n  Predictions confiance >= {args.confidence_min}: {len(high_conf):,} ({len(high_conf)/len(pred_df)*100:.1f}%)")
    print(f"  Predictions confiance <  {args.confidence_min}: {len(low_conf):,} ({len(low_conf)/len(pred_df)*100:.1f}%) -> labels lexicaux conserves")

    high_conf_dist = high_conf["predicted_sentiment"].value_counts().to_dict()
    print(f"  Distribution predictions haute confiance: {high_conf_dist}")

    # 3. Charger gold_ia_labelled (labels lexicaux actuels)
    labelled_path = goldai_base / "ia" / "gold_ia_labelled.parquet"
    if not labelled_path.exists():
        print(f"\nERREUR: {labelled_path} introuvable. Lancez d'abord build_gold_branches.py")
        return 1

    labelled_df = pd.read_parquet(labelled_path)
    print(f"\n  gold_ia_labelled: {len(labelled_df):,} lignes")

    # 4. Fusionner: remplacer le label lexical par le label ML si haute confiance
    # La cle de jointure est 'id' (present dans les deux datasets)
    id_col_pred = "id"
    id_col_label = "id" if "id" in labelled_df.columns else "raw_data_id"

    if id_col_pred not in pred_df.columns or id_col_label not in labelled_df.columns:
        print(f"\nERREUR: impossible de joindre — colonnes ID introuvables.")
        print(f"  predictions: {list(pred_df.columns)}")
        print(f"  labelled:    {list(labelled_df.columns)}")
        return 1

    # Table de substitution: id -> predicted_sentiment normalisé (haute confiance seulement)
    # On normalise pour aligner avec les labels existants (negatif sans accent)
    high_conf = high_conf.copy()
    high_conf["predicted_sentiment"] = high_conf["predicted_sentiment"].apply(normalize_sentiment_label)
    sub_map = high_conf.set_index(id_col_pred)["predicted_sentiment"].to_dict()

    # Copie du labelled_df avec substitution
    new_df = labelled_df.copy()
    new_df["label_source"] = "lexical"  # traçabilite

    # Normaliser l'id de jointure
    new_df["_id_str"] = new_df[id_col_label].astype(str)
    sub_map_str = {str(k): v for k, v in sub_map.items()}

    replaced = new_df["_id_str"].isin(sub_map_str)
    new_df.loc[replaced, "sentiment_label"] = new_df.loc[replaced, "_id_str"].map(sub_map_str)
    new_df.loc[replaced, "sentiment"] = new_df.loc[replaced, "sentiment_label"]
    new_df.loc[replaced, "label_source"] = "ml_model"
    new_df = new_df.drop(columns=["_id_str"])

    n_replaced = replaced.sum()
    n_kept_lexical = (~replaced).sum()
    print(f"\n  Labels remplaces par ML: {n_replaced:,} ({n_replaced/len(new_df)*100:.1f}%)")
    print(f"  Labels lexicaux conserves (faible confiance ou ID absent): {n_kept_lexical:,}")

    new_dist = new_df["sentiment_label"].value_counts().to_dict()
    old_dist = labelled_df["sentiment_label"].value_counts().to_dict() if "sentiment_label" in labelled_df.columns else {}
    print(f"\n  Distribution AVANT (lexical): {old_dist}")
    print(f"  Distribution APRES (ML+lexical): {new_dist}")

    if args.dry_run:
        print("\n  DRY RUN: aucun fichier ecrit.")
        return 0

    # 5. Sauvegarder le nouveau gold_ia_labelled
    out_path = goldai_base / "ia" / "gold_ia_labelled.parquet"
    # Backup de l'ancien
    backup_path = goldai_base / "ia" / "gold_ia_labelled_lexical_backup.parquet"
    import shutil
    if labelled_path.exists() and not backup_path.exists():
        shutil.copy2(labelled_path, backup_path)
        print(f"\n  Backup labels lexicaux: {backup_path.name}")

    new_df.to_parquet(out_path, index=False)
    print(f"  Nouveau gold_ia_labelled: {out_path} ({len(new_df):,} lignes)")

    # 6. Regenerer les splits
    print("\n  Regeneration des splits train/val/test...")
    import subprocess
    ret = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "create_ia_copy.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if ret.returncode != 0:
        print(f"  ERREUR create_ia_copy: {ret.stderr[:300]}")
        return 1
    print(ret.stdout.strip())

    print("\n" + "=" * 60)
    print("BOOTSTRAP TERMINE")
    print("  Prochaine etape: python scripts/finetune_sentiment.py")
    print("  Le modele sera entraine sur des labels ML, pas lexicaux.")
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
