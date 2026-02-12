#!/usr/bin/env python3
"""Liste les fichiers Parquet stockés dans MongoDB GridFS."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings


def main():
    settings = get_settings()
    mongo_uri = getattr(settings, "mongo_uri", "mongodb://localhost:27017")
    mongo_db = getattr(settings, "mongo_db", "datasens")
    bucket = getattr(settings, "mongo_gridfs_bucket", "parquet_fs")
    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        coll = client[mongo_db][f"{bucket}.files"]
        count = coll.count_documents({})
        print(f"Fichiers Parquet dans GridFS: {count}")
        for f in coll.find({}, {"filename": 1, "metadata": 1, "length": 1}):
            fn = f.get("filename", "?")
            ln = f.get("length", 0)
            meta = f.get("metadata", {})
            print(f"  - {fn} ({ln} octets) {meta.get('logical_name', '')}")
        client.close()
    except Exception as e:
        print(f"Erreur: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
