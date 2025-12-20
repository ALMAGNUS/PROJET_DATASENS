"""
DataReader Interface - PySpark E2
==================================
Interface abstraite pour lecture de données (DIP)
"""

from abc import ABC, abstractmethod

from pyspark.sql import DataFrame


class DataReader(ABC):
    """
    Interface pour lecture de données (abstraction)

    Principe: Dependency Inversion Principle (DIP)
    - Dépendances vers abstractions, pas implémentations
    - Permet substitution facile (Parquet, CSV, JDBC, etc.)
    """

    @abstractmethod
    def read(self, path: str) -> DataFrame:
        """
        Lit données depuis un path

        Args:
            path: Chemin vers les données

        Returns:
            DataFrame Spark

        Raises:
            FileNotFoundError: Si le path n'existe pas
        """
        pass
