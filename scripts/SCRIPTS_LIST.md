# 📋 Liste des Scripts Fonctionnels - DataSens E1

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

### `migrate_sources.py`
**Description**: Ajoute les sources manquantes depuis `sources_config.json` à la base de données  
**Usage**: `python scripts/migrate_sources.py`  
**Fonctionnalités**:
- Compare `sources_config.json` avec la table `source`
- Insère les sources manquantes
- Met à jour les sources existantes

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

### `test_pipeline.py`
**Description**: Teste le pipeline et vérifie les sentiments  
**Usage**: `python scripts/test_pipeline.py`  
**Fonctionnalités**:
- Vérifie les sentiments dans la base de données
- Vérifie les sentiments dans `gold.csv`
- Affiche des exemples d'articles avec sentiment
- Résumé des tests (OK/ERREUR)

### `test_before_build.py`
**Description**: Tests avant build (vérifie fichiers nécessaires)  
**Usage**: `python scripts/test_before_build.py`  
**Fonctionnalités**:
- Vérifie l'existence des fichiers essentiels
- Vérifie les imports Python
- Vérifie la structure du projet
- Exit code 0 si OK, 1 si erreur

### `test_project.py`
**Description**: Tests complets du projet  
**Usage**: `python scripts/test_project.py`  
**Fonctionnalités**:
- Test des imports
- Test du pipeline
- Test des fichiers scripts
- Test des chemins relatifs

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

## 🐳 Docker (Scripts Shell)

### `check_docker.sh` (Linux/Mac)
**Description**: Vérifie l'installation Docker  
**Usage**: `bash scripts/check_docker.sh`

### `check_docker.ps1` (Windows)
**Description**: Vérifie l'installation Docker  
**Usage**: `powershell scripts/check_docker.ps1`

---

## 📊 Résumé par Catégorie

| Catégorie | Scripts | Nombre |
|-----------|---------|--------|
| **Pipeline** | `main.py` | 1 |
| **Base de données** | `setup_with_sql.py`, `show_tables.py`, `migrate_sources.py` | 3 |
| **Visualisation** | `show_dashboard.py`, `quick_view.py`, `visualize_sentiment.py`, `view_exports.py` | 4 |
| **Enrichissement** | `enrich_all_articles.py`, `reanalyze_sentiment.py` | 2 |
| **Export** | `export_gold.py`, `regenerate_exports.py` | 2 |
| **Tests** | `test_pipeline.py`, `test_before_build.py`, `test_project.py`, `validate_json.py` | 4 |
| **Planification** | `scheduler.py` | 1 |
| **Docker** | `check_docker.sh`, `check_docker.ps1` | 2 |
| **TOTAL** | | **19 scripts** |

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
3. `python scripts/test_pipeline.py` - Tester le pipeline

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
