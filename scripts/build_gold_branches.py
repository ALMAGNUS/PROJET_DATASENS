#!/usr/bin/env python3
"""
Build separated GoldAI branches:
- data/goldai/app/gold_app_input.parquet (inference, unlabeled)
- data/goldai/ia/gold_ia_labelled.parquet (training, labeled)
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Encodage console Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import pandas as pd

from src.config import get_settings
from src.datasets import build_gold_app_input, build_gold_ia_labelled


def main() -> int:
    settings = get_settings()
    goldai_base = Path(settings.goldai_base_path)
    if not goldai_base.is_absolute():
        goldai_base = project_root / goldai_base

    merged_path = goldai_base / "merged_all_dates.parquet"
    if not merged_path.exists():
        print(f"ERREUR: {merged_path} introuvable. Lancez: python scripts/merge_parquet_goldai.py")
        return 1

    df = pd.read_parquet(merged_path)
    if df.empty:
        print("ERREUR: merged_all_dates.parquet est vide.")
        return 1

    app_df = build_gold_app_input(df)
    labelled_df = build_gold_ia_labelled(df)

    app_dir = goldai_base / "app"
    ia_dir = goldai_base / "ia"
    app_dir.mkdir(parents=True, exist_ok=True)
    ia_dir.mkdir(parents=True, exist_ok=True)

    app_path = app_dir / "gold_app_input.parquet"
    labelled_path = ia_dir / "gold_ia_labelled.parquet"
    app_df.to_parquet(app_path, index=False)
    labelled_df.to_parquet(labelled_path, index=False)

    print("Branches Gold construites:")
    print(f"  app_input:   {len(app_df):,} lignes -> {app_path}")
    print(f"  ia_labelled: {len(labelled_df):,} lignes -> {labelled_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

