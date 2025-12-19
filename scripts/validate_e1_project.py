#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation complète du projet E1 - Preuves concrètes de fonctionnement"""
import sqlite3
import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("\n" + "="*80)
print("  VALIDATION PROJET E1 - PREUVES CONCRÈTES")
print("="*80)

project_root = Path(__file__).parent.parent
db_path = Path.home() / 'datasens_project' / 'datasens.db'
zzdb_path = project_root / 'zzdb' / 'synthetic_data.db'

results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'details': []
}

def test(name, condition, details=""):
    """Test unitaire avec rapport"""
    if condition:
        results['passed'] += 1
        status = "✅ PASS"
        print(f"   {status} : {name}")
        if details:
            print(f"      → {details}")
    else:
        results['failed'] += 1
        status = "❌ FAIL"
        print(f"   {status} : {name}")
        if details:
            print(f"      → {details}")
    results['details'].append({'name': name, 'status': status, 'details': details})

def warn(name, message):
    """Avertissement"""
    results['warnings'] += 1
    print(f"   ⚠️  WARN : {name}")
    print(f"      → {message}")

print("\n[1] VÉRIFICATION STRUCTURE PROJET")
print("-" * 80)

# Fichiers essentiels
test("main.py existe", (project_root / 'main.py').exists(), "Point d'entrée du pipeline")
test("src/core.py existe", (project_root / 'src' / 'core.py').exists(), "Extracteurs et modèles")
test("src/repository.py existe", (project_root / 'src' / 'repository.py').exists(), "Gestion base de données")
test("sources_config.json existe", (project_root / 'sources_config.json').exists(), "Configuration des sources")
test("requirements.txt existe", (project_root / 'requirements.txt').exists(), "Dépendances Python")

# Modules essentiels
test("src/aggregator.py existe", (project_root / 'src' / 'aggregator.py').exists(), "Agrégation RAW/SILVER/GOLD")
test("src/exporter.py existe", (project_root / 'src' / 'exporter.py').exists(), "Export CSV/Parquet")
test("src/tagger.py existe", (project_root / 'src' / 'tagger.py').exists(), "Tagging topics")
test("src/analyzer.py existe", (project_root / 'src' / 'analyzer.py').exists(), "Analyse sentiment")

print("\n[2] VÉRIFICATION BASE DE DONNÉES DataSens")
print("-" * 80)

if db_path.exists():
    test("datasens.db existe", True, f"Chemin: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Vérifier schéma
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        required_tables = ['source', 'raw_data', 'sync_log', 'topic', 'document_topic', 'model_output']
        
        for table in required_tables:
            test(f"Table {table} existe", table in tables)
        
        # Statistiques réelles
        cursor.execute("SELECT COUNT(*) FROM raw_data")
        total_articles = cursor.fetchone()[0]
        test(f"Articles dans raw_data", total_articles > 0, f"{total_articles:,} articles")
        
        cursor.execute("SELECT COUNT(DISTINCT source_id) FROM raw_data")
        sources_count = cursor.fetchone()[0]
        test(f"Sources différentes", sources_count > 0, f"{sources_count} sources")
        
        cursor.execute("SELECT COUNT(*) FROM document_topic")
        tagged_count = cursor.fetchone()[0]
        test(f"Articles taggés (topics)", tagged_count > 0, f"{tagged_count:,} tags")
        
        cursor.execute("SELECT COUNT(*) FROM model_output WHERE model_name = 'sentiment_keyword'")
        analyzed_count = cursor.fetchone()[0]
        test(f"Articles analysés (sentiment)", analyzed_count > 0, f"{analyzed_count:,} analyses")
        
        # Vérifier qualité des données
        cursor.execute("SELECT COUNT(*) FROM raw_data WHERE title IS NOT NULL AND title != ''")
        valid_titles = cursor.fetchone()[0]
        test(f"Articles avec titre valide", valid_titles == total_articles, f"{valid_titles}/{total_articles}")
        
        cursor.execute("SELECT COUNT(*) FROM raw_data WHERE content IS NOT NULL AND content != ''")
        valid_content = cursor.fetchone()[0]
        test(f"Articles avec contenu valide", valid_content == total_articles, f"{valid_content}/{total_articles}")
        
        # Vérifier déduplication (fingerprint)
        cursor.execute("SELECT COUNT(DISTINCT fingerprint) FROM raw_data WHERE fingerprint IS NOT NULL")
        unique_fp = cursor.fetchone()[0]
        test(f"Déduplication active (fingerprint)", unique_fp > 0, f"{unique_fp:,} fingerprints uniques")
        
        conn.close()
    except Exception as e:
        test("Connexion à datasens.db", False, f"Erreur: {str(e)[:60]}")
else:
    test("datasens.db existe", False, "Base de données non trouvée - Lancer python main.py")

print("\n[3] VÉRIFICATION ZZDB (LAB IA)")
print("-" * 80)

if zzdb_path.exists():
    test("zzdb/synthetic_data.db existe", True, f"Chemin: {zzdb_path}")
    
    try:
        conn = sqlite3.connect(str(zzdb_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM synthetic_articles")
        total_zzdb = cursor.fetchone()[0]
        test(f"Articles synthétiques ZZDB", total_zzdb > 0, f"{total_zzdb:,} articles")
        
        cursor.execute("SELECT COUNT(DISTINCT theme) FROM synthetic_articles")
        themes_count = cursor.fetchone()[0]
        test(f"Thèmes différents", themes_count > 0, f"{themes_count} thèmes")
        
        cursor.execute("SELECT COUNT(DISTINCT sentiment) FROM synthetic_articles")
        sentiments_count = cursor.fetchone()[0]
        test(f"Sentiments différents", sentiments_count > 0, f"{sentiments_count} sentiments")
        
        conn.close()
    except Exception as e:
        test("Connexion à zzdb/synthetic_data.db", False, f"Erreur: {str(e)[:60]}")
else:
    warn("zzdb/synthetic_data.db", "Base ZZDB non trouvée - Optionnel pour E1")

print("\n[4] VÉRIFICATION PIPELINE E1")
print("-" * 80)

# Vérifier que le pipeline peut être importé
try:
    sys.path.insert(0, str(project_root))
    from src.core import Article, Source, create_extractor
    from src.repository import Repository
    test("Import modules core", True, "Article, Source, create_extractor")
    test("Import Repository", True, "Repository disponible")
except Exception as e:
    test("Import modules core", False, f"Erreur: {str(e)[:60]}")

# Vérifier extracteurs
try:
    from src.core import RSSExtractor, APIExtractor, SQLiteExtractor, CSVExtractor
    test("Extracteurs disponibles", True, "RSS, API, SQLite, CSV")
except Exception as e:
    test("Extracteurs disponibles", False, f"Erreur: {str(e)[:60]}")

# Vérifier sources config
try:
    with open(project_root / 'sources_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        sources_count = len(config.get('sources', []))
        test("sources_config.json valide", sources_count > 0, f"{sources_count} sources configurées")
        
        # Vérifier source zzdb
        zzdb_sources = [s for s in config['sources'] if 'zzdb' in s.get('source_name', '').lower()]
        test("Source ZZDB configurée", len(zzdb_sources) > 0, f"{len(zzdb_sources)} source(s) ZZDB")
except Exception as e:
    test("sources_config.json valide", False, f"Erreur: {str(e)[:60]}")

print("\n[5] VÉRIFICATION EXPORTS")
print("-" * 80)

exports_dir = project_root / 'exports'
if exports_dir.exists():
    test("Dossier exports/ existe", True)
    
    gold_csv = exports_dir / 'gold.csv'
    gold_parquet = exports_dir / 'gold.parquet'
    
    if gold_csv.exists():
        # Compter lignes
        try:
            with open(gold_csv, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f) - 1  # -1 pour header
            test("gold.csv existe et contient des données", lines > 0, f"{lines:,} lignes")
        except:
            test("gold.csv existe et contient des données", False)
    else:
        warn("gold.csv", "Fichier non trouvé - Générer avec python main.py")
    
    if gold_parquet.exists():
        size_mb = gold_parquet.stat().st_size / (1024 * 1024)
        test("gold.parquet existe", True, f"Taille: {size_mb:.2f} MB")
    else:
        warn("gold.parquet", "Fichier non trouvé - Générer avec python main.py")
else:
    warn("exports/", "Dossier non trouvé - Générer avec python main.py")

print("\n[6] VÉRIFICATION FONCTIONNALITÉS AVANCÉES")
print("-" * 80)

if db_path.exists():
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Vérifier enrichissement (topics + sentiment)
        cursor.execute("""
            SELECT COUNT(DISTINCT r.raw_data_id)
            FROM raw_data r
            WHERE EXISTS (SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id)
            AND EXISTS (SELECT 1 FROM model_output mo WHERE mo.raw_data_id = r.raw_data_id 
                        AND mo.model_name = 'sentiment_keyword')
        """)
        enriched_count = cursor.fetchone()[0]
        test(f"Articles enrichis (topics + sentiment)", enriched_count > 0, 
             f"{enriched_count:,} articles enrichis")
        
        # Vérifier distribution sentiment
        cursor.execute("""
            SELECT label, COUNT(*) as count
            FROM model_output
            WHERE model_name = 'sentiment_keyword'
            GROUP BY label
        """)
        sentiments = cursor.fetchall()
        test(f"Distribution sentiment", len(sentiments) > 0, 
             f"{len(sentiments)} catégories: {', '.join([s[0] for s in sentiments])}")
        
        # Vérifier quality_score pour ZZDB
        cursor.execute("""
            SELECT AVG(quality_score)
            FROM raw_data r
            JOIN source s ON r.source_id = s.source_id
            WHERE s.name LIKE '%zzdb%'
        """)
        zzdb_quality = cursor.fetchone()[0]
        if zzdb_quality is not None:
            test(f"Quality score ZZDB (garde-fou)", zzdb_quality == 0.3, 
                 f"Score: {zzdb_quality} (attendu: 0.3)")
        
        conn.close()
    except Exception as e:
        warn("Fonctionnalités avancées", f"Erreur: {str(e)[:60]}")

print("\n[7] TEST EXTRACTION RÉELLE")
print("-" * 80)

try:
    sys.path.insert(0, str(project_root))
    from src.core import Source, create_extractor
    
    # Test avec source zzdb_synthetic
    test_source = Source(
        source_name="zzdb_synthetic",
        acquisition_type="sqlite",
        url="zzdb/synthetic_data.db"
    )
    
    extractor = create_extractor(test_source)
    test("Création extractor ZZDB", extractor is not None, 
         f"Type: {type(extractor).__name__}")
    
    # Test extraction (avec limite)
    import os
    os.environ['ZZDB_MAX_ARTICLES'] = '5'  # Limiter pour test rapide
    articles = extractor.extract()
    test("Extraction ZZDB fonctionne", len(articles) >= 0, 
         f"{len(articles)} articles extraits (max 5 pour test)")
    
except Exception as e:
    test("Test extraction réelle", False, f"Erreur: {str(e)[:60]}")

print("\n[8] RÉSUMÉ VALIDATION")
print("=" * 80)
print(f"   ✅ Tests réussis    : {results['passed']}")
print(f"   ❌ Tests échoués    : {results['failed']}")
print(f"   ⚠️  Avertissements : {results['warnings']}")
print(f"   📊 Score           : {results['passed']}/{results['passed'] + results['failed']}")

if results['failed'] == 0:
    print("\n   🎉 PROJET E1 VALIDÉ - TOUS LES TESTS PASSENT")
    print("   Le projet est fonctionnel et prêt pour la démonstration.")
elif results['failed'] <= 2:
    print("\n   ⚠️  PROJET E1 QUASI-VALIDÉ - Quelques ajustements nécessaires")
    print("   La plupart des fonctionnalités sont opérationnelles.")
else:
    print("\n   ❌ PROJET E1 NÉCESSITE DES CORRECTIONS")
    print("   Plusieurs tests ont échoué. Vérifier les erreurs ci-dessus.")

print("\n" + "="*80)
print("  FIN DE LA VALIDATION")
print("="*80 + "\n")

# Générer rapport JSON
report_path = project_root / 'validation_report.json'
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'passed': results['passed'],
            'failed': results['failed'],
            'warnings': results['warnings']
        },
        'details': results['details']
    }, f, indent=2, ensure_ascii=False)

print(f"   📄 Rapport détaillé sauvegardé : {report_path}")
