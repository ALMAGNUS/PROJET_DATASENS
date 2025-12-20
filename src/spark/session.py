"""
SparkSession Singleton - PySpark E2
====================================
Gestion centralisée de SparkSession (singleton pattern)
"""


from pyspark.sql import SparkSession

# Gérer imports dans différents contextes (test vs normal)
try:
    from src.config import get_settings
except ImportError:
    from config import get_settings

_settings = get_settings()
_spark_session: SparkSession | None = None


def get_spark_session() -> SparkSession:
    """
    Get or create SparkSession singleton

    Returns:
        SparkSession instance

    Note:
        - Singleton pattern: une seule instance SparkSession
        - Configuration depuis Settings (config.py)
        - Optimisé pour lecture Parquet
    """
    global _spark_session

    if _spark_session is None:
        # Configuration pour mode local pur (PAS de connexion réseau)
        # Mode local = tout s'exécute dans le même processus JVM
        # Aucune connexion réseau nécessaire, aucun serveur distant
        _spark_session = SparkSession.builder \
            .appName(_settings.spark_app_name) \
            .master("local[*]") \
            .config("spark.driver.memory", _settings.spark_driver_memory) \
            .config("spark.executor.memory", _settings.spark_executor_memory) \
            .config("spark.sql.parquet.enableVectorizedReader", "true") \
            .config("spark.sql.parquet.mergeSchema", "false") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
            .config("spark.ui.enabled", "false") \
            .config("spark.driver.bindAddress", "127.0.0.1") \
            .config("spark.driver.host", "localhost") \
            .config("spark.executor.allowSparkContext", "true") \
            .config("spark.local.dir", "./spark-temp") \
            .config("spark.network.timeout", "600s") \
            .config("spark.executor.heartbeatInterval", "60s") \
            .getOrCreate()

    return _spark_session


def close_spark_session() -> None:
    """
    Close SparkSession singleton

    Note:
        - Appeler à la fin du traitement
        - Libère les ressources Spark
    """
    global _spark_session

    if _spark_session is not None:
        _spark_session.stop()
        _spark_session = None
