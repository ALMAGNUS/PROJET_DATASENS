"""
DataSens Streamlit Cockpit
"""

from __future__ import annotations

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
    ensure_telemetry_session,
    get_api_base,
    render_brand_logo,
    render_demo_header,
    render_mode_intro,
)
from src.streamlit._cockpit_helpers import (
    inject_css as _inject_css,
)
from src.streamlit._cockpit_helpers import (
    inject_demo_css as _inject_demo_css,
)
from src.streamlit._cockpit_helpers import (
    inject_ia_css as _inject_ia_css,
)
from src.streamlit._cockpit_helpers import (
    inject_readability_css as _inject_readability_css,
)
from src.streamlit.auth_plug import (
    get_user,
    init_session_auth,
    is_logged_in,
    render_login_page,
    render_user_and_logout,
)
from src.streamlit.cockpit_ux import (
    inject_cockpit_ux_css,
    on_ux_mode_change,
    render_expert_kpi_strip,
    render_sidebar_status,
    reset_scroll_on_mode_change,
    resolve_backend_ok,
    sync_ux_mode,
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


def _compass_body(ux_mode: str) -> str:
    if ux_mode == "Mode démo":
        return """
            <ul class="ds-compass-list">
              <li>🤖 IA — sentiment et insights</li>
              <li>🔁 Pipeline — volumes, preuve de run, historique</li>
            </ul>
            """
    if ux_mode == "Expert":
        return """
            <ul class="ds-compass-list">
              <li>🏠 Vue d'ensemble — KPI, tuiles, modèle actif</li>
              <li>🔁 Pipeline — Synthèse & run · Explorer les fichiers</li>
              <li>🤖 IA — Sentiment · Modèles (benchmark, fine-tuning)</li>
              <li>⚙️ Pilotage — Actions · Infra & MongoDB</li>
            </ul>
            """
    return """
            <ul class="ds-compass-list">
              <li>🤖 IA — sentiment et insights métier</li>
            </ul>
            """


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

    api_base = get_api_base(settings)
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
                    for candidate in ("Expert", "Mode démo", "Standard"):
                        if candidate in mode_options:
                            st.session_state["ux_mode_select"] = candidate
                            break
                    else:
                        st.session_state["ux_mode_select"] = mode_options[0]
                ux_mode = st.selectbox(
                    "Profil d'usage",
                    mode_options,
                    key="ux_mode_select",
                    help="Standard : IA seule · Démo : IA + pipeline · Expert : cockpit complet",
                    on_change=on_ux_mode_change,
                )
                sync_ux_mode(ux_mode)
                render_sidebar_status(
                    backend_ok=backend_ok,
                    project_root=PROJECT_ROOT,
                )
                show_compass = st.checkbox(
                    "Afficher la boussole",
                    value=True,
                    key="ux_show_compass",
                )
                if show_compass:
                    st.markdown(
                        f"""
            <div class="ds-compass-box">
              <div class="ds-compass-title">🧭 Boussole</div>
              {_compass_body(ux_mode)}
            </div>
            """,
                        unsafe_allow_html=True,
                    )

    if not is_logged_in():
        _inject_css()
        if render_login_page(PROJECT_ROOT):
            st.rerun()
        st.stop()

    ensure_telemetry_session()

    is_demo = ux_mode == "Mode démo"
    reset_scroll_on_mode_change()
    _inject_css()
    inject_cockpit_ux_css()
    _inject_ia_css()
    _inject_readability_css(True)
    _inject_demo_css(True)
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
    elif not render_brand_logo(PROJECT_ROOT, placement="header_main"):
        st.title("DataSens Cockpit")

    if ux_mode in ("Standard", "Expert"):
        render_mode_intro(ctx)

    if ux_mode == "Standard":
        page_ia.render(ctx)
    elif ux_mode == "Mode démo":
        # Radio (pas st.tabs) : un seul panneau rendu → évite le scroll vers le Pipeline caché.
        st.markdown('<div class="ds-demo-main-nav"></div>', unsafe_allow_html=True)
        demo_tab = st.radio(
            "Section",
            ["🤖 IA", "🔁 Pipeline"],
            horizontal=True,
            key="demo_main_tab",
            label_visibility="collapsed",
        )
        ctx.cockpit_tab = demo_tab
        if demo_tab == "🤖 IA":
            page_ia.render(ctx)
        else:
            page_pipeline_data.render(ctx)
    else:
        if ux_mode == "Expert":
            render_expert_kpi_strip(ctx)
        tab_config: list[tuple[str, Callable[[PageContext], None]]] = [
            ("🏠 Vue d'ensemble", page_overview.render),
            ("🔁 Pipeline", page_pipeline_data.render),
            ("🤖 IA", page_ia_models.render),
            ("⚙️ Pilotage", page_pilotage_ops.render),
        ]
        tab_labels = [label for label, _ in tab_config]
        st.markdown('<div class="ds-expert-main-nav"></div>', unsafe_allow_html=True)
        expert_tab = st.radio(
            "Section Expert",
            tab_labels,
            horizontal=True,
            key="expert_main_tab",
            label_visibility="collapsed",
        )
        ctx.cockpit_tab = expert_tab
        render_fn = dict(tab_config)[expert_tab]
        render_fn(ctx)


if __name__ == "__main__":
    main()
