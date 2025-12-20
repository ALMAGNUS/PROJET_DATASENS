"""
Security Module - JWT & Password Hashing
==========================================
Service pour JWT tokens et hashage de mots de passe (SRP)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from src.config import get_settings

settings = get_settings()


class SecurityService:
    """
    Service de sécurité (JWT + Password)
    SRP: Responsabilité unique = sécurité
    """
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Vérifie un mot de passe en clair contre un hash
        
        Args:
            plain_password: Mot de passe en clair
            hashed_password: Hash bcrypt
        
        Returns:
            True si le mot de passe correspond
        """
        # Utiliser bcrypt directement pour éviter problème passlib
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    
    def hash_password(self, password: str) -> str:
        """
        Hash un mot de passe avec bcrypt
        
        Args:
            password: Mot de passe en clair (max 72 bytes pour bcrypt)
        
        Returns:
            Hash bcrypt (string)
        """
        # Bcrypt limite à 72 bytes, tronquer si nécessaire
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Utiliser bcrypt directement pour éviter problème passlib
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crée un token JWT
        
        Args:
            data: Données à encoder dans le token (profil_id, email, role)
            expires_delta: Durée d'expiration (optionnel)
        
        Returns:
            Token JWT encodé
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[dict]:
        """
        Décode un token JWT
        
        Args:
            token: Token JWT à décoder
        
        Returns:
            Payload décodé ou None si invalide
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None


# Singleton instance
_security_service: Optional[SecurityService] = None


def get_security_service() -> SecurityService:
    """Get security service singleton"""
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service
