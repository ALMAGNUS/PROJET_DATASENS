"""
Auth Schemas - Pydantic Models
===============================
Modèles pour authentification
"""

from pydantic import BaseModel, Field

from src.e2.api.schemas.common import DemoSafeEmail


class LoginRequest(BaseModel):
    """Schema pour login"""

    email: DemoSafeEmail = Field(..., min_length=3, max_length=254)
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
