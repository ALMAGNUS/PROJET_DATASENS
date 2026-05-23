"""
DataSens Streamlit Cockpit
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.config import get_settings
from src.streamlit._cockpit_helpers import (
    PageContext,
    brand_logo_path,
    brand_logo_raster_path,
)
from src.streamlit.cockpit_ux import (
    inject_cockpit_ux_css,
    render_demo_tour_sidebar,
    render_expert_kpi_strip,
    resolve_backend_ok,
)
from src.streamlit._cockpit_helpers import (
    inject_css as _inject_css,
)
from src.streamlit._cockpit_helpers import (
    inject_demo_css as _inject_demo_css,
)
from src.streamlit._cockpit_helpers import (
    inject_presentation_css as _inject_presentation_css,
)
from src.streamlit._cockpit_helpers import (
    inject_readability_css as _inject_readability_css,
)
from src.streamlit._cockpit_helpers import (
    render_brand_logo,
    render_demo_header,
    render_demo_status_strip,
    render_mode_intro,
)
from src.streamlit.auth_plug import (
    get_user,
    has_any_role,
    init_session_auth,
    is_logged_in,
    render_login_page,
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


def _mode_options_for_user() -> list[str]:
    """Standard = reader · Mode démo = présentation · Expert = admin/ops."""
    user = get_user()
    role = (user.get("role") if user else "reader") or "reader"
    role = str(role).lower()
    if role == "admin":
        return ["Standard", "Mode démo", "Expert"]
    if role in ("writer", "deleter"):
        return ["Standard", "Mode démo"]
    return ["Standard"]


def main() -> None:
    settings = get_settings()
    _logo = brand_logo_raster_path(PROJECT_ROOT) or brand_logo_path(PROJECT_ROOT)
    st.set_page_config(
        page_title="DataSens Cockpit",
        layout="wide",
        page_icon=str(_logo) if _logo else "🔷",
        menu_items={
            "Get help": None,
            "Report a bug": None,
            "About": None,
        },
    )
    ux_mode = "Standard"
    show_compass = True

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    backend_ok = resolve_backend_ok(api_base)

    with st.sidebar:
        init_session_auth()
        if not is_logged_in():
            render_brand_logo(PROJECT_ROOT, placement="sidebar")
            st.subheader("Backend (API)")
            st.caption("API connectée" if backend_ok else "API arrêtée")
            st.divider()
        if is_logged_in():
            render_brand_logo(PROJECT_ROOT, placement="sidebar")
            render_user_and_logout()
            if not is_logged_in():
                st.warning("Session expirée — reconnectez-vous.")
            else:
                mode_options = _mode_options_for_user()
                current_mode = st.session_state.get("ux_mode_select", "Standard")
                if current_mode not in mode_options:
                    st.session_state["ux_mode_select"] = mode_options[0]
                ux_mode = st.selectbox(
                    "Profil d'usage",
                    mode_options,
                    key="ux_mode_select",
                    help="Standard : IA seule · Démo : IA + pipeline · Expert : cockpit complet",
                )
                demo_mode = ux_mode == "Mode démo"
                expert_mode = ux_mode == "Expert"
                st.divider()
                if demo_mode:
                    st.caption("Mode démo — IA + pipeline pour présentation jury.")
                    st.markdown(
                        """
            <div class="ds-compass-box">
              <div class="ds-compass-title">🧭 Parcours démo</div>
              <ul class="ds-compass-list">
                <li>🤖 IA — sentiment et insights</li>
                <li>🔁 Pipeline — volumes, preuve de run, historique</li>
              </ul>
            </div>
            """,
                        unsafe_allow_html=True,
                    )
                    st.caption("API connectée" if backend_ok else "API arrêtée")
                    st.checkbox(
                        "Mode présentation (plein écran)",
                        value=False,
                        key="demo_presentation",
                        help="Masque le menu et la barre Streamlit pour projection jury.",
                    )
                    render_demo_tour_sidebar()
                else:
                    st.caption(f"API · `{api_base}`")
                    st.caption("Connectée" if backend_ok else "Arrêtée")
                st.divider()
                if demo_mode:
                    show_compass = False
                else:
                    show_compass = st.checkbox(
                        "Afficher la boussole cockpit",
                        value=True,
                        key="ux_show_compass",
                        help="Repérage rapide des panneaux.",
                    )
                if not demo_mode:
                    if expert_mode:
                        compass_body = """
            <ul class="ds-compass-list">
              <li>🏠 Vue d'ensemble — état pipeline + MongoDB</li>
              <li>🔁 Pipeline — fusion, exploration, ops</li>
              <li>🤖 IA — benchmark, fine-tuning</li>
              <li>⚙️ Pilotage — run, backup, Prometheus</li>
            </ul>
            """
                    else:
                        compass_body = """
            <ul class="ds-compass-list">
              <li>🤖 IA — sentiment et insights métier</li>
            </ul>
            """
                    if not show_compass:
                        compass_body = '<div class="ds-compass-muted">Boussole masquée.</div>'
                    st.markdown(
                        f"""
            <div class="ds-compass-box">
              <div class="ds-compass-title">🧭 Boussole cockpit</div>
              {compass_body}
            </div>
            """,
                        unsafe_allow_html=True,
                    )
                    if expert_mode:
                        st.caption("Mode Expert — Pilotage, fusion, exploration.")
                    elif ux_mode == "Standard":
                        st.caption("Standard — IA et insights (lecture seule).")

    if not is_logged_in():
        _inject_css()
        if render_login_page(PROJECT_ROOT):
            st.rerun()
        st.stop()

    is_demo = ux_mode == "Mode démo"
    presentation = is_demo and st.session_state.get("demo_presentation", False)
    _inject_css()
    inject_cockpit_ux_css()
    _inject_readability_css(is_demo)
    _inject_demo_css(is_demo)
    _inject_presentation_css(presentation)
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

    if is_demo:
        render_demo_header(PROJECT_ROOT)
        render_demo_status_strip(ctx)
    elif not render_brand_logo(PROJECT_ROOT, placement="header_main"):
        st.title("DataSens Cockpit")

    if ux_mode in ("Standard", "Expert"):
        render_mode_intro(ctx)

    if ux_mode == "Standard":
        page_ia.render(ctx)
    else:
        if ux_mode == "Expert":
            render_expert_kpi_strip(ctx)
        tab_config: list[tuple[str, Callable[[PageContext], None]]] = []
        if ux_mode == "Mode démo":
            tab_config = [
                ("🤖 IA", page_ia.render),
                ("🔁 Pipeline", page_pipeline_data.render),
            ]
        else:
            tab_config = [
                ("🏠 Vue d'ensemble", page_overview.render),
                ("🔁 Pipeline", page_pipeline_data.render),
                ("🤖 IA", page_ia_models.render),
                ("⚙️ Pilotage", page_pilotage_ops.render),
            ]

        rendered_tabs = st.tabs([label for label, _ in tab_config])
        for tab_ui, (_, render_fn) in zip(rendered_tabs, tab_config, strict=False):
            with tab_ui:
                render_fn(ctx)


if __name__ == "__main__":
    main()
