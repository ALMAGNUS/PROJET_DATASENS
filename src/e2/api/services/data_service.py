"""
Data Service - Business Logic for Data Access
==============================================
Service pour lire RAW/SILVER/GOLD via E1DataReader (isolation respectée)
SRP: Responsabilité unique = accès aux données E1
"""

from datetime import date as date_type
from datetime import datetime
from pathlib import Path

import pandas as pd
from dateutil import parser as date_parser

from src.config import get_data_dir
from src.e2.api.schemas.article import ArticleResponse
from src.shared.interfaces import E1DataReader, E1DataReaderImpl


class DataService:
    """
    Service pour accéder aux données E1 (lecture seule)
    SRP: Responsabilité unique = accès données
    DIP: Dépend de l'interface E1DataReader (abstraction)
    """

    def __init__(self, data_reader: E1DataReader | None = None):
        """
        Args:
            data_reader: Instance E1DataReader (injection de dépendance)
        """
        if data_reader is None:
            base_path = get_data_dir()
            # Utiliser le même chemin que E1 (home/datasens_project/datasens.db)
            import os
            db_path_str = os.getenv('DB_PATH', str(Path.home() / 'datasens_project' / 'datasens.db'))
            db_path = Path(db_path_str)
            self.data_reader = E1DataReaderImpl(base_path, db_path)
        else:
            self.data_reader = data_reader

    def get_raw_articles(
        self,
        date: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[ArticleResponse]:
        """
        Récupère les articles RAW

        Args:
            date: Date au format YYYY-MM-DD (optionnel)
            limit: Nombre max d'articles (optionnel)
            offset: Offset pour pagination

        Returns:
            Liste d'ArticleResponse
        """
        df = self.data_reader.read_raw_data(date)

        # Pagination
        df = df.iloc[offset:offset + limit] if limit else df.iloc[offset:]

        # Convertir en ArticleResponse
        articles = []
        for _, row in df.iterrows():
            # Parser les dates si elles sont en string (gérer NaN)
            published_at_val = row.get("published_at")
            published_at = None
            if pd.notna(published_at_val):
                if isinstance(published_at_val, str):
                    try:
                        published_at = date_parser.parse(published_at_val)
                    except (ValueError, TypeError):
                        published_at = None
                elif isinstance(published_at_val, datetime | date_type):
                    published_at = published_at_val

            collected_at_val = row.get("collected_at")
            collected_at = None
            if pd.notna(collected_at_val):
                if isinstance(collected_at_val, str):
                    try:
                        collected_at = date_parser.parse(collected_at_val)
                    except (ValueError, TypeError):
                        collected_at = None
                elif isinstance(collected_at_val, datetime | date_type):
                    collected_at = collected_at_val

            articles.append(ArticleResponse(
                raw_data_id=int(row.get("raw_data_id", 0)) if pd.notna(row.get("raw_data_id")) else 0,
                source_id=int(row.get("source_id", 0)) if pd.notna(row.get("source_id")) else 0,
                source_name=row.get("source_name") if pd.notna(row.get("source_name")) else None,
                title=str(row.get("title", "")) if pd.notna(row.get("title")) else "",
                content=str(row.get("content", "")) if pd.notna(row.get("content")) else "",
                url=row.get("url") if pd.notna(row.get("url")) else None,
                published_at=published_at,
                collected_at=collected_at,
                quality_score=float(row.get("quality_score")) if pd.notna(row.get("quality_score")) else None,
                sentiment=None,  # RAW n'a pas de sentiment
                topics=None  # RAW n'a pas de topics
            ))

        return articles

    def get_silver_articles(
        self,
        date: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[ArticleResponse]:
        """
        Récupère les articles SILVER

        Args:
            date: Date au format YYYY-MM-DD (optionnel)
            limit: Nombre max d'articles (optionnel)
            offset: Offset pour pagination

        Returns:
            Liste d'ArticleResponse
        """
        df = self.data_reader.read_silver_data(date)

        # Pagination
        df = df.iloc[offset:offset + limit] if limit else df.iloc[offset:]

        # Convertir en ArticleResponse
        articles = []
        for _, row in df.iterrows():
            # Parser les dates si elles sont en string (gérer NaN)
            published_at = row.get("published_at")
            if pd.notna(published_at) and isinstance(published_at, str):
                try:
                    published_at = date_parser.parse(published_at)
                except (ValueError, TypeError):
                    published_at = None
            elif pd.isna(published_at):
                published_at = None

            collected_at = row.get("collected_at")
            if pd.notna(collected_at) and isinstance(collected_at, str):
                try:
                    collected_at = date_parser.parse(collected_at)
                except (ValueError, TypeError):
                    collected_at = None
            elif pd.isna(collected_at):
                collected_at = None

            articles.append(ArticleResponse(
                raw_data_id=int(row.get("raw_data_id", 0)) if pd.notna(row.get("raw_data_id")) else 0,
                source_id=int(row.get("source_id", 0)) if pd.notna(row.get("source_id")) else 0,
                source_name=row.get("source_name"),
                title=str(row.get("title", "")) if pd.notna(row.get("title")) else "",
                content=str(row.get("content", "")) if pd.notna(row.get("content")) else "",
                url=row.get("url") if pd.notna(row.get("url")) else None,
                published_at=published_at,
                collected_at=collected_at,
                quality_score=float(row.get("quality_score")) if pd.notna(row.get("quality_score")) else None,
                sentiment=None,  # SILVER peut avoir sentiment mais pas garanti
                topics=None  # SILVER peut avoir topics mais pas garanti
            ))

        return articles

    def get_gold_articles(
        self,
        date: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[ArticleResponse]:
        """
        Récupère les articles GOLD (enrichis)

        Args:
            date: Date au format YYYY-MM-DD (optionnel)
            limit: Nombre max d'articles (optionnel)
            offset: Offset pour pagination

        Returns:
            Liste d'ArticleResponse avec sentiment et topics
        """
        df = self.data_reader.read_gold_data(date)

        # Pagination
        df = df.iloc[offset:offset + limit] if limit else df.iloc[offset:]

        # Convertir en ArticleResponse
        articles = []
        for _, row in df.iterrows():
            # Parser les dates si elles sont en string (gérer NaN)
            published_at_val = row.get("published_at")
            published_at = None
            if pd.notna(published_at_val):
                if isinstance(published_at_val, str):
                    try:
                        published_at = date_parser.parse(published_at_val)
                    except (ValueError, TypeError):
                        published_at = None
                elif isinstance(published_at_val, datetime | date_type):
                    published_at = published_at_val

            collected_at_val = row.get("collected_at")
            collected_at = None
            if pd.notna(collected_at_val):
                if isinstance(collected_at_val, str):
                    try:
                        collected_at = date_parser.parse(collected_at_val)
                    except (ValueError, TypeError):
                        collected_at = None
                elif isinstance(collected_at_val, datetime | date_type):
                    collected_at = collected_at_val

            # Extraire topics (peut être une liste ou string)
            topics = row.get("topics")
            if pd.notna(topics):
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(",") if t.strip()]
                elif isinstance(topics, list):
                    topics = topics
                else:
                    topics = None
            else:
                topics = None

            articles.append(ArticleResponse(
                raw_data_id=int(row.get("raw_data_id", 0)) if pd.notna(row.get("raw_data_id")) else 0,
                source_id=int(row.get("source_id", 0)) if pd.notna(row.get("source_id")) else 0,
                source_name=row.get("source_name") if pd.notna(row.get("source_name")) else None,
                title=str(row.get("title", "")) if pd.notna(row.get("title")) else "",
                content=str(row.get("content", "")) if pd.notna(row.get("content")) else "",
                url=row.get("url") if pd.notna(row.get("url")) else None,
                published_at=published_at,
                collected_at=collected_at,
                quality_score=float(row.get("quality_score")) if pd.notna(row.get("quality_score")) else None,
                sentiment=row.get("sentiment") if pd.notna(row.get("sentiment")) else None,
                topics=topics
            ))

        return articles

    def get_database_stats(self) -> dict:
        """
        Récupère les statistiques de la base de données

        Returns:
            Dict avec statistiques
        """
        return self.data_reader.get_database_stats()


# Singleton instance
_data_service: DataService | None = None


def get_data_service() -> DataService:
    """Get data service singleton"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
