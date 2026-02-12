"""
Analytics Routes - E2 API
==========================
Endpoints pour analyses Big Data avec PySpark
"""

import math
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.e2.api.dependencies.permissions import require_reader
from src.e2.api.middleware.prometheus import (
    drift_articles_total,
    drift_score,
    drift_sentiment_entropy,
    drift_topic_dominance,
)
from src.spark.adapters import GoldParquetReader
from src.spark.processors import GoldDataProcessor

router = APIRouter(prefix="/analytics", tags=["analytics"])


class SentimentDistributionResponse(BaseModel):
    """Réponse distribution sentiment"""

    sentiment: str
    count: int
    percentage: float


class SourceAggregationResponse(BaseModel):
    """Réponse agrégation par source"""

    source: str
    count: int
    avg_sentiment_score: float | None = None


class StatisticsResponse(BaseModel):
    """Réponse statistiques générales"""

    total_articles: int
    total_sources: int
    sentiment_distribution: dict[str, int] | None = None
    sentiment_score: dict[str, float] | None = None


@router.get("/sentiment/distribution", response_model=list[SentimentDistributionResponse])
async def get_sentiment_distribution(
    target_date: date | None = Query(None, description="Date spécifique (optionnel)"),
    current_user=Depends(require_reader),
):
    """
    Distribution des sentiments

    Returns:
        Liste de distributions sentiment avec pourcentages
    """
    try:
        reader = GoldParquetReader()
        processor = GoldDataProcessor()

        # Lire données
        df = reader.read_gold(date=target_date) if target_date else reader.read_gold()

        # Calculer distribution
        df_dist = processor.get_sentiment_distribution(df)

        # Convertir en liste de dicts
        results = []
        for row in df_dist.collect():
            results.append(
                {
                    "sentiment": row["sentiment"],
                    "count": row["count"],
                    "percentage": round(row["percentage"], 2),
                }
            )

        return results
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Parquet GOLD not found: {e!s}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing sentiment distribution: {e!s}"
        )


@router.get("/source/aggregation", response_model=list[SourceAggregationResponse])
async def get_source_aggregation(
    target_date: date | None = Query(None, description="Date spécifique (optionnel)"),
    current_user=Depends(require_reader),
):
    """
    Agrégation par source

    Returns:
        Liste d'agrégations par source
    """
    try:
        reader = GoldParquetReader()
        processor = GoldDataProcessor()

        # Lire données
        df = reader.read_gold(date=target_date) if target_date else reader.read_gold()

        # Calculer agrégation
        df_agg = processor.aggregate_by_source(df)

        # Convertir en liste de dicts
        results = []
        for row in df_agg.collect():
            results.append(
                {
                    "source": row["source"],
                    "count": row["count"],
                    "avg_sentiment_score": round(row["avg_sentiment_score"], 3)
                    if row["avg_sentiment_score"]
                    else None,
                }
            )

        return results
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Parquet GOLD not found: {e!s}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing source aggregation: {e!s}")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    target_date: date | None = Query(None, description="Date spécifique (optionnel)"),
    current_user=Depends(require_reader),
):
    """
    Statistiques générales

    Returns:
        Statistiques complètes (total articles, sources, sentiment, etc.)
    """
    try:
        reader = GoldParquetReader()
        processor = GoldDataProcessor()

        # Lire données
        df = reader.read_gold(date=target_date) if target_date else reader.read_gold()

        # Calculer statistiques
        stats = processor.get_statistics(df)

        return StatisticsResponse(**stats)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Parquet GOLD not found: {e!s}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing statistics: {e!s}")


@router.get("/available-dates")
async def get_available_dates(current_user=Depends(require_reader)):
    """
    Liste des dates disponibles dans les partitions Parquet

    Returns:
        Liste de dates disponibles
    """
    try:
        reader = GoldParquetReader()
        dates = reader.get_available_dates()

        return {"available_dates": [d.isoformat() for d in dates], "count": len(dates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available dates: {e!s}")


class DriftMetricsResponse(BaseModel):
    """Métriques de drift pour Prometheus / Grafana"""

    sentiment_entropy: float
    topic_dominance: float
    drift_score: float
    articles_total: int


@router.get("/drift-metrics", response_model=DriftMetricsResponse)
async def get_drift_metrics(
    target_date: date | None = Query(None, description="Date (optionnel)"),
    current_user=Depends(require_reader),
):
    """
    Calcule les métriques de drift (distribution sentiment + topics) et met à jour
    les gauges Prometheus. À appeler régulièrement (cron ou cockpit) pour que
    Grafana affiche les courbes de drift dans le temps.
    """
    try:
        reader = GoldParquetReader()
        processor = GoldDataProcessor()
        df = reader.read_gold(date=target_date) if target_date else reader.read_gold()
        total = df.count()
        if total == 0:
            drift_sentiment_entropy.set(0)
            drift_topic_dominance.set(0)
            drift_score.set(0)
            drift_articles_total.set(0)
            return DriftMetricsResponse(
                sentiment_entropy=0.0, topic_dominance=0.0, drift_score=0.0, articles_total=0
            )

        stats = processor.get_statistics(df)
        sentiment_dist = stats.get("sentiment_distribution") or {}
        # Entropy: -sum(p * log2(p)), max = log2(n)
        probs = [c / total for c in sentiment_dist.values() if c > 0]
        entropy = 0.0
        if probs:
            n_classes = len(probs)
            for p in probs:
                if p > 0:
                    entropy -= p * math.log2(p)
            entropy_max = math.log2(max(n_classes, 1))
            entropy_norm = entropy / entropy_max if entropy_max > 0 else 0
        else:
            entropy_norm = 0

        # Topic dominance: fraction du topic le plus fréquent
        topic_col = None
        for col_name in ("topic_1", "topic", "topics"):
            if col_name in df.columns:
                topic_col = col_name
                break
        dominance = 0.0
        if topic_col == "topic_1" or topic_col == "topic":
            from pyspark.sql.functions import count

            topic_counts = df.groupBy(topic_col).agg(count("*").alias("c")).collect()
            if topic_counts:
                max_count = max(row["c"] for row in topic_counts)
                dominance = max_count / total

        # Score composite drift 0-1 (plus haut = plus de déséquilibre / drift)
        drift_val = (1 - entropy_norm) * 0.5 + dominance * 0.5

        drift_sentiment_entropy.set(round(entropy, 4))
        drift_topic_dominance.set(round(dominance, 4))
        drift_score.set(round(drift_val, 4))
        drift_articles_total.set(total)

        return DriftMetricsResponse(
            sentiment_entropy=round(entropy, 4),
            topic_dominance=round(dominance, 4),
            drift_score=round(drift_val, 4),
            articles_total=total,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Parquet GOLD not found: {e!s}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing drift: {e!s}")
