"""
Permissions Dependencies - FastAPI Dependency Injection
========================================================
Dépendances pour vérifier les permissions par rôle
"""


from fastapi import Depends, HTTPException, status

from src.e2.api.dependencies.auth import get_current_active_user
from src.e2.api.schemas.user import UserInDB


def require_role(allowed_roles: list[str]):
    """
    Factory pour créer une dépendance de permission par rôle

    Args:
        allowed_roles: Liste des rôles autorisés

    Returns:
        Dépendance FastAPI
    """

    async def role_checker(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        """
        Vérifie que l'utilisateur a un des rôles autorisés

        Args:
            current_user: Utilisateur actif

        Returns:
            UserInDB

        Raises:
            HTTPException 403: Si rôle non autorisé
        """
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


# Permissions par zone (selon roadmap)
require_reader = require_role(["reader", "writer", "deleter", "admin"])
require_writer = require_role(["writer", "admin"])
require_deleter = require_role(["deleter", "admin"])
require_admin = require_role(["admin"])
