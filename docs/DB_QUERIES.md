# DataSens E1 - Database Query Scripts

## 📋 Terminal Commands for Database Exploration

Copy-paste each command directly into PowerShell to query the database.

---

## 1️⃣ GLOBAL OVERVIEW

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== GLOBAL OVERVIEW ==========')
cursor.execute('SELECT COUNT(*) FROM source')
print(f'Sources: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM raw_data')
total = cursor.fetchone()[0]
print(f'Total articles: {total}')
cursor.execute('SELECT COUNT(DISTINCT fingerprint) FROM raw_data')
unique = cursor.fetchone()[0]
print(f'Unique articles: {unique}')
print(f'Duplicates: {total - unique}')
cursor.execute('SELECT COUNT(*) FROM sync_log')
print(f'Sync logs: {cursor.fetchone()[0]}')
conn.close()
"
```

---

## 2️⃣ ARTICLES PAR SOURCE (Detailed)

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== ARTICLES BY SOURCE ==========')
cursor.execute('SELECT source_id, name FROM source ORDER BY source_id')
for sid, sname in cursor.fetchall():
    cursor.execute('SELECT COUNT(*) FROM raw_data WHERE source_id=?', (sid,))
    count = cursor.fetchone()[0]
    print(f'{sname}: {count}')
conn.close()
"
```

---

## 3️⃣ TOP 10 RECENT ARTICLES

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== TOP 10 RECENT ARTICLES ==========')
cursor.execute('SELECT s.name, r.title, r.published_at FROM raw_data r JOIN source s ON r.source_id=s.source_id ORDER BY r.created_at DESC LIMIT 10')
for source, title, date in cursor.fetchall():
    print(f'[{source}] {title[:60]}... ({date})')
conn.close()
"
```

---

## 4️⃣ DEDUPLICATION ANALYSIS

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== DEDUPLICATION ANALYSIS ==========')
cursor.execute('SELECT fingerprint, COUNT(*) as cnt FROM raw_data GROUP BY fingerprint HAVING cnt > 1 ORDER BY cnt DESC LIMIT 5')
for fp, cnt in cursor.fetchall():
    print(f'Fingerprint {fp[:16]}...: {cnt} occurrences')
cursor.execute('SELECT COUNT(DISTINCT fingerprint) FROM raw_data')
unique = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM raw_data')
total = cursor.fetchone()[0]
print(f'\nUniqueness rate: {unique}/{total} = {100*unique/total:.1f}%')
conn.close()
"
```

---

## 5️⃣ TIMELINE (Articles by Day)

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== TIMELINE (by day) ==========')
cursor.execute(\"SELECT DATE(created_at), COUNT(*) FROM raw_data GROUP BY DATE(created_at) ORDER BY created_at DESC LIMIT 10\")
for date, cnt in cursor.fetchall():
    print(f'{date}: {cnt} articles')
conn.close()
"
```

---

## 6️⃣ COMPLETE STATISTICS

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== COMPLETE STATISTICS ==========')
cursor.execute('SELECT s.name, COUNT(r.source_id) FROM source s LEFT JOIN raw_data r ON s.source_id=r.source_id GROUP BY s.source_id ORDER BY COUNT(r.source_id) DESC')
for source, cnt in cursor.fetchall():
    print(f'{source}: {cnt}')
print()
cursor.execute('SELECT COUNT(*) FROM raw_data WHERE url IS NOT NULL')
with_url = cursor.fetchone()[0]
print(f'Articles with URL: {with_url}')
cursor.execute('SELECT AVG(LENGTH(content)) FROM raw_data')
avg_len = cursor.fetchone()[0]
print(f'Avg content length: {avg_len:.0f} chars')
cursor.execute('SELECT MIN(created_at), MAX(created_at) FROM raw_data')
date_range = cursor.fetchone()
print(f'Date range: {date_range[0]} to {date_range[1]}')
conn.close()
"
```

---

## 7️⃣ DATABASE SCHEMA

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== DATABASE SCHEMA ==========')
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
for table in cursor.fetchall():
    print(f'\nTable: {table[0]}')
    cursor.execute(f'PRAGMA table_info({table[0]})')
    for col in cursor.fetchall():
        print(f'  - {col[1]} ({col[2]})')
conn.close()
"
```

---

## 8️⃣ SAMPLE DATA (First 5 Articles)

```bash
cd "c:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"; python -c "
import sqlite3
conn = sqlite3.connect('C:/Users/Utilisateur/datasens_project/datasens.db')
cursor = conn.cursor()
print('\n========== SAMPLE DATA (5 articles) ==========')
cursor.execute('SELECT s.name, r.title, r.url, r.published_at FROM raw_data r JOIN source s ON r.source_id=s.source_id LIMIT 5')
for source, title, url, date in cursor.fetchall():
    print(f'\nSource: {source}')
    print(f'Title: {title}')
    print(f'URL: {url}')
    print(f'Date: {date}')
    print('-' * 60)
conn.close()
"
```

---

## 📊 Notes

- **Database Location:** `C:\Users\Utilisateur\datasens_project\datasens.db`
- **No code lines counted** - These are pure query scripts
- **Use any of these** - They don't modify the DB, only query it
- **Copy entire command** - From `cd` to final `"`

---

Generated: 2025-12-17
