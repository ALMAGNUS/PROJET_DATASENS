"""
Token Schemas - Pydantic Models
================================
Modèles pour JWT tokens
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Token JWT response"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Données dans le token JWT"""

    profil_id: int
    email: str
    role: str
