"""
Tests E2 API - FastAPI + RBAC
==============================
Tests pour l'API E2 avec pytest et httpx
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.config import get_data_dir, get_settings
from src.e2.api.main import create_app
from src.e2.auth.security import get_security_service

settings = get_settings()


@pytest.fixture
def client():
    """Client de test FastAPI"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_user():
    """Créer un utilisateur de test dans la DB"""
    db_path = settings.db_path
    if not db_path.startswith("/") and not db_path.startswith("C:"):
        db_path = str(get_data_dir().parent / db_path)

    security_service = get_security_service()
    password_hash = security_service.hash_password("testpass123")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Vérifier si la table existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profils'")
        if not cursor.fetchone():
            pytest.skip("Table PROFILS n'existe pas. Exécutez d'abord le pipeline E1.")

        # Créer ou mettre à jour utilisateur de test
        cursor.execute("SELECT profil_id FROM profils WHERE email = ?", ("test@example.com",))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE profils
                SET password_hash = ?, role = 'reader', active = 1
                WHERE email = ?
            """,
                (password_hash, "test@example.com"),
            )
            profil_id = existing[0]
        else:
            import uuid

            unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
            cursor.execute(
                """
                INSERT INTO profils (email, password_hash, firstname, lastname, role, active, username)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                ("test@example.com", password_hash, "Test", "User", "reader", 1, unique_username),
            )
            cursor.execute("SELECT profil_id FROM profils WHERE email = ?", ("test@example.com",))
            profil_id = cursor.fetchone()[0]

        conn.commit()

        yield {
            "email": "test@example.com",
            "password": "testpass123",
            "profil_id": profil_id,
            "role": "reader",
        }

        # Cleanup (optionnel - on garde l'utilisateur pour les tests)
    finally:
        conn.close()


@pytest.fixture
def auth_token(client, test_user):
    """Obtenir un token JWT pour les tests authentifiés"""
    response = client.post(
        "/api/v1/auth/login", json={"email": test_user["email"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestAuth:
    """Tests pour l'authentification"""

    def test_login_success(self, client, test_user):
        """Test login réussi"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["email"] == test_user["email"]
        assert data["role"] == test_user["role"]

    def test_login_invalid_credentials(self, client):
        """Test login avec credentials invalides"""
        response = client.post(
            "/api/v1/auth/login", json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login avec champs manquants"""
        response = client.post("/api/v1/auth/login", json={"email": "test@test.com"})
        assert response.status_code == 422  # Validation error


class TestRawZone:
    """Tests pour la zone RAW (read-only)"""

    def test_list_raw_articles_unauthorized(self, client):
        """Test liste articles RAW sans authentification"""
        response = client.get("/api/v1/raw/articles")
        assert response.status_code == 403  # Forbidden (pas de token)

    def test_list_raw_articles_authorized(self, client, auth_token):
        """Test liste articles RAW avec authentification"""
        response = client.get(
            "/api/v1/raw/articles", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)

    def test_get_raw_article_authorized(self, client, auth_token):
        """Test récupération article RAW par ID"""
        # D'abord lister pour avoir un ID
        list_response = client.get(
            "/api/v1/raw/articles?page_size=1", headers={"Authorization": f"Bearer {auth_token}"}
        )
        if list_response.status_code == 200 and list_response.json()["items"]:
            article_id = list_response.json()["items"][0]["raw_data_id"]
            response = client.get(
                f"/api/v1/raw/articles/{article_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "raw_data_id" in data
            assert "title" in data


class TestGoldZone:
    """Tests pour la zone GOLD (read-only, enriched)"""

    def test_list_gold_articles_authorized(self, client, auth_token):
        """Test liste articles GOLD avec authentification"""
        response = client.get(
            "/api/v1/gold/articles", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_gold_stats(self, client, auth_token):
        """Test statistiques GOLD"""
        response = client.get(
            "/api/v1/gold/stats", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data
        assert "total_sources" in data


class TestPermissions:
    """Tests pour les permissions RBAC"""

    def test_reader_can_read(self, client, auth_token):
        """Test que reader peut lire"""
        response = client.get(
            "/api/v1/gold/articles", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200

    def test_health_check_no_auth(self, client):
        """Test health check sans authentification"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestPagination:
    """Tests pour la pagination"""

    def test_pagination_default(self, client, auth_token):
        """Test pagination par défaut"""
        response = client.get(
            "/api/v1/raw/articles", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 50

    def test_pagination_custom(self, client, auth_token):
        """Test pagination personnalisée"""
        response = client.get(
            "/api/v1/raw/articles?page=2&page_size=10",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestAuditTrail:
    """Tests pour l'audit trail (user_action_log)"""

    def test_audit_trail_logs_read_action(self, client, auth_token, test_user):
        """Test que les actions READ sont loggées dans user_action_log"""
        db_path = settings.db_path
        if not db_path.startswith("/") and not db_path.startswith("C:"):
            db_path = str(get_data_dir().parent / db_path)

        # Compter les logs avant
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM user_action_log WHERE profil_id = ?", (test_user["profil_id"],)
        )
        count_before = cursor.fetchone()[0]
        conn.close()

        # Faire une requête qui devrait être loggée
        response = client.get(
            "/api/v1/raw/articles?page_size=1", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200

        # Vérifier qu'un log a été ajouté
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM user_action_log WHERE profil_id = ?", (test_user["profil_id"],)
        )
        count_after = cursor.fetchone()[0]

        # Vérifier le dernier log
        cursor.execute(
            """
            SELECT action_type, resource_type, ip_address, details
            FROM user_action_log
            WHERE profil_id = ?
            ORDER BY action_date DESC
            LIMIT 1
        """,
            (test_user["profil_id"],),
        )
        log = cursor.fetchone()
        conn.close()

        assert count_after > count_before, "Un log d'audit devrait avoir été créé"
        assert log is not None, "Le log devrait exister"
        assert log[0] == "read", f"Action type devrait être 'read', got '{log[0]}'"
        assert log[1] == "raw_data", f"Resource type devrait être 'raw_data', got '{log[1]}'"
        assert log[3] is not None, "Details (status_code) devrait être présent"

    def test_audit_trail_logs_gold_access(self, client, auth_token, test_user):
        """Test que les accès GOLD sont loggés"""
        db_path = settings.db_path
        if not db_path.startswith("/") and not db_path.startswith("C:"):
            db_path = str(get_data_dir().parent / db_path)

        # Faire une requête GOLD
        response = client.get(
            "/api/v1/gold/articles?page_size=1", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200

        # Vérifier le log
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT action_type, resource_type
            FROM user_action_log
            WHERE profil_id = ? AND resource_type = 'gold_data'
            ORDER BY action_date DESC
            LIMIT 1
        """,
            (test_user["profil_id"],),
        )
        log = cursor.fetchone()
        conn.close()

        assert log is not None, "Un log GOLD devrait exister"
        assert log[0] == "read", "Action type devrait être 'read'"
        assert log[1] == "gold_data", "Resource type devrait être 'gold_data'"

    def test_audit_trail_no_log_for_health_check(self, client):
        """Test que /health n'est pas loggé (exclu de l'audit)"""
        db_path = settings.db_path
        if not db_path.startswith("/") and not db_path.startswith("C:"):
            db_path = str(get_data_dir().parent / db_path)

        # Compter les logs avant
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_action_log")
        count_before = cursor.fetchone()[0]
        conn.close()

        # Faire une requête /health (non authentifiée)
        response = client.get("/health")
        assert response.status_code == 200

        # Vérifier qu'aucun log n'a été ajouté
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_action_log")
        count_after = cursor.fetchone()[0]
        conn.close()

        assert count_after == count_before, "/health ne devrait pas être loggé"

    def test_audit_trail_no_log_for_unauthorized(self, client):
        """Test que les requêtes non authentifiées ne sont pas loggées"""
        db_path = settings.db_path
        if not db_path.startswith("/") and not db_path.startswith("C:"):
            db_path = str(get_data_dir().parent / db_path)

        # Compter les logs avant
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_action_log")
        count_before = cursor.fetchone()[0]
        conn.close()

        # Faire une requête non authentifiée (devrait retourner 403)
        response = client.get("/api/v1/raw/articles")
        assert response.status_code == 403

        # Vérifier qu'aucun log n'a été ajouté (pas de profil_id)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_action_log")
        count_after = cursor.fetchone()[0]
        conn.close()

        assert (
            count_after == count_before
        ), "Les requêtes non authentifiées ne devraient pas être loggées"
