"""
E2 API Routes - Endpoints
==========================
Routers FastAPI par zone (RAW, SILVER, GOLD) et auth
"""

from .analytics import router as analytics_router
from .auth import router as auth_router
from .gold import router as gold_router
from .raw import router as raw_router
from .silver import router as silver_router

__all__ = [
    "analytics_router",
    "auth_router",
    "gold_router",
    "raw_router",
    "silver_router",
]
