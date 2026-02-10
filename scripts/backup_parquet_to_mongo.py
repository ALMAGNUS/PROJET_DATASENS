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
    try:
        latest_gold = _latest_partition(gold_base, date_re)
        if latest_gold:
            r = store.store_file(
                latest_gold,
                metadata={
                    "logical_name": "gold_articles",
                    "partition_date": latest_gold.parent.name.replace("date=", ""),
                    "source": "backup_manual",
                },
            )
            print(f"GOLD: {r['status']} {latest_gold}")
            if r["status"] == "stored":
                stored += 1

        if goldai_merged.exists():
            r = store.store_file(
                goldai_merged,
                metadata={
                    "logical_name": "goldai_merged",
                    "partition_date": date.today().isoformat(),
                    "source": "backup_manual",
                },
            )
            print(f"GoldAI merged: {r['status']} {goldai_merged}")
            if r["status"] == "stored":
                stored += 1

        if goldai_ia.exists():
            r = store.store_file(
                goldai_ia,
                metadata={
                    "logical_name": "goldai_annotated",
                    "partition_date": date.today().isoformat(),
                    "source": "backup_manual",
                },
            )
            print(f"GoldAI IA: {r['status']} {goldai_ia}")
            if r["status"] == "stored":
                stored += 1
    except Exception as e:
        print(f"Erreur: {e}")
        return 1
    finally:
        store.close()

    print(f"Backup terminé. Fichiers nouveaux stockés: {stored}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
