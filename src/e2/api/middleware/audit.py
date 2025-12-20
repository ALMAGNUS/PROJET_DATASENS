"""
Audit Trail Middleware
======================
Middleware pour logger toutes les actions API dans user_action_log
"""

import sqlite3
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_data_dir, get_settings

settings = get_settings()


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour logger les actions API dans user_action_log
    SRP: Responsabilité unique = audit trail
    """

    def __init__(self, app, db_path: str | None = None):
        super().__init__(app)
        self.db_path = db_path or settings.db_path
        # S'assurer que le chemin est absolu
        if not self.db_path.startswith("/") and not self.db_path.startswith("C:"):
            self.db_path = str(get_data_dir().parent / self.db_path)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercepte les requêtes et log les actions

        Args:
            request: Requête HTTP
            call_next: Fonction pour appeler le prochain middleware

        Returns:
            Response HTTP
        """
        # Exclure certains endpoints (health, docs, etc.)
        excluded_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/api/v1/auth/login"]
        if request.url.path in excluded_paths:
            return await call_next(request)

        # Extraire les infos de la requête
        method = request.method
        path = request.url.path
        ip_address = request.client.host if request.client else None

        # Déterminer action_type et resource_type
        action_type = self._get_action_type(method)
        resource_type = self._get_resource_type(path)
        resource_id = self._extract_resource_id(path)

        # Récupérer profil_id depuis le token (si authentifié)
        profil_id = None
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                from src.e2.auth.security import get_security_service
                security_service = get_security_service()
                payload = security_service.decode_token(token)
                if payload:
                    profil_id = payload.get("sub")
        except Exception:
            # Si erreur, on continue sans logger (pas d'authentification)
            pass

        # Exécuter la requête
        response = await call_next(request)

        # Logger l'action si authentifié
        if profil_id and action_type:
            self._log_action(
                profil_id=profil_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                status_code=response.status_code
            )

        return response

    def _get_action_type(self, method: str) -> str:
        """
        Détermine le type d'action depuis la méthode HTTP

        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)

        Returns:
            Type d'action (read, create, update, delete)
        """
        mapping = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        return mapping.get(method.upper())

    def _get_resource_type(self, path: str) -> str:
        """
        Détermine le type de ressource depuis le path

        Args:
            path: Path de la requête

        Returns:
            Type de ressource (raw_data, silver_data, gold_data, etc.)
        """
        if "/raw/" in path:
            return "raw_data"
        elif "/silver/" in path:
            return "silver_data"
        elif "/gold/" in path:
            return "gold_data"
        elif "/auth/" in path:
            return "auth"
        else:
            return "unknown"

    def _extract_resource_id(self, path: str) -> int:
        """
        Extrait l'ID de ressource depuis le path

        Args:
            path: Path de la requête

        Returns:
            ID de ressource ou None
        """
        try:
            # Chercher pattern /articles/{id} ou /{id}
            parts = path.split("/")
            for i, part in enumerate(parts):
                if part == "articles" and i + 1 < len(parts):
                    return int(parts[i + 1])
                elif part.isdigit():
                    return int(part)
        except (ValueError, IndexError):
            pass
        return None

    def _log_action(
        self,
        profil_id: int,
        action_type: str,
        resource_type: str,
        resource_id: int | None = None,
        ip_address: str | None = None,
        status_code: int | None = None
    ) -> None:
        """
        Log une action dans user_action_log

        Args:
            profil_id: ID de l'utilisateur
            action_type: Type d'action (read, create, update, delete)
            resource_type: Type de ressource (raw_data, silver_data, gold_data)
            resource_id: ID de la ressource (optionnel)
            ip_address: Adresse IP (optionnel)
            status_code: Code de statut HTTP (optionnel)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Vérifier si la table existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_action_log'")
            if not cursor.fetchone():
                # Table n'existe pas, on skip (sera créée par E1)
                conn.close()
                return

            # Insérer le log
            details = f"HTTP {status_code}" if status_code else None
            cursor.execute("""
                INSERT INTO user_action_log
                (profil_id, action_type, resource_type, resource_id, ip_address, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (profil_id, action_type, resource_type, resource_id, ip_address, details))

            conn.commit()
            conn.close()
        except Exception as e:
            # Ne pas faire échouer la requête si le log échoue
            print(f"ATTENTION: Erreur audit trail: {e}")
