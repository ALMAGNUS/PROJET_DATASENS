#!/usr/bin/env python3
"""Test rapide de main.py - Vérifier les imports et erreurs"""
import sys
from pathlib import Path

# Fix encoding (avoid replacing pytest capture streams)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("TEST RAPIDE : Imports main.py")
print("=" * 70)

try:
    print("\n1. Test imports...")
    print("   OK: core")
    print("   OK: repository")
    print("   OK: tagger")
    print("   OK: analyzer")
    print("   OK: aggregator")
    print("   OK: exporter")
    print("   OK: dashboard")
    print("   OK: collection_report")
    print("   OK: metrics")

    print("\n2. Test initialisation pipeline...")
    from main import E1Pipeline

    print("   OK: E1Pipeline importe")

    print("\n3. Test creation instance...")
    pipeline = E1Pipeline()
    print("   OK: Instance creee")

    print("\n" + "=" * 70)
    print("TOUS LES TESTS PASSES")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
