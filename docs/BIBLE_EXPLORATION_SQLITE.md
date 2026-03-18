# 📖 BIBLE COMPLÈTE - EXPLORATION SQLite DATASENS E1

**Master Reference Guide** pour explorer et analyser ta base de données SQLite  
Tous les scripts testés ✅ | Copy-paste terminal prêts 🎯

---

## 🔧 SETUP INITIAL

### Localisation de la base
```
C:\Users\Utilisateur\datasens_project\datasens.db
```

### Vérifier que la DB existe
```powershell
ls C:\Users\Utilisateur\datasens_project\datasens.db -Force
```

---

## 📊 PARTIE 1: AUTOMATISÉ (Vizualisation + Export)

### 1.1 Script Principal: Vizualiser RAW/SILVER/GOLD + Export CSV/Parquet

**Fichier**: `viz_raw_silver_gold.py` (106 lignes)

**Utilisation**:
```bash
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"
python viz_raw_silver_gold.py
```

**Résultat**:
- ✅ Affiche les 3 couches (RAW/SILVER/GOLD) dans le terminal
- ✅ Crée 4 fichiers dans `exports/`:
  - `raw.csv` (387 KB) - Tous les articles
  - `silver.csv` (100 KB) - Articles nettoyés
  - `gold.csv` (791 B) - Métriques par source
  - `gold.parquet` (5 KB) - Format Power BI/Tableau

---

## 🔍 PARTIE 2: QUERIES MANUELLES (Terminal SQL)

### 2.1 ANALYSE GLOBALE DE LA BASE

#### 2.1.1 Résumé complet
```sql
SELECT 
    (SELECT COUNT(*) FROM source) as sources,
    (SELECT COUNT(*) FROM raw_data) as total_articles,
    (SELECT COUNT(DISTINCT fingerprint) FROM raw_data) as unique_articles,
    (SELECT COUNT(*) FROM raw_data WHERE fingerprint IS NULL) as duplicates,
    (SELECT COUNT(*) FROM sync_log) as sync_operations;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
c.execute('SELECT (SELECT COUNT(*) FROM source) as sources, (SELECT COUNT(*) FROM raw_data) as total_articles, (SELECT COUNT(DISTINCT fingerprint) FROM raw_data) as unique_articles, (SELECT COUNT(*) FROM raw_data WHERE fingerprint IS NULL) as duplicates, (SELECT COUNT(*) FROM sync_log) as sync_operations')
for row in c.fetchall():
    print(f'Sources: {row[0]}, Total: {row[1]}, Unique: {row[2]}, Dupes: {row[3]}, Syncs: {row[4]}')
db.close()
"
```

#### 2.1.2 Lister tous les sources enregistrées
```sql
SELECT source_id, name, description FROM source ORDER BY source_id;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== SOURCES ENREGISTREES ==========\n')
c.execute('SELECT source_id, name FROM source ORDER BY source_id')
for row in c.fetchall():
    print(f'ID {row[0]}: {row[1]}')
print()
db.close()
"
```

---

### 2.2 COUCHE RAW - ARTICLES BRUTS

#### 2.2.1 Afficher 20 derniers articles (RAW BRUT)
```sql
SELECT 
    raw_data_id, 
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    title, 
    LENGTH(content) as content_len,
    url,
    fingerprint,
    collected_at
FROM raw_data
ORDER BY raw_data_id DESC
LIMIT 20;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== 20 DERNIERS ARTICLES (RAW) ==========\n')
c.execute('''SELECT r.raw_data_id, s.name, r.title, LENGTH(r.content), r.url, r.fingerprint, r.collected_at 
FROM raw_data r JOIN source s ON r.source_id=s.source_id ORDER BY r.raw_data_id DESC LIMIT 20''')
print(f'{'ID':<5} {'Source':<20} {'Title':<50} {'Len':<5} {'URL':<35} {'Collected':<20}')
print('-'*135)
for row in c.fetchall():
    print(f'{row[0]:<5} {row[1][:20]:<20} {row[2][:50]:<50} {row[3]:<5} {(row[4] or '-')[:35]:<35} {row[6]:<20}')
print()
db.close()
"
```

#### 2.2.2 Afficher CONTENU complet d'un article
```sql
SELECT 
    raw_data_id, 
    title, 
    content, 
    url,
    collected_at
FROM raw_data
WHERE raw_data_id = [ID_ARTICLE]
LIMIT 1;
```

**Copie-colle PowerShell** (remplace [ID_ARTICLE], ex: 100):
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
article_id = 100  # CHANGE CETTE VALEUR
c.execute('SELECT raw_data_id, title, content, url, collected_at FROM raw_data WHERE raw_data_id = ?', (article_id,))
for row in c.fetchall():
    print(f'\nID: {row[0]}')
    print(f'TITRE: {row[1]}')
    print(f'CONTENU:\n{row[2]}')
    print(f'URL: {row[3]}')
    print(f'COLLECTED: {row[4]}')
db.close()
"
```

---

### 2.3 COUCHE SILVER - ARTICLES NETTOYÉS

#### 2.3.1 Voir status UNIQUE vs DUPLICATE
```sql
SELECT 
    raw_data_id,
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    title,
    LENGTH(content) as content_len,
    CASE 
        WHEN fingerprint IS NOT NULL THEN 'UNIQUE' 
        ELSE 'DUPLICATE' 
    END as status,
    collected_at
FROM raw_data
ORDER BY raw_data_id DESC
LIMIT 30;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== STATUS UNIQUE/DUPLICATE ==========\n')
c.execute('''SELECT r.raw_data_id, s.name, r.title, LENGTH(r.content),
CASE WHEN r.fingerprint IS NOT NULL THEN 'UNIQUE' ELSE 'DUPLICATE' END,
r.collected_at FROM raw_data r JOIN source s ON r.source_id=s.source_id ORDER BY r.raw_data_id DESC LIMIT 30''')
print(f'{'ID':<5} {'Source':<20} {'Title':<50} {'Len':<5} {'Status':<12}')
print('-'*92)
for row in c.fetchall():
    print(f'{row[0]:<5} {row[1][:20]:<20} {row[2][:50]:<50} {row[3]:<5} {row[4]:<12}')
print()
db.close()
"
```

#### 2.3.2 Compter UNIQUE vs DUPLICATE
```sql
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT fingerprint) as unique_count,
    COUNT(*) - COUNT(DISTINCT fingerprint) as duplicate_count,
    ROUND(100.0 * COUNT(DISTINCT fingerprint) / COUNT(*), 1) as uniqueness_percent
FROM raw_data;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== STATISTIQUES QUALITÉ ==========\n')
c.execute('SELECT COUNT(*), COUNT(DISTINCT fingerprint), COUNT(*) - COUNT(DISTINCT fingerprint), ROUND(100.0 * COUNT(DISTINCT fingerprint) / COUNT(*), 1) FROM raw_data')
row = c.fetchone()
print(f'Total articles:    {row[0]}')
print(f'Articles uniques:  {row[1]}')
print(f'Doublons détectés: {row[2]}')
print(f'Taux qualité:      {row[3]}%\n')
db.close()
"
```

---

### 2.4 COUCHE GOLD - MÉTRIQUES AGRÉGÉES

#### 2.4.1 Résumé par SOURCE (KPIs)
```sql
SELECT 
    s.name,
    COUNT(r.raw_data_id) as total_articles,
    COUNT(DISTINCT r.fingerprint) as unique_articles,
    COUNT(r.raw_data_id) - COUNT(DISTINCT r.fingerprint) as duplicates,
    ROUND(100.0 * COUNT(DISTINCT r.fingerprint) / COUNT(r.raw_data_id), 1) as quality_percent,
    MIN(r.collected_at) as first_article,
    MAX(r.collected_at) as last_article,
    COUNT(DISTINCT DATE(r.collected_at)) as days_active
FROM raw_data r
JOIN source s ON r.source_id = s.source_id
GROUP BY s.name
ORDER BY total_articles DESC;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== KPI PAR SOURCE ==========\n')
c.execute('''SELECT s.name, COUNT(r.raw_data_id), COUNT(DISTINCT r.fingerprint),
COUNT(r.raw_data_id) - COUNT(DISTINCT r.fingerprint),
ROUND(100.0 * COUNT(DISTINCT r.fingerprint) / COUNT(r.raw_data_id), 1),
MIN(r.collected_at), MAX(r.collected_at), COUNT(DISTINCT DATE(r.collected_at))
FROM raw_data r JOIN source s ON r.source_id=s.source_id GROUP BY s.name ORDER BY COUNT(r.raw_data_id) DESC''')
print(f'{'Source':<25} {'Total':<8} {'Unique':<8} {'Dupes':<8} {'Quality%':<10} {'Days':<6}')
print('-'*70)
for row in c.fetchall():
    print(f'{row[0]:<25} {row[1]:<8} {row[2]:<8} {row[3]:<8} {row[4]:<10} {row[7]:<6}')
print()
db.close()
"
```

#### 2.4.2 Top N sources par nombre d'articles
```sql
SELECT 
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    COUNT(*) as article_count
FROM raw_data
GROUP BY source_id
ORDER BY article_count DESC
LIMIT 5;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== TOP 5 SOURCES ==========\n')
c.execute('SELECT (SELECT name FROM source WHERE source_id=raw_data.source_id), COUNT(*) FROM raw_data GROUP BY source_id ORDER BY COUNT(*) DESC LIMIT 5')
for i, row in enumerate(c.fetchall(), 1):
    print(f'{i}. {row[0]}: {row[1]} articles')
print()
db.close()
"
```

---

### 2.5 ANALYSE AVANCÉE - DÉDUPLICATION

#### 2.5.1 Voir les articles DUPLIQUÉS
```sql
SELECT 
    fingerprint,
    COUNT(*) as occurrences,
    GROUP_CONCAT(raw_data_id, ', ') as article_ids
FROM raw_data
WHERE fingerprint IS NOT NULL
GROUP BY fingerprint
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 10;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== ARTICLES DUPLIQUÉS (TOP 10) ==========\n')
c.execute('''SELECT fingerprint, COUNT(*), GROUP_CONCAT(raw_data_id, ', ')
FROM raw_data WHERE fingerprint IS NOT NULL GROUP BY fingerprint HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC LIMIT 10''')
for row in c.fetchall():
    print(f'FP: {row[0][:16]}... | Occurrences: {row[1]} | IDs: {row[2]}')
print()
db.close()
"
```

#### 2.5.2 Efficacité déduplication par source
```sql
SELECT 
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    COUNT(*) as total,
    COUNT(DISTINCT fingerprint) as unique,
    COUNT(*) - COUNT(DISTINCT fingerprint) as duplicates_removed,
    ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT fingerprint)) / COUNT(*), 1) as dedup_percent
FROM raw_data
GROUP BY source_id
HAVING COUNT(*) - COUNT(DISTINCT fingerprint) > 0
ORDER BY duplicates_removed DESC;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== EFFICACITÉ DÉDUPLICATION ==========\n')
c.execute('''SELECT (SELECT name FROM source WHERE source_id=raw_data.source_id),
COUNT(*), COUNT(DISTINCT fingerprint), COUNT(*) - COUNT(DISTINCT fingerprint),
ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT fingerprint)) / COUNT(*), 1)
FROM raw_data GROUP BY source_id HAVING COUNT(*) - COUNT(DISTINCT fingerprint) > 0
ORDER BY COUNT(*) - COUNT(DISTINCT fingerprint) DESC''')
print(f'{'Source':<25} {'Total':<8} {'Unique':<8} {'Dupes':<8} {'Dedup%':<8}')
print('-'*57)
for row in c.fetchall():
    if row[0]:  # Safety check
        print(f'{row[0]:<25} {row[1]:<8} {row[2]:<8} {row[3]:<8} {row[4]:<8}%')
print()
db.close()
"
```

---

### 2.6 TIMELINE - ANALYSE TEMPORELLE

#### 2.6.1 Articles par jour
```sql
SELECT 
    DATE(collected_at) as collection_date,
    COUNT(*) as article_count,
    COUNT(DISTINCT source_id) as sources_active
FROM raw_data
GROUP BY DATE(collected_at)
ORDER BY collection_date DESC;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== ARTICLES PAR JOUR ==========\n')
c.execute('''SELECT DATE(collected_at), COUNT(*), COUNT(DISTINCT source_id)
FROM raw_data GROUP BY DATE(collected_at) ORDER BY DATE(collected_at) DESC''')
print(f'{'Date':<15} {'Articles':<10} {'Sources':<10}')
print('-'*35)
for row in c.fetchall():
    print(f'{str(row[0]):<15} {row[1]:<10} {row[2]:<10}')
print()
db.close()
"
```

#### 2.6.2 Vitesse d'ingestion (articles par heure)
```sql
SELECT 
    DATETIME(collected_at, 'start of hour') as hour,
    COUNT(*) as articles_per_hour
FROM raw_data
GROUP BY DATETIME(collected_at, 'start of hour')
ORDER BY hour DESC
LIMIT 24;
```

**Copie-colle PowerShell**:
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
print('\n========== ARTICLES PAR HEURE (dernières 24h) ==========\n')
c.execute('''SELECT DATETIME(collected_at, 'start of hour'), COUNT(*)
FROM raw_data GROUP BY DATETIME(collected_at, 'start of hour')
ORDER BY DATETIME(collected_at, 'start of hour') DESC LIMIT 24''')
print(f'{'Heure':<20} {'Articles':<10}')
print('-'*30)
for row in c.fetchall():
    print(f'{str(row[0]):<20} {row[1]:<10}')
print()
db.close()
"
```

---

### 2.7 VALIDATION & QUALITÉ DES DONNÉES

#### 2.7.1 Articles sans URL
```sql
SELECT 
    raw_data_id,
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    title,
    collected_at
FROM raw_data
WHERE url IS NULL OR url = ''
LIMIT 20;
```

#### 2.7.2 Articles sans contenu
```sql
SELECT 
    raw_data_id,
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    title,
    LENGTH(COALESCE(content, '')) as content_length
FROM raw_data
WHERE content IS NULL OR LENGTH(TRIM(content)) < 10
LIMIT 20;
```

#### 2.7.3 Titres très courts (potentiellement invalides)
```sql
SELECT 
    raw_data_id,
    (SELECT name FROM source WHERE source_id=raw_data.source_id) as source,
    title,
    LENGTH(title) as title_length
FROM raw_data
WHERE LENGTH(title) < 5
LIMIT 20;
```

---

### 2.8 INSPECT - SCHÉMA DE LA BASE

#### 2.8.1 Afficher structure de toutes les tables
```bash
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
c.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name\")
tables = c.fetchall()
print('\n========== SCHÉMA BASE SQLITE ==========\n')
for table in tables:
    table_name = table[0]
    c.execute(f'PRAGMA table_info({table_name})')
    columns = c.fetchall()
    c.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = c.fetchone()[0]
    print(f'\n{table_name.upper()} ({count} rows)')
    print(f'  {'Col#':<5} {'Name':<25} {'Type':<15}')
    print('  ' + '-'*45)
    for col in columns:
        print(f'  {col[0]:<5} {col[1]:<25} {col[2]:<15}')
print()
db.close()
"
```

---

### 2.9 EXPORT PERSONNALISÉ

#### 2.9.1 Export RAW par SOURCE
```powershell
cd "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3, csv
from pathlib import Path
db = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
c = db.cursor()
c.execute('SELECT DISTINCT source_id, (SELECT name FROM source WHERE source_id=raw_data.source_id) FROM raw_data')
sources = c.fetchall()
Path('exports').mkdir(exist_ok=True)
for source_id, source_name in sources:
    c.execute('SELECT raw_data_id, title, content, url, collected_at FROM raw_data WHERE source_id=?', (source_id,))
    filename = f'exports/raw_{source_name.replace(\" \", \"_\")}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Title', 'Content', 'URL', 'Collected'])
        writer.writerows(c.fetchall())
    print(f'Exported: {filename}')
db.close()
"
```

---

## 📋 TABLEAU RÉCAPITULATIF

| Script | Taille | Résultat | Usage |
|--------|--------|----------|-------|
| `viz_raw_silver_gold.py` | 106 lignes | Terminal + 4 CSV/Parquet | ✅ Vizualisation complète |
| Queries RAW | - | Terminal | 🔍 Explorez articles bruts |
| Queries SILVER | - | Terminal | 🧹 Analysez qualité |
| Queries GOLD | - | Terminal | 📊 KPIs par source |
| Queries Dedup | - | Terminal | 🔄 Doublons |
| Queries Timeline | - | Terminal | 📈 Ingestion tempo |

---

## 🚀 WORKFLOW TYPIQUE

### 1️⃣ Démarrer l'exploration
```bash
python viz_raw_silver_gold.py
```
→ Visualise les 3 couches + exporte CSV/Parquet

### 2️⃣ Ouvrir les exports dans Excel
```bash
start exports\raw.csv
start exports\gold.csv
```

### 3️⃣ Questions spécifiques? Copie-colle un query du terminal
Ex: "Quels articles de google_news_rss sont dupliqués?"
```sql
SELECT raw_data_id, title FROM raw_data WHERE source_id=1 AND fingerprint IS NULL LIMIT 10
```

### 4️⃣ Pour Power BI/Tableau
```bash
# Ouvrir gold.parquet
# Data > Get Data > Parquet > gold.parquet
```

---

## 💡 CONSEILS D'UTILISATION

**Pour explorer rapidement:**
- Utilise `viz_raw_silver_gold.py` → regarde les CSV dans Excel
- Utilise les TOP queries pour premières insights

**Pour analyses pointues:**
- Copie-colle les queries du terminal
- Customise avec ton source_id ou dates spécifiques

**Pour BI/Dashboards:**
- Utilise les fichiers Parquet (gold.parquet surtout)
- Plus performant que CSV pour Power BI/Tableau

**Pour déboguer extraction:**
- Query 2.5.1: Vois les doublons détectés
- Query 2.7.x: Valide qualité des données
- Query 2.6.x: Analyse tempo ingestion

---

## 📞 FICHIERS RÉFÉRENCE

- **DB_QUERIES.md** - Queries SQL pures (terminal)
- **DB_QUERIES_EXCEL.md** - Avec instructions Excel/Parquet  
- **BIBLE_EXPLORATION_SQLITE.md** - Ce fichier (master reference)
- **viz_raw_silver_gold.py** - Auto-explore + export

---

**Dernière mise à jour**: 2025-12-17  
**Base**: `datasens.db` (592 articles, 10 sources)  
**Prêt pour production** ✅
