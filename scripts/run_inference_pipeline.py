#!/usr/bin/env python3
"""
Run inference branch (GOLD_APP_INPUT -> GOLD_APP_PREDICTIONS).

Fonctionnalités :
  --limit N          Nombre max d'articles (défaut 500, 0 = tout)
  --checkpoint-every N  Sauvegarde partielle tous les N articles (défaut 1000)
  --resume           Reprend depuis le dernier checkpoint si disponible
  --persist-model-output  Persiste aussi dans SQLite model_output (entiers seulement)
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Windows encoding fix
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from src.config import get_settings
from src.ml.inference import (  # noqa: E402
    run_sentiment_inference,
    write_inference_to_model_output,
    write_predictions_parquet,
)

settings = get_settings()


def _checkpoint_path(run_id: str) -> Path:
    root = Path(settings.goldai_base_path)
    if not root.is_absolute():
        root = project_root / root
    return root / "predictions" / f"_checkpoint_{run_id}.json"


def _load_checkpoint(run_id: str) -> list[dict]:
    p = _checkpoint_path(run_id)
    if not p.exists():
        return []
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Reprise checkpoint: {len(data):,} resultats deja sauvegardes ({p.name})")
        return data
    except Exception as e:
        print(f"  WARN: checkpoint illisible ({e}), reprise a zero.")
        return []


def _save_checkpoint(run_id: str, results: list[dict]) -> None:
    p = _checkpoint_path(run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False)
        tmp.replace(p)
        print(f"\n  [CHECKPOINT] {len(results):,} resultats sauvegardes -> {p.name}")
    except Exception as e:
        print(f"\n  WARN checkpoint write failed: {e}")


def _delete_checkpoint(run_id: str) -> None:
    p = _checkpoint_path(run_id)
    try:
        p.unlink(missing_ok=True)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline inference: GOLD_APP_INPUT -> GOLD_APP_PREDICTIONS"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Nombre max d'articles (0 = tout, defaut 500)",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1000,
        help="Sauvegarde partielle tous les N articles (defaut 1000)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprend depuis le dernier checkpoint si disponible",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="ID de run stable pour checkpoint/reprise (genere automatiquement si absent)",
    )
    parser.add_argument(
        "--persist-model-output",
        action="store_true",
        help="Persiste aussi dans SQLite model_output (lignes avec ID entier seulement)",
    )
    args = parser.parse_args()

    limit = args.limit if args.limit > 0 else None
    effective_limit = limit or 99_999_999

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    print(f"\n{'='*60}")
    print(f"INFERENCE PIPELINE  run_id={run_id}")
    print(f"{'='*60}")
    print(f"  limit={effective_limit:,}  checkpoint_every={args.checkpoint_every:,}  resume={args.resume}")

    # Checkpoint / reprise
    already_done: list[dict] = []
    if args.resume:
        already_done = _load_checkpoint(run_id)

    already_ids: set[str] = {str(r["id"]) for r in already_done}
    skip_n = len(already_done)

    # Ajuster le limit pour sauter les articles déjà traités
    fetch_limit = effective_limit + skip_n if limit else None

    # Résultats accumulés (checkpoint existant + nouveaux)
    all_results: list[dict] = list(already_done)

    # Handler Ctrl+C propre : sauvegarde avant de quitter
    interrupted = False

    def _on_sigint(sig, frame):
        nonlocal interrupted
        interrupted = True
        print(f"\n\n  Interruption detectee. Sauvegarde checkpoint ({len(all_results):,} resultats)...")
        _save_checkpoint(run_id, all_results)
        print(f"  Pour reprendre: python scripts/run_inference_pipeline.py --run-id {run_id} --resume --limit {effective_limit}")
        sys.exit(130)

    signal.signal(signal.SIGINT, _on_sigint)

    def _checkpoint_cb(partial: list[dict]) -> None:
        _save_checkpoint(run_id, partial)

    print(f"\nInference sur GOLD_APP_INPUT...")
    if skip_n > 0:
        print(f"  {skip_n:,} articles deja traites (checkpoint), inférence depuis l'article {skip_n+1}.")

    try:
        new_results = run_sentiment_inference(
            limit=fetch_limit,
            use_merged=True,
            checkpoint_callback=_checkpoint_cb,
            checkpoint_every=args.checkpoint_every,
        )
    except KeyboardInterrupt:
        # signal handler prend le relais, mais au cas où
        print(f"\n  Sauvegarde checkpoint urgence ({len(all_results):,} resultats)...")
        _save_checkpoint(run_id, all_results)
        return 130

    # Filtrer les articles déjà traités si reprise partielle
    if skip_n > 0:
        new_results = [r for r in new_results if str(r.get("id", "")) not in already_ids]

    all_results = already_done + new_results
    print(f"\n  {len(new_results):,} nouvelles predictions  |  total run: {len(all_results):,}")

    if not all_results:
        print("  Aucune ligne a traiter.")
        return 0

    # Ecriture predictions.parquet final
    out_path = write_predictions_parquet(all_results, inference_run_id=run_id)
    print(f"  GOLD_APP_PREDICTIONS: {out_path}")

    if args.persist_model_output:
        n = write_inference_to_model_output(all_results)
        print(f"  SQLite model_output: {n:,} lignes persistees")

    # Nettoyage checkpoint si succès complet
    _delete_checkpoint(run_id)
    print(f"\n  Run termine avec succes. Checkpoint supprime.")
    print(f"{'='*60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
