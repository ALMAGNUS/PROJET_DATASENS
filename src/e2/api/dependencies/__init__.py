"""
E2 API Dependencies - Dependency Injection
===========================================
Dépendances FastAPI pour auth, permissions, etc.
"""

from .auth import get_current_user, get_current_active_user
from .permissions import require_reader, require_writer, require_deleter, require_admin

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_reader",
    "require_writer",
    "require_deleter",
    "require_admin",
]
