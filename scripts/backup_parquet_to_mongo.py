#!/usr/bin/env python3
"""
Backup manuel Parquet → MongoDB GridFS (sauvegarde long terme).
À lancer depuis la racine du projet.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Encodage console Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from src.config import get_settings
from src.storage.mongo_gridfs import MongoGridFSStore


def _latest_partition(base: Path, pattern: re.Pattern) -> Path | None:
    if not base.exists():
        return None
    candidates: list[tuple[date, Path]] = []
    for d in base.iterdir():
        if not d.is_dir():
            continue
        m = pattern.match(d.name)
        if not m:
            continue
        try:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        parquet = d / "articles.parquet"
        if not parquet.exists():
            parquet = d / "goldai.parquet"
        if parquet.exists():
            candidates.append((dt, parquet))
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[0])[1]


def _all_partitions(base: Path, pattern: re.Pattern) -> list[tuple[date, Path]]:
    if not base.exists():
        return []
    out: list[tuple[date, Path]] = []
    for d in base.iterdir():
        if not d.is_dir():
            continue
        m = pattern.match(d.name)
        if not m:
            continue
        try:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        parquet = d / "articles.parquet"
        if not parquet.exists():
            parquet = d / "goldai.parquet"
        if parquet.exists():
            out.append((dt, parquet))
    return sorted(out, key=lambda x: x[0])


def main() -> int:
    settings = get_settings()
    if not settings.mongo_store_parquet:
        print("MONGO_STORE_PARQUET non activé. Définir MONGO_STORE_PARQUET=true pour ce backup.")
        return 1

    print("Connexion MongoDB (timeout 5s)...")
    gold_base = project_root / "data" / "gold"
    goldai_base = project_root / "data" / "goldai"
    goldai_merged = goldai_base / "merged_all_dates.parquet"
    goldai_ia = goldai_base / "ia" / "merged_all_dates_annotated.parquet"

    store = MongoGridFSStore(
        mongo_uri=settings.mongo_uri,
        db_name=settings.mongo_db,
        bucket=settings.mongo_gridfs_bucket,
    )
    date_re = re.compile(r"^date=(\d{4}-\d{2}-\d{2})$")
    stored = 0
    skipped = 0
    errors = 0

    def _backup(path: Path, logical_name: str, extra_meta: dict | None = None) -> None:
        nonlocal stored, skipped, errors
        if not path.exists():
            print(f"  -- ABSENT  {path.name}")
            return
        meta: dict = {
            "logical_name": logical_name,
            "partition_date": date.today().isoformat(),
            "source": "backup_manual",
            "size_mb": round(path.stat().st_size / 1024 / 1024, 2),
        }
        if extra_meta:
            meta.update(extra_meta)
        try:
            r = store.store_file(path, metadata=meta)
            status = r["status"]
            mb = meta["size_mb"]
            print(f"  {status.upper():<8} {logical_name:<35} {path.name}  ({mb} MB)")
            if status == "stored":
                stored += 1
            else:
                skipped += 1
        except Exception as exc:
            print(f"  ERREUR   {logical_name}: {exc!s}")
            errors += 1

    try:
        print("\n--- Parquets GOLD & GoldAI ---")

        # GOLD partitionné: historique complet (une entrée par date)
        all_gold = _all_partitions(gold_base, date_re)
        if all_gold:
            for dt, parquet in all_gold:
                partition_date = dt.isoformat()
                _backup(
                    parquet,
                    f"gold_articles_{partition_date}",
                    {
                        "partition_date": partition_date,
                        "dataset_family": "gold_daily",
                    },
                )
        else:
            print("  -- ABSENT  Aucun GOLD partitionné trouvé")

        # GoldAI fusionné
        _backup(goldai_merged, "goldai_merged")

        # Copie IA annotée + splits train/val/test
        ia_dir = goldai_base / "ia"
        _backup(
            ia_dir / "merged_all_dates_annotated.parquet",
            "goldai_ia_annotated",
            {"dataset_family": "ia_training"},
        )
        _backup(
            ia_dir / "gold_ia_labelled.parquet",
            "goldai_ia_labelled",
            {"dataset_family": "ia_training"},
        )
        for split in ["train", "val", "test"]:
            _backup(
                ia_dir / f"{split}.parquet",
                f"goldai_ia_{split}",
                {"dataset_family": "ia_training", "split": split},
            )
        _backup(
            goldai_base / "app" / "gold_app_input.parquet",
            "goldai_app_input",
            {"dataset_family": "ia_inference_input"},
        )

        # Sorties inférence (par run) pour audit long terme
        pred_base = goldai_base / "predictions"
        if pred_base.exists():
            pred_files = sorted(
                pred_base.glob("date=*/run=*/predictions.parquet"),
                key=lambda p: p.stat().st_mtime,
            )
            for p in pred_files:
                d = p.parent.parent.name.replace("date=", "")
                run = p.parent.name.replace("run=", "")
                _backup(
                    p,
                    f"goldai_app_predictions_{d}_{run}",
                    {
                        "dataset_family": "ia_inference_output",
                        "partition_date": d,
                        "inference_run_id": run,
                    },
                )

        print("\n--- Modèle IA entraîné ---")

        # Modèle fine-tuné (model.safetensors + config + tokenizer)
        models_dir = project_root / "models"
        for model_dir in sorted(models_dir.iterdir()) if models_dir.exists() else []:
            if not model_dir.is_dir():
                continue
            model_name = model_dir.name
            # Fichiers essentiels du modèle (pas le checkpoint intermédiaire ni optimizer)
            for fname in ["model.safetensors", "config.json", "tokenizer.json",
                          "tokenizer_config.json", "sentencepiece.bpe.model",
                          "special_tokens_map.json"]:
                fp = model_dir / fname
                _backup(fp, f"model_{model_name}_{fname}", {
                    "model_name": model_name,
                    "file_type": "model_artifact",
                })

    except Exception as e:
        print(f"Erreur générale: {e}")
        return 1
    finally:
        store.close()

    print(f"\nBackup terminé — stockés: {stored}  |  déjà présents: {skipped}  |  erreurs: {errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
