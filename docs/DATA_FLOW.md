# 📊 CHEMIN DE LA DONNÉE - DataSens E1 Pipeline

**Objectif**: Visualiser le parcours complet de la donnée de la source au GOLD

---

## 🗺️ VUE D'ENSEMBLE

```
SOURCES → COLLECT → CLEAN → LOAD → TAG → ANALYZE → AGGREGATE → GOLD
```

---

## 📥 ÉTAPE 1 : COLLECT (Extraction)

### Sources

| Type | Sources | Format Source | Emplacement |
|------|---------|--------------|-------------|
| **RSS** | `rss_french_news`, `google_news_rss`, `yahoo_finance` | XML/RSS Feed | URL en ligne |
| **API** | `openweather_api`, `insee_indicators`, `reddit_france` | JSON/HTTP | URL en ligne |
| **Scraping** | `trustpilot_reviews`, `ifop_barometers` | HTML | URL en ligne |
| **Kaggle** | `Kaggle_FrenchFinNews`, `Kaggle_InsuranceReviews`, etc. | CSV/JSON | **Local** `data/raw/Kaggle_*/` |
| **GDELT** | `gdelt_events`, `GDELT_Last15_English` | JSON/CSV | **Local** `data/raw/gdelt_*/` |

### Extraction

**Code**: `main.py` → `extract()` → `src/core.py` (extractors)

**Processus**:
1. Lecture `sources_config.json`
2. Pour chaque source active :
   - RSS → `feedparser.parse(url)`
   - API → `requests.get(url).json()`
   - Scraping → `BeautifulSoup(requests.get(url))`
   - Kaggle/GDELT → **SKIP** (déjà en local, fusionné plus tard)

**Résultat**:
- Liste d'objets `Article` en mémoire
- Format : `Article(title, content, url, source_name, published_at)`

**Exemple**:
```python
Article(
    title="Météo Paris: 15°C",
    content="Condition: ensoleillé, température 15°C",
    url="https://weather.com/...",
    source_name="openweather_api",
    published_at="2025-12-18T10:00:00"
)
```

---

## 🧹 ÉTAPE 2 : CLEAN (Nettoyage)

### Transformation

**Code**: `main.py` → `clean()` → `src/core.py` → `ContentTransformer`

**Processus**:
1. **Nettoyage HTML** : `BeautifulSoup(text).get_text()` → Supprime balises HTML
2. **Normalisation** : `re.sub(r'\s+', ' ', text)` → Espaces multiples → 1 espace
3. **Validation** : `article.is_valid()` → Vérifie `len(title) > 3` et `len(content) > 10`

**Résultat**:
- Articles nettoyés (même format `Article`)
- HTML supprimé, texte normalisé

**Exemple**:
```python
# Avant
content = "<p>Météo   Paris:   15°C</p>"

# Après
content = "Météo Paris: 15°C"
```

---

## 💾 ÉTAPE 3 : LOAD (Chargement DB)

### Stockage Base de Données

**Code**: `main.py` → `load()` → `src/repository.py` → `Repository.load_article_with_id()`

**Processus**:
1. **Déduplication** : Calcul `fingerprint = SHA256(title|content)`
2. **Insertion DB** : Table `raw_data`
   ```sql
   INSERT INTO raw_data (source_id, title, content, url, fingerprint, published_at, collected_at, quality_score)
   ```
3. **Récupération ID** : `SELECT raw_data_id WHERE fingerprint = ?`

**Résultat**:
- Articles dans la DB (`raw_data` table)
- `raw_data_id` récupéré pour chaque article

**Fichiers générés**:
- `data/raw/sources_2025-12-18/raw_articles.json` (backup)
- `data/raw/sources_2025-12-18/raw_articles.csv` (backup)

**Schéma DB**:
```
raw_data
├── raw_data_id (PK)
├── source_id (FK → source)
├── title
├── content
├── url
├── fingerprint (UNIQUE, pour déduplication)
├── published_at
├── collected_at
└── quality_score
```

---

## 🏷️ ÉTAPE 4 : TAG (Classification Topics)

### Tagging Topics

**Code**: `main.py` → `load()` → `src/tagger.py` → `TopicTagger.tag()`

**Processus**:
1. **Classification** : Analyse `title + content` avec mots-clés
2. **Top 2 Topics** : Retourne les 2 topics avec meilleur score
3. **Insertion DB** : Table `document_topic` (max 2 par article)
   ```sql
   INSERT INTO document_topic (raw_data_id, topic_id, confidence_score, tagger)
   ```

**Résultat**:
- Topics stockés dans `document_topic`
- Maximum 2 topics par article

**Schéma DB**:
```
document_topic
├── doc_topic_id (PK)
├── raw_data_id (FK → raw_data)
├── topic_id (FK → topic)
├── confidence_score (0.0-1.0)
└── tagger ('keyword')
```

**Exemple**:
```python
# Article: "Budget 2025: augmentation des impôts"
# Topics détectés:
document_topic(1) → topic_id=2 (finance), confidence=0.85
document_topic(2) → topic_id=1 (politique), confidence=0.72
```

---

## 🎭 ÉTAPE 5 : ANALYZE (Sentiment)

### Analyse Sentiment

**Code**: `main.py` → `load()` → `src/analyzer.py` → `SentimentAnalyzer.save()`

**Processus**:
1. **Analyse** : Compte mots positifs/négatifs dans `title + content`
2. **Classification** : `'positif'` | `'neutre'` | `'négatif'` + score (0.0-1.0)
3. **Insertion DB** : Table `model_output`
   ```sql
   INSERT INTO model_output (raw_data_id, model_name, label, score, created_at)
   ```

**Résultat**:
- Sentiment stocké dans `model_output`

**Schéma DB**:
```
model_output
├── output_id (PK)
├── raw_data_id (FK → raw_data)
├── model_name ('sentiment_keyword')
├── label ('positif'|'neutre'|'négatif')
├── score (0.0-1.0)
└── created_at
```

**Exemple**:
```python
# Article: "Excellent service, très satisfait"
# Sentiment:
model_output → label='positif', score=0.87
```

---

## 🔄 ÉTAPE 6 : AGGREGATE (Fusion)

### Agrégation DB + Fichiers Locaux

**Code**: `main.py` → `run()` → `src/aggregator.py` → `DataAggregator.aggregate()`

**Processus**:

#### 6.1. Données DB
```sql
-- Articles de la DB
SELECT r.raw_data_id as id, s.name as source, r.title, r.content, r.url, r.collected_at
FROM raw_data r JOIN source s ON r.source_id = s.source_id

-- Topics (max 2)
SELECT dt.raw_data_id, t.name as topic_name, dt.confidence_score, ROW_NUMBER()...
FROM document_topic dt JOIN topic t ON dt.topic_id = t.topic_id

-- Sentiment
SELECT raw_data_id, label as sentiment, score as sentiment_score
FROM model_output WHERE model_name = 'sentiment_keyword'
```

#### 6.2. Fichiers Locaux (Kaggle/GDELT)
- Lecture récursive de `data/raw/Kaggle_*/**/*.csv`
- Lecture récursive de `data/raw/Kaggle_*/**/*.json`
- Lecture récursive de `data/raw/gdelt_*/**/*.json`
- Extraction `title`, `content` depuis fichiers

#### 6.3. Fusion
- **Merge topics** : `topic_1`, `topic_1_score`, `topic_2`, `topic_2_score`
- **Merge sentiment** : `sentiment`, `sentiment_score`
- **Concat** : DB DataFrame + Local Files DataFrame

**Résultat**:
- DataFrame pandas avec toutes les colonnes :
  ```
  id, source, title, content, url, collected_at,
  topic_1, topic_1_score, topic_2, topic_2_score,
  sentiment, sentiment_score
  ```

**Exemple DataFrame**:
```python
   id  source              title                    topic_1    topic_1_score  topic_2      topic_2_score  sentiment  sentiment_score
0  1   google_news_rss    "Budget 2025..."        finance    0.85          politique    0.72          neutre     0.5
1  2   yahoo_finance       "CAC 40 en hausse..."   finance    0.92          ''           0.0           positif    0.78
3  100 Kaggle_FrenchFinNews "Actualité bourse..." finance    0.88          ''           0.0           neutre     0.5
```

---

## 🏆 ÉTAPE 7 : GOLD (Export Final)

### Export Parquet + CSV

**Code**: `main.py` → `run()` → `src/exporter.py` → `GoldExporter.export_all()`

**Processus**:
1. **Parquet** : `df.to_parquet('data/gold/date=2025-12-18/articles.parquet')`
2. **CSV** : `df.to_csv('exports/gold.csv')`

**Résultat**:
- **Parquet** : `data/gold/date=YYYY-MM-DD/articles.parquet` (partitionné par date)
- **CSV** : `exports/gold.csv` (annoté avec topics + sentiment)

**Colonnes GOLD**:
```
id, source, title, content, url, collected_at,
topic_1, topic_1_score, topic_2, topic_2_score,
sentiment, sentiment_score
```

---

## 📂 STRUCTURE FICHIERS

### RAW Zone
```
data/raw/
├── sources_2025-12-18/
│   ├── raw_articles.json      ← Backup articles du jour (RSS/API/Scraping)
│   └── raw_articles.csv       ← Backup CSV
├── Kaggle_FrenchFinNews/
│   └── date=2025-12-17/
│       └── *.csv              ← Fichiers locaux (fusionnés dans GOLD)
└── gdelt_events/
    └── date=2025-12-17/
        └── *.json              ← Fichiers locaux (fusionnés dans GOLD)
```

### SILVER Zone
```
data/silver/
└── v_2025-12-16/
    └── silver_articles.parquet ← (Optionnel, pas utilisé actuellement)
```

### GOLD Zone
```
data/gold/
└── date=2025-12-18/
    └── articles.parquet        ← FINAL : DB + Local files fusionnés

exports/
└── gold.csv                    ← FINAL : CSV annoté (topics + sentiment)
```

---

## 🔄 FLOW COMPLET

```
┌─────────────────────────────────────────────────────────────┐
│ 1. COLLECT (Extraction)                                      │
│    RSS/API/Scraping → Articles en mémoire                   │
│    Kaggle/GDELT → SKIP (fichiers locaux)                    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CLEAN (Nettoyage)                                         │
│    HTML → Texte pur                                         │
│    Normalisation espaces                                     │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. LOAD (DB)                                                 │
│    Articles → raw_data table                                │
│    Backup → data/raw/sources_YYYY-MM-DD/raw_articles.json │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. TAG (Topics)                                              │
│    Classification → document_topic (max 2)                  │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. ANALYZE (Sentiment)                                       │
│    Analyse → model_output                                   │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. AGGREGATE (Fusion)                                        │
│    DB (raw_data + document_topic + model_output)            │
│    + Fichiers locaux (Kaggle/GDELT)                         │
│    → DataFrame pandas                                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. GOLD (Export)                                             │
│    Parquet → data/gold/date=YYYY-MM-DD/articles.parquet    │
│    CSV → exports/gold.csv                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 EXEMPLE CONCRET

### Article Source (RSS)
```
Source: yahoo_finance
URL: https://finance.yahoo.com/news/...
Title: "CAC 40 en hausse de 2%"
Content: "Le CAC 40 a progressé de 2% aujourd'hui..."
```

### Après COLLECT
```python
Article(
    title="CAC 40 en hausse de 2%",
    content="Le CAC 40 a progressé de 2% aujourd'hui...",
    url="https://finance.yahoo.com/news/...",
    source_name="yahoo_finance"
)
```

### Après CLEAN
```python
Article(
    title="CAC 40 en hausse de 2%",
    content="Le CAC 40 a progressé de 2% aujourd'hui...",  # HTML supprimé
    ...
)
```

### Après LOAD (DB)
```sql
raw_data:
  raw_data_id = 1500
  source_id = 11 (yahoo_finance)
  title = "CAC 40 en hausse de 2%"
  content = "Le CAC 40 a progressé de 2% aujourd'hui..."
  fingerprint = "abc123..."
```

### Après TAG
```sql
document_topic:
  raw_data_id = 1500
  topic_id = 1 (finance)
  confidence_score = 0.92
```

### Après ANALYZE
```sql
model_output:
  raw_data_id = 1500
  label = "positif"
  score = 0.78
```

### Après AGGREGATE
```python
DataFrame:
  id=1500, source='yahoo_finance', title='CAC 40 en hausse...',
  topic_1='finance', topic_1_score=0.92,
  topic_2='', topic_2_score=0.0,
  sentiment='positif', sentiment_score=0.78
```

### Après GOLD
```
Fichier: data/gold/date=2025-12-18/articles.parquet
Fichier: exports/gold.csv

Ligne CSV:
1500,yahoo_finance,"CAC 40 en hausse de 2%","Le CAC 40...",https://...,2025-12-18,finance,0.92,,0.0,positif,0.78
```

---

## 🎯 RÉSUMÉ

| Étape | Input | Output | Format | Emplacement |
|-------|-------|--------|--------|-------------|
| **COLLECT** | URLs (RSS/API/Scraping) | Articles (mémoire) | `Article` objects | RAM |
| **CLEAN** | Articles (mémoire) | Articles nettoyés | `Article` objects | RAM |
| **LOAD** | Articles nettoyés | DB + Backup JSON/CSV | SQLite + JSON/CSV | `datasens.db` + `data/raw/sources_*/` |
| **TAG** | Articles DB | Topics DB | SQLite | `document_topic` table |
| **ANALYZE** | Articles DB | Sentiment DB | SQLite | `model_output` table |
| **AGGREGATE** | DB + Fichiers locaux | DataFrame | Pandas DataFrame | RAM |
| **GOLD** | DataFrame | Parquet + CSV | Parquet + CSV | `data/gold/` + `exports/` |

---

**Status**: ✅ Pipeline complet documenté  
**Prochaine étape**: Tester le pipeline et vérifier le flow

