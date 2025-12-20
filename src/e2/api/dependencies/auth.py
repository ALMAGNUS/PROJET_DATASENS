"""
Auth Dependencies - FastAPI Dependency Injection
================================================
Dépendances pour authentification et autorisation
DIP: Dépend de l'abstraction (UserService, SecurityService)
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.e2.api.schemas.user import UserInDB
from src.e2.api.services.user_service import get_user_service
from src.e2.auth.security import get_security_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    Dépendance FastAPI: Récupère l'utilisateur depuis le token JWT
    
    Args:
        credentials: Credentials HTTP (Bearer token)
    
    Returns:
        UserInDB
    
    Raises:
        HTTPException 401: Si token invalide ou utilisateur non trouvé
    """
    token = credentials.credentials
    security_service = get_security_service()
    user_service = get_user_service()
    
    # Décoder le token
    payload = security_service.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer profil_id depuis le payload
    profil_id: Optional[int] = payload.get("sub")
    if profil_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur
    user = user_service.get_user_by_id(profil_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Dépendance FastAPI: Récupère un utilisateur actif
    
    Args:
        current_user: Utilisateur depuis get_current_user
    
    Returns:
        UserInDB (actif)
    
    Raises:
        HTTPException 403: Si utilisateur inactif
    """
    if not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
