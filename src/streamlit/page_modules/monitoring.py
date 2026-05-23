"""
Page cockpit : onglet monitoring.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    get_telemetry_snapshot,
    reset_telemetry,
)
from src.streamlit._cockpit_helpers import (
    mongo_get_file_bytes as _mongo_get_file_bytes,
)
from src.streamlit._cockpit_helpers import (
    mongo_read_parquet_preview as _mongo_read_parquet_preview,
)
from src.streamlit._cockpit_helpers import (
    mongo_status as _mongo_status,
)
from src.streamlit._cockpit_helpers import (
    parquet_row_count_cached as _parquet_row_count_cached,
)
from src.streamlit._cockpit_helpers import (
    read_parquet_cached as _read_parquet_cached,
)
from src.streamlit._cockpit_helpers import (
    run_command as _run_command,
)
from src.streamlit.metrics import (
    chrono_data as _chrono_data,
)
from src.streamlit.metrics import (
    fmt_size as _fmt_size,
)
from src.streamlit.metrics import (
    scan_stage as _scan_stage,
)
from src.streamlit.metrics import (
    stage_time_range as _stage_time_range,
)
from src.streamlit.cockpit_ux import (
    lazy_panel,
    render_monitoring_date_filter,
    render_section_title,
    run_summary_history_cached,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    PROJECT_ROOT = ctx.project_root
    settings = ctx.settings
    api_base = ctx.api_base
    show_advanced = ctx.show_advanced

    st.caption("Monitoring MongoDB, traçabilité datasets et observabilité MLOps.")
    filter_date = render_monitoring_date_filter()

    if filter_date:
        render_section_title(f"Quality gate — {filter_date}")
        hist = run_summary_history_cached(str(PROJECT_ROOT), limit=40)
        day_runs = [
            h
            for h in hist
            if str(h.get("generated_at_utc", ""))[:10] == filter_date
        ]
        if day_runs:
            rows_qg = []
            for item in day_runs:
                kpi = item.get("kpis", {}) if isinstance(item, dict) else {}
                status = str(item.get("status", "—"))
                rows_qg.append(
                    {
                        "Heure UTC": str(item.get("generated_at_utc", ""))[11:19],
                        "Statut": status,
                        "Lignes chargées": int(float(kpi.get("loaded", 0) or 0)),
                        "Alertes": " · ".join(item.get("reasons", []) or []) or "—",
                    }
                )
            st.dataframe(pd.DataFrame(rows_qg), use_container_width=True, hide_index=True)
        else:
            st.warning(f"Aucun run_summary trouvé pour la date {filter_date}.")
        st.divider()

    render_section_title("Traçabilité historique datasets")
    monitor_stages = [
        ("RAW", PROJECT_ROOT / "data" / "raw", ["*.json", "*.csv"], "raw"),
        ("SILVER", PROJECT_ROOT / "data" / "silver", ["*.parquet", "*.csv"], "silver"),
        ("GOLD", PROJECT_ROOT / "data" / "gold", ["*.parquet", "*.csv"], "gold"),
        ("GoldAI", PROJECT_ROOT / "data" / "goldai", ["merged_all_dates.parquet", "*.parquet"], "goldai"),
        ("Copie IA", PROJECT_ROOT / "data" / "goldai" / "ia", ["*.parquet"], "ia"),
    ]
    trace_rows: list[dict] = []
    for label, path, patterns, key in monitor_stages:
        s = _scan_stage(path, patterns)
        dmin, dmax = _stage_time_range(path, key)
        latest_dt = (
            pd.to_datetime(float(s["latest_mtime"]), unit="s").strftime("%Y-%m-%d %H:%M")
            if s.get("latest_mtime")
            else "—"
        )
        trace_rows.append(
            {
                "Étape": label,
                "Fichiers": int(s.get("count", 0)),
                "Taille totale": _fmt_size(int(s.get("size", 0))),
                "Période couverte": f"{dmin} -> {dmax}",
                "Dernière MAJ": latest_dt,
                "Delta 24h (fichiers)": int(s.get("changed_24h_count", 0)),
                "Delta 24h (taille)": _fmt_size(int(s.get("changed_24h_size", 0))),
            }
        )
    st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
    st.caption("Preuve de couverture temporelle + variation 24h sur l'ensemble des couches.")

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    prometheus_url = f"http://localhost:{settings.prometheus_port}"
    grafana_url = f"http://localhost:{settings.grafana_port}"
    uptime_kuma_url = os.getenv("UPTIME_KUMA_URL", "http://localhost:3001")

    render_section_title("État MLOps live")
    st.caption("Vérification en direct des briques observabilité (API, Prometheus, Grafana, Uptime Kuma).")

    def _check_url(url: str, timeout: int = 3) -> tuple[str, str]:
        try:
            r = requests.get(url, timeout=timeout)
            if 200 <= r.status_code < 400:
                return ("UP", f"HTTP {r.status_code}")
            return ("DOWN", f"HTTP {r.status_code}")
        except Exception as exc:
            return ("DOWN", str(exc)[:120])

    status_rows = []
    api_health_status, api_health_msg = _check_url(f"{api_base}/health")
    status_rows.append(
        {"Service": "API E2 /health", "URL": f"{api_base}/health", "Statut": api_health_status, "Détail": api_health_msg}
    )
    api_metrics_status, api_metrics_msg = _check_url(f"{api_base}/metrics")
    status_rows.append(
        {"Service": "API E2 /metrics", "URL": f"{api_base}/metrics", "Statut": api_metrics_status, "Détail": api_metrics_msg}
    )
    prom_status, prom_msg = _check_url(f"{prometheus_url}/-/ready")
    status_rows.append(
        {"Service": "Prometheus", "URL": f"{prometheus_url}/-/ready", "Statut": prom_status, "Détail": prom_msg}
    )
    graf_status, graf_msg = _check_url(f"{grafana_url}/api/health")
    status_rows.append(
        {"Service": "Grafana", "URL": f"{grafana_url}/api/health", "Statut": graf_status, "Détail": graf_msg}
    )
    kuma_status, kuma_msg = _check_url(uptime_kuma_url)
    status_rows.append(
        {"Service": "Uptime Kuma", "URL": uptime_kuma_url, "Statut": kuma_status, "Détail": kuma_msg}
    )

    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    up_count = sum(1 for row in status_rows if row["Statut"] == "UP")
    if up_count == len(status_rows):
        st.success(f"MLOps opérationnel : {up_count}/{len(status_rows)} services UP.")
    else:
        st.warning(f"MLOps partiel : {up_count}/{len(status_rows)} services UP.")

    if show_advanced:
        with st.expander("Administration et diagnostic technique", expanded=False):
            st.markdown("**Contrôle scrape Prometheus (targets)**")
            try:
                r = requests.get(f"{prometheus_url}/api/v1/targets", timeout=4)
                if r.status_code == 200:
                    payload = r.json().get("data", {}).get("activeTargets", [])
                    rows = []
                    for t in payload:
                        labels = t.get("labels", {}) or {}
                        rows.append(
                            {
                                "job": labels.get("job", "n/a"),
                                "instance": labels.get("instance", "n/a"),
                                "health": t.get("health", "unknown"),
                                "last_error": (t.get("lastError") or "")[:120],
                            }
                        )
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Aucune target active remontée par Prometheus.")
                else:
                    st.warning(f"Prometheus targets indisponibles: HTTP {r.status_code}")
            except Exception as exc:
                st.warning(f"Prometheus targets indisponibles: {str(exc)[:150]}")

            st.markdown("**Liens techniques Prometheus / Grafana**")
            st.caption(
                f"API metrics : {api_base}/metrics · Prometheus : {prometheus_url} · Grafana : {grafana_url}"
            )
    else:
        st.caption("Détails techniques masqués (mode Expert requis).")

    st.divider()
    render_section_title("Chronologie")
    df_chrono = _chrono_data(PROJECT_ROOT)
    if not df_chrono.empty:
        df_chrono = df_chrono.sort_values("date")
        pivot_c = df_chrono.pivot(index="date", columns="stage", values="count").fillna(0)
        if not pivot_c.empty:
            st.line_chart(pivot_c)
    else:
        st.caption("Aucune donnée par date")

    st.divider()
    render_section_title("Stockage long terme — MongoDB GridFS")
    st.caption(
        "MongoDB stocke les Parquet GOLD et GoldAI en sauvegarde permanente. "
        "Vérifiez ici que les backups sont bien effectués."
    )

    if "mongo_status_cache" not in st.session_state:
        st.session_state.mongo_status_cache = None

    col_mongo1, col_mongo2 = st.columns([1, 1])
    with col_mongo1:
        if st.button("Vérifier MongoDB", use_container_width=True):
            with st.spinner("Connexion MongoDB..."):
                st.session_state.mongo_status_cache = _mongo_status(PROJECT_ROOT)
    with col_mongo2:
        if st.button("Backup Parquet → MongoDB", use_container_width=True,
                     help="Sauvegarde GOLD + GoldAI dans GridFS. Docker MongoDB doit être démarré."):
            _run_command(
                "backup MongoDB",
                [sys.executable, "scripts/backup_parquet_to_mongo.py"],
                extra_env={"MONGO_STORE_PARQUET": "true"},
            )

    mongo = st.session_state.mongo_status_cache
    if mongo is not None:
        if mongo["connected"]:
            st.success(
                f"MongoDB connecté · DB: `{mongo['db_name']}` · Bucket: `{mongo['bucket']}` · "
                f"{len(mongo['files'])} fichiers · {_fmt_size(mongo['total_size'])}"
            )
            if mongo["files"]:
                df_mongo = pd.DataFrame(mongo["files"])
                df_mongo = df_mongo.rename(columns={
                    "filename": "Fichier", "logical_name": "Nom logique",
                    "partition_date": "Date partition", "stored_at": "Stocké le",
                    "upload_date": "Upload Mongo",
                    "size_bytes": "Taille", "sha256": "SHA256",
                })
                df_mongo["Taille"] = df_mongo["Taille"].apply(_fmt_size)
                if "Upload Mongo" in df_mongo.columns:
                    ts = pd.to_datetime(df_mongo["Upload Mongo"], errors="coerce")
                    df_mongo = df_mongo.assign(_upload_ts=ts)
                    logical = df_mongo["Nom logique"].astype("string")
                    is_model_artifact = logical.str.startswith("model_")
                    df_dataset = df_mongo[~is_model_artifact].copy()
                    is_gold_daily = logical.str.startswith("gold_articles_")
                    has_legacy_gold = bool((logical == "gold_articles").any())
                    gold_daily_count = int(is_gold_daily.sum())
                    gold_daily_dates = pd.to_datetime(
                        df_mongo.loc[is_gold_daily, "Date partition"],
                        errors="coerce",
                    ).dropna()
                    latest_backup = df_mongo["_upload_ts"].max()
                    c_m1, c_m2, c_m3 = st.columns(3)
                    c_m1.metric("Snapshots GOLD quotidiens", f"{gold_daily_count:,}")
                    if not gold_daily_dates.empty:
                        c_m2.metric(
                            "Période GOLD couverte",
                            f"{gold_daily_dates.min().date()} → {gold_daily_dates.max().date()}",
                        )
                    else:
                        c_m2.metric("Période GOLD couverte", "—")
                    c_m3.metric(
                        "Dernier backup Mongo",
                        latest_backup.strftime("%Y-%m-%d %H:%M") if pd.notna(latest_backup) else "—",
                    )
                    if has_legacy_gold:
                        st.caption("Note: entrée legacy `gold_articles` détectée (ancien format, remplacé par `gold_articles_YYYY-MM-DD`).")

                    st.markdown("**Trace de persistance SQLite -> Parquet -> GridFS**")
                    st.caption(
                        "Chaîne de persistance en 4 étapes, de la collecte temps réel au stockage long terme."
                    )

                    def _resolve_db_path_lineage() -> Path:
                        db_candidate = os.getenv("DB_PATH")
                        if db_candidate and Path(db_candidate).exists():
                            return Path(db_candidate)
                        default_db = Path.home() / "datasens_project" / "datasens.db"
                        return default_db if default_db.exists() else PROJECT_ROOT / "datasens.db"

                    def _count_raw_sqlite_lineage(db_path: Path) -> int:
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

                    db_path_j = _resolve_db_path_lineage()
                    raw_total_j = _count_raw_sqlite_lineage(db_path_j)
                    latest_gold_date_j = (
                        gold_daily_dates.max().date().isoformat()
                        if not gold_daily_dates.empty
                        else "—"
                    )
                    latest_gold_path_j = (
                        PROJECT_ROOT / "data" / "gold" / f"date={latest_gold_date_j}" / "articles.parquet"
                        if latest_gold_date_j != "—"
                        else None
                    )
                    latest_gold_rows_j = (
                        _parquet_row_count_cached(str(latest_gold_path_j))
                        if latest_gold_path_j and latest_gold_path_j.exists()
                        else 0
                    )
                    goldai_merged_path_j = PROJECT_ROOT / "data" / "goldai" / "merged_all_dates.parquet"
                    goldai_merged_rows_j = (
                        _parquet_row_count_cached(str(goldai_merged_path_j))
                        if goldai_merged_path_j.exists()
                        else 0
                    )
                    mongo_logicals_j = set(df_mongo["Nom logique"].astype("string").fillna("").tolist())
                    has_gold_daily_j = (
                        f"gold_articles_{latest_gold_date_j}" in mongo_logicals_j
                        if latest_gold_date_j != "—"
                        else False
                    )
                    has_goldai_merged_j = "goldai_merged" in mongo_logicals_j
                    mongo_total_files_j = len(mongo.get("files", []))
                    mongo_total_size_j = _fmt_size(mongo.get("total_size", 0))

                    step_1, step_2 = st.columns(2)
                    with step_1, st.container(border=True):
                        st.markdown("**1. Extraction temps réel → SQLite**")
                        st.caption("15 connecteurs E1 (RSS, API, scraping). Buffer opérationnel.")
                        st.metric(
                            "Lignes en base SQLite",
                            f"{raw_total_j:,}",
                            help=f"Source: `{db_path_j}` (table `raw_data`).",
                        )
                    with step_2, st.container(border=True):
                        st.markdown("**2. SQLite → Parquet GOLD du jour**")
                        st.caption("Snapshot quotidien immuable, partitionné par date.")
                        st.metric(
                            f"GOLD {latest_gold_date_j}",
                            f"{latest_gold_rows_j:,} lignes" if latest_gold_rows_j else "0",
                            help=f"Local: `data/gold/date={latest_gold_date_j}/articles.parquet`.",
                        )

                    step_3, step_4 = st.columns(2)
                    with step_3, st.container(border=True):
                        st.markdown("**3. Parquet → GoldAI consolidé**")
                        st.caption("Fusion incrémentale dédupliquée, base ML.")
                        st.metric(
                            "GoldAI total (lignes)",
                            f"{goldai_merged_rows_j:,}" if goldai_merged_rows_j else "0",
                            help="Local: `data/goldai/merged_all_dates.parquet`.",
                        )
                    with step_4, st.container(border=True):
                        st.markdown("**4. Sauvegarde MongoDB GridFS**")
                        st.caption("Stockage long terme. Contrôle de cohérence end-to-end.")
                        st.metric(
                            "Fichiers stockés",
                            f"{mongo_total_files_j:,}",
                            help=f"Volume total: {mongo_total_size_j}",
                        )

                    integrity_ok = (
                        raw_total_j > 0
                        and latest_gold_rows_j > 0
                        and goldai_merged_rows_j > 0
                        and has_gold_daily_j
                        and has_goldai_merged_j
                    )
                    if integrity_ok:
                        st.success(
                            f"Chaîne de persistance cohérente : SQLite ({raw_total_j:,}) → "
                            f"GOLD {latest_gold_date_j} ({latest_gold_rows_j:,}) → "
                            f"GoldAI ({goldai_merged_rows_j:,}) → GridFS (snapshot + consolidé archivés)."
                        )
                    else:
                        missing = []
                        if raw_total_j == 0:
                            missing.append("SQLite vide")
                        if latest_gold_rows_j == 0:
                            missing.append(f"GOLD {latest_gold_date_j} absent")
                        if goldai_merged_rows_j == 0:
                            missing.append("GoldAI consolidé absent")
                        if not has_gold_daily_j:
                            missing.append(f"backup GridFS `gold_articles_{latest_gold_date_j}` manquant")
                        if not has_goldai_merged_j:
                            missing.append("backup GridFS `goldai_merged` manquant")
                        st.warning(
                            "Chaîne de persistance incomplète. Étapes à corriger : "
                            + " · ".join(missing)
                        )

                    df_latest = (
                        df_dataset.sort_values("_upload_ts", ascending=False)
                        .drop_duplicates(subset=["Nom logique"], keep="first")
                        .drop(columns=["_upload_ts"])
                    )
                    st.caption("Vue compacte datasets : dernier état par nom logique (GOLD/GoldAI/IA).")
                    st.dataframe(df_latest, use_container_width=True, hide_index=True)
                    st.markdown("**Inspection GridFS (lecture directe d'un fichier archivé)**")
                    preview_choices = (
                        df_dataset[["file_id", "Nom logique", "Fichier", "Taille"]]
                        .fillna("—")
                        .to_dict(orient="records")
                    )
                    if preview_choices:
                        labels = [
                            f"{row['Nom logique']} ({row['Fichier']}, {row['Taille']})"
                            for row in preview_choices
                        ]
                        selected_label = st.selectbox(
                            "Choisir un fichier Mongo à ouvrir",
                            labels,
                            key="mongo_preview_select",
                        )
                        selected_idx = labels.index(selected_label)
                        selected_row = preview_choices[selected_idx]
                        selected_file_id = str(selected_row.get("file_id", "") or "")
                        if selected_file_id:
                            col_prev, col_dl = st.columns([1, 1])
                            with col_prev:
                                if st.button("Afficher aperçu (100 lignes)", use_container_width=True, key="mongo_preview_btn"):
                                    with st.spinner("Lecture GridFS..."):
                                        df_preview = _mongo_read_parquet_preview(PROJECT_ROOT, selected_file_id, limit=100)
                                    if df_preview.empty:
                                        st.warning("Aperçu indisponible (fichier non parquet ou lecture impossible).")
                                    else:
                                        st.success(f"Aperçu chargé: {len(df_preview):,} lignes affichées.")
                                        st.dataframe(df_preview, use_container_width=True, hide_index=True)
                            with col_dl:
                                payload, meta, filename = _mongo_get_file_bytes(PROJECT_ROOT, selected_file_id)
                                if payload:
                                    logical = (meta or {}).get("logical_name", "mongo_file")
                                    download_name = f"{logical}.parquet"
                                    st.download_button(
                                        "Télécharger ce fichier",
                                        data=payload,
                                        file_name=download_name if logical else (filename or "mongo_file.parquet"),
                                        mime="application/octet-stream",
                                        use_container_width=True,
                                        key="mongo_download_btn",
                                    )
                                else:
                                    st.button("Télécharger ce fichier", disabled=True, use_container_width=True, key="mongo_download_btn_disabled")
                    with st.expander("Historique complet datasets", expanded=False):
                        st.dataframe(
                            df_dataset.drop(columns=["_upload_ts"]),
                            use_container_width=True,
                            hide_index=True,
                        )
                    with st.expander("Artefacts modèles (détail)", expanded=False):
                        df_models = df_mongo[is_model_artifact].copy()
                        if df_models.empty:
                            st.caption("Aucun artefact modèle stocké.")
                        else:
                            st.dataframe(
                                df_models.drop(columns=["_upload_ts"]),
                                use_container_width=True,
                                hide_index=True,
                            )
                    with st.expander("Historique complet GridFS (brut)", expanded=False):
                        def _load_gridfs_full() -> None:
                            st.dataframe(
                                df_mongo.drop(columns=["_upload_ts"]),
                                use_container_width=True,
                                hide_index=True,
                            )

                        lazy_panel(
                            "mongo_gridfs_full",
                            _load_gridfs_full,
                            label="Charger l'historique GridFS complet",
                        )
                    st.markdown("**Trace de persistance SQLite -> Parquet -> GridFS**")
                    def _resolve_db_path_local() -> Path:
                        db_candidate = os.getenv("DB_PATH")
                        if db_candidate and Path(db_candidate).exists():
                            return Path(db_candidate)
                        default_db = Path.home() / "datasens_project" / "datasens.db"
                        return default_db if default_db.exists() else PROJECT_ROOT / "datasens.db"

                    def _count_raw_sqlite_local(db_path: Path) -> int:
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

                    db_path = _resolve_db_path_local()
                    raw_total = _count_raw_sqlite_local(db_path)
                    latest_gold_date = (
                        gold_daily_dates.max().date().isoformat()
                        if not gold_daily_dates.empty
                        else "—"
                    )
                    latest_gold_path = (
                        PROJECT_ROOT / "data" / "gold" / f"date={latest_gold_date}" / "articles.parquet"
                        if latest_gold_date != "—"
                        else None
                    )
                    latest_gold_rows = (
                        _parquet_row_count_cached(str(latest_gold_path))
                        if latest_gold_path and latest_gold_path.exists()
                        else 0
                    )
                    goldai_merged_path = PROJECT_ROOT / "data" / "goldai" / "merged_all_dates.parquet"
                    goldai_merged_rows = (
                        _parquet_row_count_cached(str(goldai_merged_path))
                        if goldai_merged_path.exists()
                        else 0
                    )
                    mongo_logicals = set(df_mongo["Nom logique"].astype("string").fillna("").tolist())
                    has_gold_daily_mongo = (
                        f"gold_articles_{latest_gold_date}" in mongo_logicals
                        if latest_gold_date != "—"
                        else False
                    )
                    has_goldai_merged_mongo = "goldai_merged" in mongo_logicals
                    transfer_rows = [
                        {
                            "Étape": "SQLite buffer",
                            "Preuve locale": str(db_path),
                            "Volume (lignes)": f"{raw_total:,}",
                            "État": "OK" if raw_total > 0 else "VIDE",
                        },
                        {
                            "Étape": "Parquet GOLD du jour",
                            "Preuve locale": f"data/gold/date={latest_gold_date}/articles.parquet"
                            if latest_gold_date != "—"
                            else "Aucune partition GOLD",
                            "Volume (lignes)": f"{latest_gold_rows:,}" if latest_gold_rows else "0",
                            "État": "OK" if latest_gold_rows > 0 else "ABSENT",
                        },
                        {
                            "Étape": "Mongo backup GOLD du jour",
                            "Preuve Mongo": f"gold_articles_{latest_gold_date}" if latest_gold_date != "—" else "—",
                            "Volume (lignes)": "n/a",
                            "État": "OK" if has_gold_daily_mongo else "NON SAUVEGARDÉ",
                        },
                        {
                            "Étape": "Parquet GoldAI consolidé",
                            "Preuve locale": "data/goldai/merged_all_dates.parquet",
                            "Volume (lignes)": f"{goldai_merged_rows:,}" if goldai_merged_rows else "0",
                            "État": "OK" if goldai_merged_rows > 0 else "ABSENT",
                        },
                        {
                            "Étape": "Mongo backup GoldAI",
                            "Preuve Mongo": "goldai_merged",
                            "Volume (lignes)": "n/a",
                            "État": "OK" if has_goldai_merged_mongo else "NON SAUVEGARDÉ",
                        },
                    ]
                    st.dataframe(pd.DataFrame(transfer_rows), use_container_width=True, hide_index=True)
                    st.caption(
                        "Chaîne de persistance complète: stockage opérationnel SQLite -> "
                        "Parquet métiers -> sauvegarde GridFS MongoDB."
                    )
                    st.markdown("**Comparaison Parquet local vs sauvegarde GridFS**")
                    if latest_gold_date != "—" and latest_gold_path and latest_gold_path.exists():
                        mongo_gold_logical = f"gold_articles_{latest_gold_date}"
                        mongo_gold_row = (
                            df_dataset[df_dataset["Nom logique"] == mongo_gold_logical].head(1)
                            if "Nom logique" in df_dataset.columns
                            else pd.DataFrame()
                        )
                        if not mongo_gold_row.empty:
                            mongo_gold_file_id = str(mongo_gold_row.iloc[0].get("file_id", "") or "")
                            local_preview = _read_parquet_cached(
                                str(latest_gold_path),
                                ("id", "title", "source", "collected_at", "sentiment"),
                            ).head(20)
                            mongo_preview = (
                                _mongo_read_parquet_preview(PROJECT_ROOT, mongo_gold_file_id, limit=20)
                                if mongo_gold_file_id
                                else pd.DataFrame()
                            )
                            if not mongo_preview.empty:
                                keep_cols = [c for c in ["id", "title", "source", "collected_at", "sentiment"] if c in mongo_preview.columns]
                                if keep_cols:
                                    mongo_preview = mongo_preview[keep_cols].copy()
                            st.caption(f"GOLD local (`data/gold/date={latest_gold_date}/articles.parquet`) — 20 lignes")
                            st.dataframe(local_preview, use_container_width=True, hide_index=True, height=320)
                            st.caption(f"MongoDB GridFS (`{mongo_gold_logical}`) — 20 lignes")
                            if mongo_preview.empty:
                                st.warning("Impossible de lire l'aperçu Mongo pour ce fichier.")
                            else:
                                st.dataframe(mongo_preview, use_container_width=True, hide_index=True, height=320)
                            if not local_preview.empty and not mongo_preview.empty and "id" in local_preview.columns and "id" in mongo_preview.columns:
                                local_ids = set(local_preview["id"].astype("string").fillna("").tolist())
                                mongo_ids = set(mongo_preview["id"].astype("string").fillna("").tolist())
                                overlap = len(local_ids.intersection(mongo_ids))
                                st.caption(
                                    f"Contrôle rapide (échantillon 20 lignes): {overlap}/"
                                    f"{max(len(local_ids), 1)} IDs communs entre local et Mongo."
                                )
                        else:
                            st.info(
                                f"Aucune sauvegarde Mongo trouvée pour `{mongo_gold_logical}`. "
                                "Lancez d'abord le backup Parquet -> MongoDB."
                            )
                    else:
                        st.info("Aucune partition GOLD du jour détectée pour la comparaison côte à côte.")
                else:
                    st.dataframe(df_mongo, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun fichier dans GridFS. Lancez un backup.")
        else:
            st.warning(
                f"MongoDB non disponible : `{mongo['error']}`\n\n"
                "Pour démarrer MongoDB : `docker-compose up -d mongodb` ou via Docker Desktop."
            )
    else:
        st.caption("Cliquez sur **Vérifier MongoDB** pour tester la connexion.")

    st.divider()
    with st.expander("Détail technique — activité de session (télémétrie)", expanded=False):
        st.caption(
            "Comptage interne des clics et des commandes lancées depuis ce navigateur. "
            "Réservé au débogage ; la lecture métier se fait dans **Vue d'ensemble** et **Pipeline**."
        )
        snap = get_telemetry_snapshot()
        c_age, c_runs, c_err, c_avg = st.columns(4)
        age = snap["session_age_s"]
        h, rem = divmod(age, 3600)
        m, s = divmod(rem, 60)
        c_age.metric("Session", f"{h:02d}:{m:02d}:{s:02d}")
        c_runs.metric(
            "Commandes lancées",
            f"{snap['total_runs']:,}",
            delta=f"ok={snap['success_runs']} / ko={snap['failure_runs']}",
        )
        c_err.metric("Erreurs cockpit", f"{snap['errors']:,}")
        c_avg.metric("Durée moyenne", f"{snap['avg_run_duration_s']:.2f} s")

        col_clicks, col_runs = st.columns(2)
        with col_clicks:
            st.markdown("**Clics par action**")
            clicks = snap.get("clicks") or {}
            if clicks:
                df_clicks = (
                    pd.DataFrame(
                        [{"action": k, "clics": v} for k, v in clicks.items()]
                    )
                    .sort_values("clics", ascending=False)
                    .reset_index(drop=True)
                )
                st.dataframe(df_clicks, use_container_width=True, hide_index=True)
            else:
                st.caption("Aucun clic d'action enregistré dans cette session.")
        with col_runs:
            st.markdown("**Derniers runs**")
            runs = snap.get("recent_runs") or []
            if runs:
                df_runs = pd.DataFrame(runs)
                df_runs["status"] = df_runs["ok"].map({True: "OK", False: "KO"})
                df_runs = df_runs[["label", "duration_s", "status"]]
                st.dataframe(df_runs, use_container_width=True, hide_index=True)
            else:
                st.caption("Aucun run déclenché dans cette session.")

        if st.button("Réinitialiser la télémétrie cockpit", key="reset_telemetry"):
            reset_telemetry()
            st.success("Télémétrie réinitialisée.")
            st.rerun()
