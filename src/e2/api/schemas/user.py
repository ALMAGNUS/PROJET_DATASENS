"""
User Schemas - Pydantic Models
===============================
Modèles de validation pour utilisateurs (PROFILS table)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    role: str = Field(..., pattern="^(reader|writer|deleter|admin)$")


class UserCreate(UserBase):
    """Schema pour création utilisateur"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema pour mise à jour utilisateur (tous champs optionnels)"""
    email: Optional[EmailStr] = None
    firstname: Optional[str] = Field(None, min_length=1, max_length=100)
    lastname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, pattern="^(reader|writer|deleter|admin)$")
    active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema pour réponse API (sans password)"""
    profil_id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User avec password_hash (usage interne uniquement)"""
    password_hash: str
