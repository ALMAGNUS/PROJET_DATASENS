#!/usr/bin/env python3
"""DataSens E1+ - MAIN ENTRY (Pipeline SOLID/DRY)"""
import json, sys, os, shutil, time, io
from pathlib import Path
from datetime import date, datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        # Only wrap if not already wrapped
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        # If stdout/stderr don't have buffer attribute, skip wrapping
        pass

sys.path.insert(0, str(Path(__file__).parent / 'src'))
# Import E1 isolé depuis package e1
from e1.pipeline import E1Pipeline



if __name__ == "__main__":
    pipeline = E1Pipeline()
    pipeline.run()
