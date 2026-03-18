# 🗺️ CHEMIN DE LA DONNÉE - Résumé Visuel

## 📊 FLOW COMPLET

```
┌─────────────────────────────────────────────────────────────────┐
│ SOURCES                                                          │
├─────────────────────────────────────────────────────────────────┤
│ RSS:      rss_french_news, google_news_rss, yahoo_finance       │
│ API:      openweather_api, insee_indicators, reddit_france      │
│ Scraping: trustpilot_reviews, ifop_barometers                   │
│ Local:    Kaggle_* (CSV/JSON), gdelt_* (JSON)                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 1️⃣ COLLECT (Extraction)                                         │
├─────────────────────────────────────────────────────────────────┤
│ • RSS/API/Scraping → Articles en mémoire (Article objects)       │
│ • Kaggle/GDELT → SKIP (fichiers locaux, fusionnés plus tard)   │
│                                                                  │
│ Format: Article(title, content, url, source_name, published_at) │
│ Emplacement: RAM (mémoire)                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2️⃣ CLEAN (Nettoyage)                                            │
├─────────────────────────────────────────────────────────────────┤
│ • Suppression HTML (BeautifulSoup)                              │
│ • Normalisation espaces (regex)                                 │
│ • Validation (title > 3 chars, content > 10 chars)              │
│                                                                  │
│ Format: Article nettoyé                                          │
│ Emplacement: RAM (mémoire)                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3️⃣ LOAD (Chargement DB)                                         │
├─────────────────────────────────────────────────────────────────┤
│ • Déduplication par fingerprint (SHA256)                        │
│ • Insertion → raw_data table                                    │
│ • Backup → data/raw/sources_YYYY-MM-DD/raw_articles.json       │
│                                                                  │
│ Format: SQLite (raw_data table)                                 │
│ Emplacement: datasens.db + data/raw/sources_*/                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4️⃣ TAG (Classification Topics)                                  │
├─────────────────────────────────────────────────────────────────┤
│ • Analyse title+content avec mots-clés                          │
│ • Top 2 topics → document_topic table                          │
│                                                                  │
│ Format: SQLite (document_topic table)                           │
│ Emplacement: datasens.db                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5️⃣ ANALYZE (Sentiment)                                          │
├─────────────────────────────────────────────────────────────────┤
│ • Compte mots positifs/négatifs                                 │
│ • Classification → model_output table                           │
│                                                                  │
│ Format: SQLite (model_output table)                             │
│ Emplacement: datasens.db                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6️⃣ AGGREGATE (Fusion)                                           │
├─────────────────────────────────────────────────────────────────┤
│ • Requêtes SQL: raw_data + document_topic + model_output        │
│ • Lecture fichiers locaux: Kaggle_*/**/*.csv, gdelt_*/**/*.json │
│ • Merge topics (topic_1, topic_2) + sentiment                  │
│ • Concat DB DataFrame + Local Files DataFrame                   │
│                                                                  │
│ Format: Pandas DataFrame                                        │
│ Colonnes: id, source, title, content, url, collected_at,       │
│           topic_1, topic_1_score, topic_2, topic_2_score,       │
│           sentiment, sentiment_score                            │
│ Emplacement: RAM (mémoire)                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7️⃣ GOLD (Export Final)                                          │
├─────────────────────────────────────────────────────────────────┤
│ • Parquet → data/gold/date=YYYY-MM-DD/articles.parquet         │
│ • CSV → exports/gold.csv                                        │
│                                                                  │
│ Format: Parquet (partitionné) + CSV (annoté)                   │
│ Emplacement: data/gold/ + exports/                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 EMPLACEMENTS FICHIERS

### Pendant le Pipeline

| Étape | Fichier/Dossier | Contenu |
|-------|----------------|---------|
| **COLLECT** | RAM | Articles en mémoire (`Article` objects) |
| **CLEAN** | RAM | Articles nettoyés (`Article` objects) |
| **LOAD** | `datasens.db` → `raw_data` | Articles en DB |
| **LOAD** | `data/raw/sources_2025-12-18/raw_articles.json` | Backup JSON |
| **LOAD** | `data/raw/sources_2025-12-18/raw_articles.csv` | Backup CSV |
| **TAG** | `datasens.db` → `document_topic` | Topics (max 2) |
| **ANALYZE** | `datasens.db` → `model_output` | Sentiment |
| **AGGREGATE** | RAM | DataFrame pandas (DB + fichiers locaux) |
| **GOLD** | `data/gold/date=2025-12-18/articles.parquet` | **FINAL Parquet** |
| **GOLD** | `exports/gold.csv` | **FINAL CSV** |

### Fichiers Locaux (Fusionnés dans GOLD)

| Source | Emplacement | Format |
|--------|-------------|--------|
| Kaggle | `data/raw/Kaggle_*/**/*.csv` | CSV |
| Kaggle | `data/raw/Kaggle_*/**/*.json` | JSON |
| GDELT | `data/raw/gdelt_*/**/*.json` | JSON |

---

## 🔍 EXEMPLE CONCRET

### Article Source (Yahoo Finance RSS)
```
URL: https://finance.yahoo.com/rss/headline?region=FR
Title: "CAC 40 en hausse de 2%"
Content: "<p>Le CAC 40 a progressé de 2% aujourd'hui...</p>"
```

### Après COLLECT
```python
Article(
    title="CAC 40 en hausse de 2%",
    content="<p>Le CAC 40 a progressé de 2% aujourd'hui...</p>",
    url="https://finance.yahoo.com/news/...",
    source_name="yahoo_finance"
)
```
**Emplacement**: RAM

### Après CLEAN
```python
Article(
    title="CAC 40 en hausse de 2%",
    content="Le CAC 40 a progressé de 2% aujourd'hui...",  # HTML supprimé
    ...
)
```
**Emplacement**: RAM

### Après LOAD
```sql
-- Table raw_data
raw_data_id = 1500
source_id = 11
title = "CAC 40 en hausse de 2%"
content = "Le CAC 40 a progressé de 2% aujourd'hui..."
fingerprint = "abc123def456..."
```
**Emplacement**: `datasens.db` + `data/raw/sources_2025-12-18/raw_articles.json`

### Après TAG
```sql
-- Table document_topic
raw_data_id = 1500
topic_id = 1 (finance)
confidence_score = 0.92
```
**Emplacement**: `datasens.db`

### Après ANALYZE
```sql
-- Table model_output
raw_data_id = 1500
label = "positif"
score = 0.78
```
**Emplacement**: `datasens.db`

### Après AGGREGATE
```python
DataFrame:
  id=1500
  source='yahoo_finance'
  title='CAC 40 en hausse de 2%'
  content='Le CAC 40 a progressé de 2% aujourd'hui...'
  topic_1='finance'
  topic_1_score=0.92
  topic_2=''
  topic_2_score=0.0
  sentiment='positif'
  sentiment_score=0.78
```
**Emplacement**: RAM

### Après GOLD
```
Fichier: data/gold/date=2025-12-18/articles.parquet
Fichier: exports/gold.csv

Ligne CSV:
1500,yahoo_finance,"CAC 40 en hausse de 2%","Le CAC 40...",https://...,2025-12-18,finance,0.92,,0.0,positif,0.78
```
**Emplacement**: `data/gold/date=2025-12-18/` + `exports/`

---

## 📊 STATISTIQUES PAR ÉTAPE

| Étape | Input | Output | Exemple |
|-------|-------|--------|---------|
| COLLECT | 0 articles | 95 articles | RSS/API/Scraping extraits |
| CLEAN | 95 articles | 95 articles | HTML supprimé |
| LOAD | 95 articles | 43 nouveaux en DB | 52 dupliqués |
| TAG | 43 articles | 12 taggés | Topics ajoutés |
| ANALYZE | 43 articles | 43 analysés | Sentiment ajouté |
| AGGREGATE | DB (1499) + Local files | 1499+ articles | DataFrame fusionné |
| GOLD | DataFrame | Parquet + CSV | Export final |

---

## ✅ RÉSUMÉ

**Pipeline simplifié**:
1. **COLLECT** → RSS/API/Scraping (mémoire)
2. **CLEAN** → Nettoyage (mémoire)
3. **LOAD** → DB + Backup JSON/CSV
4. **TAG** → Topics en DB (max 2)
5. **ANALYZE** → Sentiment en DB
6. **AGGREGATE** → DB + Fichiers locaux → DataFrame
7. **GOLD** → Parquet + CSV annoté

**Fichiers finaux**:
- `data/gold/date=YYYY-MM-DD/articles.parquet` (Parquet partitionné)
- `exports/gold.csv` (CSV annoté avec topics + sentiment)

---

**Voir**: `docs/DATA_FLOW.md` pour détails complets

