"""
User Schemas - Pydantic Models
===============================
Modèles de validation pour utilisateurs (PROFILS table)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    username: str | None = Field(None, max_length=50)
    role: str = Field(..., pattern="^(reader|writer|deleter|admin)$")


class UserCreate(UserBase):
    """Schema pour création utilisateur"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema pour mise à jour utilisateur (tous champs optionnels)"""
    email: EmailStr | None = None
    firstname: str | None = Field(None, min_length=1, max_length=100)
    lastname: str | None = Field(None, min_length=1, max_length=100)
    username: str | None = Field(None, max_length=50)
    role: str | None = Field(None, pattern="^(reader|writer|deleter|admin)$")
    active: bool | None = None


class UserResponse(UserBase):
    """Schema pour réponse API (sans password)"""
    profil_id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User avec password_hash (usage interne uniquement)"""
    password_hash: str
