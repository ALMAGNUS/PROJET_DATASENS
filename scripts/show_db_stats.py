#!/usr/bin/env python3
"""Affiche les statistiques record de la base datasens.db"""
import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

db_path = Path.home() / 'datasens_project' / 'datasens.db'

if not db_path.exists():
    print(f"❌ Base non trouvée: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("\n" + "="*80)
print("  📊 STATISTIQUES RECORD - DATASENS.DB")
print("="*80)

# Total articles
cursor.execute("SELECT COUNT(*) FROM raw_data")
total = cursor.fetchone()[0]
print(f"\n📈 TOTAL ARTICLES: {total:,}")

# Par source
cursor.execute("""
    SELECT s.name, COUNT(r.raw_data_id) as count
    FROM source s
    LEFT JOIN raw_data r ON s.source_id = r.source_id
    GROUP BY s.name
    ORDER BY count DESC
""")
print("\n📋 PAR SOURCE:")
for name, count in cursor.fetchall():
    print(f"   • {name:30s}: {count:6,} articles")

# Sentiments
cursor.execute("""
    SELECT label, COUNT(*) as count
    FROM model_output
    WHERE model_name = 'sentiment_keyword'
    GROUP BY label
    ORDER BY count DESC
""")
print("\n😊 SENTIMENTS:")
sentiments = cursor.fetchall()
total_sent = sum(s[1] for s in sentiments)
for label, count in sentiments:
    pct = (count / max(total_sent, 1)) * 100
    print(f"   • {label:10s}: {count:6,} articles ({pct:5.1f}%)")

# Topics
cursor.execute("""
    SELECT t.name, COUNT(dt.doc_topic_id) as count
    FROM topic t
    LEFT JOIN document_topic dt ON t.topic_id = dt.topic_id
    GROUP BY t.name
    ORDER BY count DESC
    LIMIT 20
""")
print("\n🏷️  TOPICS (TOP 20):")
for name, count in cursor.fetchall():
    print(f"   • {name:25s}: {count:6,} articles")

# Articles enrichis
cursor.execute("""
    SELECT COUNT(DISTINCT r.raw_data_id)
    FROM raw_data r
    WHERE EXISTS (
        SELECT 1 FROM document_topic dt WHERE dt.raw_data_id = r.raw_data_id
    ) AND EXISTS (
        SELECT 1 FROM model_output mo WHERE mo.raw_data_id = r.raw_data_id
        AND mo.model_name = 'sentiment_keyword'
    )
""")
enriched = cursor.fetchone()[0]
pct_enriched = (enriched / max(total, 1)) * 100
print(f"\n✨ ARTICLES ENRICHIS: {enriched:,} / {total:,} ({pct_enriched:.1f}%)")

# ZZDB
cursor.execute("""
    SELECT COUNT(*)
    FROM raw_data r
    JOIN source s ON r.source_id = s.source_id
    WHERE s.name LIKE '%zzdb%'
""")
zzdb_total = cursor.fetchone()[0]
print(f"\n🔬 ZZDB (DONNÉES SYNTHÈSE): {zzdb_total:,} articles")

conn.close()

print("\n" + "="*80 + "\n")
