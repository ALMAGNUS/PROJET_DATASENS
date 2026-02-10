"""
GoldParquetReader - PySpark E2
===============================
Lecteur Parquet GOLD depuis E1 (isolation E1)
"""

from datetime import date as date_type
from pathlib import Path

from loguru import logger
from pyspark.sql import DataFrame

# Gérer imports dans différents contextes (test vs normal)
try:
    from src.config import get_settings
except ImportError:
    from config import get_settings

from ..interfaces.data_reader import DataReader
from ..session import get_spark_session

settings = get_settings()


class GoldParquetReader(DataReader):
    """
    Lecteur Parquet GOLD depuis E1

    Principe: Isolation E1
    - Lit uniquement les Parquet générés par E1
    - Aucune connexion directe à SQLite
    - Lecture seule (pas de modification E1)

    Architecture:
    - SRP: Responsabilité unique = lecture Parquet GOLD
    - DIP: Implémente DataReader (abstraction)
    """

    def __init__(self, base_path: str | None = None):
        """
        Initialise le lecteur Parquet GOLD

        Args:
            base_path: Chemin de base pour Parquet (défaut: data/gold)
        """
        self.base_path = Path(base_path or settings.parquet_base_path)
        self.spark = get_spark_session()

    def read(self, path: str) -> DataFrame:
        """
        Lit Parquet depuis un path

        Args:
            path: Chemin vers fichier/partition Parquet

        Returns:
            DataFrame Spark

        Raises:
            FileNotFoundError: Si le path n'existe pas
        """
        path_obj = Path(path)

        if not path_obj.exists() and "*" not in str(path):
            raise FileNotFoundError(f"Parquet not found: {path}")

        # Utiliser chemin absolu pour éviter problèmes de résolution
        abs_path = str(path_obj.resolve()) if path_obj.exists() else str(path)

        # Lecture Parquet en mode local (pas de connexion réseau)
        return self.spark.read.parquet(abs_path)

    def read_gold(self, date: date_type | None = None) -> DataFrame:
        """
        Lit Parquet GOLD pour une date donnée (ou toutes les dates)

        Args:
            date: Date au format date (optionnel, défaut: toutes les dates)

        Returns:
            DataFrame Spark avec toutes les colonnes GOLD

        Raises:
            FileNotFoundError: Si aucun Parquet trouvé

        Example:
            >>> reader = GoldParquetReader()
            >>> df = reader.read_gold(date=date(2025, 12, 20))
            >>> df.show()
        """
        if date:
            # Lecture pour une date spécifique
            partition_path = self.base_path / f"date={date:%Y-%m-%d}" / "articles.parquet"

            if not partition_path.exists():
                raise FileNotFoundError(
                    f"Parquet GOLD not found for date {date:%Y-%m-%d} at {partition_path}"
                )

            return self.read(str(partition_path))
        else:
            # Lecture de toutes les partitions
            # Lister toutes les partitions et les lire explicitement (plus robuste que wildcard)
            partitions = list(self.base_path.glob("date=*/articles.parquet"))

            if not partitions:
                raise FileNotFoundError(f"No Parquet GOLD partitions found in {self.base_path}")

            # Lire toutes les partitions et les unionner explicitement
            # (évite les problèmes de connexion avec wildcard sur Windows)
            if len(partitions) == 1:
                return self.read(str(partitions[0]))

            # Lire toutes les partitions et les unionner
            # Pour éviter problèmes de connexion, on lit une par une et on unionne progressivement
            dfs = []
            for partition in partitions:
                try:
                    df = self.read(str(partition))
                    dfs.append(df)
                except (ConnectionRefusedError, OSError) as e:
                    # Erreur de connexion réseau - skip cette partition
                    logger.warning("Connection error reading partition {}: {}", partition, e)
                    continue
                except Exception as e:
                    # Autres erreurs - skip cette partition
                    logger.warning("Failed to read partition {}: {}", partition, e)
                    continue

            if not dfs:
                raise FileNotFoundError(
                    f"Failed to read any Parquet GOLD partitions from {self.base_path}"
                )

            if len(dfs) == 1:
                return dfs[0]

            # Union de tous les DataFrames avec gestion des schémas différents
            result = dfs[0]
            for df in dfs[1:]:
                try:
                    # Essayer union standard d'abord
                    result = result.union(df)
                except Exception:
                    # Si échec (schémas différents), utiliser unionByName
                    try:
                        result = result.unionByName(df, allowMissingColumns=True)
                    except Exception as union_error:
                        # Si même unionByName échoue, on skip cette partition
                        logger.warning(
                            "Cannot union partition (schema/connection issue): {}", union_error
                        )
                        continue

            return result

    def read_gold_date_range(self, start_date: date_type, end_date: date_type) -> DataFrame:
        """
        Lit Parquet GOLD pour une plage de dates

        Args:
            start_date: Date de début
            end_date: Date de fin

        Returns:
            DataFrame Spark avec données de la plage

        Example:
            >>> reader = GoldParquetReader()
            >>> df = reader.read_gold_date_range(
            ...     date(2025, 12, 18),
            ...     date(2025, 12, 20)
            ... )
        """
        from datetime import timedelta

        # Construire liste de paths pour chaque date
        paths = []
        current_date = start_date

        while current_date <= end_date:
            partition_path = self.base_path / f"date={current_date:%Y-%m-%d}" / "articles.parquet"
            if partition_path.exists():
                paths.append(str(partition_path))
            current_date += timedelta(days=1)

        if not paths:
            raise FileNotFoundError(
                f"No Parquet GOLD found for date range {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}"
            )

        # Lire tous les Parquet et les unionner
        dfs = [self.read(path) for path in paths]
        if len(dfs) == 1:
            return dfs[0]

        # Union de tous les DataFrames avec gestion des schémas différents
        # Utiliser unionByName avec allowMissingColumns pour gérer schémas incompatibles
        result = dfs[0]
        for df in dfs[1:]:
            try:
                # Essayer union standard d'abord
                result = result.union(df)
            except Exception:
                # Si échec (schémas différents), utiliser unionByName
                try:
                    result = result.unionByName(df, allowMissingColumns=True)
                except Exception as e:
                    # Si même unionByName échoue, on skip cette partition
                    logger.warning("Cannot union partition (schema mismatch): {}", e)
                    continue

        return result

    def get_available_dates(self) -> list[date_type]:
        """
        Liste les dates disponibles dans les partitions Parquet

        Returns:
            Liste de dates disponibles

        Example:
            >>> reader = GoldParquetReader()
            >>> dates = reader.get_available_dates()
            >>> print(dates)
            [date(2025, 12, 16), date(2025, 12, 18), ...]
        """
        partitions = list(self.base_path.glob("date=*/articles.parquet"))
        dates = []

        for partition in partitions:
            # Extraire date depuis path: date=YYYY-MM-DD
            date_str = partition.parent.name.split("=")[1]
            try:
                dates.append(date_type.fromisoformat(date_str))
            except ValueError:
                continue

        return sorted(dates)
