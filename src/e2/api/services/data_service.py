"""
Data Service - Business Logic for Data Access
==============================================
Service pour lire RAW/SILVER/GOLD via E1DataReader (isolation respectée)
SRP: Responsabilité unique = accès aux données E1
"""

from typing import Optional, List
from pathlib import Path
from datetime import date
import pandas as pd
from src.config import get_data_dir
from src.shared.interfaces import E1DataReader, E1DataReaderImpl
from src.e2.api.schemas.article import ArticleResponse


class DataService:
    """
    Service pour accéder aux données E1 (lecture seule)
    SRP: Responsabilité unique = accès données
    DIP: Dépend de l'interface E1DataReader (abstraction)
    """
    
    def __init__(self, data_reader: Optional[E1DataReader] = None):
        """
        Args:
            data_reader: Instance E1DataReader (injection de dépendance)
        """
        if data_reader is None:
            base_path = get_data_dir()
            db_path = base_path.parent / "data" / "datasens.db"
            self.data_reader = E1DataReaderImpl(base_path, db_path)
        else:
            self.data_reader = data_reader
    
    def get_raw_articles(
        self, 
        date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ArticleResponse]:
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
        if limit:
            df = df.iloc[offset:offset + limit]
        else:
            df = df.iloc[offset:]
        
        # Convertir en ArticleResponse
        articles = []
        for _, row in df.iterrows():
            articles.append(ArticleResponse(
                raw_data_id=row.get("raw_data_id", 0),
                source_id=row.get("source_id", 0),
                source_name=row.get("source_name"),
                title=row.get("title", ""),
                content=row.get("content", ""),
                url=row.get("url"),
                published_at=row.get("published_at"),
                collected_at=row.get("collected_at"),
                quality_score=row.get("quality_score"),
                sentiment=None,  # RAW n'a pas de sentiment
                topics=None  # RAW n'a pas de topics
            ))
        
        return articles
    
    def get_silver_articles(
        self,
        date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ArticleResponse]:
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
        if limit:
            df = df.iloc[offset:offset + limit]
        else:
            df = df.iloc[offset:]
        
        # Convertir en ArticleResponse
        articles = []
        for _, row in df.iterrows():
            articles.append(ArticleResponse(
                raw_data_id=row.get("raw_data_id", 0),
                source_id=row.get("source_id", 0),
                source_name=row.get("source_name"),
                title=row.get("title", ""),
                content=row.get("content", ""),
                url=row.get("url"),
                published_at=row.get("published_at"),
                collected_at=row.get("collected_at"),
                quality_score=row.get("quality_score"),
                sentiment=None,  # SILVER peut avoir sentiment mais pas garanti
                topics=None  # SILVER peut avoir topics mais pas garanti
            ))
        
        return articles
    
    def get_gold_articles(
        self,
        date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ArticleResponse]:
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
        if limit:
            df = df.iloc[offset:offset + limit]
        else:
            df = df.iloc[offset:]
        
        # Convertir en ArticleResponse
        articles = []
        for _, row in df.iterrows():
            # Extraire topics (peut être une liste ou string)
            topics = row.get("topics")
            if isinstance(topics, str):
                topics = [t.strip() for t in topics.split(",") if t.strip()]
            elif isinstance(topics, list):
                topics = topics
            
            articles.append(ArticleResponse(
                raw_data_id=row.get("raw_data_id", 0),
                source_id=row.get("source_id", 0),
                source_name=row.get("source_name"),
                title=row.get("title", ""),
                content=row.get("content", ""),
                url=row.get("url"),
                published_at=row.get("published_at"),
                collected_at=row.get("collected_at"),
                quality_score=row.get("quality_score"),
                sentiment=row.get("sentiment"),
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
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    """Get data service singleton"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
