#!/usr/bin/env python3
"""Test rapide avant build Docker"""
import sys
from pathlib import Path

def test_imports():
    """Test que tous les imports fonctionnent"""
    print("[TEST] Vérification des imports...")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from metrics import MetricsCollector, start_metrics_server
        from core import Article, Source
        from repository import Repository
        from tagger import TopicTagger
        from analyzer import SentimentAnalyzer
        from aggregator import DataAggregator
        from exporter import GoldExporter
        print("   [OK] Tous les imports OK")
        return True
    except Exception as e:
        print(f"   [ERROR] Erreur import: {e}")
        return False

def test_metrics():
    """Test que les métriques peuvent être créées"""
    print("[TEST] Vérification des métriques...")
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from metrics import (
            pipeline_runs_total, articles_extracted_total,
            MetricsCollector, update_database_stats
        )
        # Test création
        with MetricsCollector('test'):
            pipeline_runs_total.inc()
        update_database_stats(100, 50)
        print("   [OK] Metriques fonctionnelles")
        return True
    except Exception as e:
        print(f"   [ERROR] Erreur metriques: {e}")
        return False

def test_files():
    """Test que les fichiers nécessaires existent"""
    print("[TEST] Vérification des fichiers...")
    required = [
        'Dockerfile',
        'docker-compose.yml',
        'requirements.txt',
        'sources_config.json',
        'main.py',
        'src/metrics.py',
        'monitoring/prometheus.yml',
        'monitoring/prometheus_rules.yml',
    ]
    missing = []
    for f in required:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        print(f"   [ERROR] Fichiers manquants: {', '.join(missing)}")
        return False
    else:
        print("   [OK] Tous les fichiers presents")
        return True

def test_dockerfile():
    """Test que le Dockerfile est valide"""
    print("[TEST] Vérification Dockerfile...")
    try:
        with open('Dockerfile', 'r') as f:
            content = f.read()
            if 'FROM python' in content and 'COPY requirements.txt' in content:
                print("   [OK] Dockerfile semble valide")
                return True
            else:
                print("   [WARN] Dockerfile incomplet")
                return False
    except Exception as e:
        print(f"   [ERROR] Erreur lecture Dockerfile: {e}")
        return False

def main():
    print("="*70)
    print("TEST AVANT BUILD - DataSens E1")
    print("="*70)
    print()
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Métriques", test_metrics()))
    results.append(("Fichiers", test_files()))
    results.append(("Dockerfile", test_dockerfile()))
    
    print()
    print("="*70)
    print("RÉSUMÉ")
    print("="*70)
    for name, result in results:
        status = "[OK]" if result else "[ECHEC]"
        print(f"   {name:20s}: {status}")
    
    all_ok = all(r for _, r in results)
    if all_ok:
        print()
        print("[OK] TOUS LES TESTS PASSENT - Pret pour le build!")
        return 0
    else:
        print()
        print("[ERROR] CERTAINS TESTS ECHOUENT - Corriger avant le build")
        return 1

if __name__ == "__main__":
    sys.exit(main())

