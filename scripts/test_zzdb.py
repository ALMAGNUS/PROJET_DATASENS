#!/usr/bin/env python3
"""Test complet de ZZDB - Base synthétique"""
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

print("\n" + "=" * 80)
print("  TEST ZZDB - Base de Données Synthétiques")
print("=" * 80)

zzdb_mongo_uri = os.getenv("ZZDB_MONGO_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
zzdb_db_name = os.getenv("ZZDB_MONGO_DB", "zzdb")
zzdb_collection_name = os.getenv("ZZDB_MONGO_COLLECTION", "synthetic_articles")

# 1. Vérifier la base
print("\n[1/6] Vérification de la base de données...")
client = None
try:
    from pymongo import MongoClient

    client = MongoClient(zzdb_mongo_uri, serverSelectionTimeoutMS=3000)
    collection = client[zzdb_db_name][zzdb_collection_name]
    count = collection.count_documents({})
    print(f"   ✅ MongoDB OK: {zzdb_mongo_uri}/{zzdb_db_name}.{zzdb_collection_name}")
    print(f"   📊 Documents: {count:,}")
except Exception as e:
    print(f"   ❌ MongoDB KO: {str(e)[:80]}")
    sys.exit(1)

# 2. Statistiques de la base
print("\n[2/6] Statistiques de la base...")
total = collection.count_documents({})
sentiments = {
    k: collection.count_documents({"sentiment": k}) for k in collection.distinct("sentiment")
}
themes = {k: collection.count_documents({"theme": k}) for k in collection.distinct("theme")}

print(f"   Total articles: {total}")
print(f"   Sentiments: {sentiments}")
print(f"   Thèmes: {themes}")

# 3. Test extraction
print("\n[3/6] Test extraction MongoExtractor...")
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core import Source, create_extractor

s = Source(source_name="zzdb_synthetic", acquisition_type="mongodb", url=zzdb_mongo_uri)
e = create_extractor(s)
articles = e.extract()

print(f"   ✅ {len(articles)} articles extraits")
if articles:
    print(f"   Exemple: {articles[0].title[:60]}...")
    print(f"   Source: {articles[0].source_name}")

# 4. Test intégration pipeline
print("\n[4/6] Test intégration dans le pipeline...")
os.environ["ZZDB_MAX_ARTICLES"] = "10"
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from main import E1Pipeline

    p = E1Pipeline()
    pipeline_articles = p.extract()
    zzdb_articles = [a for a, s in pipeline_articles if s == "zzdb_synthetic"]

    print(f"   ✅ {len(zzdb_articles)} articles ZZDB dans le pipeline")
    print(f"   Total extraits: {len(pipeline_articles)} articles")
    p.db.conn.close()
except Exception as e:
    print(f"   ⚠️  Pipeline test: {str(e)[:60]}")
    zzdb_articles = []

# 5. Vérifier dans la base principale
print("\n[5/6] Vérification dans la base principale...")
main_db = os.getenv("DB_PATH", str(Path.home() / "datasens_project" / "datasens.db"))
if Path(main_db).exists():
    main_conn = sqlite3.connect(main_db)
    main_c = main_conn.cursor()
    main_c.execute(
        """
        SELECT COUNT(*) FROM raw_data r
        JOIN source s ON r.source_id = s.source_id
        WHERE s.name = 'zzdb_synthetic'
    """
    )
    zzdb_in_main = main_c.fetchone()[0]
    print(f"   ✅ {zzdb_in_main} articles ZZDB dans la base principale")
    main_conn.close()
else:
    print(f"   ⚠️  Base principale non trouvée: {main_db}")

# 6. Test exports
print("\n[6/6] Test exports (GOLD)...")
try:
    from src.aggregator import DataAggregator

    main_db_path = main_db if Path(main_db).exists() else None
    if main_db_path:
        agg = DataAggregator(main_db_path)
        df = agg.aggregate()

        zzdb_count = len(df[df["source"] == "zzdb_synthetic"]) if "source" in df.columns else 0
        academic_count = (
            len(df[df["source_type"] == "academic"]) if "source_type" in df.columns else 0
        )

        print(f"   ✅ GOLD export - Articles ZZDB: {zzdb_count}")
        print(f"   ✅ GOLD export - Articles académiques: {academic_count}")
        print(f"   Total GOLD: {len(df)}")

        if "source_type" in df.columns:
            print("   Colonne source_type présente: ✅")
        else:
            print("   Colonne source_type manquante: ⚠️")

        agg.close()
    else:
        print("   ⚠️  Base principale non disponible pour test exports")
except Exception as e:
    print(f"   ⚠️  Erreur exports: {str(e)[:60]}")

if client is not None:
    client.close()

print("\n" + "=" * 80)
print("  RÉSUMÉ")
print("=" * 80)
print(f"  ✅ Base ZZDB: {total} articles")
print(f"  ✅ Extraction: {len(articles)} articles")
print(f"  ✅ Pipeline: {len(zzdb_articles)} articles")
if Path(main_db).exists():
    print(f"  ✅ Base principale: {zzdb_in_main} articles ZZDB")
print("=" * 80 + "\n")
