"""
Source Schemas - Pydantic models
=================================
Schémas pour CRUD Source (E2 API)
"""

from pydantic import BaseModel


class SourceBase(BaseModel):
    name: str
    source_type: str
    url: str | None = None
    sync_frequency: str | None = None
    is_active: bool = True
    is_synthetic: bool = False


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceBase):
    pass


class SourceResponse(SourceBase):
    source_id: int
