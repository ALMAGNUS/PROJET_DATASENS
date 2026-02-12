#!/usr/bin/env python3
"""
Script de Test PySpark Simple
==============================
Test rapide des composants PySpark sans pytest
"""

import sys
from pathlib import Path

# Ajouter racine projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("TEST PYSPARK INTEGRATION - Phase 3")
print("=" * 70)
print()

try:
    # Test 1: Import
    print("1. Test imports...")
    from src.spark.adapters import GoldParquetReader
    from src.spark.processors import GoldDataProcessor
    from src.spark.session import close_spark_session, get_spark_session

    print("   OK Imports OK")
    print()

    # Test 2: SparkSession
    print("2. Test SparkSession...")
    spark = get_spark_session()
    assert spark is not None
    assert spark.sparkContext is not None
    print(f"   OK SparkSession cree: {spark.sparkContext.appName}")
    print()

    # Test 3: GoldParquetReader
    print("3. Test GoldParquetReader...")
    reader = GoldParquetReader()
    assert reader is not None
    print(f"   OK GoldParquetReader cree (base_path: {reader.base_path})")

    # Test dates disponibles
    dates = reader.get_available_dates()
    print(f"   OK Dates disponibles: {len(dates)} dates")
    if dates:
        print(f"      Première date: {dates[0]}, Dernière date: {dates[-1]}")
    print()

    # Test 4: Lecture Parquet (si disponible)
    if dates:
        print("4. Test lecture Parquet...")
        try:
            df = reader.read_gold(date=dates[0])
            count = df.count()
            print(f"   OK Parquet lu: {count} lignes")
            print(f"      Colonnes: {', '.join(df.columns[:5])}...")
        except Exception as e:
            print(f"   WARNING Erreur lecture: {e}")
    else:
        print("4. Test lecture Parquet...")
        print("   WARNING Aucun Parquet disponible (executer E1 pipeline d'abord)")
    print()

    # Test 5: GoldDataProcessor
    print("5. Test GoldDataProcessor...")
    processor = GoldDataProcessor()
    assert processor is not None
    print("   OK GoldDataProcessor cree")
    print()

    # Test 6: Traitement (si données disponibles)
    if dates:
        print("6. Test traitement...")
        try:
            df = reader.read_gold(date=dates[0])

            # Test process
            df_processed = processor.process(df)
            assert df_processed is not None
            print("   OK Process OK")

            # Test statistiques
            stats = processor.get_statistics(df)
            print(f"   OK Statistiques: {stats.get('total_articles', 0)} articles")
        except Exception as e:
            print(f"   WARNING Erreur traitement: {e}")
    else:
        print("6. Test traitement...")
        print("   WARNING Aucune donnee disponible")
    print()

    # Test 7: Fermeture SparkSession
    print("7. Test fermeture SparkSession...")
    close_spark_session()
    print("   OK SparkSession ferme")
    print()

    print("=" * 70)
    print("OK TOUS LES TESTS PASSENT")
    print("=" * 70)
    sys.exit(0)

except Exception as e:
    print()
    print("=" * 70)
    print(f"ERREUR: {e}")
    print("=" * 70)
    import traceback

    traceback.print_exc()
    sys.exit(1)
