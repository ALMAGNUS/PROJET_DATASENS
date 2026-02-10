"""
User Service - Business Logic for Users
========================================
Service pour gérer les utilisateurs (PROFILS table)
SRP: Responsabilité unique = gestion utilisateurs
"""

import sqlite3

from src.config import get_data_dir, get_settings
from src.e2.api.schemas.user import UserInDB
from src.e2.auth.security import get_security_service

settings = get_settings()
security_service = get_security_service()


class UserService:
    """
    Service pour gérer les utilisateurs
    SRP: Responsabilité unique = opérations utilisateurs
    """

    def __init__(self, db_path: str | None = None):
        """
        Args:
            db_path: Chemin vers la DB (optionnel, utilise config par défaut)
        """
        self.db_path = db_path or settings.db_path
        # S'assurer que le chemin est absolu
        if not self.db_path.startswith("/") and not self.db_path.startswith("C:"):
            self.db_path = str(get_data_dir().parent / self.db_path)

    def get_user_by_email(self, email: str) -> UserInDB | None:
        """
        Récupère un utilisateur par email depuis PROFILS

        Args:
            email: Email de l'utilisateur

        Returns:
            UserInDB ou None si non trouvé
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT profil_id, email, password_hash, firstname, lastname,
                       role, active, created_at, updated_at, last_login, username
                FROM profils
                WHERE email = ?
            """,
                (email,),
            )

            row = cursor.fetchone()
            if row:
                return UserInDB(
                    profil_id=row["profil_id"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    firstname=row["firstname"],
                    lastname=row["lastname"],
                    role=row["role"],
                    active=bool(row["active"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    last_login=row["last_login"],
                    username=row["username"],
                )
            return None
        finally:
            conn.close()

    def get_user_by_id(self, profil_id: int) -> UserInDB | None:
        """
        Récupère un utilisateur par ID depuis PROFILS

        Args:
            profil_id: ID de l'utilisateur

        Returns:
            UserInDB ou None si non trouvé
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT profil_id, email, password_hash, firstname, lastname,
                       role, active, created_at, updated_at, last_login, username
                FROM profils
                WHERE profil_id = ?
            """,
                (profil_id,),
            )

            row = cursor.fetchone()
            if row:
                return UserInDB(
                    profil_id=row["profil_id"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    firstname=row["firstname"],
                    lastname=row["lastname"],
                    role=row["role"],
                    active=bool(row["active"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    last_login=row["last_login"],
                    username=row["username"],
                )
            return None
        finally:
            conn.close()

    def authenticate_user(self, email: str, password: str) -> UserInDB | None:
        """
        Authentifie un utilisateur (vérifie email + password)

        Args:
            email: Email de l'utilisateur
            password: Mot de passe en clair

        Returns:
            UserInDB si authentification réussie, None sinon
        """
        user = self.get_user_by_email(email)
        if not user:
            return None

        if not user.active:
            return None

        if not security_service.verify_password(password, user.password_hash):
            return None

        return user

    def update_last_login(self, profil_id: int) -> None:
        """
        Met à jour last_login pour un utilisateur

        Args:
            profil_id: ID de l'utilisateur
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE profils
                SET last_login = CURRENT_TIMESTAMP
                WHERE profil_id = ?
            """,
                (profil_id,),
            )
            conn.commit()
        finally:
            conn.close()


# Singleton instance
_user_service: UserService | None = None


def get_user_service() -> UserService:
    """Get user service singleton"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
