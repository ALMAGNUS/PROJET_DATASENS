#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifier le statut Kaggle dans la DB"""
import sys
import io
import sqlite3
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_kaggle():
    """Vérifier Kaggle dans la DB"""
    print("="*70)
    print("STATUT KAGGLE DANS LA DB")
    print("="*70)
    
    db_path = Path.home() / 'datasens_project' / 'datasens.db'
    if not db_path.exists():
        print(f"\n[ERREUR] Base non trouvee: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Articles Kaggle dans la DB
    cursor.execute("""
        SELECT COUNT(*)
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        WHERE s.name LIKE '%kaggle%' OR s.name LIKE '%Kaggle%'
    """)
    kaggle_in_db = cursor.fetchone()[0]
    
    print(f"\nArticles Kaggle dans la DB: {kaggle_in_db}")
    
    # Total articles
    cursor.execute("SELECT COUNT(*) FROM raw_data")
    total = cursor.fetchone()[0]
    print(f"Total articles dans la DB: {total}")
    
    # Derniers articles Kaggle
    cursor.execute("""
        SELECT s.name, r.title, r.collected_at
        FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        WHERE s.name LIKE '%kaggle%' OR s.name LIKE '%Kaggle%'
        ORDER BY r.collected_at DESC
        LIMIT 5
    """)
    print("\nDerniers articles Kaggle:")
    for name, title, collected in cursor.fetchall():
        print(f"   - {name}: {title[:60]}... ({collected})")
    
    conn.close()
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print(f"\nSi le pipeline est lent, c'est normal :")
    print(f"   - 76 680 articles extraits depuis Kaggle")
    print(f"   - {kaggle_in_db} articles deja dans la DB")
    print(f"   - Le pipeline doit traiter tous les nouveaux articles")
    print(f"\nLe pipeline va:")
    print(f"   1. Nettoyer les articles")
    print(f"   2. Les charger dans la DB (avec deduplication)")
    print(f"   3. Les tagger (topics)")
    print(f"   4. Les analyser (sentiment)")
    print(f"   5. Les agreger")
    print(f"   6. Les exporter")
    print(f"\nC'est normal que ce soit long avec autant d'articles !")

if __name__ == "__main__":
    check_kaggle()
