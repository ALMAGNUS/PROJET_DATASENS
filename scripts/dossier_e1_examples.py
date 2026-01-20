"""
Exemples E1 prêts à copier/coller.

IMPORTANT :
- Ne pas exécuter ce fichier.
- Copie simplement UN bloc à la fois vers ton Google Doc.
- Chaque bloc = 1 exemple unique.
"""

# ---------------------------------------------------------------------------
# C1 - Extraction (RSS)
# ---------------------------------------------------------------------------
EXEMPLE_RSS = """
from src.e1.core import RSSExtractor

extractor = RSSExtractor(name="rss_french_news", url="https://www.france24.com/fr/rss")
articles = extractor.extract()
print(f"RSS articles: {len(articles)}")
""".strip()

# ---------------------------------------------------------------------------
# C1 - Extraction (API)
# ---------------------------------------------------------------------------
EXEMPLE_API = """
from src.e1.core import APIExtractor

extractor = APIExtractor(name="reddit_france", url="https://www.reddit.com/r/france/")
articles = extractor.extract()
print(f"API articles: {len(articles)}")
""".strip()

# ---------------------------------------------------------------------------
# C1 - Extraction (Scraping)
# ---------------------------------------------------------------------------
EXEMPLE_SCRAPING = """
from src.e1.core import ScrapingExtractor

extractor = ScrapingExtractor(name="trustpilot_reviews", url="https://www.trustpilot.com")
articles = extractor.extract()
print(f"Scraped articles: {len(articles)}")
""".strip()

# ---------------------------------------------------------------------------
# C1 - Extraction fichiers (CSV/JSON/XML)
# ---------------------------------------------------------------------------
EXEMPLE_AGGREGATE_RAW = """
from src.e1.aggregator import DataAggregator

DB_PATH = "datasens.db"
aggregator = DataAggregator(DB_PATH)
df = aggregator.aggregate_raw()
aggregator.close()
print(df.head(3))
""".strip()

# ---------------------------------------------------------------------------
# C1 - Web scraping simple (BeautifulSoup)
# ---------------------------------------------------------------------------
EXEMPLE_SCRAPE_TITLES = """
import requests
from bs4 import BeautifulSoup

URL = "https://www.france24.com/fr"
html = requests.get(URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"}).text
soup = BeautifulSoup(html, "lxml")
titles = [h.get_text(strip=True) for h in soup.select("h1, h2")]
print(titles[:10])
""".strip()

# ---------------------------------------------------------------------------
# C1 - Connexion SQLite (lecture simple)
# ---------------------------------------------------------------------------
EXEMPLE_SQLITE_READ = """
import sqlite3

DB_PATH = "datasens.db"
conn = sqlite3.connect(DB_PATH)
rows = conn.execute("SELECT raw_data_id, title FROM raw_data").fetchall()
conn.close()
print(rows[:5])
""".strip()

# ---------------------------------------------------------------------------
# C4 - CRUD SQLite (exemple pédagogique)
# ---------------------------------------------------------------------------
EXEMPLE_CRUD_SQLITE = """
import sqlite3

DB_PATH = "datasens.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# CREATE
cur.execute(
    '''
    INSERT INTO source (name, source_type, url, sync_frequency, active, is_synthetic)
    VALUES (?, ?, ?, ?, ?, ?)
    ''',
    ("demo_source", "api", "https://example.com", "DAILY", True, False),
)
conn.commit()

# READ
cur.execute("SELECT source_id, name, source_type FROM source WHERE name = ?", ("demo_source",))
print("READ:", cur.fetchone())

# UPDATE
cur.execute("UPDATE source SET active = ? WHERE name = ?", (False, "demo_source"))
conn.commit()

# DELETE
cur.execute("DELETE FROM source WHERE name = ?", ("demo_source",))
conn.commit()

conn.close()
""".strip()

# ---------------------------------------------------------------------------
# C3 - PySpark lecture Parquet (GOLD)
# ---------------------------------------------------------------------------
EXEMPLE_SPARK_READ = """
from pyspark.sql import SparkSession

PATH = "data/gold/date=2025-12-20"
spark = SparkSession.builder.master("local[*]").getOrCreate()
df = spark.read.parquet(PATH)
df.select("id", "source", "sentiment").show(5, truncate=False)
""".strip()

# ---------------------------------------------------------------------------
# C2 - SQL (SQLite) : requetes de base
# ---------------------------------------------------------------------------
EXEMPLE_SQL_LIST_SOURCES = """
SELECT source_id, name, source_type, is_active
FROM source
ORDER BY name;
""".strip()

EXEMPLE_SQL_COUNT_BY_SOURCE = """
SELECT s.name, COUNT(*) AS nb_articles
FROM raw_data r
JOIN source s ON s.source_id = r.source_id
GROUP BY s.name
ORDER BY nb_articles DESC;
""".strip()

EXEMPLE_SQL_FILTER_BY_DATE = """
SELECT r.raw_data_id, r.title, r.collected_at
FROM raw_data r
WHERE r.collected_at >= '2025-12-20'
ORDER BY r.collected_at DESC
LIMIT 50;
""".strip()

EXEMPLE_SQL_GOLD_VIEW = """
SELECT r.title,
       s.name AS source,
       t.label AS topic,
       mo.label AS sentiment,
       mo.score AS sentiment_score
FROM raw_data r
JOIN source s ON s.source_id = r.source_id
LEFT JOIN document_topic dt ON dt.raw_data_id = r.raw_data_id
LEFT JOIN topic t ON t.topic_id = dt.topic_id
LEFT JOIN model_output mo ON mo.raw_data_id = r.raw_data_id
WHERE mo.model_name = 'sentiment_keyword'
ORDER BY r.collected_at DESC
LIMIT 100;
""".strip()

EXEMPLE_SQL_EXPLAIN = """
EXPLAIN QUERY PLAN
SELECT raw_data_id, title
FROM raw_data
WHERE collected_at >= '2025-12-01';
""".strip()

EXEMPLE_SQL_AGGREGATE_RAW = """
SELECT r.raw_data_id as id, s.name as source, s.is_synthetic as is_synthetic, r.title, r.content, r.url,
       r.fingerprint, r.collected_at, r.quality_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
ORDER BY r.collected_at DESC;
""".strip()

EXEMPLE_SQL_AGGREGATE_SILVER = """
SELECT dt.raw_data_id, t.name as topic_name, dt.confidence_score,
       ROW_NUMBER() OVER (PARTITION BY dt.raw_data_id ORDER BY dt.confidence_score DESC) as rn
FROM document_topic dt
JOIN topic t ON dt.topic_id = t.topic_id;
""".strip()

EXEMPLE_SQL_AGGREGATE_GOLD = """
SELECT raw_data_id, label as sentiment, score as sentiment_score
FROM model_output
WHERE model_name = 'sentiment_keyword';
""".strip()

# ---------------------------------------------------------------------------
# C3 - Nettoyage minimal (pandas)
# ---------------------------------------------------------------------------
EXEMPLE_MINIMAL_CLEANING = """
import pandas as pd

def minimal_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df["title"] = df["title"].fillna("").str.strip()
    df["content"] = df["content"].fillna("").str.strip()
    df = df[(df["title"].str.len() > 3) & (df["content"].str.len() > 20)]
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")
    return df
""".strip()

# ---------------------------------------------------------------------------
# C2/C3 - PySpark requetes (DataFrame + SQL)
# ---------------------------------------------------------------------------
EXEMPLE_SPARK_QUERIES = """
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

PATH = "data/gold/date=2025-12-20"
spark = SparkSession.builder.getOrCreate()
df = spark.read.parquet(PATH)

df.select("source", "title", "sentiment").show(10, truncate=False)
df.filter(col("sentiment") == "positif").show(10, truncate=False)

df.createOrReplaceTempView("articles")
result = spark.sql(
    '''
    SELECT source, sentiment, COUNT(*) AS nb
    FROM articles
    GROUP BY source, sentiment
    ORDER BY nb DESC
    '''
)
result.show(20, truncate=False)
""".strip()

# ---------------------------------------------------------------------------
# C3 - GoldParquetReader
# ---------------------------------------------------------------------------
EXEMPLE_GOLD_PARQUET_READER = """
from datetime import date
from src.spark.adapters import GoldParquetReader

reader = GoldParquetReader()
df = reader.read_gold(date=date(2025, 12, 20))
df.show(5, truncate=False)
""".strip()

# ---------------------------------------------------------------------------
# C3 - GoldDataProcessor
# ---------------------------------------------------------------------------
EXEMPLE_GOLD_PROCESSOR = """
from src.spark.processors import GoldDataProcessor

processor = GoldDataProcessor()
# Exemple: processor.get_statistics(df_gold)
""".strip()

# ---------------------------------------------------------------------------
# A2 - API : exemples JSON (documentation)
# ---------------------------------------------------------------------------
EXEMPLE_SOURCES_JSON = """
[
  {"source_id": 1, "name": "google_news_rss", "source_type": "rss", "is_active": true},
  {"source_id": 2, "name": "reddit_france", "source_type": "api", "is_active": true}
]
""".strip()

EXEMPLE_RAW_DATA_JSON = """
[
  {
    "raw_data_id": 1201,
    "source_id": 2,
    "title": "Titre exemple",
    "content": "Contenu nettoye et tronque...",
    "collected_at": "2025-12-20T10:05:00"
  },
  {
    "raw_data_id": 1202,
    "source_id": 2,
    "title": "Autre titre",
    "content": "Texte extrait depuis la source...",
    "collected_at": "2025-12-20T10:06:00"
  }
]
""".strip()

EXEMPLE_MODEL_OUTPUT_JSON = """
{
  "raw_data_id": 1201,
  "model_name": "sentiment_keyword",
  "label": "neutre",
  "score": 0.52,
  "confidence": 0.58,
  "created_at": "2025-12-20T10:05:12"
}
""".strip()

# ---------------------------------------------------------------------------
# A2 - CRUD FastAPI (exemple REST, base SQLite)
# ---------------------------------------------------------------------------
EXEMPLE_FASTAPI_CRUD = """
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "datasens.db"
app = FastAPI(title="DataSens E1 CRUD Example")


class SourceIn(BaseModel):
    name: str
    source_type: str
    url: str | None = None
    sync_frequency: str | None = None
    is_active: bool = True
    is_synthetic: bool = False


class SourceOut(SourceIn):
    source_id: int


def _conn():
    return sqlite3.connect(DB_PATH)


@app.get("/sources", response_model=list[SourceOut])
def list_sources():
    conn = _conn()
    rows = conn.execute(
        "SELECT source_id, name, source_type, url, sync_frequency, active, is_synthetic FROM source"
    ).fetchall()
    conn.close()
    return [
        {
            "source_id": r[0],
            "name": r[1],
            "source_type": r[2],
            "url": r[3],
            "sync_frequency": r[4],
            "is_active": bool(r[5]),
            "is_synthetic": bool(r[6]),
        }
        for r in rows
    ]


@app.post("/sources", response_model=SourceOut)
def create_source(payload: SourceIn):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO source (name, source_type, url, sync_frequency, active, is_synthetic)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (
            payload.name,
            payload.source_type,
            payload.url,
            payload.sync_frequency or "DAILY",
            payload.is_active,
            payload.is_synthetic,
        ),
    )
    conn.commit()
    source_id = cur.lastrowid
    conn.close()
    return SourceOut(source_id=source_id, **payload.dict())


@app.get("/sources/{source_id}", response_model=SourceOut)
def get_source(source_id: int):
    conn = _conn()
    row = conn.execute(
        "SELECT source_id, name, source_type, url, sync_frequency, active, is_synthetic FROM source WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "source_id": row[0],
        "name": row[1],
        "source_type": row[2],
        "url": row[3],
        "sync_frequency": row[4],
        "is_active": bool(row[5]),
        "is_synthetic": bool(row[6]),
    }


@app.put("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceIn):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        '''
        UPDATE source
        SET name = ?, source_type = ?, url = ?, sync_frequency = ?, active = ?, is_synthetic = ?
        WHERE source_id = ?
        ''',
        (
            payload.name,
            payload.source_type,
            payload.url,
            payload.sync_frequency or "DAILY",
            payload.is_active,
            payload.is_synthetic,
            source_id,
        ),
    )
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Source not found")
    conn.close()
    return SourceOut(source_id=source_id, **payload.dict())


@app.delete("/sources/{source_id}")
def delete_source(source_id: int):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM source WHERE source_id = ?", (source_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "deleted", "source_id": source_id}
""".strip()
