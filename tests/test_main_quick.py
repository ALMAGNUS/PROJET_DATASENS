#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test rapide de main.py - Vérifier les imports et erreurs"""
import sys
import io
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("TEST RAPIDE : Imports main.py")
print("="*70)

try:
    print("\n1. Test imports...")
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    
    from core import ContentTransformer, Source, create_extractor
    print("   OK: core")
    
    from repository import Repository
    print("   OK: repository")
    
    from tagger import TopicTagger
    print("   OK: tagger")
    
    from analyzer import SentimentAnalyzer
    print("   OK: analyzer")
    
    from aggregator import DataAggregator
    print("   OK: aggregator")
    
    from exporter import GoldExporter
    print("   OK: exporter")
    
    from dashboard import DataSensDashboard
    print("   OK: dashboard")
    
    from collection_report import CollectionReport
    print("   OK: collection_report")
    
    from metrics import MetricsCollector
    print("   OK: metrics")
    
    print("\n2. Test initialisation pipeline...")
    from main import E1Pipeline
    print("   OK: E1Pipeline importe")
    
    print("\n3. Test creation instance...")
    pipeline = E1Pipeline()
    print("   OK: Instance creee")
    
    print("\n" + "="*70)
    print("TOUS LES TESTS PASSES")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
