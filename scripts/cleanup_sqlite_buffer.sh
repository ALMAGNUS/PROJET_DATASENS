#!/bin/bash
# Script Linux pour nettoyer le buffer SQLite
cd "$(dirname "$0")/.."
python scripts/cleanup_sqlite_buffer.py
