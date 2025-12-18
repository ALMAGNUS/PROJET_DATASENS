#!/usr/bin/env python3
"""Enrichir rétroactivement tous les articles (topics + sentiment)"""
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from repository import Repository
from tagger import TopicTagger
from analyzer import SentimentAnalyzer
import sqlite3

db_path = str(Path.home() / 'datasens_project' / 'datasens.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Récupérer tous les articles non enrichis
cursor.execute("""
    SELECT r.raw_data_id, r.title, r.content
    FROM raw_data r
    WHERE NOT EXISTS (
        SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id
    ) OR NOT EXISTS (
        SELECT 1 FROM model_output mo 
        WHERE mo.raw_data_id = r.raw_data_id AND mo.model_name = 'sentiment_keyword'
    )
    ORDER BY r.collected_at DESC
""")
articles = cursor.fetchall()

if len(articles) == 0:
    print("\n[OK] Tous les articles sont déjà enrichis !\n")
    sys.exit(0)

print(f"\n[ENRICHISSEMENT] {len(articles)} articles à enrichir")
print(f"   Cela peut prendre quelques minutes...\n")

tagger = TopicTagger(db_path)
analyzer = SentimentAnalyzer(db_path)

tagged = 0
analyzed = 0

for i, (raw_id, title, content) in enumerate(articles, 1):
    if i % 50 == 0:
        print(f"   Progression: {i}/{len(articles)}...")
    
    # Tag topics
    if tagger.tag(raw_id, title or '', content or ''):
        tagged += 1
    
    # Analyze sentiment
    if analyzer.save(raw_id, title or '', content or ''):
        analyzed += 1

tagger.close()
analyzer.close()
conn.close()

print(f"\n[OK] Enrichissement terminé:")
print(f"   Articles taggés: {tagged}")
print(f"   Articles analysés: {analyzed}")
print(f"   Total traités: {len(articles)}\n")

