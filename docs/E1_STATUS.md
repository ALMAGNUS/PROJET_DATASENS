# 📊 État du Projet E1 - Collecte & Fusion/Agrégation

**Phase**: E1 - Collecte, Nettoyage, Chargement, Fusion/Agrégation  
**Status**: ✅ **COMPLET ET OPÉRATIONNEL**

---

## 🎯 Vue d'Ensemble

Le pipeline E1 est **entièrement implémenté** et fonctionnel. Il couvre toutes les étapes de la collecte jusqu'à la fusion/agrégation des données selon le schéma architectural défini.

---

## ✅ Composants Implémentés

### 1. **Collecte (Extraction)** - `src/core.py`

**Extracteurs disponibles:**
- ✅ `RSSExtractor` - Flux RSS/Atom (France24, Google News, Yahoo Finance)
- ✅ `APIExtractor` - APIs REST (Reddit, OpenWeather, INSEE)
- ✅ `ScrapingExtractor` - Web scraping (Trustpilot, IFOP)
- ✅ `GDELTExtractor` - GDELT events (scraping Google News)
- ✅ `GDELTFileExtractor` - GDELT fichiers (lastupdate.txt)
- ✅ `KaggleExtractor` - Datasets Kaggle locaux (CSV/JSON)

**Factory Pattern:** `create_extractor()` route automatiquement chaque source vers le bon extractor.

**Sources configurées:** 21 sources dans `sources_config.json`

---

### 2. **Nettoyage** - `ContentTransformer` (src/core.py)

**Transformations appliquées:**
- ✅ Suppression HTML (`BeautifulSoup.get_text()`)
- ✅ Normalisation espaces multiples → 1 espace
- ✅ Validation contenu minimal (`len(title) > 3`, `len(content) > 10`)

---

### 3. **Chargement Base de Données** - `Repository` (src/repository.py)

**Fonctionnalités:**
- ✅ **Initialisation automatique du schéma** (6 tables créées si inexistantes)
- ✅ **Initialisation automatique des sources** depuis `sources_config.json`
- ✅ Déduplication par fingerprint SHA256
- ✅ Insertion dans table `raw_data`
- ✅ Logging des synchronisations (`sync_log`)

**Tables créées automatiquement:**
1. `source` - Sources de données
2. `raw_data` - Articles bruts
3. `sync_log` - Logs de synchronisation
4. `topic` - Topics de classification
5. `document_topic` - Association articles-topics
6. `model_output` - Résultats d'analyse (sentiment)

---

### 4. **Tagging Topics** - `TopicTagger` (src/tagger.py)

**Classification:**
- ✅ 7 topics prédéfinis: finance, politique, technologie, santé, société, environnement, sport
- ✅ Maximum 2 topics par article (meilleure confiance)
- ✅ Score de confiance (0.0-1.0)
- ✅ Topic "autre" par défaut si aucun match

**Topics créés automatiquement** lors de l'initialisation.

---

### 5. **Analyse Sentiment** - `SentimentAnalyzer` (src/analyzer.py)

**Classification:**
- ✅ 3 labels: `positif`, `neutre`, `négatif`
- ✅ Score de confiance (0.0-1.0)
- ✅ Basé sur mots-clés (9 positifs, 9 négatifs)
- ✅ Stocké dans `model_output` avec `model_name='sentiment_keyword'`

---

### 6. **Fusion/Agrégation** - `DataAggregator` (src/aggregator.py)

**Trois niveaux d'agrégation:**

#### 🔴 RAW (Données brutes)
- DB: Articles de `raw_data` + `source`
- Fichiers locaux: Kaggle/GDELT depuis `data/raw/`
- **Pas d'enrichissement**

#### 🟡 SILVER (RAW + Topics)
- RAW + Topics (max 2) depuis `document_topic`
- Colonnes: `topic_1`, `topic_1_score`, `topic_2`, `topic_2_score`
- **Sans sentiment**

#### 🟢 GOLD (SILVER + Sentiment)
- SILVER + Sentiment depuis `model_output`
- Colonnes finales:
  ```
  id, source, title, content, url, collected_at,
  topic_1, topic_1_score, topic_2, topic_2_score,
  sentiment, sentiment_score
  ```

**Fusion:**
- ✅ Articles DB (RSS/API/Scraping) + Fichiers locaux (Kaggle/GDELT)
- ✅ Merge topics (pivot avec ROW_NUMBER)
- ✅ Merge sentiment
- ✅ DataFrame pandas unifié

---

### 7. **Export** - `GoldExporter` (src/exporter.py)

**Formats d'export:**
- ✅ **RAW CSV**: `exports/raw.csv`
- ✅ **SILVER CSV**: `exports/silver.csv`
- ✅ **GOLD Parquet**: `data/gold/date=YYYY-MM-DD/articles.parquet` (partitionné par date)
- ✅ **GOLD CSV**: `exports/gold.csv`

**Parquet partitionné** pour compatibilité PySpark/Apache Spark.

---

## 🔄 Pipeline Complet - `main.py`

### Orchestration E1Pipeline

```python
pipeline = E1Pipeline()
pipeline.run()
```

**Étapes exécutées:**
1. ✅ **Extract** - Extraction depuis toutes les sources actives
2. ✅ **Clean** - Nettoyage et validation
3. ✅ **Load** - Chargement DB + Tagging + Sentiment
4. ✅ **Aggregate** - Fusion RAW/SILVER/GOLD
5. ✅ **Export** - Export Parquet + CSV
6. ✅ **Reports** - Rapport de collecte + Dashboard

**Métriques Prometheus** intégrées pour monitoring.

---

## 📂 Structure des Données

### RAW Zone
```
data/raw/
├── sources_2025-12-18/
│   ├── raw_articles.json      ← Backup articles du jour
│   └── raw_articles.csv        ← Backup CSV
├── Kaggle_FrenchFinNews/
│   └── date=2025-12-17/
│       └── *.csv               ← Fichiers locaux
└── gdelt_events/
    └── date=2025-12-17/
        └── *.json              ← Fichiers locaux
```

### GOLD Zone
```
data/gold/
└── date=2025-12-18/
    └── articles.parquet        ← FINAL : DB + Local files fusionnés

exports/
├── raw.csv                     ← RAW export
├── silver.csv                  ← SILVER export
└── gold.csv                    ← GOLD export (annoté)
```

---

## 🚀 Utilisation

### 1. Lancer le Pipeline Complet

```bash
python main.py
```

**Résultat:**
- Extraction depuis toutes les sources actives
- Nettoyage et validation
- Chargement en DB avec déduplication
- Tagging topics (max 2)
- Analyse sentiment
- Fusion DB + fichiers locaux
- Export RAW/SILVER/GOLD (Parquet + CSV)
- Rapport de collecte
- Dashboard d'enrichissement

### 2. Initialisation Automatique

**Plus besoin de lancer `setup_with_sql.py` manuellement!**

Le `Repository` initialise automatiquement:
- ✅ Schéma de base de données (6 tables)
- ✅ Sources depuis `sources_config.json`
- ✅ Topics de base (7 topics + "autre")

**Première exécution:**
```bash
python main.py
# → Crée automatiquement la DB et les tables si inexistantes
```

---

## 📊 Exemple de Sortie

### Article Source (RSS)
```
Source: yahoo_finance
Title: "CAC 40 en hausse de 2%"
Content: "Le CAC 40 a progressé de 2% aujourd'hui..."
```

### Après Pipeline E1
```python
DataFrame GOLD:
  id=1500, 
  source='yahoo_finance', 
  title='CAC 40 en hausse de 2%',
  topic_1='finance', topic_1_score=0.92,
  topic_2='', topic_2_score=0.0,
  sentiment='positif', sentiment_score=0.78
```

### Export Parquet
```
data/gold/date=2025-12-18/articles.parquet
→ Compatible PySpark pour E2 (Stockage Long Terme)
```

---

## ✅ Checklist E1

- [x] **Collecte** - Extraction multi-sources (RSS/API/Scraping/Datasets)
- [x] **Nettoyage** - Transformation et validation
- [x] **Chargement DB** - Stockage avec déduplication
- [x] **Tagging** - Classification topics (max 2)
- [x] **Analyse** - Sentiment analysis
- [x] **Fusion** - Agrégation DB + fichiers locaux
- [x] **Export** - RAW/SILVER/GOLD (Parquet + CSV)
- [x] **Initialisation auto** - Schéma + Sources
- [x] **Métriques** - Prometheus monitoring
- [x] **Rapports** - Collection report + Dashboard

---

## 🎯 Prochaines Étapes (E2)

Selon le schéma architectural, E2 correspond à:
- **Stockage Long Terme** avec Apache Spark (PySpark)
- **ELT** (Extract, Load, Transform)
- **Fichiers partitionnés Parquet** pour gros volumes
- **Capacité de reprise** (recovery)

Le pipeline E1 produit déjà des fichiers Parquet partitionnés prêts pour E2.

---

## 📝 Notes Techniques

### Base de Données
- **SQLite** par défaut (`~/.datasens_project/datasens.db`)
- **Path configurable** via variable d'environnement `DB_PATH`
- **Schéma auto-initialisé** au premier lancement

### Performance
- **Déduplication** par fingerprint SHA256 (évite doublons)
- **Index** sur `source_id`, `collected_at`, `raw_data_id`
- **Limite** 50 articles par source (configurable)

### Robustesse
- **Gestion d'erreurs** dans tous les extractors
- **Retry logic** pour sources instables
- **Logging** des erreurs dans `sync_log`

---

**Status**: ✅ **E1 COMPLET - Prêt pour E2 (Stockage Long Terme avec Spark)**
