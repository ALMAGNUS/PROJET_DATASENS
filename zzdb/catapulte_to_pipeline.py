#!/usr/bin/env python3
"""
Catapulte ZZDB -> Pipeline principal (SQLite).

Objectif:
- Scanner les fichiers ZZDB (CSV/JSON)
- Convertir en Article
- Injecter en SQLite via Repository E1

Usage (PowerShell):
    & ".\\.venv\\Scripts\\python.exe" "zzdb\\catapulte_to_pipeline.py"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Bootstrap imports (E1 core/repository)
# ---------------------------------------------------------------------------


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.e1.core import Article, ContentTransformer  # noqa: E402
from src.e1.repository import Repository  # noqa: E402


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


@dataclass
class ImportStats:
    scanned_files: int = 0
    parsed_rows: int = 0
    imported_rows: int = 0
    skipped_rows: int = 0
    errors: int = 0


@dataclass
class SourceConfig:
    name: str = "zzdb_synthetic"
    acquisition_type: str = "mongodb"
    url: str = "mongodb://localhost:27017/zzdb"
    active: bool = True
    is_synthetic: int = 1


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


class ZzdbFileScanner:
    """Scan ZZDB folder for supported files."""

    def __init__(self, root_dir: Path, extensions: set[str]) -> None:
        self.root_dir = root_dir
        self.extensions = {ext.lower() for ext in extensions}

    def scan(self) -> list[Path]:
        files: list[Path] = []
        for path in self.root_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in self.extensions:
                files.append(path)
        return sorted(files)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


class ZzdbRowParser:
    """Normalize a CSV/JSON row into an Article."""

    def __init__(self, source_name: str) -> None:
        self.source_name = source_name

    def to_article(self, row: dict[str, Any]) -> Article | None:
        title = (row.get("title") or "").strip()
        content = (row.get("content") or row.get("text") or "").strip()
        url = row.get("url") or None
        published_at = row.get("published_at") or None

        if not title:
            return None
        if not content:
            content = title

        article = Article(
            title=title[:500],
            content=content[:5000],
            url=url,
            source_name=self.source_name,
            published_at=published_at,
        )
        article = ContentTransformer.transform(article)
        return article if article.is_valid() else None


class CsvReader:
    """CSV reader for ZZDB files."""

    def read(self, path: Path) -> Iterable[dict[str, Any]]:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield row


class JsonReader:
    """JSON reader for ZZDB files (list of dicts)."""

    def read(self, path: Path) -> Iterable[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    yield row


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------


class ZzdbCatapult:
    """Safe importer of ZZDB files into SQLite."""

    def __init__(
        self,
        db_path: Path,
        source_config: SourceConfig,
        dry_run: bool = False,
        limit: int | None = None,
    ) -> None:
        self.db_path = db_path
        self.source_config = source_config
        self.dry_run = dry_run
        self.limit = limit
        self.stats = ImportStats()

        self.repo = Repository(str(self.db_path))
        self.source_id = self._ensure_source()

        self.csv_reader = CsvReader()
        self.json_reader = JsonReader()
        self.row_parser = ZzdbRowParser(self.source_config.name)

    def _ensure_source(self) -> int:
        source_id = self.repo.get_source_id(self.source_config.name)
        if source_id is not None:
            return source_id

        # Safe insert if missing in DB
        cursor = self.repo.cursor
        cursor.execute(
            """
            INSERT INTO source (name, source_type, url, sync_frequency, active, is_synthetic, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                self.source_config.name,
                self.source_config.acquisition_type,
                self.source_config.url,
                "DAILY",
                1 if self.source_config.active else 0,
                self.source_config.is_synthetic,
            ),
        )
        self.repo.conn.commit()
        return int(self.repo.get_source_id(self.source_config.name) or 0)

    def import_files(self, files: list[Path]) -> ImportStats:
        for path in files:
            self.stats.scanned_files += 1
            self._import_file(path)

        # Log sync at the end (if not dry-run)
        if not self.dry_run and self.source_id:
            self.repo.log_sync(self.source_id, self.stats.imported_rows, "OK", "ZZDB catapult import")
        return self.stats

    def _import_file(self, path: Path) -> None:
        if path.suffix.lower() == ".csv":
            rows = self.csv_reader.read(path)
        elif path.suffix.lower() == ".json":
            rows = self.json_reader.read(path)
        else:
            return

        for row in rows:
            if self.limit is not None and self.stats.parsed_rows >= self.limit:
                return

            self.stats.parsed_rows += 1
            article = self.row_parser.to_article(row)
            if article is None:
                self.stats.skipped_rows += 1
                continue

            if self.dry_run:
                self.stats.imported_rows += 1
                continue

            raw_id = self.repo.load_article_with_id(article, self.source_id)
            if raw_id is None:
                self.stats.skipped_rows += 1
            else:
                self.stats.imported_rows += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZZDB -> SQLite catapult (safe)")
    parser.add_argument("--db-path", type=str, default=str(Path.home() / "datasens_project" / "datasens.db"))
    parser.add_argument("--zzdb-dir", type=str, default=str(Path(__file__).parent))
    parser.add_argument("--extensions", type=str, default=".csv,.json")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, do not insert")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to import")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    db_path = Path(args.db_path)
    zzdb_dir = Path(args.zzdb_dir)
    extensions = {ext.strip() for ext in args.extensions.split(",") if ext.strip()}

    scanner = ZzdbFileScanner(zzdb_dir, extensions)
    files = scanner.scan()

    if not files:
        print(f"[ZZDB] Aucun fichier trouvé dans: {zzdb_dir}")
        return

    catapult = ZzdbCatapult(
        db_path=db_path,
        source_config=SourceConfig(),
        dry_run=args.dry_run,
        limit=args.limit,
    )
    stats = catapult.import_files(files)

    print("\n[ZZDB] Catapulte terminée")
    print(f"- Fichiers scannés : {stats.scanned_files}")
    print(f"- Lignes parsées   : {stats.parsed_rows}")
    print(f"- Importées        : {stats.imported_rows}")
    print(f"- Ignorées         : {stats.skipped_rows}")
    print(f"- Erreurs          : {stats.errors}")


if __name__ == "__main__":
    main()
