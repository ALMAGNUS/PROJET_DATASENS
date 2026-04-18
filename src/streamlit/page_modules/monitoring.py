"""
Page cockpit : onglet monitoring.
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
    get_telemetry_snapshot,
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
    reset_telemetry,
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

    st.markdown("### Pilotage du modèle & insights")
    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    api_v1 = f"{api_base}{settings.api_v1_prefix}"
    prometheus_url = f"http://localhost:{settings.prometheus_port}"
    grafana_url = f"http://localhost:{settings.grafana_port}"
    uptime_kuma_url = os.getenv("UPTIME_KUMA_URL", "http://localhost:3001")

    st.subheader("Traçabilité historique datasets")
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

    st.subheader("État MLOps live")
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
        st.success(f"MLOps branché: {up_count}/{len(status_rows)} services UP.")
    else:
        st.warning(f"MLOps partiel: {up_count}/{len(status_rows)} services UP.")

    with st.expander("Contrôle scrape Prometheus (targets)", expanded=False):
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
                st.warning(f"Prometheus targets indisponible: HTTP {r.status_code}")
        except Exception as exc:
            st.warning(f"Prometheus targets indisponible: {str(exc)[:150]}")

    st.subheader("Métriques IA")
    st.caption("Déséquilibres, confiance, volume – pour piloter le modèle.")
    ia = _ia_metrics_from_parquet(PROJECT_ROOT)
    if ia is None:
        st.warning(
            "Aucune donnée Parquet (GOLD/GoldAI) disponible. Lancez le pipeline puis Fusion GoldAI."
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total articles", ia["total_articles"])
            st.caption(f"Source : {ia.get('source', '—')}")
        with c2:
            if "sentiment_score_mean" in ia:
                st.metric("Score sentiment (moy)", f"{ia['sentiment_score_mean']:.3f}")
            if "topic_confidence_mean" in ia:
                st.metric("Confiance topics (moy)", f"{ia['topic_confidence_mean']:.3f}")
        with c3:
            if "sentiment_distribution" in ia:
                sent = ia["sentiment_distribution"]
                st.caption("Distribution du sentiment")
                for label, count in list(sent.items())[:5]:
                    pct = ia.get("sentiment_pct", {}).get(label, 0)
                    st.caption(f"  • {label} : {count:,} ({pct}%)")
                lsrc = ia.get("label_source_breakdown", {})
                n_lex = int(lsrc.get("lexical", 0))
                n_ml = int(lsrc.get("ml_model", 0))
                tot_src = int(lsrc.get("total", n_lex + n_ml)) or 1
                if n_ml > 0:
                    st.caption(
                        f"Origine : règles lexicales {n_lex/tot_src*100:.0f}% · "
                        f"modèle IA {n_ml/tot_src*100:.0f}%"
                    )
                elif n_lex > 0:
                    st.caption("Origine : règles lexicales uniquement.")

        with st.expander("Détails du reclassement des sentiments (administrateurs)", expanded=False):
            alias_rows = int(ia.get("sentiment_alias_rows", 0) or 0)
            if alias_rows > 0:
                st.caption(
                    f"**{alias_rows:,}** lignes issues de sources multilingues "
                    "(labels `neutral` / `positive` / `negative`, notations 1-5…) "
                    "ont été normalisées vers les 3 classes de référence : "
                    "négatif, neutre, positif."
                )
            map_rows = ia.get("sentiment_mapping_table", [])
            if map_rows:
                st.dataframe(pd.DataFrame(map_rows), use_container_width=True, hide_index=True)
            raw_dist = ia.get("sentiment_distribution_raw", {})
            if raw_dist:
                st.caption("Labels bruts observés avant normalisation :")
                for lbl, n in list(raw_dist.items())[:10]:
                    st.caption(f"  • {lbl} : {n:,}")
            st.caption(
                "Cette table retrace la correspondance entre les libellés bruts "
                "des sources et les 3 classes métier (négatif / neutre / positif)."
            )

        with st.expander("Qualité du dataset d'entraînement", expanded=False):
            reco = ia.get("mistral_dataset_reco", "")
            if reco:
                st.caption(reco)
            splits = ia.get("ia_splits", {})
            if splits:
                st.dataframe(
                    pd.DataFrame(
                        [{"Jeu": k, "Lignes": v} for k, v in splits.items()]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            id_missing = int(ia.get("id_missing", 0))
            id_duplicates = int(ia.get("id_duplicates", 0))
            if id_missing or id_duplicates:
                st.caption(
                    f"Identifiants manquants : {id_missing:,} · "
                    f"Identifiants en doublon : {id_duplicates:,}."
                )

        with st.expander("Distribution des topics", expanded=False):
            full_topics = ia.get("topic_distribution_full") or ia.get("topic_distribution")
            if full_topics:
                total_topics = int(ia.get("topic_total_rows", sum(full_topics.values())))
                distinct = int(ia.get("topic_distinct_count", len(full_topics)))
                other_rows = int(ia.get("topic_other_rows", 0))
                topic_rows = [
                    {
                        "Topic": topic,
                        "Articles": count,
                        "%": round(count / total_topics * 100, 1) if total_topics else 0.0,
                    }
                    for topic, count in full_topics.items()
                ]
                st.caption(
                    f"{distinct} topics distincts · {total_topics:,} articles classés."
                )
                if other_rows:
                    pct_other = other_rows / total_topics * 100 if total_topics else 0.0
                    st.caption(
                        f"Le bucket **« autre »** regroupe {other_rows:,} articles "
                        f"({pct_other:.1f}%) — articles pour lesquels aucun mot-clé "
                        "métier n'a été reconnu lors du tagging."
                    )
                st.dataframe(
                    pd.DataFrame(topic_rows),
                    use_container_width=True,
                    hide_index=True,
                    height=min(420, 40 + 35 * len(topic_rows)),
                )
            else:
                st.caption("Aucune donnée topic disponible.")

        with st.expander("Principales sources de données (volume)", expanded=False):
            if "top_sources" in ia:
                src_rows = [
                    {"Source": src, "Articles": count}
                    for src, count in list(ia["top_sources"].items())[:10]
                ]
                st.dataframe(
                    pd.DataFrame(src_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("Aucune donnée source disponible.")

        st.caption(
            "Indicateurs de surveillance : équilibre des classes, "
            "couverture des topics, qualité du jeu d'entraînement."
        )

    st.divider()
    st.subheader("Chronologie")
    df_chrono = _chrono_data(PROJECT_ROOT)
    if not df_chrono.empty:
        df_chrono = df_chrono.sort_values("date")
        pivot_c = df_chrono.pivot(index="date", columns="stage", values="count").fillna(0)
        if not pivot_c.empty:
            st.line_chart(pivot_c)
    else:
        st.caption("Aucune donnée par date")

    st.divider()
    st.subheader("Stockage long terme — MongoDB GridFS")
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
                    df_latest = (
                        df_dataset.sort_values("_upload_ts", ascending=False)
                        .drop_duplicates(subset=["Nom logique"], keep="first")
                        .drop(columns=["_upload_ts"])
                    )
                    st.caption("Vue compacte datasets: dernier état par nom logique (GOLD/GoldAI/IA).")
                    st.dataframe(df_latest, use_container_width=True, hide_index=True)
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
                        st.dataframe(
                            df_mongo.drop(columns=["_upload_ts"]),
                            use_container_width=True,
                            hide_index=True,
                        )
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
    with st.expander("Prometheus & Grafana"):
        st.caption(
            f"API metrics : {api_base}/metrics · Prometheus : {prometheus_url} · Grafana : {grafana_url}"
        )

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
