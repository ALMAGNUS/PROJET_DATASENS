#!/usr/bin/env python3
"""
Crée la copie IA pour la prédiction : merged_all_dates → ia/ avec split train/val/test.
Usage: python scripts/create_ia_copy.py [--train 0.8] [--val 0.1] [--test 0.1]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Encodage console Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import pandas as pd

from src.config import get_settings
from src.datasets import normalize_sentiment_label


def _filter_by_topics(df: pd.DataFrame, topics: list[str]) -> pd.DataFrame:
    """Filtre les lignes où topic_1 ou topic_2 est dans la liste des topics autorisés."""
    if "topic_1" not in df.columns and "topic_2" not in df.columns:
        return df
    allowed = {t.strip().lower() for t in topics if t.strip()}
    if not allowed:
        return df
    t1 = df.get("topic_1", pd.Series(dtype=object)).fillna("").astype(str).str.strip().str.lower()
    t2 = df.get("topic_2", pd.Series(dtype=object)).fillna("").astype(str).str.strip().str.lower()
    mask = t1.isin(allowed) | t2.isin(allowed)
    return df[mask].reset_index(drop=True)


def _display_sentiment_distribution(dist: dict[str, int]) -> str:
    """Console-friendly distribution to avoid mojibake on Windows shells."""
    labels = [
        ("positif", int(dist.get("positif", 0))),
        ("neutre", int(dist.get("neutre", 0))),
        ("negatif", int(dist.get("négatif", dist.get("negatif", 0)))),
    ]
    labels = [(k, v) for k, v in labels if v > 0]
    return ", ".join(f"{k}={v:,}" for k, v in labels) if labels else "vide"


def main() -> int:
    parser = argparse.ArgumentParser(description="Copie IA avec split train/val/test")
    parser.add_argument("--train", type=float, default=0.8, help="Fraction train (défaut 0.8)")
    parser.add_argument("--val", type=float, default=0.1, help="Fraction validation (défaut 0.1)")
    parser.add_argument("--test", type=float, default=0.1, help="Fraction test (défaut 0.1)")
    parser.add_argument(
        "--topics",
        type=str,
        default="",
        help="Filtrer par topics (ex: finance,politique). Vide = toutes les données. Améliore la restitution veille.",
    )
    parser.add_argument(
        "--no-temporal",
        action="store_true",
        default=False,
        help="Désactive le split temporel (utilise un shuffle aléatoire, déconseillé en production).",
    )
    args = parser.parse_args()

    tot = args.train + args.val + args.test
    if abs(tot - 1.0) > 0.01:
        print(f"ERREUR: train+val+test doit faire 1.0 (actuel: {tot})")
        return 1

    settings = get_settings()
    goldai_base = Path(settings.goldai_base_path)
    if not goldai_base.is_absolute():
        goldai_base = project_root / goldai_base
    merged_path = goldai_base / "merged_all_dates.parquet"
    labelled_path = goldai_base / "ia" / "gold_ia_labelled.parquet"
    ia_dir = goldai_base / "ia"

    if labelled_path.exists():
        source_path = labelled_path
    else:
        source_path = merged_path

    if not source_path.exists():
        print(
            "ERREUR: dataset source introuvable. Attendu: "
            f"{labelled_path} (recommandé) ou {merged_path}. "
            "Lancez d'abord: python scripts/merge_parquet_goldai.py"
        )
        return 1

    print(f"Chargement dataset IA source: {source_path.name} ...")
    df = pd.read_parquet(source_path)
    print(f"  {len(df):,} lignes chargees")

    if "sentiment_label" in df.columns:
        df["sentiment_label"] = df["sentiment_label"].apply(normalize_sentiment_label)
        df["sentiment"] = df["sentiment_label"]
    elif "sentiment" in df.columns:
        df["sentiment"] = df["sentiment"].apply(normalize_sentiment_label)
    else:
        print(f"ERREUR: Colonne 'sentiment' ou 'sentiment_label' absente dans {source_path}")
        return 1

    # Supprimer les lignes dont le label est vide apres normalisation
    before_drop = len(df)
    df = df[df["sentiment"].notna() & (df["sentiment"] != "")].reset_index(drop=True)
    if len(df) < before_drop:
        print(f"  {before_drop - len(df):,} lignes ignorees (label inconnu apres normalisation)")

    dist = df["sentiment"].value_counts().to_dict()
    print(f"  Distribution sentiment normalisee: {_display_sentiment_distribution(dist)}")

    # Filtre par topics (finance, politique) pour veille ciblee
    if args.topics:
        print(
            "ATTENTION BIAIS: filtrer les topics pour construire le dataset d'entrainement "
            "reduit la generalisation. Recommandation: entrainer sur toutes les donnees, "
            "puis filtrer politique/finance au moment des insights."
        )
        topics_list = [t.strip() for t in args.topics.split(",") if t.strip()]
        if topics_list:
            n_before = len(df)
            df = _filter_by_topics(df, topics_list)
            n_after = len(df)
            print(f"  Filtre topics [{', '.join(topics_list)}]: {n_before:,} -> {n_after:,} lignes")
            if n_after < 100:
                print(f"  ATTENTION: Peu d'exemples ({n_after}). Verifiez que topic_1/topic_2 existent.")

    ia_dir.mkdir(parents=True, exist_ok=True)

    # Copie annotee (meme contenu, pret pour ML)
    annotated_path = ia_dir / "merged_all_dates_annotated.parquet"
    df.to_parquet(annotated_path, index=False)
    print(f"  OK: {annotated_path}")

    # n est calcule ICI, apres tous les filtres (fix bug: n avant filtre = mauvais splits)
    n = len(df)

    # Split temporel par défaut — trie par date pour éviter la fuite de données futures vers le train.
    # --no-temporal : shuffle aléatoire (utile pour debug / tests de surapprentissage).
    date_col = next(
        (c for c in ("published_at", "publication_date", "date", "created_at") if c in df.columns),
        None,
    )
    if not args.no_temporal and date_col is not None:
        df_sorted = df.sort_values(date_col, kind="stable").reset_index(drop=True)
        split_mode = f"temporel (colonne '{date_col}')"
    else:
        df_sorted = df.sample(frac=1, random_state=42).reset_index(drop=True)
        split_mode = "aléatoire (pas de colonne date trouvée)" if date_col is None else "aléatoire (--no-temporal)"
    print(f"  Split mode: {split_mode}")

    n_train = int(n * args.train)
    n_val = int(n * args.val)

    train_df = df_sorted.iloc[:n_train]
    val_df = df_sorted.iloc[n_train : n_train + n_val]
    test_df = df_sorted.iloc[n_train + n_val :]

    train_path = ia_dir / "train.parquet"
    val_path = ia_dir / "val.parquet"
    test_path = ia_dir / "test.parquet"

    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)

    print("\nSplit:")
    print(f"  train: {len(train_df):,} ({args.train*100:.0f}%) -> {train_path}")
    print(f"  val:   {len(val_df):,} ({args.val*100:.0f}%) -> {val_path}")
    print(f"  test:  {len(test_df):,} ({args.test*100:.0f}%) -> {test_path}")
    print("\nCopie IA créée. Prêt pour la prédiction / fine-tuning.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
