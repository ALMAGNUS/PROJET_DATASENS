"""
DataSens Streamlit Cockpit
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import json
import time
import csv
from pathlib import Path

import pandas as pd
import requests

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.config import get_settings
from src.observability.lineage_service import LineageService
from src.streamlit.auth_plug import (
    get_token,
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
from src.streamlit.metrics import (
    fmt_size as _fmt_size,
    scan_stage as _scan_stage,
    stage_time_range as _stage_time_range,
    chrono_data as _chrono_data,
    ia_metrics_from_parquet as _ia_metrics_from_parquet,
    enrich_profile as _enrich_profile,
    build_enrichment_table as _build_enrichment_table,
    load_benchmark_results as _load_benchmark_results,
    sentiment_benchmark_diagnosis as _sentiment_benchmark_diagnosis,
    go_no_go_snapshot as _go_no_go_snapshot,
    scan_trained_models as _scan_trained_models,
)
from src.streamlit._cockpit_helpers import (
    PageContext,
    inject_css as _inject_css,
    inject_readability_css as _inject_readability_css,
    inject_demo_css as _inject_demo_css,
    read_parquet_cached as _read_parquet_cached,
    parquet_row_count_cached as _parquet_row_count_cached,
    csv_row_count_cached as _csv_row_count_cached,
    mongo_status as _mongo_status,
    ia_history as _ia_history,
    latest_db_state_reports as _latest_db_state_reports,
    get_active_model as _get_active_model,
    activate_model as _activate_model,
    launch_api_in_new_window as _launch_api_in_new_window,
    run_command as _run_command,
    render_last_report as _render_last_report,
    record_click as _record_click,
    get_telemetry_snapshot as _get_telemetry_snapshot,
)
# Modules d'onglet du cockpit : chaque onglet vit dans son propre module.
# Dossier volontairement nommé `page_modules` (et non `pages`) pour désactiver
# l'auto-découverte multi-pages de Streamlit qui polluerait la sidebar.
from src.streamlit.page_modules import (
    demo as page_demo,
    overview as page_overview,
    pipeline as page_pipeline,
    flux as page_flux,
    pilotage as page_pilotage,
    ia as page_ia,
    modeles as page_modeles,
    monitoring as page_monitoring,
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
            st.success("Connecte")
        else:
            st.warning("Arrete")
            st.caption("Lancer : start_full.bat ou python run_e2_api.py")
        st.divider()
        init_session_auth()
        if not is_logged_in():
            if render_login_form():
                st.rerun()
        else:
            render_user_and_logout()

        st.divider()
        ux_mode = st.selectbox(
            "Ergonomie cockpit",
            ["Standard", "Lecture facile", "Mode démo", "Expert"],
            index=0,
            key="ux_mode_select",
            help=(
                "Standard : vue opérationnelle. "
                "Lecture facile : contraste renforcé. "
                "Mode démo : narration simplifiée. "
                "Expert : affiche les blocs techniques avancés (ex. Supervision buffer vs long terme)."
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
              <li>🎬 Démo guidée : parcours narratif des 8 onglets</li>
              <li>🏠 Vue d'ensemble : état global du système</li>
              <li>🔁 Pipeline & Fusion : Gold/GoldAI, doublons, ajouts</li>
              <li>🧬 Flux & Visualisation : rejets, enrichissement, qualité</li>
              <li>⚙️ Pilotage : actions run (collecte, fusion, API)</li>
              <li>🤖 IA : prédiction sentiment et insights Mistral</li>
              <li>🎯 Modèles & Sélection : benchmark, fine-tuning, GO/NO-GO</li>
              <li>📊 Monitoring : MLOps live, Prometheus/Grafana/Kuma</li>
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

    # Securite : aucun panel accessible sans connexion
    if not is_logged_in():
        st.warning("Connectez-vous dans la barre laterale pour acceder au cockpit.")
        st.stop()

    st.title("DataSens Cockpit")
    _inject_css()
    _inject_readability_css(ux_mode == "Lecture facile")
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

    tab_demo, tab_overview, tab_pipeline, tab_flux, tab_pilotage, tab_ia, tab_modeles, tab_monitoring = st.tabs(
        ["🎬 Démo guidée", "🏠 Vue d'ensemble", "🔁 Pipeline & Fusion", "🧬 Flux & Visualisation", "⚙️ Pilotage", "🤖 IA", "🎯 Modèles & Sélection", "📊 Monitoring"]
    )

    with tab_demo:
        page_demo.render(ctx)

    with tab_overview:
        page_overview.render(ctx)

    with tab_pipeline:
        page_pipeline.render(ctx)

    with tab_flux:
        page_flux.render(ctx)

    with tab_pilotage:
        page_pilotage.render(ctx)

    with tab_ia:
        page_ia.render(ctx)

    with tab_modeles:
        page_modeles.render(ctx)

    with tab_monitoring:
        page_monitoring.render(ctx)


if __name__ == "__main__":
    main()
