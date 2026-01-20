#!/usr/bin/env python3
"""Debug main.py flow"""
import sys, json
from pathlib import Path

print("1. Loading sources...")
try:
    with open(Path(__file__).parent.parent / 'sources_config.json') as f:
        config = json.load(f)
    print(f"   [OK] Loaded {len(config['sources'])} sources")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

print("\n2. Creating sources objects...")
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.core import Source
    sources = [Source(**s) for s in config['sources']]
    print(f"   [OK] Created {len(sources)} Source objects")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Connecting to DB...")
try:
    from src.core import DatabaseLoader
    db = DatabaseLoader(str(Path.home() / 'datasens_project' / 'datasens.db'))
    print(f"   [OK] DB connected")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Creating E1Pipeline...")
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from main import E1Pipeline
    pipeline = E1Pipeline()
    print(f"   [OK] Pipeline created")
except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] All initialization successful!")

