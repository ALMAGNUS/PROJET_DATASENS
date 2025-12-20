"""
DataProcessor Interface - PySpark E2
====================================
Interface abstraite pour traitement de données (DIP)
"""

from abc import ABC, abstractmethod

from pyspark.sql import DataFrame


class DataProcessor(ABC):
    """
    Interface pour traitement de données (abstraction)

    Principe: Dependency Inversion Principle (DIP)
    - Dépendances vers abstractions, pas implémentations
    - Permet substitution facile (différents processors)
    """

    @abstractmethod
    def process(self, df: DataFrame) -> DataFrame:
        """
        Traite un DataFrame

        Args:
            df: DataFrame Spark à traiter

        Returns:
            DataFrame Spark traité
        """
        pass
