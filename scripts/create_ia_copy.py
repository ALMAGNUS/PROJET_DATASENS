#!/usr/bin/env python3
"""
Crée la copie IA pour la prédiction : merged_all_dates → ia/ avec split train/val/test.
Usage: python scripts/create_ia_copy.py [--train 0.8] [--val 0.1] [--test 0.1]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Copie IA avec split train/val/test")
    parser.add_argument("--train", type=float, default=0.8, help="Fraction train (défaut 0.8)")
    parser.add_argument("--val", type=float, default=0.1, help="Fraction validation (défaut 0.1)")
    parser.add_argument("--test", type=float, default=0.1, help="Fraction test (défaut 0.1)")
    args = parser.parse_args()

    tot = args.train + args.val + args.test
    if abs(tot - 1.0) > 0.01:
        print(f"ERREUR: train+val+test doit faire 1.0 (actuel: {tot})")
        return 1

    settings = get_settings()
    goldai_base = Path(settings.goldai_base_path)
    if not goldai_base.is_absolute():
        goldai_base = project_root / goldai_base
    merged_path = goldai_base / "merged_all_dates.parquet"
    ia_dir = goldai_base / "ia"

    if not merged_path.exists():
        print(f"ERREUR: {merged_path} introuvable. Lancez d'abord: python scripts/merge_parquet_goldai.py")
        return 1

    print("Chargement merged_all_dates.parquet...")
    df = pd.read_parquet(merged_path)
    n = len(df)
    print(f"  {n:,} lignes chargées")

    ia_dir.mkdir(parents=True, exist_ok=True)

    # Copie annotée (même contenu, prêt pour ML)
    annotated_path = ia_dir / "merged_all_dates_annotated.parquet"
    df.to_parquet(annotated_path, index=False)
    print(f"  OK: {annotated_path}")

    # Split train/val/test
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    n_train = int(n * args.train)
    n_val = int(n * args.val)

    train_df = df_shuffled.iloc[:n_train]
    val_df = df_shuffled.iloc[n_train : n_train + n_val]
    test_df = df_shuffled.iloc[n_train + n_val :]

    train_path = ia_dir / "train.parquet"
    val_path = ia_dir / "val.parquet"
    test_path = ia_dir / "test.parquet"

    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)

    print("\nSplit:")
    print(f"  train: {len(train_df):,} ({args.train*100:.0f}%) -> {train_path}")
    print(f"  val:   {len(val_df):,} ({args.val*100:.0f}%) -> {val_path}")
    print(f"  test:  {len(test_df):,} ({args.test*100:.0f}%) -> {test_path}")
    print("\nCopie IA créée. Prêt pour la prédiction / fine-tuning.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
