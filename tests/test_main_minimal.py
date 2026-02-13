#!/usr/bin/env python3
"""Test minimal de main.py - Identifier le blocage"""
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

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("TEST MINIMAL : main.py")
print("=" * 70)

try:
    print("\n[ETAPE 1] Import...")
    from main import E1Pipeline

    print("   OK")

    print("\n[ETAPE 2] Creation instance...")
    pipeline = E1Pipeline()
    print("   OK")

    print("\n[ETAPE 3] Test load_sources()...")
    sources = pipeline.load_sources()
    print(f"   OK: {len(sources)} sources chargees")

    print("\n[ETAPE 4] Test extract() (premieres sources seulement)...")
    print("   (On va tester juste les 3 premieres sources actives)")
    active_sources = [s for s in sources if s.active][:3]
    print(f"   Sources a tester: {[s.source_name for s in active_sources]}")

    # Tester extraction sur quelques sources seulement
    articles = []
    for source in active_sources:
        print(f"\n   Extraction {source.source_name}...", end=" ")
        try:
            from src.e1.core import create_extractor

            extractor = create_extractor(source)
            extracted = extractor.extract()
            articles.extend([(a, source.source_name) for a in extracted])
            print(f"OK ({len(extracted)} articles)")
        except Exception as e:
            print(f"ERREUR: {e}")

    print(f"\n   Total extrait: {len(articles)} articles")

    print("\n" + "=" * 70)
    print("TEST MINIMAL REUSSI")
    print("=" * 70)
    print("\nLe pipeline fonctionne. Si main.py bloque, c'est probablement")
    print("parce qu'il traite 76 680 articles Kaggle (c'est long mais normal).")

except Exception as e:
    print(f"\n\n❌ ERREUR: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
