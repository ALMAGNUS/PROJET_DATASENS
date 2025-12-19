#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifier rapidement les exports et la DB"""
import sys
import io
import sqlite3
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_exports():
    """Vérifier les exports"""
    print("="*70)
    print("VERIFICATION RAPIDE : Exports et DB")
    print("="*70)
    
    # 1. Vérifier exports
    print("\n1. Fichiers dans exports/ :")
    exports_dir = Path(__file__).parent.parent / 'exports'
    if exports_dir.exists():
        csv_files = sorted(exports_dir.glob('*.csv'))
        parquet_files = sorted(exports_dir.glob('*.parquet'))
        
        for f in csv_files:
            size_kb = f.stat().st_size / 1024
            lines = sum(1 for _ in open(f, 'r', encoding='utf-8', errors='ignore')) - 1
            print(f"   ✅ {f.name} ({size_kb:.1f} KB, ~{lines} lignes)")
        
        for f in parquet_files:
            size_kb = f.stat().st_size / 1024
            print(f"   ✅ {f.name} ({size_kb:.1f} KB)")
        
        # Vérifier gold_zzdb.csv
        if (exports_dir / 'gold_zzdb.csv').exists():
            print(f"\n   ❌ gold_zzdb.csv existe encore (devrait etre supprime)")
        else:
            print(f"\n   ✅ gold_zzdb.csv n'existe pas (correct)")
    else:
        print("   ❌ Dossier exports/ non trouve")
    
    # 2. Vérifier DB
    print("\n2. Articles dans datasens.db :")
    # DB peut être dans le projet ou dans datasens_project
    db_path = Path(__file__).parent.parent / 'datasens.db'
    if not db_path.exists():
        db_path = Path.home() / 'datasens_project' / 'datasens.db'
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Total articles
        cursor.execute("SELECT COUNT(*) FROM raw_data")
        total = cursor.fetchone()[0]
        print(f"   Total articles: {total}")
        
        # Par source (top 10)
        cursor.execute("""
            SELECT s.name, COUNT(r.raw_data_id) as count
            FROM raw_data r
            JOIN source s ON r.source_id = s.source_id
            GROUP BY s.name
            ORDER BY count DESC
            LIMIT 10
        """)
        print("\n   Top 10 sources :")
        for name, count in cursor.fetchall():
            print(f"      - {name}: {count} articles")
        
        # Kaggle spécifiquement
        cursor.execute("""
            SELECT COUNT(r.raw_data_id)
            FROM raw_data r
            JOIN source s ON r.source_id = s.source_id
            WHERE s.name LIKE '%kaggle%' OR s.name LIKE '%Kaggle%'
        """)
        kaggle_count = cursor.fetchone()[0]
        print(f"\n   Articles Kaggle: {kaggle_count}")
        
        conn.close()
    else:
        print("   ❌ Base de donnees non trouvee")
    
    print("\n" + "="*70)
    print("VERIFICATION TERMINEE")
    print("="*70)

if __name__ == "__main__":
    check_exports()
