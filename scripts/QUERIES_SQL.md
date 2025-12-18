# 📊 Requêtes SQL Directes - DataSens E1

## 🎯 Interroger Directement SQLite

### Localisation de la Base de Données

**Chemin par défaut (Windows):**
```
C:\Users\Utilisateur\datasens_project\datasens.db
```

**Chemin par défaut (Linux/Mac):**
```
~/.datasens_project/datasens.db
```

**Ou via variable d'environnement:**
```bash
# Windows PowerShell
$env:DB_PATH="C:\chemin\vers\datasens.db"

# Linux/Mac
export DB_PATH=/chemin/vers/datasens.db
```

**⚠️ Note:** Le fichier `datasens.db` dans le répertoire du projet est vide. La vraie base de données se trouve dans votre répertoire home (`%USERPROFILE%\datasens_project\datasens.db`).

---

## 🔍 Requêtes Utiles

### 1. Voir tous les articles avec sentiment

```sql
SELECT 
    r.raw_data_id as id,
    s.name as source,
    r.title,
    mo.label as sentiment,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id 
    AND mo.model_name = 'sentiment_keyword'
ORDER BY r.collected_at DESC
LIMIT 20;
```

### 2. Distribution du sentiment

```sql
SELECT 
    label as sentiment,
    COUNT(*) as count,
    ROUND(AVG(score), 3) as avg_score
FROM model_output
WHERE model_name = 'sentiment_keyword'
GROUP BY label
ORDER BY count DESC;
```

### 3. Articles positifs

```sql
SELECT 
    r.raw_data_id,
    s.name as source,
    r.title,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
JOIN model_output mo ON r.raw_data_id = mo.raw_data_id
WHERE mo.model_name = 'sentiment_keyword'
  AND mo.label = 'positif'
ORDER BY mo.score DESC
LIMIT 20;
```

### 4. Articles négatifs

```sql
SELECT 
    r.raw_data_id,
    s.name as source,
    r.title,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
JOIN model_output mo ON r.raw_data_id = mo.raw_data_id
WHERE mo.model_name = 'sentiment_keyword'
  AND mo.label = 'négatif'
ORDER BY mo.score DESC
LIMIT 20;
```

### 5. Articles avec topics

```sql
SELECT 
    r.raw_data_id,
    s.name as source,
    r.title,
    t.name as topic,
    dt.confidence_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
JOIN document_topic dt ON r.raw_data_id = dt.raw_data_id
JOIN topic t ON dt.topic_id = t.topic_id
ORDER BY dt.confidence_score DESC
LIMIT 20;
```

### 6. Articles enrichis (topics + sentiment)

```sql
SELECT 
    r.raw_data_id as id,
    s.name as source,
    r.title,
    t1.name as topic_1,
    dt1.confidence_score as topic_1_score,
    mo.label as sentiment,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
LEFT JOIN (
    SELECT raw_data_id, topic_id, confidence_score,
           ROW_NUMBER() OVER (PARTITION BY raw_data_id ORDER BY confidence_score DESC) as rn
    FROM document_topic
) dt1 ON r.raw_data_id = dt1.raw_data_id AND dt1.rn = 1
LEFT JOIN topic t1 ON dt1.topic_id = t1.topic_id
LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id 
    AND mo.model_name = 'sentiment_keyword'
ORDER BY r.collected_at DESC
LIMIT 20;
```

### 7. Statistiques par source

```sql
SELECT 
    s.name as source,
    COUNT(r.raw_data_id) as total_articles,
    COUNT(DISTINCT CASE WHEN mo.label = 'positif' THEN r.raw_data_id END) as positifs,
    COUNT(DISTINCT CASE WHEN mo.label = 'négatif' THEN r.raw_data_id END) as negatifs,
    COUNT(DISTINCT CASE WHEN mo.label = 'neutre' THEN r.raw_data_id END) as neutres
FROM source s
LEFT JOIN raw_data r ON s.source_id = r.source_id
LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id 
    AND mo.model_name = 'sentiment_keyword'
GROUP BY s.name
ORDER BY total_articles DESC;
```

### 8. Statistiques par topic

```sql
SELECT 
    t.name as topic,
    COUNT(dt.raw_data_id) as count,
    ROUND(AVG(dt.confidence_score), 3) as avg_confidence
FROM topic t
LEFT JOIN document_topic dt ON t.topic_id = dt.topic_id
GROUP BY t.name
ORDER BY count DESC;
```

### 9. Articles récents (aujourd'hui)

```sql
SELECT 
    r.raw_data_id,
    s.name as source,
    r.title,
    r.collected_at,
    mo.label as sentiment
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
LEFT JOIN model_output mo ON r.raw_data_id = mo.raw_data_id 
    AND mo.model_name = 'sentiment_keyword'
WHERE DATE(r.collected_at) = DATE('now')
ORDER BY r.collected_at DESC;
```

### 10. Top articles par score de sentiment

```sql
SELECT 
    r.raw_data_id,
    s.name as source,
    r.title,
    mo.label as sentiment,
    mo.score as sentiment_score
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
JOIN model_output mo ON r.raw_data_id = mo.raw_data_id
WHERE mo.model_name = 'sentiment_keyword'
  AND mo.label != 'neutre'
ORDER BY mo.score DESC
LIMIT 30;
```

---

## 🛠️ Comment Exécuter

### Option 1: SQLite CLI

```bash
sqlite3 ~/.datasens_project/datasens.db
```

Puis tapez vos requêtes SQL.

### Option 2: Python Direct

```python
import sqlite3

conn = sqlite3.connect('~/.datasens_project/datasens.db')
cursor = conn.cursor()

# Exécuter une requête
cursor.execute("""
    SELECT label, COUNT(*) 
    FROM model_output 
    WHERE model_name = 'sentiment_keyword'
    GROUP BY label
""")

for row in cursor.fetchall():
    print(row)

conn.close()
```

### Option 3: Outil Graphique

- **DB Browser for SQLite** (gratuit)
- **DBeaver** (gratuit)
- **SQLiteStudio** (gratuit)

Ouvrez le fichier `~/.datasens_project/datasens.db` avec l'un de ces outils.

---

## 📋 Tables Disponibles

| Table | Description |
|-------|-------------|
| `source` | Sources de données |
| `raw_data` | Articles bruts |
| `topic` | Topics de classification |
| `document_topic` | Association articles-topics |
| `model_output` | Résultats d'analyse (sentiment) |
| `sync_log` | Logs de synchronisation |

---

## 🔗 Relations

```
source (1) ──→ (N) raw_data
raw_data (1) ──→ (N) document_topic ──→ (1) topic
raw_data (1) ──→ (N) model_output
```

---

## 💡 Astuces

### Voir le schéma d'une table

```sql
.schema raw_data
```

### Compter les articles

```sql
SELECT COUNT(*) FROM raw_data;
```

### Voir les sources actives

```sql
SELECT name, source_type, active 
FROM source 
WHERE active = 1;
```

---

**C'est tout ! Pas besoin de scripts compliqués, juste SQL direct.**
