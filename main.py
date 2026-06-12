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

# Répertoire projet = CWD pour chemins relatifs (data/, output/ Botasaurus, etc.)
_PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(_PROJECT_ROOT)
(_PROJECT_ROOT / "output").mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(_PROJECT_ROOT / "src"))
# Import E1 isolé depuis package e1
from e1.pipeline import E1Pipeline
from logging_config import setup_logging
from loguru import logger

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

    # Best-effort : rafraîchir les gauges Prometheus de drift via l'API E2.
    # Si l'API est down ou DRIFT_REFRESH_PASSWORD absent du .env, le script log et sort en 0
    # (jamais bloquant pour le pipeline). Cf. RUNBOOK § 11.4.
    if os.getenv("DRIFT_REFRESH_PASSWORD"):
        import subprocess

        refresh_script = _PROJECT_ROOT / "scripts" / "refresh_drift_metrics.py"
        try:
            result = subprocess.run(
                [sys.executable, str(refresh_script), "--quiet"],
                timeout=20,
                check=False,
                capture_output=True,
                text=True,
                cwd=str(_PROJECT_ROOT),
            )
            if result.returncode == 0:
                logger.info("Drift gauges Prometheus rafraîchies (API E2)")
            else:
                logger.warning("Drift refresh skipped (API down ou auth KO)")
        except subprocess.TimeoutExpired:
            logger.warning("Drift refresh timeout — gauges non rafraîchies")
        except Exception as e:
            logger.warning(f"Drift refresh exception : {type(e).__name__}: {e}")
    else:
        logger.debug(
            "DRIFT_REFRESH_PASSWORD absent : drift gauges non rafraîchies (cf. RUNBOOK § 11.4)"
        )

    if args.keep_metrics or os.getenv("METRICS_KEEP_ALIVE") == "1":
        port = int(os.getenv("METRICS_PORT", "8000"))
        logger.info("Pipeline terminé. Métriques exposées sur :%d — Ctrl+C pour quitter.", port)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            logger.info("Arrêt.")
