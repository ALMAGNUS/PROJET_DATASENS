"""
Auth plug - Authentification RBAC / OAuth2 pour le cockpit Streamlit
======================================================================
- Login par email/mot de passe (JWT via API E2).
- Session stockee dans st.session_state (token, user, role).
- Decodage non verifie du JWT pour exposer l'expiration (TTL) cote UI.
- Helpers RBAC (`has_role`, `has_any_role`, `can_write`, `can_admin`).
- Optionnel: brancher OAuth2 (Google, GitHub) plus tard.
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

import requests

import streamlit as st
from src.config import get_settings

ROLES_HIERARCHY = ("reader", "writer", "deleter", "admin")
FORGOT_PASSWORD_HELP = (
    "Mot de passe oublie ? Contactez l'administrateur de la plateforme "
    "(aucun workflow self-service n'est expose par l'API E2)."
)


def _api_base() -> str:
    settings = get_settings()
    return os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")


def _auth_prefix() -> str:
    from src.config import get_settings
    return get_settings().api_v1_prefix


def init_session_auth() -> None:
    """Initialise les cles auth dans session_state si absentes."""
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None


def get_token() -> str | None:
    """Retourne le token JWT en session ou None."""
    init_session_auth()
    return st.session_state.auth_token


def get_user() -> dict[str, Any] | None:
    """Retourne les infos utilisateur en session (email, role, etc.) ou None."""
    init_session_auth()
    return st.session_state.auth_user


def is_logged_in() -> bool:
    """True si un utilisateur est connecte."""
    return get_token() is not None


def has_role(role: str) -> bool:
    """True si l'utilisateur a le role donne (ou admin)."""
    user = get_user()
    if not user:
        return False
    r = (user.get("role") or "").lower()
    return r == role.lower() or r == "admin"


def has_any_role(*allowed: str) -> bool:
    """True si l'utilisateur a l'un des roles donnes (admin accepte implicitement)."""
    user = get_user()
    if not user:
        return False
    r = (user.get("role") or "").lower()
    if r == "admin":
        return True
    return r in {a.lower() for a in allowed}


def can_write() -> bool:
    """True pour writer, deleter ou admin (lance une action write-side)."""
    return has_any_role("writer", "deleter", "admin")


def can_admin() -> bool:
    """True uniquement pour les administrateurs."""
    return has_any_role("admin")


def gate_by_role(allowed: tuple[str, ...], action_label: str) -> bool:
    """
    Retourne True si l'utilisateur peut executer l'action.
    Sinon, affiche un avertissement dans l'UI et retourne False.
    Ne stoppe pas l'application (on gate uniquement le bloc appelant).
    """
    if has_any_role(*allowed):
        return True
    st.info(
        f"Action reservee aux roles {', '.join(allowed)} : **{action_label}** "
        f"(votre role courant : `{(get_user() or {}).get('role', '?')}`)."
    )
    return False


# ---------------------------------------------------------------------------
# JWT: decodage non verifie (lecture du payload uniquement)
# ---------------------------------------------------------------------------
def _decode_jwt_unsafe(token: str | None) -> dict[str, Any]:
    """Decode le payload d'un JWT sans verifier la signature (UX uniquement)."""
    if not token:
        return {}
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def token_seconds_remaining() -> int | None:
    """Retourne le nombre de secondes restantes avant expiration (ou None si indispo)."""
    payload = _decode_jwt_unsafe(get_token())
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        return None
    return int(exp - time.time())


def is_token_expired() -> bool:
    """True si le token est expire (exp <= now). False si pas d'info d'expiration."""
    remaining = token_seconds_remaining()
    return remaining is not None and remaining <= 0


def _fmt_ttl(seconds: int | None) -> str:
    if seconds is None:
        return "TTL inconnu"
    if seconds <= 0:
        return "expire"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Appelle l'API E2 POST /auth/login. Retourne (success, message).
    En cas de succes, stocke token et user dans session_state.
    """
    init_session_auth()
    url = f"{_api_base()}{_auth_prefix().rstrip('/')}/auth/login"
    try:
        r = requests.post(
            url,
            json={"email": email, "password": password},
            timeout=30,
            headers={"Content-Type": "application/json"},
        )
    except requests.exceptions.RequestException as e:
        return False, f"Erreur reseau: {e}"

    if r.status_code != 200:
        detail = (r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None) or r.text
        return False, str(detail)[:200]

    data = r.json()
    token = data.get("access_token")
    if not token:
        return False, "Reponse API sans token"

    st.session_state.auth_token = token
    st.session_state.auth_user = {
        "profil_id": data.get("profil_id"),
        "email": data.get("email"),
        "role": data.get("role"),
        "firstname": data.get("firstname"),
        "lastname": data.get("lastname"),
    }
    return True, "Connexion reussie"


def logout() -> None:
    """Deconnecte et vide la session auth."""
    init_session_auth()
    st.session_state.auth_token = None
    st.session_state.auth_user = None


def render_login_form() -> bool:
    """
    Affiche le formulaire de login dans la sidebar.
    Retourne True si une tentative de login a reussi (pour rerun).
    """
    init_session_auth()
    st.sidebar.subheader("Connexion")
    with st.sidebar.form("auth_login_form"):
        email = st.text_input("Email", placeholder="vous@exemple.com")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
    if submitted and email and password:
        ok, msg = login(email.strip(), password)
        if ok:
            st.sidebar.success(msg)
            return True
        st.sidebar.error(msg)
    st.sidebar.caption(FORGOT_PASSWORD_HELP)
    return False


def render_user_and_logout() -> None:
    """Affiche dans la sidebar l'utilisateur connecte, la TTL et un bouton Deconnexion."""
    user = get_user()
    if not user:
        return

    # Auto-logout si le JWT est expire cote client
    if is_token_expired():
        logout()
        st.sidebar.warning("Session expiree. Merci de vous reconnecter.")
        return

    email = user.get("email") or "?"
    role = user.get("role") or "?"
    st.sidebar.caption(f"Connecte: {email}")
    st.sidebar.caption(f"Role: {role}")
    remaining = token_seconds_remaining()
    if remaining is not None:
        if remaining <= 60:
            st.sidebar.warning(f"Session: {_fmt_ttl(remaining)}")
        elif remaining <= 300:
            st.sidebar.info(f"Session: {_fmt_ttl(remaining)}")
        else:
            st.sidebar.caption(f"Session: {_fmt_ttl(remaining)}")
    if st.sidebar.button("Deconnexion", key="auth_logout"):
        logout()
        st.rerun()


def require_auth(show_message: bool = True) -> bool:
    """
    Si non connecte: affiche un message (optionnel) et st.stop().
    Retourne True si connecte (le code apres peut s'executer).
    """
    if is_logged_in():
        return True
    if show_message:
        st.warning("Cette section necessite une connexion. Connectez-vous dans la barre laterale.")
    st.stop()
    return False


# ---------------------------------------------------------------------------
# OAuth2: point d'extension pour brancher Google / GitHub plus tard
# ---------------------------------------------------------------------------
# def login_oauth2(provider: str) -> bool:
#     """Placeholder: redirection OAuth2 vers provider (google, github)."""
#     # TODO: integrer streamlit-oauth ou authlib + redirect_uri
#     return False
