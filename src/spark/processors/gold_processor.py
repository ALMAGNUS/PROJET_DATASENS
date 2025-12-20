"""
GoldDataProcessor - PySpark E2
===============================
Processeur pour données GOLD (agrégations, analyses)
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import avg, col, count
from pyspark.sql.functions import max as spark_max
from pyspark.sql.functions import min as spark_min

from ..interfaces.data_processor import DataProcessor


class GoldDataProcessor(DataProcessor):
    """
    Processeur pour données GOLD

    Principe: SRP (Single Responsibility Principle)
    - Responsabilité unique = traitement données GOLD
    - Agrégations, analyses, transformations

    Architecture:
    - DIP: Implémente DataProcessor (abstraction)
    - OCP: Extensible sans modification (nouvelles méthodes)
    """

    def process(self, df: DataFrame) -> DataFrame:
        """
        Traite un DataFrame GOLD (par défaut: pas de transformation)

        Args:
            df: DataFrame Spark GOLD

        Returns:
            DataFrame Spark traité
        """
        # Par défaut, retourner tel quel
        # Les méthodes spécialisées font les transformations
        return df

    def aggregate_by_sentiment(self, df: DataFrame) -> DataFrame:
        """
        Agrège par sentiment

        Args:
            df: DataFrame GOLD

        Returns:
            DataFrame avec colonnes: sentiment, count

        Example:
            >>> processor = GoldDataProcessor()
            >>> df_agg = processor.aggregate_by_sentiment(df_gold)
            >>> df_agg.show()
            +---------+-----+
            |sentiment|count|
            +---------+-----+
            |positif  |  123|
            |negatif  |   45|
            |neutre   |  234|
            +---------+-----+
        """
        return df.groupBy("sentiment").agg(
            count("*").alias("count")
        ).orderBy(col("count").desc())

    def aggregate_by_source(self, df: DataFrame) -> DataFrame:
        """
        Agrège par source

        Args:
            df: DataFrame GOLD

        Returns:
            DataFrame avec colonnes: source, count, avg_sentiment_score
        """
        return df.groupBy("source").agg(
            count("*").alias("count"),
            avg("sentiment_score").alias("avg_sentiment_score")
        ).orderBy(col("count").desc())

    def aggregate_by_topic(self, df: DataFrame) -> DataFrame:
        """
        Agrège par topic

        Args:
            df: DataFrame GOLD (doit avoir colonne topics ou topic)

        Returns:
            DataFrame avec colonnes: topic, count
        """
        # Si colonne topics existe (liste), exploser
        if "topics" in df.columns:
            from pyspark.sql.functions import explode
            df_exploded = df.select(
                explode(col("topics")).alias("topic"),
                col("raw_data_id")
            )
            return df_exploded.groupBy("topic").agg(
                count("*").alias("count")
            ).orderBy(col("count").desc())
        elif "topic" in df.columns:
            return df.groupBy("topic").agg(
                count("*").alias("count")
            ).orderBy(col("count").desc())
        else:
            # Pas de colonne topic, retourner vide
            return df.limit(0)

    def get_sentiment_distribution(self, df: DataFrame) -> DataFrame:
        """
        Distribution des sentiments avec pourcentages

        Args:
            df: DataFrame GOLD

        Returns:
            DataFrame avec colonnes: sentiment, count, percentage
        """
        total = df.count()

        if total == 0:
            return df.limit(0)

        return df.groupBy("sentiment").agg(
            count("*").alias("count")
        ).withColumn(
            "percentage",
            (col("count") / total * 100).cast("double")
        ).orderBy(col("count").desc())

    def get_daily_sentiment_trend(
        self,
        df: DataFrame,
        date_column: str = "published_at"
    ) -> DataFrame:
        """
        Tendance sentiment par jour

        Args:
            df: DataFrame GOLD
            date_column: Nom de la colonne date

        Returns:
            DataFrame avec colonnes: date, sentiment, count
        """
        from pyspark.sql.functions import date_format, to_date

        if date_column not in df.columns:
            return df.limit(0)

        return df.select(
            date_format(to_date(col(date_column)), "yyyy-MM-dd").alias("date"),
            col("sentiment")
        ).groupBy("date", "sentiment").agg(
            count("*").alias("count")
        ).orderBy("date", "sentiment")

    def filter_by_sentiment(
        self,
        df: DataFrame,
        sentiment: str
    ) -> DataFrame:
        """
        Filtre par sentiment

        Args:
            df: DataFrame GOLD
            sentiment: Sentiment à filtrer (positif, negatif, neutre)

        Returns:
            DataFrame filtré
        """
        return df.filter(col("sentiment") == sentiment)

    def filter_by_source(
        self,
        df: DataFrame,
        source: str
    ) -> DataFrame:
        """
        Filtre par source

        Args:
            df: DataFrame GOLD
            source: Nom de la source

        Returns:
            DataFrame filtré
        """
        return df.filter(col("source") == source)

    def get_top_articles(
        self,
        df: DataFrame,
        limit: int = 10,
        order_by: str = "sentiment_score"
    ) -> DataFrame:
        """
        Top articles par score

        Args:
            df: DataFrame GOLD
            limit: Nombre d'articles à retourner
            order_by: Colonne pour trier (défaut: sentiment_score)

        Returns:
            DataFrame avec top articles
        """
        if order_by not in df.columns:
            order_by = "raw_data_id"  # Fallback

        return df.orderBy(col(order_by).desc()).limit(limit)

    def get_statistics(self, df: DataFrame) -> dict:
        """
        Statistiques générales sur le DataFrame

        Args:
            df: DataFrame GOLD

        Returns:
            Dictionnaire avec statistiques
        """
        stats = {
            "total_articles": df.count(),
            "total_sources": df.select("source").distinct().count() if "source" in df.columns else 0,
        }

        # Statistiques sentiment si colonne existe
        if "sentiment" in df.columns:
            sentiment_counts = df.groupBy("sentiment").agg(
                count("*").alias("count")
            ).collect()
            stats["sentiment_distribution"] = {
                row["sentiment"]: row["count"]
                for row in sentiment_counts
            }

        # Statistiques score si colonne existe
        if "sentiment_score" in df.columns:
            score_stats = df.agg(
                avg("sentiment_score").alias("avg_score"),
                spark_max("sentiment_score").alias("max_score"),
                spark_min("sentiment_score").alias("min_score")
            ).collect()[0]
            stats["sentiment_score"] = {
                "avg": score_stats["avg_score"],
                "max": score_stats["max_score"],
                "min": score_stats["min_score"]
            }

        return stats
