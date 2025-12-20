"""
E2 API Dependencies - Dependency Injection
===========================================
Dépendances FastAPI pour auth, permissions, etc.
"""

from .auth import get_current_active_user, get_current_user
from .permissions import require_admin, require_deleter, require_reader, require_writer

__all__ = [
    "get_current_active_user",
    "get_current_user",
    "require_admin",
    "require_deleter",
    "require_reader",
    "require_writer",
]
