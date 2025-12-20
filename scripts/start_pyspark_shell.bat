@echo off
REM Script pour lancer PySpark Shell avec les imports DataSens
echo ============================================================
echo PYSPARK SHELL - DataSens Phase 3
echo ============================================================
echo.

cd /d "%~dp0\.."

REM Lancer PySpark avec PYTHONPATH
set PYTHONPATH=%CD%\src;%PYTHONPATH%

python -c "import sys; sys.path.insert(0, '.'); from src.spark.session import get_spark_session; from src.spark.adapters import GoldParquetReader; from src.spark.processors import GoldDataProcessor; from datetime import date; spark = get_spark_session(); reader = GoldParquetReader(); processor = GoldDataProcessor(); print('\\n============================================================'); print('Variables disponibles:'); print('  - spark: SparkSession'); print('  - reader: GoldParquetReader'); print('  - processor: GoldDataProcessor'); print('\\nExemples:'); print('  dates = reader.get_available_dates()'); print('  df = reader.read_gold(date=dates[0])'); print('  df.show()'); print('============================================================\\n'); import IPython; IPython.embed()" 2>nul

if errorlevel 1 (
    echo.
    echo IPython non disponible, utilisation du shell Python standard...
    python scripts/pyspark_shell.py
)

pause
