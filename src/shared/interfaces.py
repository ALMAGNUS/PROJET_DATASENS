"""
Interfaces entre E1 et E2/E3 - CONTRAT IMMUABLE

RÈGLE: E2/E3 ne touchent JAMAIS directement à E1
- Utiliser UNIQUEMENT cette interface
- Lecture SEULE (pas d'écriture)
- Contrat stable (pas de breaking changes)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import date
from typing import Optional
import pandas as pd
import sqlite3


class E1DataReader(ABC):
    """
    Interface de lecture E1 - E2/E3 utilisent UNIQUEMENT cette interface
    
    RÈGLES:
    - Lecture SEULE (pas d'écriture)
    - Pas de modification de E1
    - Contrat stable (pas de breaking changes)
    """
    
    @abstractmethod
    def read_raw_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Lit données RAW depuis data/raw/
        
        Args:
            date: Date au format 'YYYY-MM-DD' (optionnel, défaut: aujourd'hui)
        
        Returns:
            DataFrame avec colonnes: source, title, content, url, published_at
        
        Raises:
            FileNotFoundError: Si données RAW n'existent pas
        """
        pass
    
    @abstractmethod
    def read_silver_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Lit données SILVER depuis data/silver/
        
        Args:
            date: Date au format 'YYYY-MM-DD' (optionnel, défaut: aujourd'hui)
        
        Returns:
            DataFrame avec colonnes: raw_data_id, title, content, quality_score, topics
        
        Raises:
            FileNotFoundError: Si données SILVER n'existent pas
        """
        pass
    
    @abstractmethod
    def read_gold_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Lit données GOLD depuis data/gold/
        
        Args:
            date: Date au format 'YYYY-MM-DD' (optionnel, défaut: aujourd'hui)
        
        Returns:
            DataFrame avec colonnes: raw_data_id, title, content, sentiment, topics, confidence
        
        Raises:
            FileNotFoundError: Si données GOLD n'existent pas
        """
        pass
    
    @abstractmethod
    def get_database_stats(self) -> dict:
        """
        Lit statistiques depuis datasens.db (lecture seule)
        
        Returns:
            Dict avec clés: total_articles, total_sources, articles_by_source, etc.
        
        Raises:
            sqlite3.Error: Si erreur DB
        """
        pass


class E1DataReaderImpl(E1DataReader):
    """Implémentation concrète de E1DataReader"""
    
    def __init__(self, base_path: Path, db_path: Path):
        """
        Args:
            base_path: Chemin vers data/ (ex: Path('data/'))
            db_path: Chemin vers datasens.db
        """
        self.base_path = base_path
        self.db_path = db_path
    
    def read_raw_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Lit RAW depuis data/raw/sources_YYYY-MM-DD/raw_articles.csv"""
        if date is None:
            date_str = date.today().isoformat()
        else:
            date_str = date
        
        csv_path = self.base_path / 'raw' / f'sources_{date_str}' / 'raw_articles.csv'
        if not csv_path.exists():
            # Fallback: lire depuis exports/raw.csv
            csv_path = self.base_path.parent / 'exports' / 'raw.csv'
            if not csv_path.exists():
                raise FileNotFoundError(f"RAW data not found for date {date_str}")
        
        return pd.read_csv(csv_path)
    
    def read_silver_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Lit SILVER depuis data/silver/v_YYYY-MM-DD/silver_articles.parquet"""
        if date is None:
            date_str = date.today().isoformat()
        else:
            date_str = date
        
        parquet_path = self.base_path / 'silver' / f'v_{date_str}' / 'silver_articles.parquet'
        if not parquet_path.exists():
            # Fallback: lire depuis exports/silver.csv
            csv_path = self.base_path.parent / 'exports' / 'silver.csv'
            if not csv_path.exists():
                raise FileNotFoundError(f"SILVER data not found for date {date_str}")
            return pd.read_csv(csv_path)
        
        return pd.read_parquet(parquet_path)
    
    def read_gold_data(self, date: Optional[str] = None) -> pd.DataFrame:
        """Lit GOLD depuis data/gold/date=YYYY-MM-DD/articles.parquet"""
        if date is None:
            date_str = date.today().isoformat()
        else:
            date_str = date
        
        parquet_path = self.base_path / 'gold' / f'date={date_str}' / 'articles.parquet'
        if not parquet_path.exists():
            # Fallback: lire depuis exports/gold.csv
            csv_path = self.base_path.parent / 'exports' / 'gold.csv'
            if not csv_path.exists():
                raise FileNotFoundError(f"GOLD data not found for date {date_str}")
            return pd.read_csv(csv_path)
        
        return pd.read_parquet(parquet_path)
    
    def get_database_stats(self) -> dict:
        """Lit stats depuis datasens.db (lecture seule)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM raw_data")
            total_articles = cursor.fetchone()[0]
            
            # Total sources
            cursor.execute("SELECT COUNT(*) FROM source WHERE active = 1")
            total_sources = cursor.fetchone()[0]
            
            # Articles par source
            cursor.execute("""
                SELECT s.name, COUNT(r.raw_data_id) as count
                FROM source s
                LEFT JOIN raw_data r ON s.source_id = r.source_id
                WHERE s.active = 1
                GROUP BY s.name
                ORDER BY count DESC
            """)
            articles_by_source = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Articles enrichis (topics + sentiment)
            cursor.execute("""
                SELECT COUNT(DISTINCT dt.raw_data_id)
                FROM document_topic dt
                JOIN model_output mo ON dt.raw_data_id = mo.raw_data_id
                WHERE mo.model_name = 'sentiment_keyword'
            """)
            enriched_articles = cursor.fetchone()[0]
            
            return {
                'total_articles': total_articles,
                'total_sources': total_sources,
                'articles_by_source': articles_by_source,
                'enriched_articles': enriched_articles,
            }
        finally:
            conn.close()
