"""
Page cockpit : onglet demo.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from src.observability.lineage_service import LineageService
from src.streamlit._cockpit_helpers import (
    PageContext,
    activate_model as _activate_model,
    csv_row_count_cached as _csv_row_count_cached,
    get_active_model as _get_active_model,
    ia_history as _ia_history,
    inject_css as _inject_css,
    inject_demo_css as _inject_demo_css,
    inject_readability_css as _inject_readability_css,
    latest_db_state_reports as _latest_db_state_reports,
    launch_api_in_new_window as _launch_api_in_new_window,
    mongo_status as _mongo_status,
    parquet_row_count_cached as _parquet_row_count_cached,
    read_parquet_cached as _read_parquet_cached,
    render_last_report as _render_last_report,
    run_command as _run_command,
)
from src.streamlit.auth_plug import (
    get_token,
    init_session_auth,
    is_logged_in,
    render_login_form,
    render_user_and_logout,
)
from src.streamlit.metrics import (
    build_enrichment_table as _build_enrichment_table,
    chrono_data as _chrono_data,
    enrich_profile as _enrich_profile,
    fmt_size as _fmt_size,
    go_no_go_snapshot as _go_no_go_snapshot,
    ia_metrics_from_parquet as _ia_metrics_from_parquet,
    load_benchmark_results as _load_benchmark_results,
    scan_stage as _scan_stage,
    scan_trained_models as _scan_trained_models,
    sentiment_benchmark_diagnosis as _sentiment_benchmark_diagnosis,
    stage_time_range as _stage_time_range,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    project_root = ctx.project_root
    PROJECT_ROOT = ctx.project_root
    settings = ctx.settings
    api_base = ctx.api_base
    backend_ok = ctx.backend_ok
    ux_mode = ctx.ux_mode
    show_advanced = ctx.show_advanced
    history_mode = ctx.history_mode
    raw_dir = ctx.raw_dir
    silver_dir = ctx.silver_dir
    gold_dir = ctx.gold_dir
    goldai_dir = ctx.goldai_dir
    ia_dir = ctx.ia_dir

    st.subheader("Parcours démo (8 onglets)")
    st.caption("Vue opérable du flux data/IA : ingestion, fusion, scoring, IA temps réel et observabilité.")

    st.markdown(
        """
        1. **Vue d'ensemble** : état système, volumétrie, disponibilité API, signaux de santé.
        2. **Pipeline & Fusion** : delta journalier GOLD → GoldAI, overlap, déduplication, stock net.
        3. **Flux & Visualisation** : lineage SOURCE → RAW → SILVER → GOLD avec points de contrôle.
        4. **Pilotage** : commandes run, supervision buffer/long terme, actions opérationnelles.
        5. **IA** : prédiction sentiment temps réel (E2 `/ai/predict`) et insights Mistral.
        6. **Modèles & Sélection** : benchmark, trade-off qualité/latence, lecture GO/NO-GO.
        7. **Monitoring** : statut live des briques MLOps et cohérence de la collecte.
        8. **Démo guidée** (cet onglet) : narration synthétique pour la présentation.
        """
    )

    st.info(
        "Astuce usage : activez `Mode démo` dans la barre latérale pour une lecture plus fluide pendant la présentation."
    )

    with st.expander("Prise en main (script de présentation)", expanded=True):
        st.markdown(
            """
            **Intro**  
            « Ce cockpit donne une lecture exécutable du pipeline : de l'ingestion au monitoring de prod. »

            **Écran 1 — Vue d'ensemble**  
            « On valide le socle : volumes, présence des artefacts, accessibilité API et cohérence globale. »

            **Écran 2 — Pipeline & Fusion**  
            « On lit le différentiel du jour : lignes candidates, recouvrement historique, puis résultat dédupliqué. »

            **Écran 3 — Flux & Visualisation**  
            « On explicite la transformation inter-couches et les contrôles qualité associés. »

            **Écran 4 — Pilotage**  
            « On exécute les actions clés (pipeline, fusion, copie IA) avec retour opérationnel immédiat. »

            **Écran 5 — IA**  
            « On démontre l'inférence temps réel : prédiction de sentiment et insight Mistral sur requête utilisateur. »

            **Écran 6 — Modèles & Sélection**  
            « On compare les modèles sur des métriques actionnables (F1, accuracy, latence) pour décider l'usage. »

            **Écran 7 — Monitoring**  
            « On clôture par la télémétrie live (API, Prometheus, Grafana, Uptime Kuma) pour valider l'exploitabilité. »
            """
        )
