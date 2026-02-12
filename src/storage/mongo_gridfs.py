"""
MongoDB GridFS storage for Parquet files.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import gridfs
from pymongo import MongoClient


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class MongoGridFSStore:
    mongo_uri: str
    db_name: str
    bucket: str

    def __post_init__(self) -> None:
        self.client = MongoClient(
            self.mongo_uri,
            serverSelectionTimeoutMS=5000,
        )
        self.db = self.client[self.db_name]
        self.fs = gridfs.GridFS(self.db, collection=self.bucket)

    def close(self) -> None:
        self.client.close()

    def _find_existing(self, sha256: str, logical_name: str | None) -> dict | None:
        query = {"metadata.sha256": sha256}
        if logical_name:
            query["metadata.logical_name"] = logical_name
        return self.db[f"{self.bucket}.files"].find_one(query, {"_id": 1})

    def store_file(self, file_path: Path, metadata: dict) -> dict:
        file_path = Path(file_path)
        if not file_path.exists():
            return {"status": "missing", "file_id": None}

        sha256 = _sha256_file(file_path)
        logical_name = metadata.get("logical_name")
        existing = self._find_existing(sha256, logical_name)
        if existing:
            return {"status": "skipped", "file_id": str(existing["_id"])}

        enriched = dict(metadata)
        enriched.update(
            {
                "sha256": sha256,
                "size_bytes": file_path.stat().st_size,
                "stored_at": datetime.utcnow().isoformat(),
            }
        )
        with file_path.open("rb") as handle:
            file_id = self.fs.put(handle, filename=file_path.name, metadata=enriched)
        return {"status": "stored", "file_id": str(file_id)}
