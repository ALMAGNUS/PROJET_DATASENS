"""
Article Schemas - Pydantic Models
==================================
Modèles pour articles (RAW/SILVER/GOLD)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleBase(BaseModel):
    """Base article schema"""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    url: str | None = Field(None, max_length=500)
    published_at: datetime | None = None


class ArticleCreate(ArticleBase):
    """Schema pour création article (SILVER uniquement)"""

    source_id: int | None = None
    quality_score: float | None = Field(None, ge=0.0, le=1.0)


class ArticleUpdate(BaseModel):
    """Schema pour mise à jour article (SILVER uniquement)"""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1)
    url: str | None = Field(None, max_length=500)
    quality_score: float | None = Field(None, ge=0.0, le=1.0)


class ArticleResponse(ArticleBase):
    """Schema pour réponse API"""

    raw_data_id: int
    source_id: int
    source_name: str | None = None
    quality_score: float | None = None
    collected_at: datetime | None = None
    sentiment: str | None = None
    topics: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Schema pour liste paginée d'articles"""

    items: list[ArticleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
