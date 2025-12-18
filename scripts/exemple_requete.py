#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exemple: Exécuter une requête SQL directement"""
import sqlite3
from pathlib import Path
import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Chemin de la base de données
db_path = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))

# Connexion
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
cursor = conn.cursor()

# Votre requête SQL
sql = """
SELECT 
    r.raw_data_id as id,
    s.name as source,
    r.title,
    mo.label as sentiment,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id 
    AND mo.model_name = 'sentiment_keyword'
ORDER BY r.collected_at DESC
LIMIT 20
"""

# Exécution
cursor.execute(sql)
rows = cursor.fetchall()

# Affichage
print("\n" + "="*80)
print("Articles avec sentiment")
print("="*80)
for row in rows:
    print(f"ID: {row['id']} | Source: {row['source']:20s} | Sentiment: {row['sentiment'] or 'N/A':8s} | Score: {row['sentiment_score'] or 0:.3f}")
    print(f"  Titre: {row['title'][:60]}...")
    print()

print(f"Total: {len(rows)} articles")

conn.close()
