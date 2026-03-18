# DataSens E1 - Excel-Style Data Export Queries

## 📊 Script Principal: viz_raw_silver_gold.py

**Purpose**: Visualize and export data across 3 analytical layers (RAW / SILVER / GOLD)

**Usage**:
```bash
python viz_raw_silver_gold.py
```

**Outputs** (4 fichiers automatiquement créés dans `exports/`):
- `raw.csv` - ALL articles (592) with all fields
- `silver.csv` - Cleaned articles with quality status
- `gold.csv` - Aggregated metrics per source (KPIs)
- `gold.parquet` - Binary compressed format (for Power BI / Tableau)

---

## 9️⃣ RAW LAYER - Brut (Sans transformation)

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
import csv
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== RAW LAYER (Excel-Style) ==========')
cursor.execute('SELECT raw_data_id, s.name, r.title, r.content, r.url, r.fingerprint, r.created_at, r.published_at FROM raw_data r JOIN source s ON r.source_id=s.source_id LIMIT 20')
# Header
print(f\"{'ID':<5} {'Source':<20} {'Title':<50} {'URL':<40} {'Created':<20}\")
print('-' * 135)
for row in cursor.fetchall():
    print(f\"{row[0]:<5} {row[1]:<20} {row[2][:50]:<50} {(row[4] or 'N/A')[:40]:<40} {row[6]:<20}\")
conn.close()
"
```

---

## 🔟 SILVER LAYER - Nettoyé (Avec quality flags)

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== SILVER LAYER (Cleaned data) ==========')
cursor.execute('''SELECT 
    r.raw_data_id,
    s.name as source,
    r.title,
    LENGTH(r.content) as content_length,
    CASE WHEN r.fingerprint IS NOT NULL THEN 'Unique' ELSE 'Duplicate' END as status,
    r.created_at
FROM raw_data r 
JOIN source s ON r.source_id=s.source_id 
ORDER BY r.created_at DESC LIMIT 20''')
print(f\"{'ID':<5} {'Source':<20} {'Title':<50} {'Content_Len':<12} {'Status':<10} {'Created':<20}\")
print('-' * 117)
for row in cursor.fetchall():
    print(f\"{row[0]:<5} {row[1]:<20} {row[2][:50]:<50} {row[3]:<12} {row[4]:<10} {row[5]:<20}\")
conn.close()
"
```

---

## 1️⃣1️⃣ GOLD LAYER - Agrégé (Métriques par source)

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== GOLD LAYER (Aggregated Insights) ==========')
cursor.execute('''SELECT 
    s.name as source,
    COUNT(r.raw_data_id) as total_articles,
    COUNT(DISTINCT r.fingerprint) as unique_articles,
    COUNT(r.raw_data_id) - COUNT(DISTINCT r.fingerprint) as duplicates,
    ROUND(100.0 * COUNT(DISTINCT r.fingerprint) / COUNT(r.raw_data_id), 1) as uniqueness_percent,
    MIN(r.created_at) as first_article,
    MAX(r.created_at) as last_article
FROM raw_data r
JOIN source s ON r.source_id=s.source_id
GROUP BY s.name
ORDER BY total_articles DESC''')
print(f\"{'Source':<25} {'Total':<8} {'Unique':<8} {'Dupes':<8} {'Quality%':<10} {'First':<20} {'Last':<20}\")
print('-' * 121)
for row in cursor.fetchall():
    print(f\"{row[0]:<25} {row[1]:<8} {row[2]:<8} {row[3]:<8} {row[4]:<10} {str(row[5])[:20]:<20} {str(row[6])[:20]:<20}\")
conn.close()
"
```

---

## 📥 CSV Exports

Automatiquement créés par le script `viz_raw_silver_gold.py`:

| Format | Fichier | Taille | Colonnes | Usage |
|--------|---------|--------|----------|-------|
| CSV | `exports/raw.csv` | 387 KB | ID, Source, Title, Content, URL, Fingerprint, Collected | ✅ Excel / Google Sheets |
| CSV | `exports/silver.csv` | 100 KB | ID, Source, Title, Content_Length, Status, Collected | ✅ Excel / Power Query |
| CSV | `exports/gold.csv` | 791 B | Source, Total, Unique, Quality%, First, Last | ✅ Excel / Dashboard |
| **PARQUET** | `exports/gold.parquet` | 5 KB | Same as gold.csv | ✅ Power BI, Tableau, Python |

**Pour ouvrir en Excel**:
1. `File > Open` → sélectionne `exports/raw.csv` (ou silver/gold)
2. Excel détecte UTF-8 automatiquement
3. Pivot tables / Charts disponibles directement

**Pour Power BI**:
```
Data > Get Data > Parquet > Sélectionne gold.parquet
```

---

## 📋 Notes

- **RAW**: Tous les 592 articles avec tous les champs (titre, contenu, URL, fingerprint, dates)
- **SILVER**: Données nettoyées avec quality flags (status = UNIQUE/DUPLICATE)
- **GOLD**: Métriques agrégées par source (Total, Unique, Quality%, Date Range)
- **PARQUET**: Format binaire compressé pour Power BI, Tableau, Python/Pandas
- **Auto-Export**: Tous les fichiers créés automatiquement par `python viz_raw_silver_gold.py`

---

## 🚀 Quick Start

```bash
# 1. Afficher les 3 couches + créer les exports
python viz_raw_silver_gold.py

# 2. Ouvrir raw.csv dans Excel
start exports\raw.csv

# 3. Ouvrir gold.parquet dans Power BI
# Data > Get Data > Parquet > Sélectionne gold.parquet
```

Generated: 2025-12-17
