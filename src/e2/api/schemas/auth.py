"""
Auth Schemas - Pydantic Models
===============================
Modèles pour authentification
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema pour login"""

    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Schema pour réponse login"""

    access_token: str
    token_type: str = "bearer"
    profil_id: int
    email: str
    role: str
    firstname: str
    lastname: str
