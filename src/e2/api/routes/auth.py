"""
Auth Routes - Authentication Endpoints
=======================================
Endpoints pour authentification (login)
"""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, status

from src.config import get_settings
from src.e2.api.middleware.audit import log_login
from src.e2.api.middleware.prometheus import record_auth_failure, record_auth_success
from src.e2.api.schemas.auth import LoginRequest, LoginResponse
from src.e2.api.schemas.token import TokenData
from src.e2.api.services.user_service import get_user_service
from src.e2.auth.security import get_security_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
security_service = get_security_service()
user_service = get_user_service()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(login_data: LoginRequest, request: Request):
    """
    Endpoint de login

    Authentifie un utilisateur et retourne un token JWT

    Args:
        login_data: Email et password

    Returns:
        LoginResponse avec token JWT et infos utilisateur

    Raises:
        HTTPException 401: Si credentials invalides
    """
    # Authentifier l'utilisateur
    user = user_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        record_auth_failure()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enregistrer succès authentification
    record_auth_success()

    # Créer le token JWT
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token_data = TokenData(profil_id=user.profil_id, email=user.email, role=user.role)
    access_token = security_service.create_access_token(
        data={"sub": str(token_data.profil_id), "email": token_data.email, "role": token_data.role},
        expires_delta=access_token_expires,
    )

    # Mettre à jour last_login
    user_service.update_last_login(user.profil_id)

    # Audit : enregistrer la connexion dans user_action_log
    ip_address = request.client.host if request.client else None
    log_login(user.profil_id, ip_address)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        profil_id=user.profil_id,
        email=user.email,
        role=user.role,
        firstname=user.firstname,
        lastname=user.lastname,
    )
