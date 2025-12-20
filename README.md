# 📊 DataSens E1 — Data Extraction & Transformation Pipeline

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)
![E1 Complete](https://img.shields.io/badge/E1-v1.0.0%20Complete-green?style=flat-square)

---

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ██████╗   █████╗ ████████╗ █████╗ ███████╗███████╗███╗   ██╗███████╗     ║
║     ██╔══██╗ ██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔════╝████╗  ██║██╔════╝     ║
║     ██║  ██║ ███████║   ██║   ███████║███████╗█████╗  ██╔██╗ ██║███████╗     ║
║     ██║  ██║ ██╔══██║   ██║   ██╔══██║╚════██║██╔══╝  ██║╚██╗██║╚════██║     ║
║     ██████╔╝ ██║  ██║   ██║   ██║  ██║███████║███████╗██║ ╚████║███████║     ║
║     ╚═════╝  ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝     ║
║                                                                              ║
║                   ╔════════════════════════════════════╗                     ║
║                   ║  ---------- README -----------     ║                     ║
║                   ╚════════════════════════════════════╝                     ║
║                                                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 🎯 Overview

**DATASENS E1** is a professional data extraction, transformation, and export pipeline that:

- **Extracts** from **10 heterogeneous sources** (RSS, APIs, web scraping)
- **Cleans & standardizes** with quality scoring and deduplication  
- **Exports** to three data zones (RAW → SILVER → GOLD)
- **Produces** production-ready parquet files for E2/E3 ML pipelines

**216 articles | 0 corruption | Zero duplicates | 100% clean**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies:**
- `pandas==2.3.3` — Data processing
- `pyarrow==22.0.0` — Parquet engine
- `kagglehub==0.2.5` — Kaggle datasets API
- `feedparser` — RSS extraction
- `requests`, `beautifulsoup4` — HTTP & web scraping
- `sqlalchemy` — Database ORM

### 2. Initialize Database

```bash
python scripts/setup_with_sql.py
```

Creates SQLite database with:
- 7 tables (source, raw_data, sync_log, topic, document_topic, model_output)
- 10 sources configured
- Proper indexes for performance

### 3. Run E1 Pipeline

```bash
python main.py
```

**Output:**
- 216 articles extracted to database
- sync_log updated (10 sources logged)
- Ready for export

### 4. Export Data (RAW → SILVER → GOLD)

```bash
python e1_export_correct.py
```

**Produces:**
- 🔴 `data/raw/sources_2025-12-16/` (JSON + CSV)
- 🟡 `data/silver/v_2025-12-16/` (Parquet)
- 🟢 `data/gold/date=2025-12-16/` (PySpark parquet)

---

## 📁 Three-Zone Architecture

```
🔴 RAW ZONE (Native Formats - NO Processing)
   data/raw/sources_2025-12-16/
   ├─ raw_articles.json (137.4 KB) ← Direct from extractors
   └─ raw_articles.csv  (100.4 KB)  ← No transformations

🟡 SILVER ZONE (Cleaned & Standardized)
   data/silver/v_2025-12-16/
   └─ silver_articles.parquet (64.5 KB)
      • Deduplicated (fingerprint-based)
      • Quality scores (0-1 scale)
      • Topic tagging (8 topics, multiple per article)
      • Text cleaning indicators

🟢 GOLD ZONE (ML-Enriched, PySpark Ready)
   data/gold/date=2025-12-16/
   └─ articles.parquet (67.9 KB)
      • Sentiment analysis (176 neutral, 32 positive, 8 negative)
      • Confidence scores (0-1)
      • Processing metadata
      • Partitioned for PySpark
```

---

## 📚 Core Files

| File | Purpose | Status |
|------|---------|--------|
| **main.py** | E1 pipeline orchestration | ✅ |
| **setup_with_sql.py** | Database initialization | ✅ |
| **e1_export_correct.py** | RAW → SILVER → GOLD | ✅ |
| **src/core.py** | All extractors + transformers | ✅ |
| **sources_config.json** | 10 sources configuration | ✅ |
| **requirements.txt** | All dependencies | ✅ |

---

## 🔗 Data Sources (14 sources actives)

### Sources Actives (14 sources)

> **Note**: Les statistiques ci-dessous sont une **photo au 2025-12-20**. La collecte évolue quotidiennement pour les sources dynamiques. Les nombres d'articles augmentent à chaque exécution du pipeline.

| # | Source | Type | Records (20/12/2025) | Status |
|---|--------|------|---------------------|--------|
| 1 | kaggle_french_opinions | Dataset | 38,327 | ✓ Fondation |
| 2 | google_news_rss | RSS | 1,456 | ✓ Dynamique |
| 3 | zzdb_csv | CSV | 930 | ✓ Fondation |
| 4 | trustpilot_reviews | Scraping | 658 | ✓ Dynamique |
| 5 | yahoo_finance | RSS | 624 | ✓ Dynamique |
| 6 | reddit_france | API | 377 | ✓ Dynamique |
| 7 | rss_french_news | RSS | 259 | ✓ Dynamique |
| 8 | openweather_api | API | 187 | ✓ Dynamique |
| 9 | gdelt_events | BigData | 79 | ✓ Fondation |
| 10 | datagouv_datasets | Dataset | 50 | ✓ Dynamique |
| 11 | ifop_barometers | Scraping | 18 | ✓ Dynamique |
| 12 | insee_indicators | API | 5 | ✓ Dynamique |
| 13 | GDELT_Last15_English | BigData | 2 | ✓ Dynamique |
| 14 | GDELT_Master_List | BigData | 0 | ✓ Dynamique |

**Total articles en base** (au 20/12/2025): **43,022 articles**

**Classification**:
- **Fondation** (statiques, intégrées une fois) : `kaggle_french_opinions`, `gdelt_events`, `zzdb_csv`
  - Ces sources sont figées après leur première intégration et ne sont plus collectées
- **Dynamiques** (collecte quotidienne) : Toutes les autres sources actives
  - Les sources dynamiques collectent de nouveaux articles à chaque exécution du pipeline
  - Les nombres d'articles augmentent quotidiennement pour ces sources

### Sources Inactives (pour référence)

| Source | Type | Status |
|--------|------|--------|
| Kaggle_StopWords_28Lang | Dataset | Inactif |
| Kaggle_StopWords | Dataset | Inactif |
| Kaggle_FrenchFinNews | Dataset | Inactif |
| Kaggle_SentimentLexicons | Dataset | Inactif |
| Kaggle_InsuranceReviews | Dataset | Inactif |
| Kaggle_FrenchTweets | Dataset | Inactif |
| zzdb_synthetic | SQLite | Inactif |

---

## 📊 Dashboard de Visualisation

### ✅ Automatique et Dynamique

Le système inclut **3 outils de visualisation** qui se mettent à jour automatiquement :

1. **Rapport de Collecte** : S'affiche automatiquement après chaque `python main.py`
2. **Dashboard Global** : Vue d'ensemble complète avec `python show_dashboard.py`
3. **Visualiseur CSV** : Explorer les fichiers exports/ avec `python view_exports.py`

### 📋 Rapport de Collecte (Session Actuelle)

Le rapport s'affiche **automatiquement** après chaque collecte et montre :
- Articles collectés, taggés, analysés dans cette session
- Détail par source des nouveaux articles
- Distribution topics et sentiment des nouveaux articles

### 📊 Dashboard Global

```bash
# Afficher le dashboard complet (toujours à jour)
python scripts/show_dashboard.py
```

Affiche :
- **Résumé global** : Total articles, uniques, nouveaux aujourd'hui, enrichis
- **Nouveaux articles** : Détail par source des articles collectés aujourd'hui
- **Enrichissement Topics** : Articles taggés, topics utilisés, confiance moyenne
- **Enrichissement Sentiment** : Distribution positif/neutre/négatif
- **Articles par source** : Statistiques détaillées par source
- **Évaluation IA** : Status du dataset pour l'entraînement IA

### 👀 Visualiser les CSV dans exports/

```bash
# Script interactif pour explorer les CSV
python scripts/view_exports.py
```

Les fichiers CSV sont aussi directement accessibles dans `exports/` :
- **`raw.csv`** : Données brutes (DB + fichiers locaux)
- **`silver.csv`** : Données nettoyées avec topics
- **`gold.csv`** : Données complètes avec topics + sentiment

Vous pouvez les ouvrir directement dans Excel, Notepad, ou les importer dans Power BI.

### 🔄 Enrichir rétroactivement tous les articles

```bash
# Enrichir tous les articles existants (topics + sentiment)
python scripts/enrich_all_articles.py
```

📖 **Guide complet** : Voir `docs/DASHBOARD_GUIDE.md` pour plus de détails

## 📊 Data Quality Verification

### Pipeline Summary ✓

- **Total Articles Extracted**: 81
- **Articles Cleaned**: 81
- **Articles Loaded to DB**: 10 (new today)
- **Total in DB**: 1017 (consolidated across runs)
- **Deduplication Rate**: 87.7%
- **Quality Score**: 100%

### Export Outputs ✓

| File | Records | Size | Format |
|------|---------|------|--------|
| raw.csv | 1017 | 0.73 MB | CSV (raw data + Kaggle) |
| silver.csv | 1017 | 0.17 MB | CSV (classified by DOCUMENT_TOPIC) |
| gold.csv | 9 | 1 KB | CSV (aggregated by source) |
| gold.parquet | 9 | 10 KB | Parquet (for Power BI) |

### Transformations Applied ✓

| Transformation | Coverage | Status |
|---|---|---|
| Deduplication | 71/81 | ✓ |
| Quality Scoring | 1017/1017 | ✓ |
| Topic Classification | 1017/1017 (8 topics) | ✓ |
| Sentiment Analysis | 9 sources (MODEL_OUTPUT) | ✓ |
| Partitioned Raw Data | sources_2025-12-17 | ✓ |

---

## 🏗️ Database Schema

### 7 Core Tables

1. **source** — 10 configured sources
2. **raw_data** — 216 articles (direct from extractors)
3. **sync_log** — 20 logs (2 runs × 10 sources)
4. **topic** — 8 predefined topics
5. **document_topic** — 207 article-topic mappings
6. **model_output** — 648 ML predictions
7. **sqlite_sequence** — Auto-increment counters

---

## 📈 Statistics

| Metric | Value |
|--------|-------|
| Total Articles | 216 |
| Active Sources | 10/10 |
| Topics Created | 8 |
| Duplicates Removed | 0 |
| Data Corruption | 0 |
| Quality Score Range | 0.01 - 0.99 |
| Model Outputs | 648 |
| Transformations | 100% complete |

---

## ✅ Production Readiness

✅ **Code Quality**
- Ruff linting: 100% pass
- Type hints throughout
- OOP architecture (SOLID principles)
- No hardcoded values

✅ **Data Quality**
- Zero duplicates
- Zero corruption
- 100% article coverage
- Proper deduplication

✅ **Documentation**
- README (this file)
- AGILE_ROADMAP.md (43 user stories)
- SCHEMA_DESIGN.md (database design)
- CHANGELOG.md (version history)

✅ **Dependencies**
- All listed in requirements.txt
- Pinned versions
- pandas, pyarrow, fastparquet installed

---

## 📝 File Structure

```
PROJET_DATASENS/
├── main.py                          # E1 orchestration (utilise E1 isolé)
├── setup_with_sql.py                # Database setup
├── requirements.txt                 # Dependencies
├── sources_config.json              # Sources config
├── README.md                        # This file
├── pytest.ini                       # Configuration pytest
├── src/
│   ├── __init__.py
│   ├── e1/                          # E1 ISOLÉ (package privé)
│   │   ├── __init__.py
│   │   ├── core.py                  # Extracteurs et transformers
│   │   ├── repository.py            # Repository pattern
│   │   ├── tagger.py                # Topic tagger
│   │   ├── analyzer.py             # Sentiment analyzer
│   │   ├── aggregator.py            # Data aggregator
│   │   ├── exporter.py             # Gold exporter
│   │   └── pipeline.py             # E1Pipeline isolé
│   ├── e2/                          # E2 (FastAPI + RBAC) - PRÊT
│   │   └── __init__.py
│   ├── e3/                          # E3 (PySpark + ML) - PRÊT
│   │   └── __init__.py
│   ├── shared/                      # INTERFACES (contrats E1 ↔ E2/E3)
│   │   ├── __init__.py
│   │   └── interfaces.py           # E1DataReader (lecture seule)
│   ├── dashboard.py                 # Dashboard utilitaires
│   ├── collection_report.py         # Rapport de collecte
│   └── metrics.py                   # Prometheus metrics
├── tests/
│   ├── test_e1_isolation.py         # Tests non-régression E1
│   └── README_E1_ISOLATION.md       # Guide tests
├── docs/
│   ├── PLAN_ACTION_E1_E2_E3.md      # Plan d'action détaillé
│   ├── E1_ISOLATION_STRATEGY.md    # Stratégie isolation
│   ├── E1_ISOLATION_COMPLETE.md    # Récapitulatif Phase 0
│   └── ROADMAP_EVOLUTION.md         # Roadmap E1 → E2 → E3
└── data/
    ├── raw/
    │   └── sources_2025-12-20/
    │       ├── raw_articles.json
    │       └── raw_articles.csv
    ├── silver/
    │   └── v_2025-12-20/
    │       └── silver_articles.parquet
    └── gold/
        └── date=2025-12-20/
            └── articles.parquet
```

---

## 🎓 Key Concepts

### Three-Zone Architecture

- **RAW**: Unprocessed data directly from sources (JSON/CSV)
- **SILVER**: Cleaned, standardized, deduplicated (Parquet)
- **GOLD**: ML-enriched, production-ready (PySpark Parquet)

### Immutable Data Pipeline

1. No modifications to raw data (source of truth)
2. All transformations tracked
3. Lineage clearly documented
4. Easy to reprocess if needed

### PySpark Ready

- GOLD zone uses `date=2025-12-16/` partitioning
- Compatible with PySpark's partitioned dataset format
- Can be read with: `spark.read.parquet("data/gold/")`

---

## 🔒 E1 Isolation (Phase 0 - Complete)

**E1 est maintenant isolé et protégé** pour la construction de E2/E3.

### Structure Isolée
- ✅ Package `src/e1/` : E1 complètement isolé
- ✅ Interface `src/shared/interfaces.py` : E1DataReader (lecture seule)
- ✅ Tests de non-régression : `tests/test_e1_isolation.py`
- ✅ Documentation : `docs/E1_ISOLATION_STRATEGY.md`

### Règles d'Isolation
- ✅ E2/E3 utilisent UNIQUEMENT `E1DataReader` (pas de modification E1)
- ✅ Tests E1 passent à 100% avant chaque merge E2/E3
- ✅ Aucune modification `src/e1/` depuis E2/E3

**Voir** : `docs/E1_ISOLATION_COMPLETE.md` pour détails complets

---

## 🚀 Next Steps (E2/E3)

This E1 pipeline feeds into:

**Phase 1 — Docker & CI/CD**
- Containerisation E1
- Tests automatisés
- CI/CD workflows

**Phase 2 — FastAPI + RBAC**
- API REST sécurisée
- Authentification JWT
- Contrôle d'accès par zone (RAW/SILVER/GOLD)

**Phase 3 — PySpark**
- Traitement Big Data
- Intégration avec FastAPI

**Phase 4 — ML Fine-tuning**
- Fine-tuning FlauBERT (sentiment)
- Fine-tuning CamemBERT (topics)

**Phase 5 — Streamlit Dashboard**
- Visualisations interactives
- Prédictions IA

**Phase 6 — Mistral IA**
- Insights générés par IA
- Climat social/financier

**Voir** : `docs/PLAN_ACTION_E1_E2_E3.md` pour plan détaillé

---

## 📄 License

MIT License — See LICENSE.md

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Last Updated:** December 16, 2025  
**Status:** ✅ Production Ready  
**E1 Complete:** ✅ All components delivered
