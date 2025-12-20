"""
E2 API Middleware
=================
Middlewares pour l'application FastAPI
"""

from .audit import AuditMiddleware

__all__ = ["AuditMiddleware"]
