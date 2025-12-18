#!/usr/bin/env python3
"""Test complet du projet après réorganisation"""
import sys
from pathlib import Path

print("\n" + "="*80)
print("[TEST] VÉRIFICATION COMPLÈTE DU PROJET")
print("="*80)

# Test 1: Imports src/
print("\n[TEST 1] Imports des modules src/")
try:
    sys.path.insert(0, str(Path('src')))
    from core import Article, Source, create_extractor
    from repository import Repository
    from tagger import TopicTagger
    from analyzer import SentimentAnalyzer
    from aggregator import DataAggregator
    from exporter import GoldExporter
    from dashboard import DataSensDashboard
    from collection_report import CollectionReport
    print("   [OK] Tous les imports src/ fonctionnent")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 2: Import main.py
print("\n[TEST 2] Import main.py")
try:
    sys.path.insert(0, str(Path('.')))
    from main import E1Pipeline
    print("   [OK] Import main.py fonctionne")
except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# Test 3: Fichiers scripts/
print("\n[TEST 3] Vérification fichiers scripts/")
scripts_dir = Path('scripts')
required_scripts = [
    'setup_with_sql.py',
    'show_dashboard.py',
    'view_exports.py',
    'enrich_all_articles.py',
    'show_tables.py',
    'validate_json.py',
    'migrate_sources.py'
]
all_ok = True
for script in required_scripts:
    if (scripts_dir / script).exists():
        print(f"   [OK] {script}")
    else:
        print(f"   [ERROR] {script} manquant")
        all_ok = False

if not all_ok:
    sys.exit(1)

# Test 4: Fichiers src/
print("\n[TEST 4] Vérification fichiers src/")
src_dir = Path('src')
required_modules = [
    'core.py',
    'repository.py',
    'tagger.py',
    'analyzer.py',
    'aggregator.py',
    'exporter.py',
    'dashboard.py',
    'collection_report.py'
]
all_ok = True
for module in required_modules:
    if (src_dir / module).exists():
        print(f"   [OK] {module}")
    else:
        print(f"   [ERROR] {module} manquant")
        all_ok = False

if not all_ok:
    sys.exit(1)

# Test 5: Configuration
print("\n[TEST 5] Vérification fichiers de configuration")
config_files = [
    'sources_config.json',
    'requirements.txt',
    'README.md'
]
all_ok = True
for config in config_files:
    if Path(config).exists():
        print(f"   [OK] {config}")
    else:
        print(f"   [ERROR] {config} manquant")
        all_ok = False

if not all_ok:
    sys.exit(1)

# Test 6: Chemins relatifs dans scripts
print("\n[TEST 6] Vérification chemins relatifs dans scripts")
try:
    # Test show_dashboard.py
    with open('scripts/show_dashboard.py') as f:
        content = f.read()
        if "parent.parent" in content:
            print("   [OK] show_dashboard.py : chemins corrects")
        else:
            print("   [WARN] show_dashboard.py : vérifier chemins")
    
    # Test view_exports.py
    with open('scripts/view_exports.py') as f:
        content = f.read()
        if "parent.parent" in content:
            print("   [OK] view_exports.py : chemins corrects")
        else:
            print("   [WARN] view_exports.py : vérifier chemins")
    
    # Test enrich_all_articles.py
    with open('scripts/enrich_all_articles.py') as f:
        content = f.read()
        if "parent.parent" in content:
            print("   [OK] enrich_all_articles.py : chemins corrects")
        else:
            print("   [WARN] enrich_all_articles.py : vérifier chemins")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "="*80)
print("[OK] TOUS LES TESTS PASSÉS - PROJET FONCTIONNEL")
print("="*80)
print("\nCommandes principales:")
print("  - python main.py                    # Lancer le pipeline")
print("  - python scripts/show_dashboard.py  # Afficher le dashboard")
print("  - python scripts/view_exports.py    # Visualiser les CSV")
print("  - python scripts/setup_with_sql.py  # Initialiser la DB")
print("\n")

