#!/usr/bin/env python3
"""Injecte un CSV à la demande dans le pipeline E1.

Usage:
    python scripts/inject_csv.py chemin/vers/fichier.csv [--source-name csv_inject]

Colonnes CSV attendues: title, content (obligatoires), url, published_at (optionnels).
Tag + sentiment appliqués automatiquement.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.e1.core import Article, ContentTransformer
from src.e1.repository import Repository
from src.e1.tagger import TopicTagger
from src.e1.analyzer import SentimentAnalyzer


def parse_csv(path: Path, source_name: str) -> list[Article]:
    """Parse un CSV et retourne une liste d'Article."""
    articles = []
    with open(path, encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("title") or "").strip()
            content = (row.get("content") or row.get("text") or "").strip()
            url = row.get("url") or "https://inject.datasens.fr"
            published_at = row.get("published_at") or ""
            if not title:
                continue
            if not content:
                content = title
            title_clean = title[:500].strip()
            content_clean = content[:2000].strip()
            if len(title_clean) < 5 or len(content_clean) < 20:
                continue
            a = Article(
                title=title_clean,
                content=content_clean,
                url=url,
                source_name=source_name,
                published_at=published_at or None,
            )
            a = ContentTransformer.transform(a)
            if a.is_valid():
                articles.append(a)
    return articles


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Injecte un CSV ponctuellement dans le pipeline E1 (tag + sentiment inclus)"
    )
    parser.add_argument("csv_path", type=str, help="Chemin vers le fichier CSV")
    parser.add_argument(
        "--source-name",
        type=str,
        default="csv_inject",
        help="Nom de la source (défaut: csv_inject)",
    )
    parser.add_argument("--db-path", type=str, default=None)
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"ERREUR: Fichier introuvable: {csv_path}")
        sys.exit(1)

    db_path = args.db_path or os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    articles = parse_csv(csv_path, args.source_name)
    if not articles:
        print("Aucun article valide dans le CSV (colonnes: title, content)")
        sys.exit(1)

    repo = Repository(str(db_path))
    source_id = repo.get_source_id(args.source_name)
    if source_id is None:
        repo.cursor.execute(
            """
            INSERT INTO source (name, source_type, url, sync_frequency, active, is_synthetic, created_at)
            VALUES (?, 'csv', ?, 'DAILY', 1, 1, datetime('now'))
            """,
            (args.source_name, str(csv_path)),
        )
        repo.conn.commit()
        source_id = repo.get_source_id(args.source_name)

    tagger = TopicTagger(str(db_path))
    analyzer = SentimentAnalyzer(str(db_path))
    loaded, skipped = 0, 0

    for a in articles:
        raw_id = repo.load_article_with_id(a, source_id)
        if raw_id:
            loaded += 1
            tagger.tag(raw_id, a.title, a.content)
            analyzer.save(raw_id, a.title, a.content)
        else:
            skipped += 1

    repo.log_sync(source_id, loaded, "OK", f"Inject CSV: {csv_path.name}")
    print(f"[Inject CSV] {loaded} articles importés (tag + sentiment), {skipped} doublons ignorés")


if __name__ == "__main__":
    main()
