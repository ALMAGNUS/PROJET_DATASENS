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
)
from src.streamlit._cockpit_helpers import (
    csv_row_count_cached as _csv_row_count_cached,
)
from src.streamlit._cockpit_helpers import (
    mongo_status as _mongo_status,
)
from src.streamlit._cockpit_helpers import (
    parquet_row_count_cached as _parquet_row_count_cached,
)
from src.streamlit.metrics import fmt_size as _fmt_size
from src.streamlit.pipeline_proof import render_last_run_proof_compact
from src.streamlit.cockpit_ux import (
    layer_sparkline_values,
    render_active_model_card,
    render_expert_breadcrumb,
    render_layer_tile,
    render_section_title,
    render_warn_monitoring_link,
    status_color,
)


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
        [sdir / "silver_articles.csv", sdir / "silver_articles.parquet", *list(sdir.rglob("*.csv")), *list(sdir.rglob("*.parquet"))]
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

    # --- Bandeau d'identité -------------------------------------------------
    if ctx.show_advanced:
        render_expert_breadcrumb("Vue d'ensemble")
        st.caption(
            "État consolidé RAW → GoldAI, volumétrie par couche et activité du dernier run."
        )
    else:
        st.markdown("### DataSens — cockpit d'analyse de sentiment multi-source")
        st.caption(
            "Collecte multi-sources → normalisation → enrichissement "
            "(topics + sentiments) → jeu d'entraînement IA."
        )
    st.divider()

    if ctx.show_advanced:
        render_active_model_card(project_root)
        render_warn_monitoring_link(ctx)
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

    render_section_title("État du pipeline")
    spark_raw = layer_sparkline_values(project_root, "RAW")
    spark_silver = layer_sparkline_values(project_root, "SILVER")
    spark_gold = layer_sparkline_values(project_root, "GOLD")
    spark_goldai = layer_sparkline_values(project_root, "GoldAI")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_layer_tile(
            "RAW",
            f"{raw_total:,}",
            "Buffer SQLite cumulé",
            spark_raw,
            color=status_color("PASS"),
        )
    with c2:
        render_layer_tile(
            "SILVER",
            f"{silver_rows:,}",
            f"Partition {silver_label}",
            spark_silver,
            color="#60a5fa",
        )
    with c3:
        render_layer_tile(
            "GOLD",
            f"{gold_rows:,}",
            f"Partition {gold_label}",
            spark_gold,
            color="#a78bfa",
        )
    with c4:
        render_layer_tile(
            "GoldAI",
            f"{goldai_rows:,}",
            f"splits IA {ia_train + ia_val + ia_test:,}",
            spark_goldai,
            color="#34d399",
        )
    st.caption(
        f"Splits IA : train {ia_train:,} · val {ia_val:,} · test {ia_test:,}. "
        "Lecture : une ligne = un article, une couche = une étape d'enrichissement."
    )
    st.divider()

    # --- Section 2 : Lineage de la donnée (SQLite -> Parquet -> GoldAI -> Mongo) ---
    render_section_title("Lineage de la donnée")
    st.caption(
        "Chaîne de persistance multi-couche, du stockage opérationnel au stockage long terme. "
        "Quatre étapes, contrôle de cohérence end-to-end."
    )

    mongo_cache = st.session_state.get("mongo_status_cache")
    mongo_was_checked = isinstance(mongo_cache, dict)
    mongo_connected = mongo_was_checked and bool(mongo_cache.get("connected"))
    mongo_error = (mongo_cache or {}).get("error") if mongo_was_checked else None
    if mongo_connected:
        files_list = mongo_cache.get("files", []) or []
        mongo_logicals = {str(f.get("logical_name", "")) for f in files_list}
        latest_gold_logical = f"gold_articles_{gold_label}" if gold_label != "—" else None
        has_gold_daily_mongo = bool(latest_gold_logical and latest_gold_logical in mongo_logicals)
        has_goldai_merged_mongo = "goldai_merged" in mongo_logicals
        mongo_files_count = len(files_list)
        mongo_total_size = _fmt_size(int(mongo_cache.get("total_size", 0) or 0))
    else:
        has_gold_daily_mongo = False
        has_goldai_merged_mongo = False
        mongo_files_count = 0
        mongo_total_size = "—"

    j1, j2, j3, j4 = st.columns(4)
    with j1, st.container(border=True):
        st.markdown("**1. Extraction → SQLite**")
        st.caption("Buffer opérationnel des articles bruts.")
        st.metric(
            label=" ",
            value=f"{raw_total:,}",
            label_visibility="collapsed",
            help=f"Source : `{db_path}` (table `raw_data`).",
        )
    with j2, st.container(border=True):
        st.markdown("**2. SQLite → Parquet GOLD**")
        st.caption(f"Snapshot enrichi du jour ({gold_label}).")
        st.metric(
            label=" ",
            value=f"{gold_rows:,}",
            label_visibility="collapsed",
            help=f"Local : `data/gold/date={gold_label}/articles.parquet`.",
        )
    with j3, st.container(border=True):
        st.markdown("**3. Parquet → GoldAI consolidé**")
        st.caption("Stock historique dédupliqué, base ML.")
        st.metric(
            label=" ",
            value=f"{goldai_rows:,}",
            label_visibility="collapsed",
            help="Local : `data/goldai/merged_all_dates.parquet`.",
        )
    with j4, st.container(border=True):
        st.markdown("**4. Sauvegarde MongoDB**")
        st.caption("Stockage long terme (GridFS).")
        if mongo_connected:
            st.metric(
                label=" ",
                value=f"{mongo_files_count:,} fichiers",
                label_visibility="collapsed",
                help=f"Volume total : {mongo_total_size}",
            )
        elif mongo_was_checked:
            st.metric(
                label=" ",
                value="hors ligne",
                label_visibility="collapsed",
            )
            st.code("docker compose up -d mongodb", language="powershell")
            b1, b2 = st.columns(2)
            if b1.button("Réessayer", key="overview_check_mongo_retry", use_container_width=True):
                with st.spinner("Connexion MongoDB..."):
                    st.session_state.mongo_status_cache = _mongo_status(project_root)
                st.rerun()
            if b2.button("Copier commande Docker", key="overview_copy_docker", use_container_width=True):
                st.session_state["clipboard_hint"] = "docker compose up -d mongodb"
                st.toast("Commande affichée ci-dessus — copiez depuis le bloc code.")
        else:
            st.metric(
                label=" ",
                value="non vérifié",
                label_visibility="collapsed",
            )
            if st.button("Vérifier MongoDB", key="overview_check_mongo", use_container_width=True):
                with st.spinner("Connexion MongoDB..."):
                    st.session_state.mongo_status_cache = _mongo_status(project_root)
                st.rerun()

    if mongo_connected:
        chain_ok = (
            raw_total > 0
            and gold_rows > 0
            and goldai_rows > 0
            and has_gold_daily_mongo
            and has_goldai_merged_mongo
        )
        if chain_ok:
            st.success(
                f"Chaîne de persistance cohérente : SQLite ({raw_total:,}) → "
                f"GOLD {gold_label} ({gold_rows:,}) → "
                f"GoldAI ({goldai_rows:,}) → GridFS (snapshot + consolidé archivés)."
            )
        else:
            missing = []
            if raw_total == 0:
                missing.append("SQLite vide")
            if gold_rows == 0:
                missing.append(f"GOLD {gold_label} absent")
            if goldai_rows == 0:
                missing.append("GoldAI consolidé absent")
            if not has_gold_daily_mongo:
                missing.append(f"backup GridFS `gold_articles_{gold_label}` manquant")
            if not has_goldai_merged_mongo:
                missing.append("backup GridFS `goldai_merged` manquant")
            st.warning("Chaîne de persistance incomplète : " + " · ".join(missing))
    elif mongo_was_checked:
        st.error(
            "MongoDB hors ligne — la sauvegarde long terme ne peut pas être validée pour l'instant."
        )
        if mongo_error:
            short_err = str(mongo_error).split(":")[0][:80]
            st.caption(f"Détail : {short_err}…")
        with st.expander("Comment relancer MongoDB ?", expanded=True):
            st.markdown(
                """
                MongoDB est déployé via Docker. Si Docker Desktop tourne mais que le conteneur est arrêté :

                ```powershell
                docker compose up -d mongodb
                ```

                Si Docker Desktop lui-même est éteint, le démarrer puis relancer la commande ci-dessus.
                Une fois Mongo en ligne, cliquez **Réessayer** dans la 4e carte.
                """
            )
    else:
        st.caption(
            "Étapes 1 à 3 lues en local. Cliquez **Vérifier MongoDB** dans la 4e carte "
            "pour valider la chaîne complète."
        )
    st.divider()

    # --- Section 3 : Activité du dernier run --------------------------------
    render_last_run_proof_compact(ctx)
    st.divider()

    # --- Expander : Santé technique (fermé par défaut) ---------------------
    with st.expander("Santé technique (API, branches App/IA)", expanded=False):
        api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
        api_v1 = f"{api_base}{settings.api_v1_prefix}"
        api_ok = ctx.backend_ok

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
