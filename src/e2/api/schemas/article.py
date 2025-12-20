"""
Article Schemas - Pydantic Models
==================================
Modèles pour articles (RAW/SILVER/GOLD)
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ArticleBase(BaseModel):
    """Base article schema"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    url: Optional[str] = Field(None, max_length=500)
    published_at: Optional[datetime] = None


class ArticleCreate(ArticleBase):
    """Schema pour création article (SILVER uniquement)"""
    source_id: Optional[int] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class ArticleUpdate(BaseModel):
    """Schema pour mise à jour article (SILVER uniquement)"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    url: Optional[str] = Field(None, max_length=500)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class ArticleResponse(ArticleBase):
    """Schema pour réponse API"""
    raw_data_id: int
    source_id: int
    source_name: Optional[str] = None
    quality_score: Optional[float] = None
    collected_at: Optional[datetime] = None
    sentiment: Optional[str] = None
    topics: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Schema pour liste paginée d'articles"""
    items: List[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
