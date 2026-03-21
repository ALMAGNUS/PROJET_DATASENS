# 🚀 Guide de Démarrage Rapide - DataSens E1

## 📋 Ce qui s'affiche automatiquement

Quand vous lancez `python main.py`, vous voyez automatiquement :

### 1️⃣ **Extraction** 
```
[EXTRACTION] Sources actives
rss_french_news... [RSS] OK 23
yahoo_finance... [RSS] OK 40
reddit_france... [API (JSON)] OK 15
...
OK Total extracted: 95
```

### 2️⃣ **Nettoyage**
```
[CLEANING] Articles validation
OK Cleaned: 95
```

### 3️⃣ **Chargement + Enrichissement**
```
[LOADING] Database ingestion + Tagging + Sentiment
OK Total loaded: 43
   Tagged: 12
   Analyzed: 43
Deduplicated: 52
```

### 4️⃣ **Statistiques Pipeline**
```
[STATS] Pipeline results
   Extracted:    95
   Cleaned:      95
   Loaded:       43
   Deduplicated: 52
   Database: 1499 total records
   By source:
      • google_news_rss: 690
      • trustpilot_reviews: 365
      ...
```

### 5️⃣ **Exports RAW/SILVER/GOLD**
```
[EXPORTS] RAW/SILVER/GOLD Generation
   OK RAW CSV: exports/raw.csv (1949 rows)
   OK SILVER CSV: exports/silver.csv (1949 rows)
   OK GOLD parquet: data/gold/date=2025-12-18/articles.parquet
   OK GOLD CSV: exports/gold.csv (1949 rows)
```

### 6️⃣ **📊 Rapport de Collecte (Session Actuelle)** ⭐
```
[RAPPORT] COLLECTE SESSION ACTUELLE
================================================================================

[SESSION] RÉSUMÉ DE LA COLLECTE
   Articles collectés:     43
   Articles taggés:        12 (27.9%)
   Articles analysés:      43 (100.0%)
   Heure de début:        2025-12-18T12:30:00

[SOURCES] DÉTAIL PAR SOURCE
   Source                            Collectés     Taggés   Analysés
   ------------------------------ ---------- ---------- ----------
   google_news_rss                        15          5         15
   yahoo_finance                          10          3         10
   reddit_france                           8          2          8
   ...

[TOPICS] DISTRIBUTION DES TOPICS (SESSION)
   • finance                    :    5 articles (41.7%)
   • technologie                :    4 articles (33.3%)
   ...

[SENTIMENT] DISTRIBUTION DU SENTIMENT (SESSION)
   • neutre    :   35 articles (81.4%)
   • positif   :    5 articles (11.6%)
   • négatif   :    3 articles (7.0%)
```

### 7️⃣ **📊 Dashboard Global**
```
[DASHBOARD] DATASENS - ENRICHISSEMENT DATASET
================================================================================

[RESUME] RÉSUMÉ GLOBAL
   Total articles:        1,657
   Articles uniques:      1,657
   Nouveaux aujourd'hui:  294
   Articles enrichis:     55 (3.3%)

[NOUVEAUX] NOUVEAUX ARTICLES AUJOURD'HUI PAR SOURCE
   • google_news_rss               :  135 articles
   • yahoo_finance                 :   40 articles
   ...

[TOPICS] ENRICHISSEMENT TOPICS
   Articles taggés:        119
   Topics utilisés:       14
   Confiance moyenne:     0.52

[SENTIMENT] ENRICHISSEMENT SENTIMENT
   neutre    :  185 articles ( 92.0%) - Score moyen: 0.50
   positif   :   10 articles (  5.0%) - Score moyen: 0.91
   négatif   :    6 articles (  3.0%) - Score moyen: 0.82

[IA] ÉVALUATION DATASET POUR IA
   Status: [OK] EXCELLENT (1,657 articles)
   Message: Dataset prêt pour l'IA
```

## 🎯 Commandes utiles

```bash
# Lancer le pipeline complet (avec rapport automatique)
python main.py

# Afficher uniquement le dashboard global
python scripts/show_dashboard.py

# Visualiser les fichiers CSV
python scripts/view_exports.py

# Enrichir rétroactivement tous les articles
python scripts/enrich_all_articles.py
```

## 📊 Fichiers générés

Après chaque run, vous avez :
- `exports/raw.csv` : Toutes les données brutes
- `exports/silver.csv` : Données avec topics
- `exports/gold.csv` : Données complètes (topics + sentiment)
- `data/gold/date=YYYY-MM-DD/articles.parquet` : Parquet partitionné

## ✅ Tout est automatique !

- ✅ Rapport de collecte : S'affiche automatiquement
- ✅ Dashboard global : S'affiche automatiquement
- ✅ Exports CSV/Parquet : Générés automatiquement
- ✅ Enrichissement : Topics + Sentiment automatiques

