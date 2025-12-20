"""
E2 API Schemas - Pydantic Models
=================================
Modèles de données pour validation et sérialisation
"""

from .article import ArticleBase, ArticleCreate, ArticleListResponse, ArticleResponse, ArticleUpdate
from .auth import LoginRequest, LoginResponse
from .token import Token, TokenData
from .user import UserBase, UserCreate, UserInDB, UserResponse, UserUpdate

__all__ = [
    # Article
    "ArticleBase",
    "ArticleCreate",
    "ArticleListResponse",
    "ArticleResponse",
    "ArticleUpdate",
    # Auth
    "LoginRequest",
    "LoginResponse",
    # Token
    "Token",
    "TokenData",
    # User
    "UserBase",
    "UserCreate",
    "UserInDB",
    "UserResponse",
    "UserUpdate",
]
