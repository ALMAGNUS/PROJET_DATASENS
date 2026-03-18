# 🗄️ Architecture des Bases de Données - DataSens

## Vue d'Ensemble

Le projet DataSens utilise une **architecture multi-bases de données** avec communication inter-bases :

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE E1 → E2                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   ZZDB SQLite    │         │  DataSens SQLite │         │  PySpark (E2)    │
│  (LAB IA)        │         │  (Base Principale)│         │  (Big Data)      │
│                  │         │                  │         │                  │
│  - Synthétique   │         │  - Production    │         │  - Analytics     │
│  - 1,189 articles│         │  - 2,000+ articles│         │  - Parquet      │
│  - Climat FR     │         │  - Enrichi       │         │  - Distribué    │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
         │ LECTURE (SELECT)           │                            │
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   Pipeline E1 (main.py) │
                         │                         │
                         │  - Extract              │
                         │  - Clean                │
                         │  - Load                 │
                         │  - Enrich               │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │   Pipeline E2 (futur)   │
                         │                         │
                         │  - Spark Transform      │
                         │  - ML Models            │
                         │  - Analytics            │
                         └─────────────────────────┘
```

---

## 📊 Base 1 : ZZDB SQLite (LAB IA)

### Caractéristiques

- **Rôle** : Base de données synthétique pour recherche académique
- **Emplacement** : `zzdb/synthetic_data.db`
- **Type** : SQLite (non relationnelle, table unique)
- **Contenu** : 1,189 articles synthétiques spécialisés
- **Thèmes** : Climat social, politique, économique, financier français

### Schéma

```sql
CREATE TABLE synthetic_articles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    sentiment TEXT,              -- positif, négatif, neutre
    theme TEXT,                  -- social, économique, finance, politique
    source_type TEXT,            -- api, rss, web_scraping, synthetic_lab
    region TEXT,                 -- Régions françaises
    keywords TEXT,               -- Mots-clés séparés par virgules
    author TEXT,
    language TEXT DEFAULT 'fr',
    word_count INTEGER,
    published_at DATETIME,
    collected_at DATETIME,
    created_at DATETIME
);
```

### Accès

- **Mode** : Lecture seule depuis le pipeline
- **Extractor** : `SQLiteExtractor` (src/core.py)
- **Garde-fous** :
  - `DISABLE_ZZDB` : Variable d'environnement
  - `ZZDB_MAX_ARTICLES` : Limite max (défaut: 50)
  - Filtre temporel : `published_at < datetime('now', '-1 hour')`

---

## 📊 Base 2 : DataSens SQLite (Base Principale)

### Caractéristiques

- **Rôle** : Base de données principale de production
- **Emplacement** : `~/datasens_project/datasens.db`
- **Type** : SQLite relationnelle (6 tables)
- **Contenu** : 2,000+ articles enrichis (topics + sentiment)

### Schéma

```sql
-- 1. SOURCE
CREATE TABLE source (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    acquisition_type VARCHAR(50),
    url TEXT,
    description TEXT,
    active BOOLEAN DEFAULT 1
);

-- 2. RAW_DATA
CREATE TABLE raw_data (
    raw_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(source_id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    fingerprint VARCHAR(64) UNIQUE,  -- SHA256 pour déduplication
    published_at DATETIME,
    collected_at DATETIME,
    quality_score FLOAT DEFAULT 0.5  -- 0.3 pour ZZDB, 0.5 pour sources réelles
);

-- 3. SYNC_LOG
CREATE TABLE sync_log (
    sync_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES source(source_id),
    sync_date DATETIME,
    rows_synced INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    error_message TEXT
);

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
    confidence_score FLOAT DEFAULT 0.5
);

-- 6. MODEL_OUTPUT
CREATE TABLE model_output (
    output_id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_data_id INTEGER NOT NULL REFERENCES raw_data(raw_data_id),
    model_name VARCHAR(100) NOT NULL,
    label VARCHAR(50),
    score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Accès

- **Mode** : Lecture/Écriture
- **Repository** : `Repository` (src/repository.py)
- **Fonctionnalités** :
  - Déduplication par `fingerprint` (SHA256)
  - Enrichissement automatique (topics + sentiment)
  - Quality scoring (0.3 pour ZZDB, 0.5 pour sources réelles)

---

## 📊 Base 3 : PySpark (E2 - Futur)

### Caractéristiques (Prévu)

- **Rôle** : Big Data analytics et ML
- **Type** : PySpark DataFrame / Parquet
- **Format** : Parquet partitionné par date
- **Emplacement** : `data/gold/date=YYYY-MM-DD/`

### Schéma Prévisionnel

```python
# DataFrame Spark avec colonnes enrichies
schema = StructType([
    StructField("id", IntegerType()),
    StructField("source", StringType()),
    StructField("title", StringType()),
    StructField("content", StringType()),
    StructField("sentiment", StringType()),
    StructField("topics", ArrayType(StringType())),
    StructField("quality_score", FloatType()),
    StructField("source_type", StringType()),  # real_source, db_non_relational, flat_files
    StructField("collected_at", TimestampType()),
    StructField("date", DateType())
])
```

---

## 🔄 Communication Inter-Bases

### E1 : ZZDB → DataSens

**Flux** : Unidirectionnel (ZZDB → Pipeline → DataSens)

```python
# 1. LECTURE depuis ZZDB
conn_zzdb = sqlite3.connect('zzdb/synthetic_data.db')
cursor = conn_zzdb.cursor()
cursor.execute("SELECT title, content, url, published_at FROM synthetic_articles LIMIT 50")
rows = cursor.fetchall()

# 2. TRANSFORMATION
articles = []
for row in rows:
    article = Article(title=row[0], content=row[1], url=row[2], 
                     source_name='zzdb_synthetic', published_at=row[3])
    articles.append(article)

# 3. ÉCRITURE dans DataSens
conn_datasens = sqlite3.connect('datasens.db')
repository = Repository(conn_datasens)
for article in articles:
    source_id = repository.get_source_id('zzdb_synthetic')
    repository.load_article_with_id(article, source_id)  # quality_score=0.3
```

**Garde-fous** :
- Déduplication par `fingerprint` (évite les doublons)
- Quality score réduit (0.3 vs 0.5)
- Limite max par exécution (50 articles)

---

### E2 : DataSens → PySpark (Futur)

**Flux** : Unidirectionnel (DataSens → Spark Transform → Parquet)

```python
# 1. LECTURE depuis DataSens
df = spark.read.format("jdbc") \
    .option("url", "jdbc:sqlite:datasens.db") \
    .option("dbtable", "raw_data") \
    .load()

# 2. TRANSFORMATION Spark
df_enriched = df \
    .join(topics_df, "raw_data_id") \
    .join(sentiment_df, "raw_data_id") \
    .withColumn("date", to_date("collected_at")) \
    .withColumn("source_type", classify_source_udf("source"))

# 3. ÉCRITURE Parquet partitionné
df_enriched.write \
    .mode("overwrite") \
    .partitionBy("date", "source_type") \
    .parquet("data/gold/")
```

---

## 🔍 Identification des Sources

### Classification dans DataSens

```python
def classify_source(source_name: str) -> str:
    """Classifie le type de source"""
    source_lower = source_name.lower()
    if 'zzdb' in source_lower:
        return 'db_non_relational'  # Base de données non relationnelle
    elif 'kaggle' in source_lower:
        return 'flat_files'  # Fichiers plats (CSV/JSON)
    else:
        return 'real_source'  # Source réelle (RSS, API, Scraping)
```

### Colonne `source_type` dans Exports

- **RAW/SILVER/GOLD** : Contiennent `source_type` pour identifier l'origine
- **Rapports** : Classifient les sources (ZZDB [LAB IA], Kaggle [FICHIERS PLATS], etc.)

---

## 📈 Évolution Architecture

### E1 (Actuel)

```
ZZDB SQLite ──READ──> Pipeline E1 ──WRITE──> DataSens SQLite
                                    └─EXPORT──> CSV/Parquet
```

### E2 (Futur)

```
ZZDB SQLite ──READ──> Pipeline E1 ──WRITE──> DataSens SQLite
                                    └─READ──> Spark Transform
                                              └─WRITE──> PySpark Parquet
                                                         └─ML Models
```

### E3 (Vision)

```
ZZDB SQLite ──READ──> Pipeline E1 ──WRITE──> DataSens SQLite
                                    └─READ──> Spark Transform
                                              └─WRITE──> PySpark Parquet
                                                         └─ML Models
                                                           └─API──> FastAPI
```

---

## 🔐 Isolation et Sécurité

### Isolation Complète

- ✅ **ZZDB** : Isolé dans `zzdb/` (pas de dépendance circulaire)
- ✅ **DataSens** : Base principale indépendante
- ✅ **PySpark** : Format Parquet (pas de dépendance SQLite)

### Garde-fous Multiples

1. **Volume** : Limites max par source (ZZDB: 50, CSV: 100)
2. **Qualité** : Quality scoring différencié (0.3 vs 0.5)
3. **Déduplication** : Fingerprint SHA256
4. **Validation** : Contenu, longueur, répétitivité
5. **Temporel** : Filtres de date pour éviter re-collecte

---

## 📝 Commandes Utiles

### Vérifier Communication ZZDB → DataSens

```bash
# Compter articles ZZDB dans DataSens
python scripts/query_sqlite.py "SELECT COUNT(*) FROM raw_data r JOIN source s ON r.source_id = s.source_id WHERE s.name LIKE '%zzdb%'"
```

### Vérifier Quality Score ZZDB

```bash
python scripts/query_sqlite.py "SELECT AVG(quality_score) FROM raw_data r JOIN source s ON r.source_id = s.source_id WHERE s.name LIKE '%zzdb%'"
```

### Voir Articles ZZDB avec Enrichissement

```bash
python scripts/query_sqlite.py "SELECT r.title, mo.label as sentiment FROM raw_data r JOIN source s ON r.source_id = s.source_id LEFT JOIN model_output mo ON mo.raw_data_id = r.raw_data_id WHERE s.name = 'zzdb_synthetic' LIMIT 5"
```

---

## 🎯 Résumé

| Base | Type | Rôle | Mode Accès | Communication |
|------|------|------|------------|---------------|
| **ZZDB** | SQLite | Synthétique (LAB IA) | Lecture seule | → Pipeline E1 |
| **DataSens** | SQLite | Production principale | Lecture/Écriture | ← Pipeline E1, → E2 |
| **PySpark** | Parquet | Big Data Analytics | Lecture/Écriture | ← DataSens (E2) |

**Architecture prête pour E2 : Communication inter-bases opérationnelle** ✅
