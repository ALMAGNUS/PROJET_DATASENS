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
from pathlib import Path
from typing import Any

import requests
import streamlit as st

from src.config import get_settings
from src.streamlit._cockpit_helpers import (
    get_api_base,
    render_brand_logo,
)
from src.streamlit.cockpit_ux import prefetch_backend_ok

ROLES_HIERARCHY = ("reader", "writer", "deleter", "admin")


def _api_base() -> str:
    return get_api_base()


def _auth_prefix() -> str:
    from src.config import get_settings

    return get_settings().api_v1_prefix


def init_session_auth() -> None:
    """Initialise les clés auth dans session_state si absentes."""
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
    """True si un utilisateur est connecté."""
    return get_token() is not None


def has_role(role: str) -> bool:
    """True si l'utilisateur a le rôle donné (ou admin)."""
    user = get_user()
    if not user:
        return False
    r = (user.get("role") or "").lower()
    return r == role.lower() or r == "admin"


def has_any_role(*allowed: str) -> bool:
    """True si l'utilisateur a l'un des rôles donnés (admin accepté implicitement)."""
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
    Retourne True si l'utilisateur peut exécuter l'action.
    Sinon, affiche un avertissement dans l'UI et retourne False.
    Ne stoppe pas l'application (on gate uniquement le bloc appelant).
    """
    if has_any_role(*allowed):
        return True
    st.info(
        f"Action réservée aux rôles {', '.join(allowed)} : **{action_label}** "
        f"(votre rôle courant : `{(get_user() or {}).get('role', '?')}`)."
    )
    return False


# ---------------------------------------------------------------------------
# JWT: decodage non verifie (lecture du payload uniquement)
# ---------------------------------------------------------------------------
def _decode_jwt_unsafe(token: str | None) -> dict[str, Any]:
    """Décode le payload d'un JWT sans vérifier la signature (UX uniquement)."""
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
    if not isinstance(exp, int | float):
        return None
    return int(exp - time.time())


def session_elapsed_seconds() -> int | None:
    """Durée depuis la connexion (session_state ou claim JWT iat)."""
    logged_at = st.session_state.get("auth_logged_in_at")
    if isinstance(logged_at, int | float):
        return max(0, int(time.time() - logged_at))
    payload = _decode_jwt_unsafe(get_token())
    iat = payload.get("iat")
    if isinstance(iat, int | float):
        return max(0, int(time.time() - iat))
    return None


def is_token_expired() -> bool:
    """True si le token est expiré (exp <= now). False si pas d'info d'expiration."""
    remaining = token_seconds_remaining()
    return remaining is not None and remaining <= 0


def _fmt_ttl(seconds: int | None) -> str:
    if seconds is None:
        return "TTL inconnu"
    if seconds <= 0:
        return "expiré"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def api_reachable(timeout: float = 2.0) -> bool:
    """True si GET /health répond (API E2 démarrée)."""
    try:
        r = requests.get(f"{_api_base()}/health", timeout=timeout)
        return r.ok
    except requests.exceptions.RequestException:
        return False


def _login_network_error_message(exc: Exception) -> str:
    base = _api_base()
    if isinstance(exc, requests.exceptions.ConnectionError):
        return (
            f"**API injoignable** ({base}). "
            "Le cockpit a besoin du backend FastAPI pour l'authentification JWT.\n\n"
            "→ Lancez **`python run_e2_api.py`** ou **`.\\start_full.bat`** "
            "et gardez la fenêtre **DataSensBackend** ouverte."
        )
    return f"Erreur réseau : {exc}"


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Appelle l'API E2 POST /auth/login. Retourne (success, message).
    En cas de succès, stocke token et user dans session_state.
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
        return False, _login_network_error_message(e)

    if r.status_code != 200:
        detail = (
            r.json().get("detail")
            if r.headers.get("content-type", "").startswith("application/json")
            else None
        ) or r.text
        return False, str(detail)[:200]

    data = r.json()
    token = data.get("access_token")
    if not token:
        return False, "Réponse API sans token"

    st.session_state.auth_token = token
    st.session_state.auth_user = {
        "profil_id": data.get("profil_id"),
        "email": data.get("email"),
        "role": data.get("role"),
        "firstname": data.get("firstname"),
        "lastname": data.get("lastname"),
    }
    st.session_state.auth_logged_in_at = time.time()
    # UX: toujours repartir en mode Standard après connexion
    # pour éviter de réutiliser un ancien choix de session.
    st.session_state["ux_mode_select"] = "Standard"
    api_base = os.getenv("API_BASE", f"http://localhost:{get_settings().fastapi_port}")
    prefetch_backend_ok(api_base)
    return True, "Connexion réussie"


def logout() -> None:
    """Déconnecte et vide la session auth."""
    init_session_auth()
    st.session_state.auth_token = None
    st.session_state.auth_user = None
    st.session_state.pop("auth_logged_in_at", None)
    # Remet le profil d'usage par défaut pour la prochaine connexion.
    st.session_state["ux_mode_select"] = "Standard"


def render_login_form() -> bool:
    """
    Affiche le formulaire de login (sidebar — appeler dans `with st.sidebar:`).
    Retourne True si une tentative de login a réussi (pour rerun).
    """
    init_session_auth()
    st.subheader("Connexion")
    with st.form("auth_login_form"):
        email = st.text_input("Email", placeholder="vous@exemple.com")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", use_container_width=True)
    if submitted and email and password:
        ok, msg = login(email.strip(), password)
        if ok:
            st.success(msg)
            return True
        st.error(msg)
    return False


def render_login_page(project_root: Path | None = None) -> bool:
    """
    Page de connexion centrale (zone principale).
    Retourne True si connexion réussie (pour rerun).
    """
    init_session_auth()
    root = project_root or Path(__file__).resolve().parents[2]
    _left, center, _right = st.columns([1, 1.15, 1])
    with center:
        if not render_brand_logo(root, placement="login"):
            st.markdown(
                """
                <div style="text-align:center;margin:1.5rem 0 0.5rem 0;">
                  <div style="font-size:1.35rem;font-weight:700;color:#e8eeff;">DataSens Cockpit</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            """
            <div style="text-align:center;font-size:0.9rem;color:#9eb8f5;margin-bottom:1rem;">
              Connectez-vous pour accéder à l'IA, aux insights et au pipeline.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not api_reachable():
            st.warning(
                f"Backend **hors ligne** (`{_api_base()}`). "
                "Démarrez l'API : `python run_e2_api.py` ou `.\\start_full.bat` "
                "(fenêtre **DataSensBackend**)."
            )
        with st.form("auth_login_main", clear_on_submit=False):
            email = st.text_input("Email", placeholder="vous@exemple.com")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button(
                "Se connecter", type="primary", use_container_width=True
            )
        if submitted and email and password:
            ok, msg = login(email.strip(), password)
            if ok:
                st.success(msg)
                return True
            st.error(msg)
    return False


def render_user_and_logout() -> None:
    """Affiche dans la sidebar l'utilisateur connecté, la TTL et un bouton Déconnexion."""
    user = get_user()
    if not user:
        return

    # Auto-logout si le JWT est expiré côté client
    if is_token_expired():
        logout()
        st.warning("Session expirée. Merci de vous reconnecter.")
        return

    render_role_badge(user)
    compact = st.session_state.get("ux_mode_select", "Standard") == "Mode démo"
    if not compact:
        elapsed = session_elapsed_seconds()
        if elapsed is not None:
            st.caption(f"Connecté depuis : {_fmt_ttl(elapsed)}")

    remaining = token_seconds_remaining()
    if remaining is not None and (not compact or remaining <= 300):
        ttl_label = f"Expire dans : {_fmt_ttl(remaining)}"
        if remaining <= 60:
            st.warning(ttl_label)
        elif remaining <= 300:
            st.info(ttl_label)
        elif not compact:
            st.caption(ttl_label)
    if st.button("Déconnexion", key="auth_logout"):
        logout()
        st.rerun()


_ROLE_META: dict[str, dict[str, str]] = {
    "reader": {
        "label": "Lecteur",
        "color": "#1565c0",
        "bg": "rgba(21, 101, 192, 0.18)",
        "summary": "Consultation, prédiction IA, insights — pas d'exécution pipeline.",
    },
    "writer": {
        "label": "Éditeur",
        "color": "#2e7d32",
        "bg": "rgba(46, 125, 50, 0.18)",
        "summary": "Lecture + lancement pipeline, benchmark, fusion GoldAI.",
    },
    "deleter": {
        "label": "Suppression",
        "color": "#ef6c00",
        "bg": "rgba(239, 108, 0, 0.18)",
        "summary": "Droits writer + actions de suppression SILVER.",
    },
    "admin": {
        "label": "Administrateur",
        "color": "#6a1b9a",
        "bg": "rgba(106, 27, 154, 0.22)",
        "summary": "Accès complet : fine-tuning, activation modèle, ops.",
    },
}


def render_role_badge(user: dict[str, Any] | None = None) -> None:
    """Badge rôle + droits — visible pour la démo RBAC."""
    user = user or get_user()
    if not user:
        return
    email = user.get("email") or "?"
    role = (user.get("role") or "reader").lower()
    meta = _ROLE_META.get(role, _ROLE_META["reader"])
    first = (user.get("firstname") or "").strip()
    display_name = first if first else email.split("@")[0]
    ux_mode = st.session_state.get("ux_mode_select", "Standard")
    compact = ux_mode == "Mode démo"
    summary_block = (
        ""
        if compact
        else f"""<div style="margin-top:0.45rem;font-size:0.74rem;color:#cfd8dc;line-height:1.35;">
            {meta['summary']}
          </div>"""
    )
    st.markdown(
        f"""
        <div style="margin:0.4rem 0 0.6rem 0;padding:0.65rem 0.75rem;border-radius:10px;
             border:1px solid {meta['color']}55;background:{meta['bg']};">
          <div style="font-size:0.72rem;color:#90caf9;text-transform:uppercase;letter-spacing:0.06em;">
            Profil connecté
          </div>
          <div style="font-weight:700;color:#fff;font-size:0.95rem;margin:0.15rem 0;">
            {display_name}
          </div>
          <div style="font-size:0.78rem;color:#b0bec5;">{email}</div>
          <div style="margin-top:0.45rem;display:inline-block;padding:0.15rem 0.55rem;
               border-radius:999px;background:{meta['color']}33;color:{meta['color']};
               font-size:0.76rem;font-weight:700;border:1px solid {meta['color']}88;">
            {meta['label']} ({role})
          </div>
          {summary_block}
        </div>
        """,
        unsafe_allow_html=True,
    )


def require_auth(show_message: bool = True) -> bool:
    """
    Si non connecté: affiche un message (optionnel) et st.stop().
    Retourne True si connecté (le code après peut s'exécuter).
    """
    if is_logged_in():
        return True
    if show_message:
        st.warning("Cette section nécessite une connexion. Connectez-vous dans la barre latérale.")
    st.stop()
    return False
