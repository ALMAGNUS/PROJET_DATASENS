# 📁 FICHIERS FONCTIONNELS - DataSens E1

## 🎯 FICHIER PRINCIPAL

### `main.py`
**Pipeline complet E1** - Point d'entrée unique
```bash
python main.py
```
**Fonctions :** Extraction → Nettoyage → Chargement → Enrichissement → Exports → Rapports

---

## 📦 MODULES CORE (`src/`)

### Fichiers fonctionnels purs :

1. **`src/core.py`**
   - Classes : `Article`, `Source`, `BaseExtractor`
   - Extractors : `RSSExtractor`, `APIExtractor`, `ScrapingExtractor`, `GDELTFileExtractor`, `KaggleExtractor`, `SQLiteExtractor`, `CSVExtractor`
   - Factory : `create_extractor()`
   - Transformer : `ContentTransformer`

2. **`src/repository.py`**
   - Classe : `Repository` (CRUD complet)
   - Méthodes : `load_article_with_id()`, `log_sync()`, `log_foundation_integration()`, `is_foundation_integrated()`

3. **`src/analyzer.py`**
   - Classe : `SentimentAnalyzer`
   - Analyse sentiment : positif, négatif, neutre (100+ mots-clés)

4. **`src/tagger.py`**
   - Classe : `TopicTagger`
   - 18 topics : finance, entreprise, politique, technologie, santé, société, environnement, sport, média, culture, transport, logement, sécurité, éducation, travail, retraite, jeunesse, international

5. **`src/aggregator.py`**
   - Classe : `DataAggregator`
   - Agrégation : RAW, SILVER, GOLD

6. **`src/exporter.py`**
   - Classe : `GoldExporter`
   - Exports : CSV, Parquet (partitionné par date/source)

7. **`src/dashboard.py`**
   - Classe : `DataSensDashboard`
   - Dashboard d'enrichissement global

8. **`src/collection_report.py`**
   - Classe : `CollectionReport`
   - Rapport de collecte session actuelle

9. **`src/metrics.py`**
   - Métriques Prometheus
   - Serveur métriques (port 8000)

---

## 🚀 SCRIPTS DE DÉMARRAGE

### Scripts principaux :

#### 1. **Pipeline complet**
```bash
python main.py
```

#### 2. **Dashboard global**
```bash
python scripts/show_dashboard.py
```

#### 3. **Statistiques base de données**
```bash
python scripts/show_db_stats.py
```

#### 4. **Vue rapide**
```bash
python scripts/quick_view.py
```

#### 5. **Voir les exports**
```bash
python scripts/view_exports.py
```

#### 6. **Requêtes SQL directes**
```bash
python scripts/query_sqlite.py
```

---

## 🔧 SCRIPTS UTILITAIRES

### Enrichissement :

#### **Enrichir tous les articles rétroactivement**
```bash
python scripts/enrich_all_articles.py
```

#### **Réanalyser les sentiments**
```bash
python scripts/reanalyze_sentiment.py
```

### Base de données :

#### **Afficher les tables**
```bash
python scripts/show_tables.py
```

#### **Initialiser la base**
```bash
python scripts/setup_with_sql.py
```

#### **Migrer les sources**
```bash
python scripts/migrate_sources.py
```

### Exports :

#### **Régénérer les exports**
```bash
python scripts/regenerate_exports.py
```

#### **Exporter GOLD uniquement**
```bash
python scripts/export_gold.py
```

### Visualisation :

#### **Visualiser les datasets**
```bash
python scripts/view_datasets.py
```

#### **Visualiser les sentiments**
```bash
python scripts/visualize_sentiment.py
```

---

## 📊 FICHIERS DE CONFIGURATION

### `sources_config.json`
Configuration de toutes les sources de données
- Format : JSON
- Contient : sources actives/inactives, types, URLs, fréquences

### `requirements.txt`
Dépendances Python du projet

### `.env.example`
Variables d'environnement (template)

---

## 🗄️ BASE DE DONNÉES

### Localisation par défaut :
```
C:\Users\Utilisateur\datasens_project\datasens.db
```

### Ou via variable d'environnement :
```bash
$env:DB_PATH="C:\chemin\vers\datasens.db"
python main.py
```

---

## 📈 COMMANDES RAPIDES

### Démarrage complet :
```bash
# 1. Pipeline complet
python main.py

# 2. Voir les stats
python scripts/show_db_stats.py

# 3. Dashboard
python scripts/show_dashboard.py
```

### Requête SQL directe :
```bash
sqlite3 C:\Users\Utilisateur\datasens_project\datasens.db
```

### Voir les exports :
```bash
# CSV
python scripts/view_exports.py

# Ou directement
cat exports/gold.csv
```

---

## ✅ CHECKLIST DÉMARRAGE

1. ✅ Installer les dépendances : `pip install -r requirements.txt`
2. ✅ Configurer les sources : `sources_config.json`
3. ✅ Lancer le pipeline : `python main.py`
4. ✅ Vérifier les stats : `python scripts/show_db_stats.py`
5. ✅ Consulter le dashboard : `python scripts/show_dashboard.py`

---

## 🎯 FICHIERS ESSENTIELS (MINIMUM)

Pour faire fonctionner le projet, seuls ces fichiers sont nécessaires :

1. `main.py` - Point d'entrée
2. `src/core.py` - Extractors
3. `src/repository.py` - Base de données
4. `src/analyzer.py` - Sentiment
5. `src/tagger.py` - Topics
6. `src/aggregator.py` - Agrégation
7. `src/exporter.py` - Exports
8. `sources_config.json` - Configuration
9. `requirements.txt` - Dépendances

**Tous les autres fichiers sont optionnels (scripts utilitaires, docs, tests).**
