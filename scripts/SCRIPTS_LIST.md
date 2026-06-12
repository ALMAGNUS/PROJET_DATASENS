# 📋 Liste des Scripts Fonctionnels - DataSens E1

> **Note (2026-05-08)** : audit code étape 4. Les scripts marqués `(archivé)` ont été déplacés dans `scripts/_archive/` (one-shot terminés, démos, tests ad-hoc). Ils restent exécutables (`python scripts/_archive/<nom>.py`) mais ne sont plus référencés dans le pipeline runtime.

## 🚀 Pipeline Principal

### `main.py` (racine du projet)
**Description**: Pipeline complet E1 (Extract → Clean → Load → Tag → Analyze → Aggregate → Export)  
**Usage**: `python main.py`  
**Fonctionnalités**:
- Extraction depuis toutes les sources actives
- Nettoyage et validation
- Chargement en base de données
- Tagging topics (max 2)
- Analyse sentiment
- Fusion RAW/SILVER/GOLD
- Export Parquet + CSV
- Rapport de collecte + Dashboard

---

## 🗄️ Base de Données

### `setup_with_sql.py`
**Description**: Initialise la base de données SQLite avec le schéma complet  
**Usage**: `python scripts/setup_with_sql.py`  
**Fonctionnalités**:
- Crée 6 tables (source, raw_data, sync_log, topic, document_topic, model_output)
- Insère les sources depuis `sources_config.json`
- Crée les index pour performance
- **Note**: Plus nécessaire si `Repository` initialise automatiquement

### `show_tables.py`
**Description**: Affiche la structure des tables de la base de données  
**Usage**: `python scripts/show_tables.py`  
**Fonctionnalités**:
- Liste toutes les tables
- Affiche le schéma de chaque table
- Compte les enregistrements par table

### `migrate_sources.py` (archivé)
**Description**: Ajoute les sources manquantes depuis `sources_config.json` à la base de données  
**Usage**: `python scripts/_archive/migrate_sources.py`  
**Statut**: Migration ponctuelle terminée. Conservé pour réutilisation éventuelle.

---

## 📊 Visualisation & Rapports

### `show_dashboard.py`
**Description**: Affiche le dashboard global d'enrichissement  
**Usage**: `python scripts/show_dashboard.py`  
**Fonctionnalités**:
- Résumé global (total articles, enrichis, nouveaux)
- Nouveaux articles par source aujourd'hui
- Enrichissement Topics (articles taggés, confiance moyenne)
- Enrichissement Sentiment (distribution positif/neutre/négatif)
- Articles par source
- Évaluation dataset pour IA

### `quick_view.py`
**Description**: Aperçu rapide des données enrichies (GOLD)  
**Usage**: `python scripts/quick_view.py`  
**Fonctionnalités**:
- Distribution des topics
- Distribution du sentiment avec emojis
- Top 10 sources
- 5 exemples d'articles enrichis (topics + sentiment)

### `visualize_sentiment.py`
**Description**: Crée des graphiques de visualisation des sentiments  
**Usage**: `python scripts/visualize_sentiment.py`  
**Fonctionnalités**:
- 4 graphiques PNG (barres, camembert, histogramme)
- Statistiques détaillées par sentiment
- Exemples d'articles par sentiment
- Sentiment par source (top 10)
- Sentiment par topic (top 10)
- **Fichier généré**: `visualizations/sentiment_analysis.png`

### `view_exports.py`
**Description**: Visualiseur interactif des fichiers CSV dans `exports/`  
**Usage**: `python scripts/view_exports.py`  
**Fonctionnalités**:
- Menu interactif pour choisir le fichier
- Aperçu de `raw.csv`, `silver.csv`, `gold.csv`
- Affiche les premières lignes avec formatage

---

## 🔄 Enrichissement & Ré-analyse

### `enrich_all_articles.py`
**Description**: Enrichit rétroactivement tous les articles (topics + sentiment)  
**Usage**: `python scripts/enrich_all_articles.py`  
**Fonctionnalités**:
- Trouve les articles sans topics ou sans sentiment
- Applique le tagging topics
- Applique l'analyse sentiment
- Affiche le nombre d'articles enrichis

### `reanalyze_sentiment.py`
**Description**: Ré-analyse tous les articles avec l'analyseur de sentiment  
**Usage**: `python scripts/reanalyze_sentiment.py`  
**Fonctionnalités**:
- Ré-analyse tous les articles dans la base de données
- Met à jour les sentiments dans `model_output`
- Affiche la distribution finale
- Statistiques par sentiment

---

## 📤 Export & Régénération

### `export_gold.py`
**Description**: Exporte uniquement le dataset GOLD  
**Usage**: `python scripts/export_gold.py`  
**Fonctionnalités**:
- Génère `exports/gold.csv`
- Génère `data/gold/date=YYYY-MM-DD/articles.parquet`
- Affiche les statistiques

### `regenerate_exports.py`
**Description**: Régénère tous les exports RAW/SILVER/GOLD  
**Usage**: `python scripts/regenerate_exports.py`  
**Fonctionnalités**:
- Régénère `exports/raw.csv`
- Régénère `exports/silver.csv`
- Régénère `exports/gold.csv` + Parquet
- Affiche la distribution des sentiments dans GOLD

---

## 🧪 Tests & Validation

### `test_pipeline.py` (archivé), `test_before_build.py` (archivé), `test_project.py` (archivé)
Smoke tests ad-hoc (Catégorie B de l'audit code). Couverture redondante avec la suite `tests/` (pytest, CI). Disponibles sous `scripts/_archive/` pour exécution manuelle si besoin.

### `validate_json.py`
**Description**: Valide le fichier `sources_config.json`  
**Usage**: `python scripts/validate_json.py`  
**Fonctionnalités**:
- Vérifie la syntaxe JSON
- Vérifie les champs requis
- Affiche les erreurs de validation

---

## ⏰ Planification

### `scheduler.py`
**Description**: Planificateur pour exécuter le pipeline automatiquement  
**Usage**: `python scripts/scheduler.py`  
**Fonctionnalités**:
- Planification quotidienne (9h00 par défaut)
- Planification horaire
- Planification personnalisée
- Logs des exécutions

---

## 🐳 Docker

### `check_docker.ps1` (Windows)
**Description**: Vérifie l'installation Docker  
**Usage**: `powershell scripts/check_docker.ps1`

---

## 📊 Résumé par Catégorie

| Catégorie | Scripts actifs | Nombre |
|-----------|---------|--------|
| **Pipeline** | `main.py` | 1 |
| **Base de données** | `setup_with_sql.py`, `show_tables.py` | 2 |
| **Visualisation** | `show_dashboard.py`, `quick_view.py`, `visualize_sentiment.py`, `view_exports.py` | 4 |
| **Enrichissement** | `enrich_all_articles.py`, `reanalyze_sentiment.py` | 2 |
| **Export** | `export_gold.py`, `regenerate_exports.py` | 2 |
| **Tests** | `validate_json.py` (autres tests : suite pytest dans `tests/`) | 1 |
| **Planification** | `scheduler.py` | 1 |
| **Docker** | `check_docker.ps1` | 1 |
| **Archivés** | `scripts/_archive/` (one-shot terminés, démos, smoke tests redondants) | 17 |

---

## 🎯 Scripts les Plus Utilisés

### Pour le développement quotidien:
1. `python main.py` - Pipeline complet
2. `python scripts/show_dashboard.py` - Voir les statistiques
3. `python scripts/quick_view.py` - Aperçu rapide
4. `python scripts/visualize_sentiment.py` - Graphiques

### Pour la maintenance:
1. `python scripts/enrich_all_articles.py` - Enrichir tous les articles
2. `python scripts/regenerate_exports.py` - Régénérer les exports
3. `pytest tests/` - Suite de tests automatisés

### Pour le debugging:
1. `python scripts/show_tables.py` - Voir la structure DB
2. `python scripts/view_exports.py` - Explorer les CSV
3. `python scripts/validate_json.py` - Valider la config

---

## 📝 Notes

- Tous les scripts Python sont compatibles Python 3.10+
- Les scripts utilisent le chemin de DB par défaut: `~/.datasens_project/datasens.db`
- Variable d'environnement `DB_PATH` peut être utilisée pour changer le chemin
- Tous les scripts gèrent l'encodage UTF-8 pour Windows

---

**Dernière mise à jour**: Tous les scripts sont fonctionnels et testés
