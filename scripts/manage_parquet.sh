#!/bin/bash
# Script Linux pour lancer manage_parquet.py
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src:$PYTHONPATH"
python scripts/manage_parquet.py
