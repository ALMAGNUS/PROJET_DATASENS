#!/usr/bin/env python3
"""
Shell PySpark Interactif - Phase 3
===================================
Lance un shell PySpark interactif pour tester les composants
"""

import sys
from pathlib import Path

# Ajouter racine projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("PYSPARK SHELL - DataSens Phase 3")
print("=" * 70)
print()
print("Importation des composants...")

try:
    from datetime import date

    from src.spark.adapters import GoldParquetReader
    from src.spark.processors import GoldDataProcessor
    from src.spark.session import close_spark_session, get_spark_session

    print("OK Imports reussis")
    print()

    # Créer SparkSession
    print("Creation SparkSession (mode local, pas de connexion reseau)...")
    spark = get_spark_session()
    print(f"OK SparkSession cree: {spark.sparkContext.appName}")
    print(f"   Master: {spark.sparkContext.master}")
    print()

    # Créer reader et processor
    reader = GoldParquetReader()
    processor = GoldDataProcessor()

    print("=" * 70)
    print("SHELL PYSPARK PRET")
    print("=" * 70)
    print()
    print("Variables disponibles:")
    print("  - spark: SparkSession")
    print("  - reader: GoldParquetReader")
    print("  - processor: GoldDataProcessor")
    print()
    print("Exemples:")
    print("  dates = reader.get_available_dates()")
    print("  df = reader.read_gold(date=dates[0])")
    print("  df.show()")
    print("  stats = processor.get_statistics(df)")
    print()
    print("Tapez 'exit()' pour quitter")
    print("=" * 70)
    print()

    # Lancer shell interactif
    try:
        # Essayer IPython si disponible (meilleure expérience)
        import IPython

        IPython.embed()
    except ImportError:
        # Fallback vers code.interact standard
        import code

        shell_vars = {
            "spark": spark,
            "reader": reader,
            "processor": processor,
            "date": date,
        }
        code.interact(local=shell_vars, banner="")

except Exception as e:
    print(f"ERREUR: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
finally:
    try:
        close_spark_session()
        print("\nSparkSession ferme")
    except:
        pass
