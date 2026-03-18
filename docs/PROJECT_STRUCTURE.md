# 📁 Structure du Projet DataSens E1

## 🎯 Vue d'ensemble

```
PROJET_DATASENS/
├── main.py                    # Point d'entrée principal du pipeline
├── sources_config.json        # Configuration des sources de données
├── requirements.txt           # Dépendances Python
├── pyproject.toml            # Configuration ruff (linter)
├── README.md                 # Documentation principale
│
├── src/                      # Code source principal
│   ├── __init__.py
│   ├── core.py              # Classes de base (Article, Source, Extractors)
│   ├── repository.py         # CRUD database (Repository)
│   ├── tagger.py            # Classification topics (TopicTagger)
│   ├── analyzer.py          # Analyse sentiment (SentimentAnalyzer)
│   ├── aggregator.py        # Agrégation RAW/SILVER/GOLD (DataAggregator)
│   ├── exporter.py          # Export Parquet/CSV (GoldExporter)
│   ├── dashboard.py         # Dashboard global (DataSensDashboard)
│   └── collection_report.py # Rapport de collecte session (CollectionReport)
│
├── scripts/                  # Scripts utilitaires
│   ├── setup_with_sql.py    # Initialisation base de données
│   ├── show_dashboard.py    # Afficher le dashboard
│   ├── view_exports.py      # Visualiser les CSV exports/
│   ├── enrich_all_articles.py # Enrichir rétroactivement tous les articles
│   ├── show_tables.py       # Afficher tables DB
│   ├── validate_json.py     # Valider sources_config.json
│   └── migrate_sources.py   # Ajouter sources manquantes
│
├── tests/                    # Tests unitaires
│   └── test_init.py         # Test initialisation pipeline
│
├── docs/                     # Documentation
│   ├── README.md            # Index documentation
│   ├── DATA_FLOW.md        # Chemin de la donnée
│   ├── DASHBOARD_GUIDE.md  # Guide dashboard
│   ├── ARCHITECTURE.md     # Architecture technique
│   ├── PROJECT_STRUCTURE.md # Ce fichier
│   ├── CHEMIN_DONNEE.md    # Chemin de la donnée (détails)
│   ├── PROJECT_ANALYSIS.md # Analyse du projet
│   └── AUDIT_ARCHITECTURE.md # Audit architecture
│
├── data/                     # Données (ignorées par Git)
│   ├── raw/                 # Zone RAW
│   ├── silver/              # Zone SILVER
│   ├── gold/                # Zone GOLD
│   └── lake/                # Data lake consolidé
│
├── exports/                  # Exports CSV/Parquet (ignorés par Git)
│   ├── raw.csv
│   ├── silver.csv
│   └── gold.csv
│
└── notebooks/                # Notebooks Jupyter (anciennes versions)
    ├── datasens_E1/
    └── datasens_E1_v1/
```

## 📂 Détails des dossiers

### `src/` - Code source principal

**Modules core :**
- `core.py` : Classes de base (Article, Source, BaseExtractor, extractors concrets)
- `repository.py` : CRUD database (Repository extends DatabaseLoader)
- `tagger.py` : Classification topics (TopicTagger)
- `analyzer.py` : Analyse sentiment (SentimentAnalyzer)

**Modules traitement :**
- `aggregator.py` : Agrégation données RAW/SILVER/GOLD (DataAggregator)
- `exporter.py` : Export Parquet/CSV (GoldExporter)

**Modules visualisation :**
- `dashboard.py` : Dashboard global (DataSensDashboard)
- `collection_report.py` : Rapport de collecte session (CollectionReport)

### `scripts/` - Scripts utilitaires

Tous les scripts sont exécutables depuis la racine du projet :

```bash
# Initialiser la base de données
python scripts/setup_with_sql.py

# Afficher le dashboard
python scripts/show_dashboard.py

# Visualiser les CSV
python scripts/view_exports.py

# Enrichir tous les articles
python scripts/enrich_all_articles.py
```

### `docs/` - Documentation

- **README.md** : Index de la documentation
- **DATA_FLOW.md** : Chemin de la donnée détaillé
- **DASHBOARD_GUIDE.md** : Guide d'utilisation du dashboard
- **ARCHITECTURE.md** : Architecture technique complète
- **PROJECT_STRUCTURE.md** : Ce fichier (structure du projet)

### `data/` - Données (ignorées par Git)

- **raw/** : Données brutes (sources, Kaggle, GDELT)
- **silver/** : Données nettoyées avec topics
- **gold/** : Données enrichies (topics + sentiment)
- **lake/** : Data lake consolidé

### `exports/` - Exports (ignorés par Git)

Fichiers CSV/Parquet générés automatiquement :
- `raw.csv` : Toutes les données brutes
- `silver.csv` : Données avec topics
- `gold.csv` : Données complètes (topics + sentiment)

## 🔄 Workflow principal

1. **Initialisation** : `python scripts/setup_with_sql.py`
2. **Collecte** : `python main.py`
3. **Visualisation** : `python scripts/show_dashboard.py`
4. **Exploration** : `python scripts/view_exports.py`

## 📝 Fichiers de configuration

- `sources_config.json` : Configuration des sources (RSS, API, scraping)
- `requirements.txt` : Dépendances Python
- `pyproject.toml` : Configuration ruff (linter)
- `.gitignore` : Fichiers ignorés par Git

## 🗑️ Fichiers obsolètes supprimés

- `src/extractors_old.py` : Ancienne version extractors
- `src/extractors.py` : Non utilisé (logique dans core.py)
- `src/ingestion.py` : Non utilisé
- `src/lineage.py` : Non utilisé
- `dashboard.py` (racine) : Ancien dashboard (remplacé par src/dashboard.py)
- `viz_raw_silver_gold.py` : Fonctionnalité intégrée dans aggregator.py

## ✅ Organisation finale

- **Code source** : `src/` (modules organisés par responsabilité)
- **Scripts** : `scripts/` (tous les utilitaires)
- **Tests** : `tests/` (tests unitaires)
- **Documentation** : `docs/` (toute la doc)
- **Données** : `data/` (zones RAW/SILVER/GOLD)
- **Exports** : `exports/` (CSV/Parquet)
