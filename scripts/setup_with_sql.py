#!/usr/bin/env python
"""
DataSens E1 - Direct SQL approach
Creates ONLY 6 tables using raw SQL, bypassing SQLAlchemy metadata registry
"""

import sqlite3
from pathlib import Path

print("\n" + "=" * 70)
print("[OK] DataSens E1 - Direct SQL Setup")
print("=" * 70)

# Setup paths
DATA_PATH = Path.home() / "datasens_project"
DATA_PATH.mkdir(parents=True, exist_ok=True)
RAW_DB_PATH = DATA_PATH / "datasens.db"

# Try to delete if exists, but skip if locked by Jupyter
try:
    if RAW_DB_PATH.exists():
        RAW_DB_PATH.unlink()
        print("\n[OK] Deleted old database")
except PermissionError:
    print("\n[WARN] Database file locked (Jupyter session), will recreate with new name")
    RAW_DB_PATH = DATA_PATH / "datasens_fresh.db"

print("\n1. Creating RAW database with SQL...")
conn = sqlite3.connect(str(RAW_DB_PATH))
cursor = conn.cursor()

# Create 6 core tables with SQL
sql_tables = """
-- 1. SOURCE
CREATE TABLE source (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    sync_frequency VARCHAR(50) DEFAULT 'DAILY',
    last_sync_date DATETIME,
    retry_policy VARCHAR(50) DEFAULT 'SKIP',
    active BOOLEAN DEFAULT 1,
    created_at DATETIME
);

-- 2. RAW_DATA
CREATE TABLE raw_data (
    raw_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(source_id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(500),
    fingerprint VARCHAR(64) UNIQUE,
    published_at DATETIME,
    collected_at DATETIME,
    quality_score FLOAT DEFAULT 0.5
);
CREATE INDEX idx_raw_data_source ON raw_data(source_id);
CREATE INDEX idx_raw_data_collected ON raw_data(collected_at);

-- 3. SYNC_LOG
CREATE TABLE sync_log (
    sync_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(source_id),
    sync_date DATETIME,
    rows_synced INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    error_message TEXT
);
CREATE INDEX idx_sync_log_source ON sync_log(source_id);
CREATE INDEX idx_sync_log_date ON sync_log(sync_date);

-- 4. TOPIC
CREATE TABLE topic (
    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    keywords VARCHAR(500),
    category VARCHAR(50),
    active BOOLEAN DEFAULT 1
);

-- 5. DOCUMENT_TOPIC
CREATE TABLE document_topic (
    doc_topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_data_id INTEGER NOT NULL REFERENCES raw_data(raw_data_id),
    topic_id INTEGER NOT NULL REFERENCES topic(topic_id),
    confidence_score FLOAT DEFAULT 0.5,
    tagger VARCHAR(100)
);
CREATE INDEX idx_doc_topic_raw ON document_topic(raw_data_id);
CREATE INDEX idx_doc_topic_topic ON document_topic(topic_id);

-- 6. MODEL_OUTPUT
CREATE TABLE model_output (
    output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_data_id INTEGER NOT NULL REFERENCES raw_data(raw_data_id),
    model_name VARCHAR(100),
    label VARCHAR(100),
    score FLOAT DEFAULT 0.5,
    created_at DATETIME
);
CREATE INDEX idx_model_output_raw ON model_output(raw_data_id);
"""

# Execute table creation
cursor.executescript(sql_tables)
conn.commit()

# Verify tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print(f"   [OK] Tables created: {len(tables)}")
for t in sorted(tables):
    print(f"      - {t}")

# Insert 11 sources
print("\n2. Inserting 11 news sources...")
sources = [
    ("rss_french_news", "rss", "https://www.france24.com/fr/rss"),
    ("gdelt_events", "bigdata", "https://blog.gdeltproject.org/"),
    ("reddit_france", "api_scraping", "https://www.reddit.com/r/france"),
    ("trustpilot_reviews", "scraping", "https://fr.trustpilot.com"),
    ("openweather_api", "api", "https://openweathermap.org/api"),
    ("insee_indicators", "api", "https://api.insee.fr"),
    ("datagouv_datasets", "dataset", "https://www.data.gouv.fr"),
    ("kaggle_french_opinions", "dataset", "https://www.kaggle.com"),
    ("google_news_rss", "rss", "https://news.google.com/rss"),
    ("ifop_barometers", "scraping", "https://www.ifop.com/publications/"),
    ("yahoo_finance", "rss", "https://finance.yahoo.com/news/rss"),
]

insert_sql = "INSERT INTO source (name, source_type, url) VALUES (?, ?, ?)"
for name, stype, url in sources:
    cursor.execute(insert_sql, (name, stype, url))
    print(f"   [OK] {name}")

conn.commit()

# Verify sources
cursor.execute("SELECT COUNT(*) FROM source")
count = cursor.fetchone()[0]
print(f"\n   [OK] {count} sources inserted")

conn.close()

print("\n" + "=" * 70)
print("[OK] DATABASE READY FOR E1")
print("=" * 70)
print(f"Database: {RAW_DB_PATH}")
print("Tables: 6 core")
print(f"Sources: {count}")
print("[OK] Ready for data ingestion pipeline")
print("=" * 70 + "\n")
