"""
SparkSession Singleton - PySpark E2
====================================
Gestion centralisée de SparkSession (singleton pattern)
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

from pyspark.sql import SparkSession

# Gérer imports dans différents contextes (test vs normal)
try:
    from src.config import get_settings
except ImportError:
    from config import get_settings

_settings = get_settings()
_spark_session: SparkSession | None = None


def _project_root() -> Path:
    """Racine du dépôt (parent de src/)."""
    return Path(__file__).resolve().parents[2]


def _ensure_windows_hadoop_home() -> str | None:
    """
    Sur Windows, Hadoop attend HADOOP_HOME + bin/winutils.exe.
    Si non défini, on pointe vers <projet>/hadoop/ (voir hadoop/README.md).
    À appeler avant toute création de SparkContext / SparkSession.
    """
    if platform.system() != "Windows":
        return os.environ.get("HADOOP_HOME")

    existing = os.environ.get("HADOOP_HOME")
    if existing:
        return existing

    hadoop_home = _project_root() / "hadoop"
    bin_dir = hadoop_home / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    home_str = str(hadoop_home.resolve())
    os.environ["HADOOP_HOME"] = home_str
    return home_str


def prepare_windows_spark_environment() -> str | None:
    """
    À appeler avant ``SparkSession.builder`` dans un notebook ou un script
    si vous n'utilisez pas :func:`get_spark_session`. Corrige ``HADOOP_HOME`` sur Windows.
    Placez ``winutils.exe`` dans ``hadoop/bin/`` (voir ``hadoop/README.md``).
    """
    return _ensure_windows_hadoop_home()


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
        hadoop_home = _ensure_windows_hadoop_home()
        # Configuration pour mode local pur (PAS de connexion réseau)
        # Mode local = tout s'exécute dans le même processus JVM
        # Aucune connexion réseau nécessaire, aucun serveur distant
        # Atténue les WARN bruyants en local (Windows : pas de libhadoop native → fallback Java OK)
        _java_quiet = (
            "-Dlog4j.logger.org.apache.hadoop.util.NativeCodeLoader=ERROR "
            "-Dlog4j.logger.org.apache.spark.SparkConf=ERROR"
        )
        builder = (
            SparkSession.builder.appName(_settings.spark_app_name)
            .master("local[*]")
            .config("spark.driver.memory", _settings.spark_driver_memory)
            .config("spark.executor.memory", _settings.spark_executor_memory)
            .config("spark.sql.parquet.enableVectorizedReader", "true")
            .config("spark.sql.parquet.mergeSchema", "false")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.sql.execution.arrow.pyspark.enabled", "false")
            .config("spark.ui.enabled", "false")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.driver.host", "localhost")
            .config("spark.executor.allowSparkContext", "true")
            .config("spark.local.dir", "./spark-temp")
            .config("spark.network.timeout", "600s")
            .config("spark.executor.heartbeatInterval", "60s")
            .config("spark.driver.extraJavaOptions", _java_quiet.strip())
        )
        if hadoop_home and platform.system() == "Windows":
            builder = builder.config("spark.hadoop.hadoop.home.dir", hadoop_home)
        _spark_session = builder.getOrCreate()
        # Filtre les logs Spark côté JVM après démarrage (complément aux -D log4j)
        _spark_session.sparkContext.setLogLevel("ERROR")

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
