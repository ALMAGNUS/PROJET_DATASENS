"""
PySpark E2 - Big Data Processing
=================================
Intégration PySpark pour traitement Big Data (Phase 3)

Architecture:
- Isolation E1: Lecture seule depuis Parquet (pas de modification E1)
- OOP/SOLID/DRY: Interfaces, singleton, séparation responsabilités
- Scalabilité: Traitement distribué avec Spark

Composants:
- session: SparkSession singleton
- adapters: Lecteurs de données (GoldParquetReader)
- processors: Processeurs de données (GoldDataProcessor)
- interfaces: Interfaces abstraites (DataReader, DataProcessor)
"""

from .adapters import GoldParquetReader
from .interfaces import DataProcessor, DataReader
from .processors import GoldDataProcessor
from .session import close_spark_session, get_spark_session

__version__ = "0.1.0"
__status__ = "IN_DEVELOPMENT"

__all__ = [
    "DataProcessor",
    "DataReader",
    "GoldDataProcessor",
    "GoldParquetReader",
    "close_spark_session",
    "get_spark_session",
]
