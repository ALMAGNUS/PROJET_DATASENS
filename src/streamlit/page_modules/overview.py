"""
Page cockpit : onglet Vue d'ensemble.

Refonte UX : 3 sections uniquement
  1. Bandeau court (une ligne d'identité + statut du run)
  2. État du pipeline : 4 tuiles, une par couche (RAW / SILVER / GOLD / GoldAI)
  3. Activité du dernier run : preuve d'enrichissement compacte
  Expander fermé : Santé technique (API, branches App/IA)

Le flow "Sources -> RAW -> ... -> Copie IA" a été retiré (redondant avec la
sidebar et l'onglet Pipeline). Les tests /health et /metrics vivent dans
l'onglet Pilotage pour l'action et ici pour la simple lecture de santé.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import requests
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    csv_row_count_cached as _csv_row_count_cached,
    parquet_row_count_cached as _parquet_row_count_cached,
)
from src.streamlit.pipeline_proof import render_last_run_proof_compact


def _resolve_db_path(project_root: Path) -> Path:
    db_candidate = os.getenv("DB_PATH")
    if db_candidate and Path(db_candidate).exists():
        return Path(db_candidate)
    default_db = Path.home() / "datasens_project" / "datasens.db"
    return default_db if default_db.exists() else project_root / "datasens.db"


def _count_raw_sqlite(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute("SELECT COUNT(*) FROM raw_data").fetchone()
            return int(row[0]) if row else 0
        finally:
            conn.close()
    except Exception:
        return 0


def _latest_silver(silver_dir: Path) -> tuple[int, str]:
    if not silver_dir.exists():
        return 0, "—"
    silver_dirs = sorted(
        [d for d in silver_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name.replace("date=", "").replace("v_", ""),
        reverse=True,
    )
    if not silver_dirs:
        return 0, "—"
    sdir = silver_dirs[0]
    label = sdir.name.replace("date=", "").replace("v_", "")
    cands = (
        [sdir / "silver_articles.csv", sdir / "silver_articles.parquet"]
        + list(sdir.rglob("*.csv"))
        + list(sdir.rglob("*.parquet"))
    )
    sfile = next((p for p in cands if p.exists()), None)
    if sfile is None:
        return 0, label
    if sfile.suffix.lower() == ".parquet":
        return _parquet_row_count_cached(str(sfile)), label
    return _csv_row_count_cached(str(sfile)), label


def _latest_gold(gold_dir: Path) -> tuple[int, str]:
    if not gold_dir.exists():
        return 0, "—"
    gold_dates = sorted(
        [d.name.replace("date=", "") for d in gold_dir.iterdir() if d.is_dir() and d.name.startswith("date=")],
        reverse=True,
    )
    if not gold_dates:
        return 0, "—"
    label = gold_dates[0]
    gfile = gold_dir / f"date={label}" / "articles.parquet"
    if not gfile.exists():
        return 0, label
    return _parquet_row_count_cached(str(gfile)), label


def render(ctx: PageContext) -> None:
    project_root = ctx.project_root
    settings = ctx.settings
    silver_dir = ctx.silver_dir
    gold_dir = ctx.gold_dir
    goldai_dir = ctx.goldai_dir
    ia_dir = ctx.ia_dir

    # --- Bandeau d'identité (1 ligne) --------------------------------------
    st.markdown("### DataSens — cockpit d'analyse de sentiment multi-source")
    st.caption(
        "Collecte multi-sources → normalisation → enrichissement "
        "(topics + sentiments) → jeu d'entraînement IA."
    )
    st.divider()

    # --- Section 1 : État du pipeline (4 tuiles, 1 par couche) -------------
    db_path = _resolve_db_path(project_root)
    raw_total = _count_raw_sqlite(db_path)
    silver_rows, silver_label = _latest_silver(silver_dir)
    gold_rows, gold_label = _latest_gold(gold_dir)

    goldai_path = goldai_dir / "merged_all_dates.parquet"
    goldai_rows = _parquet_row_count_cached(str(goldai_path)) if goldai_path.exists() else 0

    ia_train = _parquet_row_count_cached(str(ia_dir / "train.parquet")) if (ia_dir / "train.parquet").exists() else 0
    ia_val = _parquet_row_count_cached(str(ia_dir / "val.parquet")) if (ia_dir / "val.parquet").exists() else 0
    ia_test = _parquet_row_count_cached(str(ia_dir / "test.parquet")) if (ia_dir / "test.parquet").exists() else 0

    st.markdown("#### État du pipeline")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RAW (buffer SQLite)", f"{raw_total:,}")
    c2.metric("SILVER (dernière partition)", f"{silver_rows:,}", delta=silver_label)
    c3.metric("GOLD (partition du jour)", f"{gold_rows:,}", delta=gold_label)
    c4.metric(
        "GoldAI (stock consolidé)",
        f"{goldai_rows:,}",
        delta=f"splits : {ia_train + ia_val + ia_test:,}",
    )
    st.caption(
        f"Splits IA : train {ia_train:,} · val {ia_val:,} · test {ia_test:,}. "
        "Lecture : une ligne = un article, une couche = une étape d'enrichissement."
    )
    st.divider()

    # --- Section 2 : Activité du dernier run -------------------------------
    render_last_run_proof_compact(ctx)
    st.divider()

    # --- Expander : Santé technique (fermé par défaut) ---------------------
    with st.expander("Santé technique (API, branches App/IA)", expanded=False):
        # --- API E2 --------------------------------------------------------
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"
        try:
            requests.get(f"{api_base}/health", timeout=2)
            api_ok = True
        except Exception:
            api_ok = False

        api_col, mongo_col = st.columns(2)
        if api_ok:
            api_col.success(f"API E2 : en ligne · {api_base}")
        else:
            api_col.warning(
                "API E2 : hors ligne. Démarrer via l'onglet **Pilotage → Lancer API E2**."
            )
        # Statut Mongo uniquement informatif : déjà surveillé en profondeur
        # dans le panel Monitoring, on évite le doublon ici.
        mongo_col.caption("Mongo/lineage : voir l'onglet **Monitoring** pour le détail.")

        if api_ok:
            ba, bb = st.columns(2)
            if ba.button("Tester /health"):
                try:
                    resp = requests.get(f"{api_base}/health", timeout=5)
                    st.code(resp.text, language="json")
                except Exception as exc:
                    st.error(str(exc)[:200])
            if bb.button("Afficher /metrics (extrait)"):
                try:
                    resp = requests.get(f"{api_base}/metrics", timeout=5)
                    st.code(resp.text[-1500:], language="text")
                except Exception as exc:
                    st.error(str(exc)[:200])
            st.caption("Endpoints principaux :")
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

        st.divider()

        # --- Branches App / IA --------------------------------------------
        app_input_path = goldai_dir / "app" / "gold_app_input.parquet"
        ia_labelled_path = ia_dir / "gold_ia_labelled.parquet"
        preds_root = goldai_dir / "predictions"
        app_input_rows = _parquet_row_count_cached(str(app_input_path)) if app_input_path.exists() else 0
        ia_labelled_rows = _parquet_row_count_cached(str(ia_labelled_path)) if ia_labelled_path.exists() else 0
        pred_candidates = (
            sorted(preds_root.glob("date=*/run=*/predictions.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
            if preds_root.exists()
            else []
        )
        latest_pred = pred_candidates[0] if pred_candidates else None
        latest_pred_rows = _parquet_row_count_cached(str(latest_pred)) if latest_pred and latest_pred.exists() else 0
        latest_pred_label = (
            f"{latest_pred.parent.parent.name.replace('date=', '')} · {latest_pred.parent.name.replace('run=', '')}"
            if latest_pred
            else "—"
        )

        st.markdown("**Branches App vs IA** — séparation des datasets d'inférence et d'entraînement.")
        b1, b2, b3 = st.columns(3)
        b1.metric("APP_INPUT (inférence, sans label)", f"{app_input_rows:,}", delta=app_input_path.name)
        b2.metric("IA_LABELLED (entraînement)", f"{ia_labelled_rows:,}", delta=ia_labelled_path.name)
        b3.metric("PREDICTIONS (dernier run)", f"{latest_pred_rows:,}", delta=latest_pred_label)
        st.caption(
            "App input (texte brut) → modèle → prédictions ; IA labelled → train/val/test pour fine-tuning."
        )
