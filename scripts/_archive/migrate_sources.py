#!/usr/bin/env python3
"""Add missing Kaggle + GDELT sources to existing DB"""

import sqlite3
from pathlib import Path

db_path = Path.home() / "datasens_project" / "datasens.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("\n" + "=" * 70)
print("MIGRATION: Adding missing Kaggle + GDELT sources")
print("=" * 70)

# Check existing sources
cursor.execute("SELECT COUNT(*) FROM source")
count_before = cursor.fetchone()[0]
print(f"\nBefore: {count_before} sources")

# Add missing sources (if not exist)
new_sources = [
    (
        "Kaggle_StopWords_28Lang",
        "dataset",
        "https://www.kaggle.com/datasets/heeraldedhia/stop-words-in-28-languages",
    ),
    ("Kaggle_StopWords", "dataset", "https://www.kaggle.com/datasets/dliciuc/stop-words"),
    (
        "Kaggle_FrenchFinNews",
        "dataset",
        "https://www.kaggle.com/datasets/arcticgiant/french-financial-news",
    ),
    (
        "Kaggle_SentimentLexicons",
        "dataset",
        "https://www.kaggle.com/datasets/rtatman/sentiment-lexicons-for-81-languages",
    ),
    (
        "Kaggle_InsuranceReviews",
        "dataset",
        "https://www.kaggle.com/datasets/fedi1996/insurance-reviews-france",
    ),
    ("GDELT_Last15_English", "bigdata", "http://data.gdeltproject.org/events/"),
    ("GDELT_Master_List", "bigdata", "http://data.gdeltproject.org/events/"),
]

for name, stype, url in new_sources:
    try:
        cursor.execute(
            "INSERT INTO source (name, source_type, url) VALUES (?, ?, ?)", (name, stype, url)
        )
        print(f"  [OK] Added: {name}")
    except sqlite3.IntegrityError:
        print(f"  - Exists: {name}")

conn.commit()

# Check after
cursor.execute("SELECT COUNT(*) FROM source")
count_after = cursor.fetchone()[0]

print(f"\nAfter: {count_after} sources")
print(f"Added: {count_after - count_before} sources")

# Show all sources
print("\nAll sources:")
cursor.execute("SELECT name FROM source ORDER BY name")
for (name,) in cursor.fetchall():
    print(f"  - {name}")

conn.close()
print("\n" + "=" * 70)
