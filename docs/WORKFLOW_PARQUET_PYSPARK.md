# 📊 Workflow Parquet GOLD ↔ PySpark - Guide Complet

## 🎯 Vue d'ensemble

Ce document explique le workflow complet entre :
- **SQLite Database** (`datasens.db`) - **BUFFER TEMPORAIRE** E1 (collecte quotidienne)
- **Fichiers Parquet GOLD** - **STOCKAGE PERMANENT** (après export depuis buffer)
- **PySpark** - Consommation Big Data depuis Parquet GOLD (E2/E3)

---

## 🔄 Workflow Complet

```
┌─────────────────────────────────────────────────────────────────┐
│              E1 PIPELINE - BUFFER SQLite (TEMPORAIRE)            │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   RAW Zone   │───▶│  SILVER Zone │───▶│  GOLD Zone   │       │
│  │  (SQLite)    │    │  (SQLite)    │    │  (SQLite)    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│       │                    │                    │                 │
│       │                    │                    │                 │
│       │                    │                    ▼                 │
│       │                    │         ┌─────────────────────┐     │
│       │                    │         │  EXPORT PARQUET     │     │
│       │                    │         │  data/gold/         │     │
│       │                    │         │  date=YYYY-MM-DD/   │     │
│       │                    │         │  articles.parquet   │     │
│       │                    │         └─────────────────────┘     │
│       │                    │                    │                 │
│       │                    │                    │                 │
│       ▼                    ▼                    ▼                 │
│  ┌──────────────────────────────────────────────────────┐        │
│  │    SQLite BUFFER (datasens.db) - TEMPORAIRE           │        │
│  │  ⚠️ BUFFER: Collecte quotidienne                      │        │
│  │  - raw_data (articles bruts)                          │        │
│  │  - document_topic (topics)                            │        │
│  │  - model_output (sentiment)                          │        │
│  │                                                        │        │
│  │  🔄 Après export Parquet → Peut être vidé/nettoyé    │        │
│  └──────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ EXPORT (E1 Pipeline)
                              │ Buffer → Stockage Permanent
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│         FICHIERS PARQUET GOLD (STOCKAGE PERMANENT)              │
│                                                                   │
│  data/gold/                                                      │
│  ├── date=2025-12-16/                                           │
│  │   └── articles.parquet  (216 lignes)                         │
│  ├── date=2025-12-18/                                           │
│  │   └── articles.parquet  (2,094 lignes)                       │
│  ├── date=2025-12-19/                                           │
│  │   └── articles.parquet  (42,466 lignes)                      │
│  └── date=2025-12-20/                                           │
│       └── articles.parquet  (43,131 lignes)                     │
│                                                                   │
│  ✅ STOCKAGE PERMANENT:                                          │
│     - Export depuis buffer SQLite                               │
│     - Fichiers immutables (une fois créés, ne changent pas)     │
│     - Chaque jour = nouveau fichier Parquet                     │
│     - Les fichiers restent sur le disque (pas de suppression)   │
│     - Source de vérité pour PySpark                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ LECTURE (PySpark E2/E3)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYSPARK (E2/E3)                               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  GoldParquetReader                                    │       │
│  │  - Lit les fichiers Parquet GOLD                     │       │
│  │  - Mode LECTURE SEULE (isolation E1)                 │       │
│  │  - Pas de modification des fichiers                  │       │
│  └──────────────────────────────────────────────────────┘       │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  GoldDataProcessor                                    │       │
│  │  - Agrégations                                        │       │
│  │  - Analyses Big Data                                  │       │
│  │  - Statistiques                                       │       │
│  └──────────────────────────────────────────────────────┘       │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  E2 API Endpoints                                     │       │
│  │  - /api/v1/analytics/sentiment/distribution          │       │
│  │  - /api/v1/analytics/source/aggregation              │       │
│  │  - /api/v1/analytics/statistics                      │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Buffer SQLite vs Stockage Permanent Parquet

### Buffer SQLite (`datasens.db`) - TEMPORAIRE

**SQLite est un BUFFER** qui collecte les données quotidiennement :

Les zones RAW/SILVER/GOLD dans SQLite sont des **concepts logiques** utilisés par l'agrégateur E1 :

| Zone | Tables SQLite | Description |
|------|---------------|-------------|
| **RAW** | `raw_data` + `source` | Articles bruts directement depuis les extracteurs |
| **SILVER** | RAW + `document_topic` + `topic` | Articles nettoyés avec topics assignés |
| **GOLD** | SILVER + `model_output` | Articles enrichis avec topics + sentiment |

**Important** : Ces zones sont des **vues logiques** créées par `DataAggregator` :
- `aggregate_raw()` : Joint `raw_data` + `source`
- `aggregate_silver()` : Joint RAW + `document_topic` + `topic`
- `aggregate()` : Joint SILVER + `model_output`

**Rôle du Buffer SQLite** :
- ✅ Collecte quotidienne des articles depuis les sources
- ✅ Enrichissement (topics + sentiment)
- ✅ Export vers Parquet GOLD (stockage permanent)
- ⚠️ **Peut être vidé/nettoyé après export** (données sauvegardées dans Parquet)

### Fichiers Parquet GOLD (Stockage Permanent)

Les fichiers Parquet sont le **STOCKAGE PERMANENT** créés par `GoldExporter` depuis le buffer SQLite :

```
data/gold/date=YYYY-MM-DD/articles.parquet
```

**Contenu** : Toutes les colonnes GOLD (RAW + SILVER + GOLD) dans un seul fichier Parquet.

---

## 🔄 Processus d'Export E1 → Parquet

### Étape 1 : Exécution Pipeline E1

```bash
python main.py
```

**Ce qui se passe** :
1. **Extraction** : Collecte depuis 14 sources → `raw_data` (SQLite)
2. **Nettoyage** : Qualité, déduplication → `raw_data` (SQLite)
3. **Enrichissement Topics** : Assignation topics → `document_topic` (SQLite)
4. **Enrichissement Sentiment** : Analyse sentiment → `model_output` (SQLite)

### Étape 2 : Agrégation GOLD

```python
# Dans src/e1/pipeline.py
aggregator = DataAggregator(db_path)
df_gold = aggregator.aggregate()  # Joint toutes les tables
```

**Ce qui se passe** :
- `aggregate()` fait des JOINs SQL :
  ```sql
  SELECT 
    r.*,                    -- RAW (raw_data)
    t1.name as topic_1,     -- SILVER (document_topic + topic)
    t2.name as topic_2,     -- SILVER
    mo.label as sentiment,  -- GOLD (model_output)
    mo.score as sentiment_score
  FROM raw_data r
  LEFT JOIN document_topic dt1 ON r.raw_data_id = dt1.raw_data_id
  LEFT JOIN topic t1 ON dt1.topic_id = t1.topic_id
  LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id
  WHERE mo.model_name = 'sentiment_keyword'
  ```

### Étape 3 : Export Parquet

```python
# Dans src/e1/pipeline.py
exporter = GoldExporter()
result = exporter.export_all(df_gold, date.today())
```

**Ce qui se passe** :
- Crée le dossier : `data/gold/date=2025-12-20/`
- Exporte en Parquet : `data/gold/date=2025-12-20/articles.parquet`
- Exporte aussi en CSV : `exports/gold.csv` (pour référence)

**Code source** (`src/e1/exporter.py`) :
```python
def export_all(self, df: pd.DataFrame, partition_date: date | None = None) -> dict:
    d = partition_date or date.today()
    
    # Partitionnement par date
    p_path = self.base_dir / f"date={d:%Y-%m-%d}"
    p_path.mkdir(parents=True, exist_ok=True)
    
    # Export Parquet
    parquet = p_path / 'articles.parquet'
    df.to_parquet(parquet, index=False, engine='pyarrow')
    
    return {'parquet': parquet, 'rows': len(df)}
```

---

## 📥 Processus de Lecture PySpark ← Parquet

### Comment PySpark récupère les Parquet

PySpark **NE MODIFIE JAMAIS** les fichiers Parquet. Il les lit en **lecture seule**.

#### 1. GoldParquetReader

```python
# Dans src/spark/adapters/gold_parquet_reader.py
reader = GoldParquetReader()

# Lire toutes les dates
df = reader.read_gold()

# Lire une date spécifique
df = reader.read_gold(date=date(2025, 12, 20))

# Lire une plage de dates
df = reader.read_gold_date_range(
    date(2025, 12, 18),
    date(2025, 12, 20)
)
```

**Ce qui se passe** :
1. Liste les partitions : `data/gold/date=*/articles.parquet`
2. Lit chaque fichier Parquet avec `spark.read.parquet()`
3. Unionne les DataFrames si plusieurs dates
4. Retourne un DataFrame Spark

**Code source** :
```python
def read_gold(self, date: date_type | None = None) -> DataFrame:
    if date:
        # Lecture date spécifique
        partition_path = self.base_path / f"date={date:%Y-%m-%d}" / "articles.parquet"
        return self.read(str(partition_path))
    else:
        # Lecture toutes les dates
        partitions = list(self.base_path.glob("date=*/articles.parquet"))
        # Lit et unionne toutes les partitions
        ...
```

#### 2. Isolation E1

**Principe** : PySpark ne touche JAMAIS à SQLite. Il lit uniquement les Parquet.

```
┌─────────────────────────────────────────┐
│         SQLite (datasens.db)            │
│  ✅ Protégé - Pas d'accès PySpark       │
└─────────────────────────────────────────┘
              │
              │ EXPORT (E1 uniquement)
              ▼
┌─────────────────────────────────────────┐
│    Parquet GOLD (data/gold/)             │
│  ✅ Lecture seule PySpark                │
│  ✅ Pas de modification                  │
└─────────────────────────────────────────┘
              │
              │ LECTURE (PySpark)
              ▼
┌─────────────────────────────────────────┐
│         PySpark (E2/E3)                 │
│  ✅ Analyse Big Data                     │
│  ✅ Agrégations                          │
│  ✅ API Endpoints                        │
└─────────────────────────────────────────┘
```

---

## 🔄 Concept de Buffer SQLite et Stockage Permanent Parquet

### ✅ SQLite = BUFFER TEMPORAIRE

**Clarification importante** :
- **SQLite (`datasens.db`)** = **BUFFER** qui collecte les données quotidiennement
- Les données sont **exportées** vers Parquet GOLD (stockage permanent)
- Le buffer SQLite **PEUT être vidé/nettoyé** après export
- Les données sont **sauvegardées** dans les fichiers Parquet avant nettoyage

### ✅ Parquet GOLD = STOCKAGE PERMANENT

**Les fichiers Parquet** :
- **Sont le stockage permanent** (export depuis le buffer SQLite)
- **NE SONT PAS** supprimés après lecture par PySpark
- **RESTENT** sur le disque indéfiniment
- **Source de vérité** pour PySpark et analyses

### ✅ Workflow Quotidien

#### 1. Collecte Quotidienne dans Buffer SQLite

Chaque jour, E1 collecte les données dans le **buffer SQLite** :
- Extraction depuis 14 sources → `raw_data` (SQLite)
- Enrichissement topics → `document_topic` (SQLite)
- Enrichissement sentiment → `model_output` (SQLite)

#### 2. Export Quotidien Buffer → Parquet GOLD

Chaque jour, E1 **exporte** le buffer SQLite vers Parquet GOLD :

```
Buffer SQLite (datasens.db)
    ↓ EXPORT
data/gold/date=2025-12-20/articles.parquet  (43,131 lignes)
```

**Chaque fichier Parquet contient** :
- Tous les articles du buffer SQLite exportés ce jour-là
- Les fichiers plus récents peuvent contenir plus d'articles (cumul si buffer non vidé)

#### 3. Nettoyage Buffer SQLite (Optionnel)

**Après export vers Parquet**, le buffer SQLite peut être nettoyé :
- Les données sont **sauvegardées** dans Parquet avant nettoyage
- Le buffer peut être vidé pour libérer de l'espace
- Les données restent disponibles dans les fichiers Parquet

#### 4. Lecture PySpark depuis Parquet GOLD

PySpark lit depuis le **stockage permanent Parquet** :
- **Une date spécifique** : `reader.read_gold(date=date(2025, 12, 20))`
- **Toutes les dates** : `reader.read_gold()` (unionne tous les fichiers)
- **Une plage de dates** : `reader.read_gold_date_range(...)`

**PySpark ne lit JAMAIS directement depuis SQLite** (isolation E1)

---

## 🗑️ Gestion du Cycle de Vie : Buffer SQLite et Parquet GOLD

### Nettoyage Buffer SQLite (après export)

**Après export vers Parquet**, vous pouvez nettoyer le buffer SQLite :

```python
# scripts/cleanup_sqlite_buffer.py
import sqlite3
from pathlib import Path

def cleanup_sqlite_buffer(db_path: str, keep_days: int = 7):
    """
    Nettoie le buffer SQLite après export Parquet
    
    ⚠️ ATTENTION: Ne nettoyer QUE après export Parquet réussi
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Exemple: Supprimer les articles plus anciens que X jours
    # (à adapter selon vos besoins)
    cursor.execute("""
        DELETE FROM raw_data 
        WHERE collected_at < date('now', '-' || ? || ' days')
    """, (keep_days,))
    
    # Nettoyer aussi les tables liées
    cursor.execute("DELETE FROM document_topic WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
    cursor.execute("DELETE FROM model_output WHERE raw_data_id NOT IN (SELECT raw_data_id FROM raw_data)")
    
    conn.commit()
    conn.close()
    print(f"Buffer SQLite nettoye (articles > {keep_days} jours supprimes)")
```

### Parquet GOLD = Stockage Permanent

**Les fichiers Parquet GOLD ne doivent PAS être supprimés** (sauf si vraiment nécessaire) :
- Ils sont le stockage permanent
- PySpark en dépend pour les analyses
- Ils servent d'historique

### Script de Nettoyage Parquet (si vraiment nécessaire)

```python
# scripts/cleanup_old_parquet.py
from pathlib import Path
from datetime import date, timedelta

def cleanup_old_parquet(days_to_keep: int = 90):
    """
    ⚠️ ATTENTION: Supprime les fichiers Parquet anciens
    Utiliser avec précaution - les Parquet sont le stockage permanent
    """
    gold_path = Path("data/gold")
    cutoff_date = date.today() - timedelta(days=days_to_keep)
    
    for partition_dir in gold_path.glob("date=*"):
        date_str = partition_dir.name.split("=")[1]
        partition_date = date.fromisoformat(date_str)
        
        if partition_date < cutoff_date:
            print(f"Suppression: {partition_dir}")
            # import shutil
            # shutil.rmtree(partition_dir)  # Décommenter pour exécuter
```

---

## 📖 Comment Récupérer les Parquet

### Option 1 : Via PySpark (Recommandé)

```python
from spark.adapters import GoldParquetReader
from datetime import date

reader = GoldParquetReader()

# Lire toutes les dates
df = reader.read_gold()

# Lire une date spécifique
df = reader.read_gold(date=date(2025, 12, 20))

# Lire une plage
df = reader.read_gold_date_range(
    date(2025, 12, 18),
    date(2025, 12, 20)
)
```

### Option 2 : Via Script Interactif

```bash
python scripts/manage_parquet.py
# Option 2: Lire Parquet (toutes dates)
# Option 3: Lire Parquet (date spécifique)
```

### Option 3 : Via API E2

```bash
# Liste des dates disponibles
GET /api/v1/analytics/available-dates

# Statistiques (lit Parquet en arrière-plan)
GET /api/v1/analytics/statistics?target_date=2025-12-20
```

### Option 4 : Directement avec PyArrow (sans Spark)

```python
import pyarrow.parquet as pq
import pandas as pd

# Lire un fichier Parquet directement
df = pd.read_parquet("data/gold/date=2025-12-20/articles.parquet")
print(df.head())
```

---

## 🔍 Différence : SQLite vs Parquet

| Aspect | SQLite (datasens.db) | Parquet GOLD |
|--------|---------------------|--------------|
| **Format** | Base de données relationnelle | Fichiers colonnaires |
| **Structure** | Tables normalisées (raw_data, document_topic, model_output) | Fichier dénormalisé (toutes colonnes) |
| **Accès** | SQL queries | Lecture via PySpark/PyArrow |
| **Modification** | ✅ CRUD complet | ❌ Lecture seule |
| **Partitionnement** | Par tables | Par date (`date=YYYY-MM-DD/`) |
| **Performance** | Optimisé pour transactions | Optimisé pour analytics Big Data |
| **Taille** | ~72 MB (43,022 articles) | ~87,907 lignes réparties sur 4 fichiers |

---

## 📊 Exemple Complet : Workflow Journée

### Jour 1 (2025-12-20)

**1. Exécution E1 Pipeline** :
```bash
python main.py
```

**Résultat** :
- SQLite : 43,022 articles (cumulé)
- Export Parquet : `data/gold/date=2025-12-20/articles.parquet` (43,131 lignes)

**2. Lecture PySpark** :
```python
reader = GoldParquetReader()
df = reader.read_gold(date=date(2025, 12, 20))
# df contient 43,131 lignes
```

**3. Analyse** :
```python
processor = GoldDataProcessor()
stats = processor.get_statistics(df)
# Analyse Big Data sur les 43,131 lignes
```

### Jour 2 (2025-12-21)

**1. Exécution E1 Pipeline** :
```bash
python main.py
```

**Résultat** :
- SQLite : 43,500 articles (nouveaux articles ajoutés)
- Export Parquet : `data/gold/date=2025-12-21/articles.parquet` (43,500 lignes)

**2. Lecture PySpark** :
```python
# Lire seulement le nouveau fichier
df_new = reader.read_gold(date=date(2025, 12, 21))

# OU lire toutes les dates (cumul)
df_all = reader.read_gold()  # Unionne date=2025-12-20 + date=2025-12-21
```

**3. Les anciens fichiers restent** :
- `data/gold/date=2025-12-20/articles.parquet` ✅ Toujours présent
- `data/gold/date=2025-12-21/articles.parquet` ✅ Nouveau fichier

---

## ✅ Résumé

1. **SQLite (`datasens.db`)** : **BUFFER TEMPORAIRE** E1
   - Collecte quotidienne des articles
   - Zones RAW/SILVER/GOLD sont des vues logiques
   - Peut être vidé/nettoyé après export Parquet

2. **Export Parquet GOLD** : **STOCKAGE PERMANENT**
   - Créé quotidiennement depuis le buffer SQLite
   - Partitionné par date (`date=YYYY-MM-DD/`)
   - Fichiers immutables (ne changent jamais)

3. **PySpark** : Lit les Parquet en lecture seule
   - Ne lit JAMAIS directement SQLite (isolation E1)
   - Utilise uniquement les fichiers Parquet GOLD
   - Ne modifie jamais les fichiers Parquet

4. **Workflow** : Buffer SQLite → Export Parquet → Stockage Permanent → PySpark
   - Buffer SQLite peut être nettoyé après export
   - Parquet GOLD reste sur le disque (stockage permanent)
   - PySpark consomme depuis Parquet (pas depuis SQLite)

---

## 🔗 Fichiers Clés

- **Export E1** : `src/e1/exporter.py` → `export_all()`
- **Agrégation E1** : `src/e1/aggregator.py` → `aggregate()`
- **Lecture PySpark** : `src/spark/adapters/gold_parquet_reader.py` → `read_gold()`
- **Traitement PySpark** : `src/spark/processors/gold_processor.py`

---

**Dernière mise à jour** : 2025-12-20
