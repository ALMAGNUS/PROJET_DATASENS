# 📊 Guide de Gestion Parquet GOLD

## Vue d'ensemble

Les fichiers **Parquet GOLD** sont générés par le pipeline E1 lors de chaque exécution. Ils contiennent les articles enrichis (topics + sentiment) dans un format optimisé pour PySpark.

## Structure des Fichiers Parquet

```
data/gold/
├── date=2025-12-16/
│   └── articles.parquet          (216 lignes)
├── date=2025-12-18/
│   └── articles.parquet          (2,094 lignes)
├── date=2025-12-19/
│   ├── articles.parquet          (42,466 lignes)
│   ├── source=zzdb_csv/
│   │   └── zzdb_csv_articles.parquet
│   └── source=zzdb_synthetic/
│       └── zzdb_articles.parquet
└── date=2025-12-20/
    ├── articles.parquet          (43,131 lignes)
    └── ...
```

## Pourquoi seulement 219 lignes dans un Parquet ?

### Explication

Le **dashboard E1** affiche le **total des articles dans la base de données SQLite** (`datasens.db`), qui contient **tous les articles collectés depuis le début** (43,022 articles au 20/12/2025).

Les **fichiers Parquet GOLD** sont **exportés par date** lors de chaque exécution du pipeline E1. Chaque fichier Parquet contient uniquement les articles **exportés pour cette date spécifique**.

**Exemple** :
- Si vous regardez `date=2025-12-16/articles.parquet`, il contient **216 lignes** (articles exportés le 16/12/2025)
- Le dashboard E1 montre **43,022 articles** (total cumulé dans la base de données)

### Différence Parquet vs Base de Données

| Source | Contenu | Nombre d'articles |
|--------|---------|-------------------|
| **Base de données** (`datasens.db`) | Tous les articles collectés depuis le début | 43,022 (cumulé) |
| **Parquet GOLD** (`date=2025-12-16/`) | Articles exportés pour cette date | 216 (par date) |
| **Parquet GOLD** (`date=2025-12-20/`) | Articles exportés pour cette date | 43,131 (par date) |

**Note** : Les fichiers Parquet plus récents peuvent contenir plus d'articles car ils incluent les articles des dates précédentes si le pipeline a été réexécuté.

## Manipuler les Parquet avec PySpark

### Script Interactif

Utilisez le script `scripts/manage_parquet.py` pour manipuler vos fichiers Parquet :

```bash
# Windows
scripts\manage_parquet.bat

# Linux/Mac
bash scripts/manage_parquet.sh

# Directement
python scripts/manage_parquet.py
```

### Fonctionnalités Disponibles

#### 1. Lire les Parquet

```python
from spark.adapters import GoldParquetReader

reader = GoldParquetReader()

# Lire toutes les dates
df = reader.read_gold()

# Lire une date spécifique
from datetime import date
df = reader.read_gold(date=date(2025, 12, 20))

# Lire une plage de dates
df = reader.read_gold_date_range(
    date(2025, 12, 18),
    date(2025, 12, 20)
)
```

#### 2. Filtrer les Données

```python
# Filtrer par sentiment
df_positif = df.filter(df.sentiment == "positif")

# Filtrer par source
df_google = df.filter(df.source == "google_news_rss")

# Condition SQL complexe
df.createOrReplaceTempView("articles")
df_filtered = spark.sql("""
    SELECT * FROM articles 
    WHERE sentiment = 'positif' 
    AND sentiment_score > 0.7
""")
```

#### 3. Modifier les Données

```python
from pyspark.sql.functions import when, col, lit

# Modifier une valeur
df_modified = df.withColumn(
    "sentiment",
    when(col("sentiment") == "neutre", lit("neutral"))
    .otherwise(col("sentiment"))
)

# Ajouter une colonne
df_with_new_col = df.withColumn("is_positive", 
    when(col("sentiment") == "positif", lit(True))
    .otherwise(lit(False))
)
```

#### 4. Supprimer des Lignes

```python
# Supprimer les lignes avec sentiment neutre
df_filtered = df.filter(df.sentiment != "neutre")

# Supprimer avec condition SQL
df.createOrReplaceTempView("articles")
df_filtered = spark.sql("""
    SELECT * FROM articles 
    WHERE NOT (sentiment = 'neutre' AND sentiment_score < 0.3)
""")
```

#### 5. Sauvegarder en Parquet

```python
# Sauvegarder sans partitionnement
df.write.mode("overwrite").parquet("data/gold/custom/articles.parquet")

# Sauvegarder avec partitionnement par date
from datetime import date
df.write.mode("overwrite").partitionBy("date").parquet("data/gold/custom/")

# Sauvegarder avec partitionnement personnalisé
df.write.mode("overwrite").partitionBy("source", "sentiment").parquet("data/gold/custom/")
```

#### 6. Appliquer des Traitements

```python
from spark.processors import GoldDataProcessor

processor = GoldDataProcessor()

# Agrégation par sentiment
df_agg = processor.aggregate_by_sentiment(df)
df_agg.show()

# Agrégation par source
df_source = processor.aggregate_by_source(df)
df_source.show()

# Distribution sentiment
df_dist = processor.get_sentiment_distribution(df)
df_dist.show()

# Statistiques générales
stats = processor.get_statistics(df)
print(stats)
```

## Exemples d'Utilisation

### Exemple 1 : Extraire les Articles Positifs

```python
from spark.adapters import GoldParquetReader
from spark.session import get_spark_session

reader = GoldParquetReader()
df = reader.read_gold()

# Filtrer articles positifs
df_positifs = df.filter(df.sentiment == "positif")

# Sauvegarder
df_positifs.write.mode("overwrite").parquet("data/gold/positifs/articles.parquet")
print(f"Articles positifs: {df_positifs.count()}")
```

### Exemple 2 : Compléter les Données Manquantes

```python
from pyspark.sql.functions import when, col, lit

df = reader.read_gold()

# Remplacer les valeurs NULL
df_complete = df.withColumn(
    "sentiment",
    when(col("sentiment").isNull(), lit("neutre"))
    .otherwise(col("sentiment"))
).withColumn(
    "sentiment_score",
    when(col("sentiment_score").isNull(), lit(0.5))
    .otherwise(col("sentiment_score"))
)

# Sauvegarder
df_complete.write.mode("overwrite").parquet("data/gold/complete/articles.parquet")
```

### Exemple 3 : Fusionner Plusieurs Dates

```python
from datetime import date, timedelta

reader = GoldParquetReader()

# Lire plusieurs dates
start_date = date(2025, 12, 18)
end_date = date(2025, 12, 20)

df_merged = reader.read_gold_date_range(start_date, end_date)

# Sauvegarder fusion
df_merged.write.mode("overwrite").parquet("data/gold/merged/articles.parquet")
print(f"Total lignes fusionnees: {df_merged.count()}")
```

### Exemple 4 : Créer un Nouveau Parquet avec Données Modifiées

```python
from pyspark.sql.functions import col, when, lit, concat

df = reader.read_gold()

# Ajouter une colonne calculée
df_enhanced = df.withColumn(
    "sentiment_label",
    when(col("sentiment_score") > 0.7, lit("tres_positif"))
    .when(col("sentiment_score") > 0.4, lit("positif"))
    .when(col("sentiment_score") > 0.2, lit("neutre"))
    .otherwise(lit("negatif"))
)

# Ajouter une colonne combinée
df_enhanced = df_enhanced.withColumn(
    "full_text",
    concat(col("title"), lit(" - "), col("content"))
)

# Sauvegarder
df_enhanced.write.mode("overwrite").parquet("data/gold/enhanced/articles.parquet")
```

## Bonnes Pratiques

### 1. Toujours Vérifier avant de Modifier

```python
# Afficher les statistiques avant modification
from spark.processors import GoldDataProcessor

processor = GoldDataProcessor()
stats_before = processor.get_statistics(df)
print("Avant modification:", stats_before)

# Faire les modifications
df_modified = modify_dataframe(df, ...)

# Vérifier après modification
stats_after = processor.get_statistics(df_modified)
print("Apres modification:", stats_after)
```

### 2. Sauvegarder les Versions

```python
from datetime import datetime

# Créer un backup avant modification
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"data/gold/backup/articles_{timestamp}.parquet"
df.write.mode("overwrite").parquet(backup_path)
```

### 3. Utiliser le Mode Append pour Ajouter des Données

```python
# Ajouter de nouvelles données sans écraser
df_new.write.mode("append").parquet("data/gold/existing/articles.parquet")
```

### 4. Gérer les Schémas Différents

```python
# Si vous fusionnez des DataFrames avec schémas différents
df1.unionByName(df2, allowMissingColumns=True)
```

## Dépannage

### Problème : "ConnectionRefusedError: [WinError 10061]"

**Solution** : Le SparkSession est configuré en mode local pur. Si vous rencontrez encore des erreurs, vérifiez que `src/spark/session.py` contient toutes les configurations de mode local.

### Problème : "NUM_COLUMNS_MISMATCH"

**Solution** : Utilisez `unionByName` avec `allowMissingColumns=True` :

```python
df1.unionByName(df2, allowMissingColumns=True)
```

### Problème : "FileNotFoundError: Parquet GOLD not found"

**Solution** : Vérifiez que le pipeline E1 a été exécuté et a généré les fichiers Parquet :

```bash
python main.py
```

## Ressources

- **Script interactif** : `scripts/manage_parquet.py`
- **Documentation PySpark** : https://spark.apache.org/docs/latest/api/python/
- **Documentation Parquet** : https://parquet.apache.org/
