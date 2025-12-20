#!/bin/bash
# Script pour lancer PySpark Shell avec les imports DataSens

echo "============================================================"
echo "PYSPARK SHELL - DataSens Phase 3"
echo "============================================================"
echo

cd "$(dirname "$0")/.."

# Lancer PySpark avec PYTHONPATH
export PYTHONPATH="$PWD/src:$PYTHONPATH"

python -c "
import sys
sys.path.insert(0, '.')
from src.spark.session import get_spark_session
from src.spark.adapters import GoldParquetReader
from src.spark.processors import GoldDataProcessor
from datetime import date

spark = get_spark_session()
reader = GoldParquetReader()
processor = GoldDataProcessor()

print('\n============================================================')
print('Variables disponibles:')
print('  - spark: SparkSession')
print('  - reader: GoldParquetReader')
print('  - processor: GoldDataProcessor')
print('\nExemples:')
print('  dates = reader.get_available_dates()')
print('  df = reader.read_gold(date=dates[0])')
print('  df.show()')
print('============================================================\n')

try:
    import IPython
    IPython.embed()
except ImportError:
    import code
    code.interact(local={'spark': spark, 'reader': reader, 'processor': processor, 'date': date})
"
