"""
E2 API Routes - Endpoints
==========================
Routers FastAPI par zone (RAW, SILVER, GOLD) et auth
"""

from .ai import router as ai_router
from .analytics import router as analytics_router
from .auth import router as auth_router
from .gold import router as gold_router
from .raw import router as raw_router
from .silver import router as silver_router
from .sources import router as sources_router

__all__ = [
    "analytics_router",
    "auth_router",
    "gold_router",
    "raw_router",
    "silver_router",
    "sources_router",
    "ai_router",
]
