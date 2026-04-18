"""
Page cockpit : onglet overview.
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
from src.streamlit.pipeline_proof import render_last_run_proof_compact
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

    st.markdown(
        """
    <div class="ds-hero">
    <h3>Objectif</h3>
    <p>Interface d'évaluation des sentiments croisant différentes sources de données.</p>
    <div class="ds-flow">
    <span>Sources</span><span class="arrow">→</span><span>RAW</span><span class="arrow">→</span><span>SILVER</span><span>(+ topics)</span><span class="arrow">→</span><span>GOLD</span><span>(+ sentiment)</span><span class="arrow">→</span><span>GoldAI</span><span class="arrow">→</span><span>Copie IA</span>
    </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Résumé de la preuve d'enrichissement du dernier run (audit pipeline).
    render_last_run_proof_compact(ctx)
    st.divider()

    # Vue métier: lignes comparables par couche (pas de mélange fichiers/poids).
    raw_total = 0
    db_candidate = os.getenv("DB_PATH")
    if db_candidate and Path(db_candidate).exists():
        db_path = Path(db_candidate)
    else:
        default_db = Path.home() / "datasens_project" / "datasens.db"
        db_path = default_db if default_db.exists() else PROJECT_ROOT / "datasens.db"
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            raw_total = int(cur.execute("SELECT COUNT(*) FROM raw_data").fetchone()[0])
            conn.close()
        except Exception:
            raw_total = 0

    silver_rows, silver_label = 0, "—"
    if silver_dir.exists():
        silver_dirs = sorted(
            [d for d in silver_dir.iterdir() if d.is_dir()],
            key=lambda d: d.name.replace("date=", "").replace("v_", ""),
            reverse=True,
        )
        if silver_dirs:
            sdir = silver_dirs[0]
            silver_label = sdir.name.replace("date=", "").replace("v_", "")
            cands = [sdir / "silver_articles.csv", sdir / "silver_articles.parquet"] + list(sdir.rglob("*.csv")) + list(sdir.rglob("*.parquet"))
            sfile = next((p for p in cands if p.exists()), None)
            if sfile is not None:
                silver_rows = _parquet_row_count_cached(str(sfile)) if sfile.suffix.lower() == ".parquet" else _csv_row_count_cached(str(sfile))

    gold_rows, gold_label = 0, "—"
    if gold_dir.exists():
        gold_dates = sorted(
            [d.name.replace("date=", "") for d in gold_dir.iterdir() if d.is_dir() and d.name.startswith("date=")],
            reverse=True,
        )
        if gold_dates:
            gold_label = gold_dates[0]
            gpart = gold_dir / f"date={gold_label}"
            gfile = gpart / "articles.parquet"
            if gfile.exists():
                gold_rows = _parquet_row_count_cached(str(gfile))

    goldai_rows = _parquet_row_count_cached(str(goldai_dir / "merged_all_dates.parquet")) if (goldai_dir / "merged_all_dates.parquet").exists() else 0
    ia_train = _parquet_row_count_cached(str(ia_dir / "train.parquet")) if (ia_dir / "train.parquet").exists() else 0
    ia_val = _parquet_row_count_cached(str(ia_dir / "val.parquet")) if (ia_dir / "val.parquet").exists() else 0
    ia_test = _parquet_row_count_cached(str(ia_dir / "test.parquet")) if (ia_dir / "test.parquet").exists() else 0
    ia_total = ia_train + ia_val + ia_test
    app_input_path = goldai_dir / "app" / "gold_app_input.parquet"
    ia_labelled_path = ia_dir / "gold_ia_labelled.parquet"
    preds_root = goldai_dir / "predictions"
    app_input_rows = _parquet_row_count_cached(str(app_input_path)) if app_input_path.exists() else 0
    ia_labelled_rows = _parquet_row_count_cached(str(ia_labelled_path)) if ia_labelled_path.exists() else 0
    pred_candidates = sorted(preds_root.glob("date=*/run=*/predictions.parquet"), key=lambda p: p.stat().st_mtime, reverse=True) if preds_root.exists() else []
    latest_pred = pred_candidates[0] if pred_candidates else None
    latest_pred_rows = _parquet_row_count_cached(str(latest_pred)) if latest_pred and latest_pred.exists() else 0
    latest_pred_label = (
        f"{latest_pred.parent.parent.name.replace('date=', '')} · {latest_pred.parent.name.replace('run=', '')}"
        if latest_pred
        else "—"
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("RAW SQLite (buffer)", f"{raw_total:,}")
    k2.metric("SILVER dernière partition", f"{silver_rows:,}", delta=silver_label)
    k3.metric("GOLD du jour (partition)", f"{gold_rows:,}", delta=gold_label)
    k4, k5, k6 = st.columns(3)
    k4.metric("GoldAI fusion long terme", f"{goldai_rows:,}")
    k5.metric("IA split total", f"{ia_total:,}", delta=f"train {ia_train:,} · val {ia_val:,} · test {ia_test:,}")
    k6.metric("Écart GoldAI - GOLD jour", f"{goldai_rows - gold_rows:+,}")
    st.caption("Périmètre homogène: lignes par couche. On ne mélange pas ici avec des compteurs de fichiers/MB.")
    st.markdown("#### Séparation entraînement / inférence (branches)")
    b1, b2, b3 = st.columns(3)
    b1.metric("GOLD_APP_INPUT (inférence)", f"{app_input_rows:,}", delta=f"`{app_input_path.name}`")
    b2.metric("GOLD_IA_LABELLED (entraînement)", f"{ia_labelled_rows:,}", delta=f"`{ia_labelled_path.name}`")
    b3.metric("GOLD_APP_PREDICTIONS (dernier run)", f"{latest_pred_rows:,}", delta=latest_pred_label)
    st.caption("Lecture métier: App input (sans label) -> prédictions ; IA labelled -> train/val/test.")
    st.divider()
    st.caption("API & Dependencies")
    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    api_v1 = f"{api_base}{settings.api_v1_prefix}"

    try:
        _ = requests.get(f"{api_base}/health", timeout=2)
        api_ok = True
    except Exception:
        api_ok = False
    if not api_ok:
        st.info(
            "**API non démarrée.** Pour activer /health et /metrics : "
            "onglet **Pilotage** -> bouton **Lancer API E2**. "
            "Gardez ce terminal ouvert (l’API tourne dans un autre)."
        )

    st.write("Endpoints clés:")
    st.code(
        "\n".join(
            [
                f"{api_base}/health",
                f"{api_base}/metrics",
                f"{api_v1}/ai/predict",
                f"{api_v1}/ai/dataset",
            ]
        ),
        language="text",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Vérifie que l'API répond et affiche le JSON de santé (version, status).")
        if st.button("Tester /health"):
            try:
                resp = requests.get(f"{api_base}/health", timeout=5)
                st.code(resp.text, language="json")
            except requests.exceptions.ConnectionError:
                st.warning("Connexion refusée. Démarrez l’API (Pilotage → Lancer API E2).")
            except Exception as exc:
                st.error(str(exc)[:200])

    with col_b:
        st.caption("Récupère les métriques Prometheus de l'API (requêtes, latence, etc.).")
        if st.button("Afficher /metrics"):
            try:
                resp = requests.get(f"{api_base}/metrics", timeout=5)
                st.code(resp.text[-2000:], language="text")
            except requests.exceptions.ConnectionError:
                st.warning("Connexion refusée. Démarrez l’API (Pilotage → Lancer API E2).")
            except Exception as exc:
                st.error(str(exc)[:200])
