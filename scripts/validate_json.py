"""Validate sources_config.json"""
import json
from pathlib import Path

fp = Path(__file__).parent.parent / "sources_config.json"
try:
    with open(str(fp)) as f:
        data = json.load(f)
    print(f"[OK] JSON valid - {len(data['sources'])} sources")
except json.JSONDecodeError as e:
    print(f"[ERROR] JSON Error: {e}")
    # Show context
    with open(str(fp)) as f:
        lines = f.readlines()
    line_num = e.lineno - 1
    print(f"\nContext around line {e.lineno}:")
    for i in range(max(0, line_num - 2), min(len(lines), line_num + 3)):
        print(f"  {i+1}: {lines[i]}", end="")
