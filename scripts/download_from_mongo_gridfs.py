#!/usr/bin/env python3
"""
Extraction GridFS -> fichiers locaux.

Usages:
  - Lister:
      python scripts/download_from_mongo_gridfs.py --list
  - Télécharger un logical_name exact:
      python scripts/download_from_mongo_gridfs.py --logical-name goldai_ia_train --output-dir exports/mongo
  - Télécharger par préfixe (batch):
      python scripts/download_from_mongo_gridfs.py --prefix goldai_ia_ --output-dir exports/mongo
  - Télécharger seulement les derniers fichiers d'un type:
      python scripts/download_from_mongo_gridfs.py --prefix gold_articles_ --limit 3 --output-dir exports/mongo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import gridfs
from pymongo import MongoClient

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.config import get_settings


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Download files from MongoDB GridFS")
    p.add_argument("--list", action="store_true", help="List files only (no download)")
    p.add_argument("--logical-name", type=str, default="", help="Exact logical_name filter")
    p.add_argument("--prefix", type=str, default="", help="Prefix filter on logical_name")
    p.add_argument("--output-dir", type=str, default="exports/mongo_gridfs", help="Destination directory")
    p.add_argument("--limit", type=int, default=0, help="Max files to download/list (0 = no limit)")
    return p


def main() -> int:
    args = _build_parser().parse_args()
    settings = get_settings()
    client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    try:
        db = client[settings.mongo_db]
        bucket = settings.mongo_gridfs_bucket
        files_coll = db[f"{bucket}.files"]
        fs = gridfs.GridFS(db, collection=bucket)

        query: dict = {}
        if args.logical_name:
            query["metadata.logical_name"] = args.logical_name
        elif args.prefix:
            query["metadata.logical_name"] = {"$regex": f"^{args.prefix}"}

        cursor = files_coll.find(
            query,
            {"filename": 1, "metadata": 1, "length": 1, "uploadDate": 1},
        ).sort("uploadDate", -1)
        if args.limit and args.limit > 0:
            cursor = cursor.limit(args.limit)

        docs = list(cursor)
        if not docs:
            print("Aucun fichier trouvé avec ces filtres.")
            return 0

        if args.list:
            print(f"Fichiers trouvés: {len(docs)}")
            for d in docs:
                meta = d.get("metadata", {}) or {}
                logical = meta.get("logical_name", "")
                up = d.get("uploadDate")
                size_mb = (d.get("length", 0) or 0) / 1024 / 1024
                print(f"- {logical:<45} {size_mb:8.2f} MB  uploaded={up}")
            return 0

        out_dir = (project_root / args.output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        downloaded = 0
        for d in docs:
            file_id = d["_id"]
            meta = d.get("metadata", {}) or {}
            logical = meta.get("logical_name") or d.get("filename") or str(file_id)
            safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in logical)
            target = out_dir / f"{safe_name}.parquet"
            gf = fs.get(file_id)
            target.write_bytes(gf.read())
            downloaded += 1
            print(f"DOWNLOADED {logical} -> {target}")

        print(f"Terminé. {downloaded} fichier(s) exporté(s) dans {out_dir}")
        return 0
    except Exception as exc:
        print(f"Erreur: {exc}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
