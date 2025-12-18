# LOGGING — Documentation Complète des Logs

Guide complet de tous les mécanismes de logging et monitoring dans DataSens E1.

---

## Vue d'ensemble

DataSens utilise **3 tables de logging principales** + **console output structuré** pour traçabilité complète:

| Table | Rôle | Fréquence | Rétention |
|-------|------|-----------|-----------|
| **sync_log** | Ingestion tracking | Par source/run | 6 mois |
| **cleaning_audit** | Transformation trail | Par article | 12 mois |
| **data_quality_metrics** | Quality snapshots | Par source/jour | 12 mois |

---

## 1. SYNC_LOG — Ingestion Tracking

### Schéma

```sql
CREATE TABLE sync_log (
    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    sync_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sync_end TIMESTAMP,
    articles_fetched INTEGER DEFAULT 0,
    articles_inserted INTEGER DEFAULT 0,
    articles_skipped INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('SUCCESS', 'PARTIAL', 'FAILED')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    timeout_occurred BOOLEAN DEFAULT 0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Colonnes Détaillées

#### sync_id (INTEGER, PRIMARY KEY)
- Identifiant unique de l'ingestion
- Auto-incrémenté
- **Exemple**: 1, 2, 3, ...

#### source_name (TEXT, NOT NULL)
- Nom de la source ingérée
- **Valeurs acceptées**: 
  - `rss_french_news`
  - `gdelt_events`
  - `openweather_api`
  - `insee_api`
  - `kaggle_french_opinions`
  - `google_news_rss`
  - `regional_media_rss`
  - `ifop_barometers`
  - `reddit_france`
  - `trustpilot_reviews`

#### sync_start (TIMESTAMP)
- Moment de début de l'ingestion
- **Format**: `YYYY-MM-DD HH:MM:SS`
- **Exemple**: `2025-12-15 10:00:00`

#### sync_end (TIMESTAMP)
- Moment de fin de l'ingestion
- **Durée**: `sync_end - sync_start` = temps écoulé
- **Exemple**: `2025-12-15 10:05:30`

#### articles_fetched (INTEGER)
- Nombre d'articles récupérés depuis la source
- **Range**: 0 à ∞
- **Exemple**: 500

#### articles_inserted (INTEGER)
- Nombre d'articles insérés en RAW zone
- **Relation**: articles_inserted ≤ articles_fetched
- **Raison d'écart**: Erreurs parsing, doublons détectés, schema validation
- **Exemple**: 485

#### articles_skipped (INTEGER)
- Nombre d'articles ignorés (intentionnellement)
- **Raisons**: Duplicates, invalid format, missing mandatory fields
- **Exemple**: 15

#### errors_count (INTEGER)
- Nombre total d'erreurs rencontrées
- **Exemple**: 8 (timeouts + parsing errors)

#### status (TEXT, CHECK)
- État global de l'ingestion
- **Valeurs**:
  - `SUCCESS`: Tous articles insérés, 0 erreur
  - `PARTIAL`: Articles insérés mais quelques erreurs
  - `FAILED`: Aucun article inséré ou crash

**Logique**:
```
IF articles_inserted == articles_fetched AND errors_count == 0:
    status = 'SUCCESS'
ELIF articles_inserted > 0:
    status = 'PARTIAL'
ELSE:
    status = 'FAILED'
```

#### error_message (TEXT)
- Message d'erreur détaillé (si status != SUCCESS)
- **Exemple**: `"Connection timeout after 30s. Retrying..."`
- **Format**: Exception message complet (traceback + context)

#### retry_count (INTEGER)
- Nombre de tentatives (au-delà de la 1ère)
- **Logique**: Max 3 tentatives par source
- **Exemple**: 2 (= 3 tentatives totales)

#### timeout_occurred (BOOLEAN)
- Flag indiquant timeout réseau
- **Valeurs**: 0 (non), 1 (oui)
- **Impact**: Peut déclencher retry automatique

#### metadata (JSON)
- Données supplémentaires (flexible)
- **Exemple**:
```json
{
    "response_time_ms": 2450,
    "api_version": "2.0",
    "endpoint": "https://api.gdelt.org/api/v2/...",
    "rate_limit_remaining": 9999,
    "pagination_pages": 5,
    "content_language": "fr"
}
```

#### created_at (TIMESTAMP)
- Timestamp d'enregistrement (audit trail)
- **Différent de sync_start** si log inséré différé

### Exemples d'Entrées

#### ✅ SUCCESS
```sql
INSERT INTO sync_log (
    source_name, sync_start, sync_end,
    articles_fetched, articles_inserted, articles_skipped,
    errors_count, status, retry_count, timeout_occurred
) VALUES (
    'rss_french_news',
    '2025-12-15 10:00:00',
    '2025-12-15 10:03:45',
    500, 500, 0,
    0, 'SUCCESS', 0, 0
);
```

#### ⚠️ PARTIAL
```sql
INSERT INTO sync_log (
    source_name, sync_start, sync_end,
    articles_fetched, articles_inserted, articles_skipped,
    errors_count, status, error_message, retry_count, timeout_occurred
) VALUES (
    'gdelt_events',
    '2025-12-15 10:10:00',
    '2025-12-15 10:18:30',
    1000, 985, 15,
    8, 'PARTIAL', 
    'URLError: Connection refused (8 items). Partial success.',
    1, 1
);
```

#### ❌ FAILED
```sql
INSERT INTO sync_log (
    source_name, sync_start, sync_end,
    articles_fetched, articles_inserted, articles_skipped,
    errors_count, status, error_message, retry_count, timeout_occurred
) VALUES (
    'kaggle_french_opinions',
    '2025-12-15 11:00:00',
    '2025-12-15 11:00:05',
    0, 0, 0,
    1, 'FAILED',
    'ConnectionError: Unable to reach API. Max retries exceeded.',
    3, 1
);
```

### Requêtes Utiles

#### Voir toutes les ingestions
```sql
SELECT 
    sync_id, source_name, sync_start, articles_inserted,
    status, errors_count
FROM sync_log
ORDER BY sync_id DESC;
```

#### Résumé par source
```sql
SELECT 
    source_name,
    COUNT(*) as total_syncs,
    SUM(articles_inserted) as total_articles,
    SUM(errors_count) as total_errors,
    ROUND(AVG(articles_inserted), 0) as avg_per_sync,
    ROUND((julianday(MAX(sync_end)) - julianday(MIN(sync_start))) * 24, 1) as hours_elapsed
FROM sync_log
GROUP BY source_name
ORDER BY total_articles DESC;
```

#### Dernière ingestion par source
```sql
SELECT DISTINCT
    source_name,
    (SELECT sync_end FROM sync_log s2 
     WHERE s2.source_name = s1.source_name 
     ORDER BY sync_id DESC LIMIT 1) as last_sync,
    (SELECT articles_inserted FROM sync_log s2 
     WHERE s2.source_name = s1.source_name 
     ORDER BY sync_id DESC LIMIT 1) as last_count
FROM sync_log s1;
```

#### Erreurs par jour
```sql
SELECT 
    DATE(sync_start) as sync_date,
    COUNT(CASE WHEN status != 'SUCCESS' THEN 1 END) as failed_syncs,
    SUM(errors_count) as total_errors
FROM sync_log
GROUP BY DATE(sync_start)
ORDER BY sync_date DESC;
```

---

## 2. CLEANING_AUDIT — Transformation Trail

### Schéma

```sql
CREATE TABLE cleaning_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    raw_article_id INTEGER,
    step_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    action TEXT NOT NULL,
    value_before TEXT,
    value_after TEXT,
    change_type TEXT,  -- 'MODIFIED', 'DELETED', 'KEPT'
    reason TEXT,
    fingerprint TEXT,
    quality_score REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_article_id) REFERENCES raw_data(id)
);
```

### Pipeline Étapes (10 Steps)

#### Step 1: LOAD
- **Action**: Charge article depuis RAW
- **change_type**: KEPT
- **Exemple**:
```json
{
    "step_number": 1,
    "step_name": "LOAD",
    "action": "Loaded from raw_data table",
    "value_before": null,
    "value_after": "Article object initialized",
    "change_type": "KEPT"
}
```

#### Step 2: NORMALIZE
- **Action**: Trim espaces, lowercase
- **Colonnes modifiées**: title, content, author
- **Exemple**:
```json
{
    "step_number": 2,
    "step_name": "NORMALIZE",
    "action": "Trimmed whitespace from title",
    "value_before": "  Opinion sur climat  ",
    "value_after": "Opinion sur climat",
    "change_type": "MODIFIED"
}
```

#### Step 3: PARSE_DATES
- **Action**: Parse published_at en DATE
- **Format**: ISO 8601 → Python DATE
- **Exemple**:
```json
{
    "step_number": 3,
    "step_name": "PARSE_DATES",
    "action": "Parsed published_at",
    "value_before": "2025-12-15T10:30:00Z",
    "value_after": "2025-12-15",
    "change_type": "MODIFIED"
}
```

#### Step 4: QUALITY_SCORE
- **Action**: Calcule quality_score (0-1)
- **Logique**: 
```
score = (len(content) / 1000) * 0.5 + (completeness_ratio) * 0.5
score = min(1.0, max(0.0, score))  # Clamp 0-1
```
- **Exemple**:
```json
{
    "step_number": 4,
    "step_name": "QUALITY_SCORE",
    "action": "Calculated quality score",
    "value_before": null,
    "value_after": "0.75",
    "quality_score": 0.75,
    "change_type": "MODIFIED"
}
```

#### Step 5: FINGERPRINT
- **Action**: Génère SHA256 fingerprint
- **Format**: SHA256(title + content).hex()
- **Exemple**:
```json
{
    "step_number": 5,
    "step_name": "FINGERPRINT",
    "action": "Generated SHA256 fingerprint",
    "value_before": null,
    "value_after": "a3f4b8c9d2e1f6a7...",
    "fingerprint": "a3f4b8c9d2e1f6a7...",
    "change_type": "MODIFIED"
}
```

#### Step 6: FILTER_QUALITY
- **Action**: Filtre par quality_score ≥ 0.5
- **Raison**: Quality threshold
- **Exemple**:
```json
{
    "step_number": 6,
    "step_name": "FILTER_QUALITY",
    "action": "Evaluated against quality threshold",
    "quality_score": 0.35,
    "reason": "Quality score 0.35 < 0.5 threshold",
    "change_type": "DELETED",
    "action": "Filtered out (quality too low)"
}
```
ou
```json
{
    "step_number": 6,
    "step_name": "FILTER_QUALITY",
    "action": "Passed quality filter",
    "quality_score": 0.75,
    "reason": "Quality score 0.75 >= 0.5",
    "change_type": "KEPT"
}
```

#### Step 7: DEDUP_CHECK
- **Action**: Compare fingerprint avec existants
- **Raison**: Duplicate detection
- **Exemple** (Duplicate):
```json
{
    "step_number": 7,
    "step_name": "DEDUP_CHECK",
    "action": "Duplicate detected via fingerprint",
    "fingerprint": "a3f4b8c9d2e1f6a7...",
    "reason": "Exact match with article_id 1234",
    "change_type": "DELETED",
    "action": "Marked as duplicate, skipped insertion"
}
```

#### Step 8: INSERT_SILVER
- **Action**: Insère dans raw_data_cleaned
- **change_type**: KEPT (succès) ou DELETED (erreur)
- **Exemple**:
```json
{
    "step_number": 8,
    "step_name": "INSERT_SILVER",
    "action": "Inserted into raw_data_cleaned",
    "value_after": "article_id = 5678",
    "change_type": "KEPT"
}
```

#### Step 9: AUDIT_LOG
- **Action**: Enregistre cet audit trail
- **Exemple**:
```json
{
    "step_number": 9,
    "step_name": "AUDIT_LOG",
    "action": "Logged transformation history",
    "value_after": "audit_id = 99999",
    "change_type": "KEPT"
}
```

#### Step 10: PARTITION
- **Action**: Crée partition_date column
- **Format**: YEAR-MONTH-DAY
- **Exemple**:
```json
{
    "step_number": 10,
    "step_name": "PARTITION",
    "action": "Created partition_date column",
    "value_before": "2025-12-15T10:30:00Z",
    "value_after": "2025-12-15",
    "change_type": "MODIFIED"
}
```

### Exemple Complet Audit Trail

```sql
SELECT * FROM cleaning_audit 
WHERE raw_article_id = 1001
ORDER BY step_number;

-- Résultat:
audit_id | raw_article_id | step_number | step_name      | change_type | quality_score
---------|----------------|-------------|----------------|-------------|---------------
100001   | 1001           | 1           | LOAD           | KEPT        | NULL
100002   | 1001           | 2           | NORMALIZE      | MODIFIED    | NULL
100003   | 1001           | 3           | PARSE_DATES    | MODIFIED    | NULL
100004   | 1001           | 4           | QUALITY_SCORE  | MODIFIED    | 0.78
100005   | 1001           | 5           | FINGERPRINT    | MODIFIED    | 0.78
100006   | 1001           | 6           | FILTER_QUALITY | KEPT        | 0.78
100007   | 1001           | 7           | DEDUP_CHECK    | KEPT        | 0.78
100008   | 1001           | 8           | INSERT_SILVER  | KEPT        | 0.78
100009   | 1001           | 9           | AUDIT_LOG      | KEPT        | 0.78
100010   | 1001           | 10          | PARTITION      | MODIFIED    | 0.78
```

### Requêtes Utiles

#### Articles supprimés et raisons
```sql
SELECT 
    raw_article_id,
    step_name,
    reason,
    COUNT(*) as count
FROM cleaning_audit
WHERE change_type = 'DELETED'
GROUP BY step_name, reason
ORDER BY count DESC;
```

#### Distribution des quality scores
```sql
SELECT 
    ROUND(quality_score, 1) as score_bucket,
    COUNT(*) as articles,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM cleaning_audit WHERE step_number = 4), 1) as percent
FROM cleaning_audit
WHERE step_number = 4 AND quality_score IS NOT NULL
GROUP BY ROUND(quality_score, 1)
ORDER BY score_bucket DESC;
```

#### Doublons détectés
```sql
SELECT 
    source_name,
    fingerprint,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(raw_article_id, ', ') as article_ids
FROM (
    SELECT ca.fingerprint, ca.raw_article_id, rd.source_name
    FROM cleaning_audit ca
    JOIN raw_data rd ON ca.raw_article_id = rd.id
    WHERE ca.step_name = 'DEDUP_CHECK' AND ca.change_type = 'DELETED'
)
GROUP BY fingerprint
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
```

---

## 3. DATA_QUALITY_METRICS — Quality Snapshots

### Schéma

```sql
CREATE TABLE data_quality_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    metric_date DATE NOT NULL,
    total_articles_raw INTEGER,
    total_articles_silver INTEGER,
    avg_quality_score REAL,
    null_count INTEGER,
    duplicate_count INTEGER,
    invalid_urls INTEGER,
    incomplete_records INTEGER,
    processing_time_seconds REAL,
    success_rate_percent REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Exemple d'Entrée

```sql
INSERT INTO data_quality_metrics (
    source_name, metric_date,
    total_articles_raw, total_articles_silver,
    avg_quality_score, null_count, duplicate_count,
    invalid_urls, incomplete_records, processing_time_seconds,
    success_rate_percent
) VALUES (
    'rss_french_news', '2025-12-15',
    500, 450,
    0.72, 8, 25,
    3, 14, 245.5,
    90.0
);
```

### Requêtes Utiles

#### Quality par source (aujourd'hui)
```sql
SELECT 
    source_name,
    total_articles_raw,
    total_articles_silver,
    ROUND(avg_quality_score, 2) as avg_quality,
    success_rate_percent
FROM data_quality_metrics
WHERE metric_date = DATE('now')
ORDER BY avg_quality DESC;
```

#### Trend qualité par source (derniers 7 jours)
```sql
SELECT 
    source_name,
    metric_date,
    ROUND(avg_quality_score, 2) as quality,
    success_rate_percent as success
FROM data_quality_metrics
WHERE metric_date >= DATE('now', '-7 days')
ORDER BY source_name, metric_date DESC;
```

---

## 4. Console Output Structuré

### Format Standard

```
[TIMESTAMP] [LEVEL] [MODULE] Message...
```

**Niveaux**:
- `DEBUG`: Détails pour debug
- `INFO`: Événements importants
- `WARNING`: Situations anormales
- `ERROR`: Erreurs (non-fatales)
- `CRITICAL`: Erreurs fatales

### Exemple Session

```
[2025-12-15 10:00:00] [INFO] [INGESTION] Starting E1 pipeline...
[2025-12-15 10:00:01] [INFO] [SCHEMA] Creating 18 tables in datasens.db
[2025-12-15 10:00:05] [INFO] [SCHEMA] 18 tables created successfully
[2025-12-15 10:00:10] [INFO] [INGEST] Fetching rss_french_news (source 1/10)...
[2025-12-15 10:00:15] [INFO] [INGEST] ✓ rss_french_news: 500 articles
[2025-12-15 10:00:20] [INFO] [SYNC_LOG] Logged sync_id=1 (SUCCESS)
...
[2025-12-15 10:05:00] [INFO] [CLEANING] Starting cleaning pipeline (10 steps)
[2025-12-15 10:05:01] [INFO] [CLEANING] Step 1: LOAD (5000 articles)
[2025-12-15 10:05:02] [INFO] [CLEANING] Step 2: NORMALIZE (5000 articles)
[2025-12-15 10:05:03] [INFO] [CLEANING] Step 3: PARSE_DATES (5000 articles)
[2025-12-15 10:05:04] [INFO] [CLEANING] Step 4: QUALITY_SCORE (5000 articles, avg=0.72)
[2025-12-15 10:05:05] [INFO] [CLEANING] Step 5: FINGERPRINT (5000 articles)
[2025-12-15 10:05:06] [INFO] [CLEANING] Step 6: FILTER_QUALITY (4200 passed, 800 filtered)
[2025-12-15 10:05:07] [INFO] [CLEANING] Step 7: DEDUP_CHECK (4050 unique, 150 duplicates)
[2025-12-15 10:05:08] [INFO] [CLEANING] Step 8: INSERT_SILVER (4050 articles inserted)
[2025-12-15 10:05:09] [INFO] [AUDIT_LOG] Logged 40500 audit records
[2025-12-15 10:05:10] [INFO] [PARTITION] Created partition_date column
[2025-12-15 10:05:30] [INFO] [CLEANING] Cleaning completed in 30 seconds
[2025-12-15 10:05:35] [INFO] [TESTS] Running CRUD tests...
[2025-12-15 10:05:36] [INFO] [TESTS] ✓ CREATE test passed
[2025-12-15 10:05:37] [INFO] [TESTS] ✓ READ test passed (RAW: 5000, SILVER: 4050)
[2025-12-15 10:05:38] [INFO] [TESTS] ✓ UPDATE test passed
[2025-12-15 10:05:39] [INFO] [TESTS] ✓ DELETE test passed
[2025-12-15 10:05:40] [INFO] [TESTS] ✓ SCHEMA test passed (18/18 tables)
[2025-12-15 10:05:50] [INFO] [VISUALIZATION] Generating dashboards...
[2025-12-15 10:06:00] [INFO] [VISUALIZATION] ✓ dashboard_e1.png created
[2025-12-15 10:06:10] [INFO] [VISUALIZATION] ✓ plot_01_pie.html created
[2025-12-15 10:06:20] [INFO] [VISUALIZATION] ✓ rapport_complet_e1.html created
[2025-12-15 10:06:30] [INFO] [PIPELINE] E1 pipeline completed successfully!
```

---

## Monitoring Dashboard

### KPIs Essentiels à Suivre

```sql
-- RAW Zone Stats
SELECT 
    COUNT(*) as total_articles,
    COUNT(DISTINCT source_name) as unique_sources,
    MIN(collected_at) as oldest_article,
    MAX(collected_at) as newest_article,
    ROUND((julianday(MAX(collected_at)) - julianday(MIN(collected_at))), 1) as days_span
FROM raw_data;

-- SILVER Zone Stats
SELECT 
    COUNT(*) as total_articles_cleaned,
    ROUND(AVG(quality_score), 2) as avg_quality,
    ROUND(MIN(quality_score), 2) as min_quality,
    ROUND(MAX(quality_score), 2) as max_quality,
    COUNT(DISTINCT source_name) as unique_sources
FROM raw_data_cleaned;

-- Ingestion Health
SELECT 
    source_name,
    COUNT(*) as total_syncs,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate_percent
FROM sync_log
WHERE sync_start >= DATE('now', '-7 days')
GROUP BY source_name
ORDER BY success_rate_percent DESC;
```

---

## Best Practices

### ✅ À Faire

✅ **Log toujours**: sync_log + cleaning_audit pour chaque run  
✅ **Traçabilité**: Inclure timestamps précis  
✅ **Métadonnées**: Contexte supplémentaire en JSON  
✅ **Alertes**: Sur status = 'FAILED'  
✅ **Archivage**: Exporter logs > 6 mois vers backup  

### ❌ À Éviter

❌ **Logs vides**: Toujours inclure détails  
❌ **Pas d'erreur_message**: Toujours capturer exception  
❌ **Silence sur erreurs**: Log PARTIAL, FAILED statuses  
❌ **Perte de logs**: Pas de purge sans backup  

---

## Export & Reporting

### Export Logs en CSV

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('datasens.db')

# Export sync_log
sync_df = pd.read_sql_query("SELECT * FROM sync_log", conn)
sync_df.to_csv('sync_log_export.csv', index=False)

# Export cleaning_audit
audit_df = pd.read_sql_query("SELECT * FROM cleaning_audit", conn)
audit_df.to_csv('cleaning_audit_export.csv', index=False)

# Export metrics
metrics_df = pd.read_sql_query("SELECT * FROM data_quality_metrics", conn)
metrics_df.to_csv('quality_metrics_export.csv', index=False)
```

### Dashboard Loggé dans HTML

Le fichier `rapport_complet_e1.html` inclut déjà:
- ✅ KPIs (articles, qualité, duplicatas)
- ✅ Graphiques (Matplotlib embeddings)
- ✅ Tables sync_log (derniers syncs)
- ✅ Quality trend (7 jours)
- ✅ Checklist validation

---

**Documentation**: Complète et à jour pour production.  
**Dernière mise à jour**: 15 décembre 2025  
**Version**: 1.0.0
