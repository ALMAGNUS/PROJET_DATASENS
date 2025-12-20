"""
E2 API Schemas - Pydantic Models
=================================
Modèles de données pour validation et sérialisation
"""

from .user import UserBase, UserCreate, UserUpdate, UserResponse, UserInDB
from .token import Token, TokenData
from .article import ArticleBase, ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse
from .auth import LoginRequest, LoginResponse

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    # Token
    "Token",
    "TokenData",
    # Article
    "ArticleBase",
    "ArticleCreate",
    "ArticleUpdate",
    "ArticleResponse",
    "ArticleListResponse",
    # Auth
    "LoginRequest",
    "LoginResponse",
]
