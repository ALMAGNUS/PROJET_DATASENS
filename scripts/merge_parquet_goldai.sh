#!/bin/bash
# Script de fusion incrémentale Parquet GOLD → GoldAI (Linux/Mac)
cd "$(dirname "$0")/.."
python scripts/merge_parquet_goldai.py "$@"
