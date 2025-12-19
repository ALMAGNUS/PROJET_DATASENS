#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test rapide : Vérifier que Kaggle est bien dans la DB"""
import sys
import io
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repository import Repository
import sqlite3

def test_kaggle_in_db():
    """Vérifier que Kaggle est dans la DB"""
    print("="*70)
    print("TEST RAPIDE : Kaggle dans la DB")
    print("="*70)
    
    # DB peut être dans le projet ou dans datasens_project
    db_path = Path(__file__).parent.parent / 'datasens.db'
    if not db_path.exists():
        db_path = Path.home() / 'datasens_project' / 'datasens.db'
    if not db_path.exists():
        print(f"\n[ERREUR] Base de donnees non trouvee : {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Vérifier sources Kaggle
    print("\n1. Sources Kaggle dans la DB :")
    cursor.execute("""
        SELECT source_id, name, active 
        FROM source 
        WHERE name LIKE '%kaggle%' OR name LIKE '%Kaggle%'
        ORDER BY name
    """)
    kaggle_sources = cursor.fetchall()
    if not kaggle_sources:
        print("   [ATTENTION] Aucune source Kaggle trouvee")
    else:
        for sid, name, active in kaggle_sources:
            print(f"   - {name} (ID: {sid}, Active: {active})")
    
    # Compter articles Kaggle
    print("\n2. Articles Kaggle dans raw_data :")
    cursor.execute("""
        SELECT s.name, COUNT(r.raw_data_id) as count
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        WHERE s.name LIKE '%kaggle%' OR s.name LIKE '%Kaggle%'
        GROUP BY s.name
        ORDER BY count DESC
    """)
    kaggle_articles = cursor.fetchall()
    if not kaggle_articles:
        print("   [ATTENTION] Aucun article Kaggle dans raw_data")
    else:
        total = 0
        for name, count in kaggle_articles:
            print(f"   - {name}: {count} articles")
            total += count
        print(f"\n   TOTAL Kaggle: {total} articles")
    
    # Vérifier exports
    print("\n3. Fichiers exports :")
    exports_dir = Path(__file__).parent.parent / 'exports'
    if exports_dir.exists():
        files = list(exports_dir.glob('*.csv')) + list(exports_dir.glob('*.parquet'))
        for f in sorted(files):
            size_kb = f.stat().st_size / 1024
            print(f"   - {f.name} ({size_kb:.1f} KB)")
        
        # Vérifier que gold_zzdb.csv n'existe pas
        if (exports_dir / 'gold_zzdb.csv').exists():
            print("\n   [ERREUR] gold_zzdb.csv existe encore !")
        else:
            print("\n   [OK] gold_zzdb.csv n'existe pas (corrige)")
    else:
        print("   [ATTENTION] Dossier exports/ non trouve")
    
    conn.close()
    print("\n" + "="*70)
    print("TEST TERMINE")
    print("="*70)

if __name__ == "__main__":
    test_kaggle_in_db()
