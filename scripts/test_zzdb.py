#!/usr/bin/env python3
"""Test ZZDB - Données synthétiques (CSV, pas MongoDB)."""
import os
import sqlite3
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 80)
print("  TEST ZZDB - Données synthétiques (CSV)")
print("=" * 80)

# 1. Vérifier fichier CSV ZZDB
print("\n[1/6] Vérification fichier ZZDB CSV...")
zzdb_paths = [
    project_root / "zzdb" / "zzdb_dataset.csv",
    project_root / "zzdb" / "export" / "zzdb_dataset.csv",
    project_root / "data" / "raw" / "zzdb_csv" / "zzdb_dataset.csv",
]
zzdb_csv = next((p for p in zzdb_paths if p.exists()), None)
if not zzdb_csv:
    print("   ❌ zzdb_dataset.csv introuvable")
    sys.exit(1)
print(f"   ✅ {zzdb_csv}")

# 2. Test extraction CSVExtractor
print("\n[2/6] Test extraction CSVExtractor...")
from src.e1.core import Source, create_extractor

s = Source(source_name="zzdb_csv", acquisition_type="csv", url=str(zzdb_csv))
e = create_extractor(s)
articles = e.extract()
print(f"   ✅ {len(articles)} articles extraits")
if articles:
    print(f"   Exemple: {articles[0].title[:60]}...")

# 3. Test pipeline (zzdb_csv dans sources_config)
print("\n[3/6] Test intégration pipeline...")
try:
    from src.e1.pipeline import E1Pipeline
    p = E1Pipeline(quiet=True)
    pipeline_articles = p.extract()
    zzdb_articles = [a for a, src in pipeline_articles if "zzdb" in src.lower()]
    print(f"   ✅ {len(zzdb_articles)} articles ZZDB dans le pipeline")
    print(f"   Total extraits: {len(pipeline_articles)} articles")
    p.db.conn.close()
except Exception as ex:
    print(f"   ⚠️  Pipeline: {str(ex)[:60]}")
    zzdb_articles = []

# 4. Vérifier base principale
print("\n[4/6] Vérification base principale...")
main_db = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
if Path(main_db).exists():
    conn = sqlite3.connect(main_db)
    cur = conn.cursor()
    cur.execute(
        """SELECT COUNT(*) FROM raw_data r
           JOIN source s ON r.source_id = s.source_id
           WHERE s.name LIKE '%zzdb%'"""
    )
    count = cur.fetchone()[0]
    print(f"   ✅ {count} articles ZZDB dans la base principale")
    conn.close()
else:
    print(f"   ⚠️  Base non trouvée: {main_db}")

# 5. Test catapulte
print("\n[5/6] Test catapulte...")
try:
    from zzdb.catapulte_to_pipeline import ZzdbCatapult, ZzdbFileScanner, SourceConfig
    scanner = ZzdbFileScanner(Path(project_root / "zzdb"), {".csv", ".json"})
    files = scanner.scan()
    if files:
        catapult = ZzdbCatapult(
            db_path=Path(main_db),
            source_config=SourceConfig(name="zzdb_csv"),
            dry_run=True,
            limit=5,
        )
        stats = catapult.import_files(files[:1])
        print(f"   ✅ Catapulte (dry-run): {stats.parsed_rows} lignes parsées")
    else:
        print("   ⚠️  Aucun fichier à catapulter")
except Exception as ex:
    print(f"   ⚠️  Catapulte: {str(ex)[:60]}")

# 6. Test inject_csv
print("\n[6/6] Test inject_csv script...")
try:
    import subprocess
    r = subprocess.run(
        [sys.executable, "scripts/inject_csv.py", str(zzdb_csv), "--source-name", "test_zzdb"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode == 0:
        print("   ✅ inject_csv.py OK")
    else:
        print(f"   ⚠️  {r.stderr[:80] if r.stderr else r.stdout[:80]}")
except Exception as ex:
    print(f"   ⚠️  inject_csv: {str(ex)[:60]}")

print("\n" + "=" * 80 + "\n")
