#!/usr/bin/env python3
"""DataSens E1+ - MAIN ENTRY (Pipeline SOLID/DRY)"""
import argparse
import io
import os
import sys
import time
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    try:
        # Only wrap if not already wrapped
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != "utf-8":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != "utf-8":
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        # If stdout/stderr don't have buffer attribute, skip wrapping
        pass

sys.path.insert(0, str(Path(__file__).parent / "src"))
# Import E1 isolé depuis package e1
from loguru import logger

from e1.pipeline import E1Pipeline
from logging_config import setup_logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DataSens E1 pipeline")
    parser.add_argument("--quiet", action="store_true", help="Disable console output")
    parser.add_argument(
        "--inject-csv",
        type=str,
        metavar="PATH",
        help="Injecter un CSV ponctuellement (parcourt le pipeline complet comme une source)",
    )
    parser.add_argument(
        "--source-name",
        type=str,
        default="csv_inject",
        help="Nom de la source pour --inject-csv (défaut: csv_inject)",
    )
    parser.add_argument(
        "--keep-metrics",
        action="store_true",
        help="Garder le processus vivant après le pipeline pour exposer /metrics (Prometheus)",
    )
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting E1 pipeline")
    pipeline = E1Pipeline(quiet=args.quiet)
    pipeline.run(inject_csv_path=args.inject_csv, inject_source_name=args.source_name)

    # Option : garder le processus vivant pour que Prometheus puisse scraper les métriques
    if args.keep_metrics or os.getenv("METRICS_KEEP_ALIVE") == "1":
        port = int(os.getenv("METRICS_PORT", "8000"))
        logger.info("Pipeline terminé. Métriques exposées sur :%d — Ctrl+C pour quitter.", port)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Arrêt.")
