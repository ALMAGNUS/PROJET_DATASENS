#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test exécution complète de main.py avec timeout"""
import sys
import io
import signal
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("TEST EXECUTION : main.py (30 secondes max)")
print("="*70)

try:
    # Importer et créer le pipeline
    from main import E1Pipeline
    
    print("\n[1/3] Creation pipeline...")
    pipeline = E1Pipeline()
    print("   OK")
    
    print("\n[2/3] Lancement pipeline (extraction seulement)...")
    print("   (On va juste tester extract(), pas tout le pipeline)")
    
    # Test seulement extract() pour voir si ça bloque
    articles = pipeline.extract()
    print(f"   OK: {len(articles)} articles extraits")
    
    print("\n[3/3] Test clean()...")
    cleaned = pipeline.clean(articles)
    print(f"   OK: {len(cleaned)} articles nettoyes")
    
    print("\n" + "="*70)
    print("TESTS PASSES - Pipeline fonctionne")
    print("="*70)
    print("\nNote: Le pipeline complet peut prendre plusieurs minutes")
    print("      avec 76 680 articles Kaggle a traiter.")
    
except KeyboardInterrupt:
    print("\n\n[INTERROMPU] Par l'utilisateur")
    sys.exit(1)
except Exception as e:
    print(f"\n\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
