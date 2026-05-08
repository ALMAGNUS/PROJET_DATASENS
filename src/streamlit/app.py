"""
DataSens Streamlit Cockpit
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.config import get_settings
from src.streamlit._cockpit_helpers import (
    PageContext,
)
from src.streamlit._cockpit_helpers import (
    inject_css as _inject_css,
)
from src.streamlit._cockpit_helpers import (
    inject_demo_css as _inject_demo_css,
)
from src.streamlit._cockpit_helpers import (
    inject_readability_css as _inject_readability_css,
)
from src.streamlit.auth_plug import (
    init_session_auth,
    is_logged_in,
    render_login_form,
    render_user_and_logout,
)

# M6 refactor — helpers de calcul pur extraits dans metrics.py.
# Phase 1 : fmt_size, scan_stage
# Phase 2 : stage_time_range, chrono_data, ia_metrics_from_parquet, enrich_profile, build_enrichment_table
# Phase 3 : load_benchmark_results, sentiment_benchmark_diagnosis, go_no_go_snapshot, scan_trained_models
# Phase 4 (cockpit audit 2026-04) : helpers UI centralisés dans src/streamlit/_cockpit_helpers.py
# Modules d'onglet du cockpit : chaque onglet vit dans son propre module.
# Dossier volontairement nommé `page_modules` (et non `pages`) pour désactiver
# l'auto-découverte multi-pages de Streamlit qui polluerait la sidebar.
from src.streamlit.page_modules import (
    demo as page_demo,
)
from src.streamlit.page_modules import (
    ia as page_ia,
)
from src.streamlit.page_modules import (
    ia_models as page_ia_models,
)
from src.streamlit.page_modules import (
    overview as page_overview,
)
from src.streamlit.page_modules import (
    pilotage_ops as page_pilotage_ops,
)
from src.streamlit.page_modules import (
    pipeline_data as page_pipeline_data,
)


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title="DataSens Cockpit", layout="wide")
    ux_mode = "Standard"
    show_compass = True

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    try:
        r = requests.get(f"{api_base}/health", timeout=2)
        backend_ok = r.ok
    except Exception:
        backend_ok = False

    with st.sidebar:
        st.subheader("Backend (API)")
        st.caption(f"`{api_base}`")
        if backend_ok:
            st.success("Connecté")
        else:
            st.warning("Arrêté")
            st.caption("Lancer : start_full.bat ou python run_e2_api.py")
        st.divider()
        init_session_auth()
        if not is_logged_in():
            if render_login_form():
                st.rerun()
        else:
            render_user_and_logout()
            # Si la session vient d'expirer pendant ce render, proposer
            # immédiatement le formulaire sans forcer un refresh manuel.
            if not is_logged_in():
                if render_login_form():
                    st.rerun()

        st.divider()
        ux_mode = st.selectbox(
            "Profil d’usage",
            ["Standard", "Mode démo", "Expert"],
            index=0,
            key="ux_mode_select",
            help=(
                "Standard : onglet IA uniquement (utilisateur final). "
                "Mode démo : 4 onglets épurés pour la démonstration (sans admin). "
                "Expert : 4 onglets dont Pilotage & Ops (MongoDB, Prometheus, fine-tuning)."
            ),
        )
        show_compass = st.checkbox(
            "Afficher la boussole cockpit",
            value=True,
            key="ux_show_compass",
            help="Repérage rapide des panneaux selon votre besoin.",
        )
        compass_body = (
            """
            <ul class="ds-compass-list">
              <li>🎬 Démo guidée : narration (Mode démo seul)</li>
              <li>🏠 Vue d'ensemble : état pipeline + Lineage de la donnée (SQLite → MongoDB)</li>
              <li>🔁 Pipeline & Données : Pipeline du jour + preuve de fusion + exploration</li>
              <li>🤖 IA &amp; Modèles : prédiction live, insights Mistral, benchmark</li>
              <li>⚙️ Pilotage &amp; Ops : admin (run/backup, MongoDB, Prometheus) — Expert seul</li>
            </ul>
            """
            if show_compass
            else '<div class="ds-compass-muted">Boussole masquée. Activez le switch pour afficher le guide.</div>'
        )
        st.markdown(
            f"""
            <div class="ds-compass-box">
              <div class="ds-compass-title">🧭 Boussole cockpit</div>
              {compass_body}
            </div>
            """,
            unsafe_allow_html=True,
        )
        mode_summary = {
            "Standard": "Mode actif : Standard — onglet IA utilisateur uniquement.",
            "Mode démo": "Mode actif : Démo — Démo guidée + Vue d'ensemble + Pipeline & Données + IA & Modèles. Pas d'admin technique.",
            "Expert": "Mode actif : Expert — 4 onglets dont Pilotage & Ops (admin, MongoDB, Prometheus).",
        }
        st.caption(mode_summary.get(ux_mode, ""))

    # Securite : aucun panel accessible sans connexion
    if not is_logged_in():
        st.warning("Connectez-vous dans la barre latérale pour accéder au cockpit.")
        st.stop()

    st.title("DataSens Cockpit")
    _inject_css()
    _inject_readability_css(False)
    _inject_demo_css(ux_mode == "Mode démo")
    history_mode = True
    show_advanced = ux_mode == "Expert"

    raw_dir = PROJECT_ROOT / "data" / "raw"
    silver_dir = PROJECT_ROOT / "data" / "silver"
    gold_dir = PROJECT_ROOT / "data" / "gold"
    goldai_dir = PROJECT_ROOT / "data" / "goldai"
    ia_dir = goldai_dir / "ia"

    ctx = PageContext(
        project_root=PROJECT_ROOT,
        api_base=api_base,
        backend_ok=backend_ok,
        ux_mode=ux_mode,
        show_advanced=show_advanced,
        history_mode=history_mode,
        raw_dir=raw_dir,
        silver_dir=silver_dir,
        gold_dir=gold_dir,
        goldai_dir=goldai_dir,
        ia_dir=ia_dir,
        settings=settings,
    )

    page_registry = {
        "🎬 Démo guidée": page_demo.render,
        "🏠 Vue d'ensemble": page_overview.render,
        "🔁 Pipeline & Données": page_pipeline_data.render,
        "🤖 IA": page_ia.render,
        "🤖 IA & Modèles": page_ia_models.render,
        "⚙️ Pilotage & Ops": page_pilotage_ops.render,
    }
    tabs_by_mode = {
        "Standard": ["🤖 IA"],
        "Mode démo": [
            "🎬 Démo guidée",
            "🏠 Vue d'ensemble",
            "🔁 Pipeline & Données",
            "🤖 IA & Modèles",
        ],
        "Expert": [
            "🏠 Vue d'ensemble",
            "🔁 Pipeline & Données",
            "🤖 IA & Modèles",
            "⚙️ Pilotage & Ops",
        ],
    }
    selected_tabs = tabs_by_mode.get(ux_mode, tabs_by_mode["Standard"])
    rendered_tabs = st.tabs(selected_tabs)
    for tab_ui, tab_label in zip(rendered_tabs, selected_tabs, strict=False):
        with tab_ui:
            page_registry[tab_label](ctx)


if __name__ == "__main__":
    main()
