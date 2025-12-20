"""
PySpark Adapters - Data Readers
================================
Adapters pour lecture de données (Parquet, etc.)
"""

from .gold_parquet_reader import GoldParquetReader

__all__ = ["GoldParquetReader"]
