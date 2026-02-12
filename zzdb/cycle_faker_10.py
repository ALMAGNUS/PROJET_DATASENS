#!/usr/bin/env python3
"""
Cycle ZZDB -> Pipeline (10 lignes Faker).

Etapes:
1) Genere 10 articles Faker (CSV)
2) Envoie dans SQLite via catapulte_to_pipeline.py
3) Verifie l'insertion dans la collecte du jour
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from faker import Faker
except Exception as exc:  # pragma: no cover - explicit message for user
    raise SystemExit(
        "Faker n'est pas installe. Lance: python -m pip install faker"
    ) from exc

from zzdb.catapulte_to_pipeline import ZzdbCatapult, SourceConfig  # noqa: E402
import sqlite3  # noqa: E402


@dataclass
class CycleConfig:
    count: int = 10
    output_csv: Path = Path(__file__).parent / "export" / "zzdb_faker_cycle.csv"
    db_path: Path = Path.home() / "datasens_project" / "datasens.db"
    title_prefix: str = "faker_cycle"


class FakerArticleGenerator:
    """Generate faker articles with stable schema."""

    def __init__(self, count: int, title_prefix: str) -> None:
        self.count = count
        self.title_prefix = title_prefix
        self.faker = Faker("fr_FR")

    def generate(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i in range(self.count):
            title = f"{self.title_prefix}_{stamp}_{i:02d} - {self.faker.sentence(nb_words=6)}"
            content = self.faker.paragraph(nb_sentences=4)
            row = {
                "title": title[:500],
                "content": content[:5000],
                "url": self.faker.url(),
                "published_at": datetime.now().isoformat(),
            }
            rows.append(row)
        return rows


class CsvExporter:
    """Write rows to CSV (compatible catapulte)."""

    def write(self, path: Path, rows: Iterable[dict[str, str]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["title", "content", "url", "published_at"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


class SqliteVerifier:
    """Verify that new rows exist in today's collection."""

    def __init__(self, db_path: Path, title_prefix: str) -> None:
        self.db_path = db_path
        self.title_prefix = title_prefix

    def count_today(self) -> int:
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            """
            SELECT COUNT(*)
            FROM raw_data r
            JOIN source s ON r.source_id = s.source_id
            WHERE s.name = 'zzdb_synthetic'
              AND r.title LIKE ?
              AND r.collected_at LIKE ?
            """,
            (f"{self.title_prefix}%", f"{today}%"),
        )
        count = cur.fetchone()[0]
        conn.close()
        return count


class CycleRunner:
    """Run a full faker -> catapult -> verify cycle."""

    def __init__(self, config: CycleConfig) -> None:
        self.config = config
        self.generator = FakerArticleGenerator(config.count, config.title_prefix)
        self.exporter = CsvExporter()
        self.catapult = ZzdbCatapult(db_path=config.db_path, source_config=SourceConfig())
        self.verifier = SqliteVerifier(config.db_path, config.title_prefix)

    def run(self) -> None:
        rows = self.generator.generate()
        self.exporter.write(self.config.output_csv, rows)
        self.catapult.import_files([self.config.output_csv])
        inserted_today = self.verifier.count_today()

        print("\n[ZZDB] Cycle termine")
        print(f"- CSV genere : {self.config.output_csv}")
        print(f"- Lignes generees : {len(rows)}")
        print(f"- Lignes detectees aujourd'hui : {inserted_today}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cycle Faker -> ZZDB -> SQLite")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--db-path", type=str, default=str(Path.home() / "datasens_project" / "datasens.db"))
    parser.add_argument("--output-csv", type=str, default=str(Path(__file__).parent / "export" / "zzdb_faker_cycle.csv"))
    parser.add_argument("--title-prefix", type=str, default="faker_cycle")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = CycleConfig(
        count=args.count,
        db_path=Path(args.db_path),
        output_csv=Path(args.output_csv),
        title_prefix=args.title_prefix,
    )
    CycleRunner(config).run()


if __name__ == "__main__":
    main()
