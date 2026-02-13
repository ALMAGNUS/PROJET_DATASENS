#!/usr/bin/env python3
"""Serveur métriques E1 standalone — expose /metrics en continu pour Prometheus.

Usage:
    python scripts/run_e1_metrics.py

Lance un serveur HTTP sur le port METRICS_PORT (défaut 8000) exposant les
métriques E1. Les gauges (articles_in_database, etc.) sont mises à jour
périodiquement depuis la base SQLite.

Alternative : lancer `python main.py --keep-metrics` pour garder le processus
vivant après une exécution du pipeline (métriques à jour avec le dernier run).
"""
import os
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.metrics import (
    articles_enriched,
    articles_in_database,
    enrichment_rate,
    start_metrics_server,
    update_database_stats,
)


def _fetch_db_stats():
    """Lit total articles et enrichis (topics + sentiment) depuis datasens.db."""
    import sqlite3

    db_path = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
    if not Path(db_path).exists():
        return 0, 0
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM raw_data")
        total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT COUNT(DISTINCT r.raw_data_id) FROM raw_data r
            WHERE EXISTS (SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id)
            AND EXISTS (SELECT 1 FROM model_output mo
                        WHERE mo.raw_data_id = r.raw_data_id
                        AND mo.model_name = 'sentiment_keyword')
            """
        )
        enriched = cur.fetchone()[0] or 0
        conn.close()
        return total, enriched
    except Exception:
        return 0, 0


def main():
    port = int(os.getenv("METRICS_PORT", "8000"))
    interval = int(os.getenv("METRICS_UPDATE_INTERVAL", "30"))

    start_metrics_server(port)

    print(f"Métriques E1 sur http://localhost:{port}/metrics — mise à jour toutes les {interval}s")
    print("Ctrl+C pour quitter.")

    while True:
        total, enriched = _fetch_db_stats()
        update_database_stats(total, enriched)
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt.")
        sys.exit(0)
