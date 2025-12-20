"""
Analytics Routes - E2 API
==========================
Endpoints pour analyses Big Data avec PySpark
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.e2.api.dependencies.permissions import require_reader
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
    current_user=Depends(require_reader)
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
            results.append({
                "sentiment": row["sentiment"],
                "count": row["count"],
                "percentage": round(row["percentage"], 2)
            })

        return results
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Parquet GOLD not found: {e!s}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing sentiment distribution: {e!s}"
        )


@router.get("/source/aggregation", response_model=list[SourceAggregationResponse])
async def get_source_aggregation(
    target_date: date | None = Query(None, description="Date spécifique (optionnel)"),
    current_user=Depends(require_reader)
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
            results.append({
                "source": row["source"],
                "count": row["count"],
                "avg_sentiment_score": round(row["avg_sentiment_score"], 3) if row["avg_sentiment_score"] else None
            })

        return results
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Parquet GOLD not found: {e!s}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing source aggregation: {e!s}"
        )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    target_date: date | None = Query(None, description="Date spécifique (optionnel)"),
    current_user=Depends(require_reader)
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
        raise HTTPException(
            status_code=404,
            detail=f"Parquet GOLD not found: {e!s}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing statistics: {e!s}"
        )


@router.get("/available-dates")
async def get_available_dates(
    current_user=Depends(require_reader)
):
    """
    Liste des dates disponibles dans les partitions Parquet

    Returns:
        Liste de dates disponibles
    """
    try:
        reader = GoldParquetReader()
        dates = reader.get_available_dates()

        return {
            "available_dates": [d.isoformat() for d in dates],
            "count": len(dates)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting available dates: {e!s}"
        )
