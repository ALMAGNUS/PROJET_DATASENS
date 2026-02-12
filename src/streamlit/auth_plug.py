"""
Auth plug - Authentification RBAC / OAuth2 pour le cockpit Streamlit
======================================================================
- Login par email/mot de passe (JWT via API E2).
- Session stockee dans st.session_state (token, user, role).
- Optionnel: brancher OAuth2 (Google, GitHub) plus tard.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

from src.config import get_settings


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


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Appelle l'API E2 POST /auth/login. Retourne (success, message).
    En cas de succes, stocke token et user dans session_state.
    """
    init_session_auth()
    url = f"{_api_base()}{_auth_prefix()}auth/login"
    try:
        r = requests.post(
            url,
            json={"email": email, "password": password},
            timeout=10,
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
    return False


def render_user_and_logout() -> None:
    """Affiche dans la sidebar l'utilisateur connecte et un bouton Deconnexion."""
    user = get_user()
    if not user:
        return
    email = user.get("email") or "?"
    role = user.get("role") or "?"
    st.sidebar.caption(f"Connecte: {email}")
    st.sidebar.caption(f"Role: {role}")
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
