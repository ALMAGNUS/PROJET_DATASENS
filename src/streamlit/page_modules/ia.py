"""
Page cockpit : onglet ia.
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

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    api_v1 = f"{api_base}{settings.api_v1_prefix}"

    st.markdown("### IA – Modèles & Assistant")
    try:
        api_ok = requests.get(f"{api_base}/health", timeout=2).ok
    except Exception:
        api_ok = False
    if not api_ok:
        st.warning(
            "L’API n’est pas démarrée. Allez dans **Pilotage** → *Lancer API E2* avant d’utiliser la prédiction ou l’assistant."
        )
    with st.expander("Comment utiliser cet onglet ?", expanded=True):
        st.markdown("""
        **1. Prédiction** : Testez l’analyse de sentiment sur un texte (ex. « Le marché affiche une hausse »).  
        → Saisissez un texte, choisissez un modèle, cliquez sur *Prédire*. Si un modèle fine-tuné est configuré (SENTIMENT_FINETUNED_MODEL_PATH), il est utilisé automatiquement.

        **2. Assistant** : Posez des questions par domaine (Politique, Financier, Utilisateurs).  
        → Sélectionnez un thème, tapez votre question dans le champ en bas. L’assistant répond en fonction des données du projet.
        """)

    st.subheader("1. Prédiction de sentiment")
    st.caption(
        "Analysez le sentiment (positif / négatif / neutre) d’un texte avec FlauBERT ou CamemBERT."
    )
    pred_text = st.text_area(
        "Texte à analyser",
        "Le marché affiche une hausse.",
        height=70,
        help="Ex. une phrase ou un paragraphe",
    )
    pred_model = st.selectbox(
        "Modèle",
        ["sentiment_fr", "camembert", "flaubert"],
        format_func=lambda x: {
            "sentiment_fr": "sentiment_fr — RECOMMANDÉ (57.5% bench, meilleur FR)",
            "camembert": "CamemBERT distil (32.9% bench, léger/CPU)",
            "flaubert": "FlauBERT base uncased (FR, non benchmarké seul)",
        }.get(x, x),
        key="pred_model",
        help="sentiment_fr (ac0hik/Sentiment_Analysis_French) est le meilleur modèle sur vos données.",
    )
    if st.button("Prédire le sentiment"):
        token = get_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            r = requests.post(
                f"{api_v1}/ai/predict",
                json={"text": pred_text, "model": pred_model, "task": "sentiment-analysis"},
                headers=headers,
                timeout=120,
            )
            if r.ok:
                data = r.json()
                res = data.get("result", data)
                if res and isinstance(res, list) and res[0].get("sentiment_score") is not None:
                    r0 = res[0]
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Label", r0.get("label", "-"))
                    c2.metric("Confidence", f"{r0.get('confidence', 0):.1%}")
                    c3.metric("Score [-1,+1]", r0.get("sentiment_score", 0))
                    st.json(res)
                else:
                    st.json(res)
            else:
                err_detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
                st.error(f"Erreur {r.status_code}: {err_detail[:300]}")
        except requests.exceptions.ConnectionError:
            st.warning("API non démarrée (Pilotage → Lancer API E2)")
        except Exception as e:
            st.error(str(e)[:150])

    st.divider()
    st.subheader("2. Assistant Mistral — Analyse client en temps réel")

    # Statut Mistral
    mistral_ok = False
    try:
        r_status = requests.get(
            f"{api_v1}/ai/status",
            headers={"Authorization": f"Bearer {get_token()}"} if get_token() else {},
            timeout=3,
        )
        mistral_ok = r_status.ok and r_status.json().get("configured", False)
    except Exception:
        pass

    if mistral_ok:
        st.success(
            "Mistral connecte — L'assistant s'appuie sur vos donnees GoldAI pour repondre."
        )
    elif api_ok:
        st.warning(
            "Mistral non configure. Verifiez `MISTRAL_API_KEY` dans `.env`."
        )
    else:
        st.warning("API non demarree. Pilotage → Lancer API E2.")

    st.caption(
        "Posez des questions metier sur vos donnees. Mistral repond en s'appuyant sur le contexte reel "
        "(distribution sentiment, topics, sources, tendances) extrait de votre dataset GoldAI."
    )

    theme_options = {
        "Politique": "politique",
        "Financier": "financier",
        "Utilisateurs": "utilisateurs",
    }
    theme_display_to_api = theme_options  # clé affichée -> valeur API

    assist_col1, assist_col2 = st.columns([2, 1])
    with assist_col1:
        theme_display = st.selectbox(
            "Theme d'analyse",
            list(theme_options.keys()),
            key="ia_theme",
            help="Politique : veille, tendances | Financier : marche, indicateurs | Utilisateurs : comportement",
        )
        theme = theme_display_to_api[theme_display]
    with assist_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Effacer la conversation", key="ia_clear", use_container_width=True):
            st.session_state.ia_chat_messages = []
            st.rerun()

    # Exemples de questions
    with st.expander("Exemples de questions clients", expanded=False):
        ex_cols = st.columns(3)
        examples = {
            "Politique": [
                "Quelles sont les tendances politiques cette semaine ?",
                "Quel est le sentiment dominant sur le gouvernement ?",
                "Résume les sujets politiques les plus couverts.",
            ],
            "Financier": [
                "Quelle est la tendance sur l'inflation ?",
                "Le sentiment sur les marchés est-il positif ou négatif ?",
                "Quels indicateurs économiques ressortent le plus ?",
            ],
            "Utilisateurs": [
                "Quelles sources génèrent le plus de contenu négatif ?",
                "Quel est le volume de collecte par source ?",
                "Y a-t-il un déséquilibre dans les données ?",
            ],
        }
        # Utiliser theme_display (Politique/Financier/Utilisateurs) pour les exemples
        examples_for_theme = examples.get(theme_display, [])
        for i, ex in enumerate(examples_for_theme):
            with ex_cols[i]:
                if st.button(ex, key=f"ex_{theme_display}_{i}", use_container_width=True):
                    st.session_state.ia_prefill = ex

    if "ia_chat_messages" not in st.session_state:
        st.session_state.ia_chat_messages = []

    for msg in st.session_state.ia_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Prefill depuis les exemples
    prefill_val = st.session_state.pop("ia_prefill", "")
    prompt = st.chat_input("Votre question d'analyse client...", key="ia_chat_input")
    if not prompt and prefill_val:
        prompt = prefill_val

    if prompt:
        st.session_state.ia_chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"), st.spinner("Mistral analyse vos donnees..."):
            token = get_token()
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            try:
                r = requests.post(
                    f"{api_v1}/ai/insight",
                    json={"theme": theme, "message": prompt},
                    headers=headers,
                    timeout=60,
                )
                if r.ok:
                    reply = r.json().get("reply", "—")
                else:
                    detail = r.json().get("detail", r.text) if "application/json" in r.headers.get("content-type", "") else r.text
                    reply = f"Erreur {r.status_code} : {detail[:200]}"
            except requests.exceptions.ConnectionError:
                reply = "API non disponible. Demarrez l'API (Pilotage → Lancer API E2)."
            except Exception as e:
                reply = f"Erreur : {e!s}"[:200]
            st.markdown(reply)
        st.session_state.ia_chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()
