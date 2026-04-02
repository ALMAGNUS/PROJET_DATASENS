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
try:
    import pyarrow.parquet as pq
except Exception:
    pq = None

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
# Phase 4 (à venir) : découper app.py en sous-modules src/streamlit/pages/*.py
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


def _inject_css() -> None:
    st.markdown(
        """
    <style>
    :root {
      --ds-bg-0: #0a0f1f;
      --ds-bg-1: #111a33;
      --ds-card: rgba(20, 28, 52, 0.78);
      --ds-border: rgba(116, 149, 255, 0.28);
      --ds-text-soft: #b8c8ff;
      --ds-accent: #74a3ff;
      --ds-accent-2: #9c7bff;
    }
    [data-testid="stAppViewContainer"] {
      background:
        radial-gradient(circle at 15% 12%, rgba(76, 110, 245, 0.25), transparent 30%),
        radial-gradient(circle at 85% 8%, rgba(156, 123, 255, 0.22), transparent 32%),
        linear-gradient(180deg, var(--ds-bg-0) 0%, var(--ds-bg-1) 100%);
    }
    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, rgba(10, 16, 33, 0.95) 0%, rgba(16, 25, 49, 0.92) 100%);
      border-right: 1px solid rgba(116, 149, 255, 0.2);
    }
    .ds-hero { background: linear-gradient(135deg, #1f2f63 0%, #2b3f89 55%, #4a3ea5 100%); padding: 1.5rem; border-radius: 14px; margin-bottom: 1.2rem; border: 1px solid rgba(143, 168, 255, 0.35); box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35); }
    .ds-hero h3 { color: #e8eaf6; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .ds-hero p { color: #c5cae9; margin: 0; font-size: 0.9rem; }
    .ds-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 0.3rem; margin: 1rem 0; font-size: 0.85rem; }
    .ds-flow span { color: #90caf9; }
    .ds-flow .arrow { color: #64b5f6; }
    .ds-card { background: var(--ds-card); border: 1px solid var(--ds-border); border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; backdrop-filter: blur(7px); box-shadow: 0 8px 24px rgba(0,0,0,0.25); }
    .ds-card-title { color: #9dc0ff; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.3rem; }
    .ds-card-value { color: #fff; font-size: 1.1rem; }
    .ds-card-empty { color: #78909c; }
    .ds-panel-title { margin: 0.2rem 0 0.6rem 0; padding: 0.9rem 1rem; border-radius: 12px; border: 1px solid var(--ds-border); background: linear-gradient(135deg, rgba(26, 39, 76, 0.9) 0%, rgba(41, 52, 99, 0.9) 100%); color: #d6e1ff; font-weight: 700; letter-spacing: 0.2px; }
    .ds-panel-sub { color: var(--ds-text-soft); font-size: 0.88rem; margin-top: 0.2rem; font-weight: 400; }
    .ds-chip { display: inline-block; border: 1px solid rgba(138, 166, 255, 0.45); color: #c7d7ff; border-radius: 999px; padding: 0.24rem 0.7rem; margin: 0.15rem 0.3rem 0.15rem 0; font-size: 0.76rem; background: rgba(65, 84, 150, 0.28); }
    [data-testid="stMetric"] {
      background: linear-gradient(160deg, rgba(27, 37, 72, 0.78) 0%, rgba(19, 27, 56, 0.78) 100%);
      border: 1px solid rgba(126, 158, 255, 0.35);
      border-radius: 12px;
      padding: 0.45rem 0.7rem;
      box-shadow: 0 6px 16px rgba(0,0,0,0.22);
    }
    [data-testid="stMetricLabel"] p { color: #a9c3ff !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #f4f7ff !important; }
    .stButton > button {
      border: 1px solid rgba(122, 161, 255, 0.45) !important;
      color: #eaf0ff !important;
      background: linear-gradient(135deg, rgba(55, 86, 189, 0.85) 0%, rgba(91, 68, 198, 0.85) 100%) !important;
      border-radius: 11px !important;
      font-weight: 600 !important;
      box-shadow: 0 8px 18px rgba(0,0,0,0.25) !important;
    }
    .stButton > button:hover {
      transform: translateY(-1px);
      filter: brightness(1.08);
      border-color: rgba(170, 192, 255, 0.8) !important;
    }
    [data-baseweb="tab-list"] {
      gap: 0.35rem;
      background: rgba(23, 32, 64, 0.68);
      border: 1px solid rgba(109, 139, 237, 0.28);
      border-radius: 12px;
      padding: 0.3rem;
    }
    [data-baseweb="tab"] {
      border-radius: 9px !important;
      font-weight: 600;
    }
    [data-baseweb="tab"][aria-selected="true"] {
      background: linear-gradient(135deg, rgba(65, 94, 201, 0.85), rgba(126, 84, 220, 0.85)) !important;
      color: #f4f6ff !important;
    }
    [data-testid="stTabs"] [role="tabpanel"] {
      background: rgba(13, 20, 39, 0.72);
      border: 1px solid rgba(106, 138, 238, 0.24);
      border-radius: 12px;
      padding: 1rem 1rem 1.15rem 1rem;
      margin-top: 0.65rem;
      overflow: clip;
      isolation: isolate;
    }
    [data-testid="stTabs"] [role="tabpanel"] > div {
      row-gap: 0.85rem;
    }
    [data-testid="stVerticalBlock"] > div {
      row-gap: 0.65rem;
    }
    .stSlider [data-baseweb="slider"] > div > div {
      background: linear-gradient(90deg, #6f9bff, #9f7cff) !important;
    }
    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput [data-baseweb="input"] {
      background: rgba(20, 30, 59, 0.78) !important;
      border: 1px solid rgba(122, 159, 255, 0.36) !important;
      border-radius: 10px !important;
    }
    [data-testid="stExpander"] {
      border: 1px solid rgba(118, 150, 245, 0.3);
      border-radius: 12px;
      background: rgba(19, 28, 54, 0.86);
    }
    [data-testid="stDataFrame"] {
      border: 1px solid rgba(113, 144, 237, 0.3);
      border-radius: 10px;
      overflow: hidden;
    }
    .ds-compass-box {
      border: 1px solid rgba(118, 150, 245, 0.28);
      border-radius: 11px;
      background: rgba(17, 25, 48, 0.72);
      padding: 0.65rem 0.75rem;
      margin-top: 0.35rem;
      min-height: 150px;
    }
    .ds-compass-title {
      color: #c9d8ff;
      font-weight: 700;
      margin-bottom: 0.45rem;
      font-size: 0.84rem;
    }
    .ds-compass-list {
      margin: 0;
      padding-left: 1rem;
      color: #a8bdf6;
      font-size: 0.79rem;
      line-height: 1.34;
    }
    .ds-compass-list li {
      margin: 0.2rem 0;
    }
    .ds-compass-muted {
      color: #8ea2d8;
      font-size: 0.79rem;
      margin-top: 0.15rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _inject_readability_css(enabled: bool) -> None:
    """Mode accessibilité: contraste et lisibilité renforcés."""
    if not enabled:
        return
    st.markdown(
        """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
      font-size: 17px !important;
    }
    p, li, span, label, [data-testid="stMarkdownContainer"] {
      line-height: 1.55 !important;
    }
    [data-testid="stMetric"] {
      border: 2px solid rgba(173, 199, 255, 0.75) !important;
    }
    [data-baseweb="tab"] {
      font-size: 1rem !important;
      padding-top: 0.55rem !important;
      padding-bottom: 0.55rem !important;
    }
    [data-testid="stDataFrame"] {
      border: 2px solid rgba(151, 184, 255, 0.55) !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _inject_demo_css(enabled: bool) -> None:
    """Mode démo: interface allégée et focus narration."""
    if not enabled:
        return
    st.markdown(
        """
    <style>
    .stExpander { margin-bottom: 0.6rem !important; }
    [data-testid="stMetric"] { min-height: 105px; }
    [data-testid="stCaptionContainer"] p { opacity: 0.92; }
    </style>
    """,
        unsafe_allow_html=True,
    )


# _scan_stage, _fmt_size, _stage_time_range, _chrono_data, _ia_metrics_from_parquet,
# _enrich_profile, _build_enrichment_table importés depuis src/streamlit/metrics.py


@st.cache_data(show_spinner=False, ttl=60)
def _read_parquet_cached(path_str: str, columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    path = Path(path_str)
    if columns:
        selected = list(columns)
        if pq is not None:
            try:
                available = set(pq.ParquetFile(path).schema.names)
                selected = [c for c in columns if c in available]
            except Exception:
                selected = list(columns)
        if selected:
            return pd.read_parquet(path, columns=selected)
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False, ttl=60)
def _parquet_row_count_cached(path_str: str) -> int:
    path = Path(path_str)
    if not path.exists():
        return 0
    if pq is not None:
        try:
            return int(pq.ParquetFile(path).metadata.num_rows)
        except Exception:
            pass
    try:
        return int(len(pd.read_parquet(path, columns=[])))
    except Exception:
        return int(len(pd.read_parquet(path)))


@st.cache_data(show_spinner=False, ttl=60)
def _csv_row_count_cached(path_str: str) -> int:
    path = Path(path_str)
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            next(reader, None)
            return sum(1 for _ in reader)
    except Exception:
        return 0


# _chrono_data → src/streamlit/metrics.py


# _ia_metrics_from_parquet → src/streamlit/metrics.py


# _enrich_profile, _build_enrichment_table → src/streamlit/metrics.py


def _mongo_status(root: Path) -> dict:
    """Teste la connexion MongoDB et retourne le statut + liste des fichiers GridFS."""
    result: dict = {"connected": False, "error": None, "files": [], "total_size": 0, "db_name": "", "bucket": ""}
    try:
        import sys as _sys
        _sys.path.insert(0, str(root))
        _sys.path.insert(0, str(root / "src"))
        from src.config import get_settings
        settings = get_settings()
        mongo_uri = getattr(settings, "mongo_uri", "mongodb://localhost:27017")
        mongo_db = getattr(settings, "mongo_db", "datasens")
        bucket = getattr(settings, "mongo_gridfs_bucket", "parquet_fs")
        result["db_name"] = mongo_db
        result["bucket"] = bucket
        from pymongo import MongoClient
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        result["connected"] = True
        coll = client[mongo_db][f"{bucket}.files"]
        files = []
        total_size = 0
        for f in coll.find({}, {"filename": 1, "metadata": 1, "length": 1, "uploadDate": 1}).sort("uploadDate", -1):
            size = f.get("length", 0)
            total_size += size
            meta = f.get("metadata", {})
            upload_dt = f.get("uploadDate")
            files.append({
                "filename": f.get("filename", "?"),
                "logical_name": meta.get("logical_name", "—"),
                "partition_date": meta.get("partition_date", "—"),
                "stored_at": meta.get("stored_at", "—"),
                "upload_date": upload_dt.isoformat() if upload_dt else "—",
                "size_bytes": size,
                "sha256": meta.get("sha256", "")[:12] + "…" if meta.get("sha256") else "—",
            })
        result["files"] = files
        result["total_size"] = total_size
        client.close()
    except Exception as exc:
        result["error"] = str(exc)
    return result


def _ia_history(root: Path) -> pd.DataFrame:
    """Construit l'historique des snapshots GoldAI (évolution du volume de données)."""
    import json as _json
    goldai_dir = root / "data" / "goldai"
    meta_path = goldai_dir / "metadata.json"
    rows: list[dict] = []
    if meta_path.exists():
        try:
            meta = _json.loads(meta_path.read_text(encoding="utf-8"))
            dates = sorted(meta.get("dates_included", []))
            total = meta.get("total_rows", 0)
            # Simule une courbe cumulative depuis les dates connues
            step = total // max(len(dates), 1) if dates else 0
            for i, d in enumerate(dates):
                rows.append({"date": d, "lignes_cumulées": step * (i + 1)})
            if rows:
                rows[-1]["lignes_cumulées"] = total
        except Exception:
            pass
    # Scanne les partitions GOLD pour construire une courbe réelle si metadata absent
    if not rows:
        gold_dir = root / "data" / "gold"
        if gold_dir.exists():
            cumul = 0
            for d in sorted(gold_dir.iterdir()):
                if not d.is_dir() or not d.name.startswith("date="):
                    continue
                p = d / "articles.parquet"
                if not p.exists():
                    continue
                try:
                    n = len(pd.read_parquet(p))
                    cumul += n
                    rows.append({"date": d.name.replace("date=", ""), "lignes_cumulées": cumul})
                except Exception:
                    pass
    if not rows:
        return pd.DataFrame(columns=["date", "lignes_cumulées"])
    return pd.DataFrame(rows).sort_values("date")


def _latest_db_state_reports(root: Path) -> tuple[dict | None, dict | None]:
    """Retourne (dernier, précédent) rapports db_state JSON."""
    rep = root / "reports"
    files = sorted(rep.glob("db_state_*.json"))
    if not files:
        return None, None

    def _load(p: Path) -> dict | None:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    latest = _load(files[-1])
    previous = _load(files[-2]) if len(files) >= 2 else None
    return latest, previous


# _load_benchmark_results, _sentiment_benchmark_diagnosis, _active_inference_benchmark_key,
# _go_no_go_snapshot, _scan_trained_models → src/streamlit/metrics.py


def _get_active_model(root: Path) -> str | None:
    """Lit SENTIMENT_FINETUNED_MODEL_PATH depuis .env."""
    env_file = root / ".env"
    if not env_file.exists():
        return None
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("SENTIMENT_FINETUNED_MODEL_PATH="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                return val if val else None
    except Exception:
        pass
    return None


def _activate_model(root: Path, model_path: str) -> bool:
    """Écrit SENTIMENT_FINETUNED_MODEL_PATH dans .env."""
    env_file = root / ".env"
    key = "SENTIMENT_FINETUNED_MODEL_PATH"
    try:
        lines: list[str] = []
        if env_file.exists():
            lines = env_file.read_text(encoding="utf-8").splitlines()
        new_line = f"{key}={model_path}"
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(key + "=") or line.startswith(f"# {key}"):
                lines[i] = new_line
                updated = True
                break
        if not updated:
            lines.append(new_line)
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


def _launch_api_in_new_window() -> None:
    """Lance l'API E2 dans une nouvelle fenêtre (ne bloque pas le Cockpit)."""
    bat = PROJECT_ROOT / "_launch_api.bat"
    if bat.exists():
        subprocess.Popen(
            ["cmd", "/c", "start", "API E2", str(bat)],
            cwd=str(PROJECT_ROOT),
        )
        st.success("API E2 lancée dans une nouvelle fenêtre.")
    else:
        cmd = [sys.executable, "run_e2_api.py"]
        subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        st.success("API E2 lancée dans une nouvelle fenêtre.")


def _run_command(label: str, command: list[str], extra_env: dict | None = None) -> None:
    st.write(f"Commande: `{' '.join(command)}`")
    out, err = "", None
    with st.spinner(f"Exécution: {label}"):
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            if extra_env:
                env.update({k: str(v) for k, v in extra_env.items() if v is not None})
            proc = subprocess.run(
                command,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=1800,
            )
            out = (proc.stdout or "").strip()
            if len(out) > 15000:
                out = "... (début tronqué)\n\n" + out[-15000:]
            err = (proc.stderr or "").strip() if proc.returncode != 0 else None
            if err and len(err) > 3000:
                err = err[-3000:]
        except subprocess.TimeoutExpired:
            out = ""
            err = None
            st.warning("Timeout: commande trop longue")

        # Persister le rapport pour qu'il reste après rechargement Streamlit
        if "last_command_report" not in st.session_state:
            st.session_state.last_command_report = {}
        st.session_state.last_command_report = {
            "label": label,
            "out": out or "OK",
            "err": err,
            "command": " ".join(command),
        }


def _render_last_report(panel_key: str) -> None:
    """Affiche le dernier rapport d'exécution (persiste après rerun)."""
    report = st.session_state.get("last_command_report")
    if not report:
        return
    with st.expander("📋 Rapport d'exécution (cliquez pour afficher)", expanded=True):
        st.text_area(
            "Sortie",
            value=report.get("out", "OK"),
            height=350,
            disabled=True,
            label_visibility="collapsed",
            key=f"last_report_output_{panel_key}",
        )
        if report.get("err"):
            st.error(report.get("err", "Erreur inconnue"))


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title="DataSens Cockpit", layout="wide")
    ux_mode = "Standard"
    show_compass = True
    data_scope = "Historique complet"

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
            ["Standard", "Lecture facile", "Mode démo"],
            index=0,
            key="ux_mode_select",
            help="Lecture facile: contraste renforcé. Mode démo: parcours simplifié en 5 écrans.",
        )
        show_compass = st.checkbox(
            "Afficher la boussole cockpit",
            value=True,
            key="ux_show_compass",
            help="Repérage rapide des panneaux selon votre besoin.",
        )
        data_scope = st.selectbox(
            "Périmètre visualisation données",
            ["Historique complet", "Date sélectionnée"],
            index=0,
            key="ux_data_scope",
            help="Historique complet: charge toutes les partitions disponibles dans les panels de visualisation.",
        )
        compass_body = (
            """
            <ul class="ds-compass-list">
              <li>🏠 Vue d'ensemble: état global du système</li>
              <li>🔁 Pipeline & Fusion: Gold/GoldAI, doublons, ajouts</li>
              <li>⚙️ Pilotage: actions run (collecte, fusion, API)</li>
              <li>🎯 Modèles & Sélection: benchmark, fine-tuning, GO/NO-GO</li>
              <li>📊 Monitoring: MLOps live, Prometheus/Grafana/Kuma</li>
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
    history_mode = data_scope == "Historique complet"

    raw_dir = PROJECT_ROOT / "data" / "raw"
    silver_dir = PROJECT_ROOT / "data" / "silver"
    gold_dir = PROJECT_ROOT / "data" / "gold"
    goldai_dir = PROJECT_ROOT / "data" / "goldai"
    ia_dir = goldai_dir / "ia"

    tab_demo, tab_overview, tab_pipeline, tab_flux, tab_pilotage, tab_ia, tab_modeles, tab_monitoring = st.tabs(
        ["🎬 Démo guidée", "🏠 Vue d'ensemble", "🔁 Pipeline & Fusion", "🧬 Flux & Visualisation", "⚙️ Pilotage", "🤖 IA", "🎯 Modèles & Sélection", "📊 Monitoring"]
    )

    with tab_demo:
        st.subheader("Parcours démo (6 panneaux)")
        st.caption("Vue opérable du flux data/IA: ingestion, fusion, scoring et observabilité.")

        st.markdown(
            """
            1. **Vue d'ensemble**: état système, volumétrie, disponibilité API, signaux de santé.
            2. **Pipeline & Fusion**: delta journalier GOLD -> GoldAI, overlap, déduplication, stock net.
            3. **Flux & Visualisation**: lineage SOURCE -> RAW -> SILVER -> GOLD avec points de contrôle.
            4. **Pilotage**: commandes run, supervision buffer/long terme, actions opérationnelles.
            5. **Modèles & Sélection**: benchmark, trade-off qualité/latence, lecture GO/NO-GO.
            6. **Monitoring**: statut live des briques MLOps et cohérence de la collecte.
            """
        )

        st.info(
            "Astuce usage: activez `Mode démo` dans la barre latérale pour une lecture plus fluide pendant la présentation."
        )

        with st.expander("Prise en main (6 panneaux)", expanded=True):
            st.markdown(
                """
                **Intro**  
                « Ce cockpit donne une lecture exécutable du pipeline: de l'ingestion au monitoring de prod. »

                **Écran 1 - Vue d'ensemble**  
                « On valide le socle: volumes, présence des artefacts, accessibilité API et cohérence globale. »

                **Écran 2 - Pipeline & Fusion**  
                « On lit le différentiel du jour: lignes candidates, recouvrement historique, puis résultat dédupliqué. »

                **Écran 3 - Flux & Visualisation**  
                « On explicite la transformation inter-couches et les contrôles qualité associés. »

                **Écran 4 - Pilotage**  
                « On exécute les actions clés (pipeline, fusion, copie IA) avec retour opérationnel immédiat. »

                **Écran 5 - Modèles & Sélection**  
                « On compare les modèles sur des métriques actionnables (F1, accuracy, latence) pour décider l'usage. »

                **Écran 6 - Monitoring**  
                « On clôture par la télémétrie live (API, Prometheus, Grafana, Uptime Kuma) pour valider l'exploitabilité. »
                """
            )

    with tab_overview:
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

    with tab_pipeline:
        gold_dir = PROJECT_ROOT / "data" / "gold"
        goldai_dir = PROJECT_ROOT / "data" / "goldai"
        merged_path = goldai_dir / "merged_all_dates.parquet"
        meta_path = goldai_dir / "metadata.json"

        fusion_err = st.session_state.pop("fusion_error", None)
        if fusion_err:
            st.error(f"Erreur fusion : {fusion_err}")
        fusion = st.session_state.get("fusion_success")
        if fusion:
            st.balloons()
            st.success(
                f"**Fusion réalisée.** GOLD ({fusion['date']}) → GoldAI. "
                f"Avant : **{fusion['avant']:,}** · Maintenant : **{fusion['apres']:,}** (+{fusion['ajoutes']:,})"
            )
            st.session_state.pop("fusion_success", None)

        st.markdown("### Fusion Parquet : GOLD quotidien + GoldAI")
        dates_in_goldai = []
        if meta_path.exists():
            import json

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            dates_in_goldai = meta.get("dates_included", [])
        if dates_in_goldai:
            dates_sorted = sorted(dates_in_goldai)
            st.caption(
                f"GoldAI contient {len(dates_sorted)} dates "
                f"(de {dates_sorted[0]} à {dates_sorted[-1]})."
            )
            with st.expander("Voir la liste complète des dates GoldAI", expanded=False):
                st.caption(", ".join(dates_sorted))

        gold_dates = (
            sorted(
                [
                    d.name.replace("date=", "")
                    for d in gold_dir.iterdir()
                    if d.is_dir() and d.name.startswith("date=")
                ],
                reverse=True,
            )
            if gold_dir.exists()
            else []
        )
        if gold_dates:
            selected_date = st.select_slider(
                "Date GOLD",
                options=gold_dates,
                value=gold_dates[0],
                help="Sélection directe sans menu déroulant.",
            )
        else:
            selected_date = "—"
            st.caption("Date GOLD: aucune partition disponible.")
        already_merged_selected = (
            selected_date != "—" and selected_date in set(dates_in_goldai)
        )

        df_gold = df_goldai = None
        gold_file = (
            gold_dir / f"date={selected_date}" / "articles.parquet"
            if selected_date != "—"
            else None
        )
        cols_min = tuple(["id", "fingerprint", "url", "title", "source", "collected_at", "sentiment"])
        cols_goldai = tuple(["id", "fingerprint", "url", "title", "source", "collected_at", "sentiment", "raw_data_id"])
        if gold_file and gold_file.exists():
            df_gold = _read_parquet_cached(str(gold_file), cols_min)
        if merged_path.exists():
            df_goldai = _read_parquet_cached(str(merged_path), cols_goldai)
        n_gold = _parquet_row_count_cached(str(gold_file)) if (gold_file and gold_file.exists()) else 0
        n_goldai = _parquet_row_count_cached(str(merged_path)) if merged_path.exists() else 0

        # Bloc de vérité métier: un seul périmètre (partition GOLD sélectionnée -> fusion GoldAI -> fichiers IA)
        st.markdown("#### Périmètre métier du jour (partition unique)")
        st.caption(
            "Lecture unique: `GOLD(date sélectionnée)` -> fusion dans `GoldAI` -> génération des fichiers IA. "
            "Ne pas mélanger ici avec les compteurs globaux `raw_data`."
        )
        ia_train = goldai_dir / "ia" / "train.parquet"
        ia_val = goldai_dir / "ia" / "val.parquet"
        ia_test = goldai_dir / "ia" / "test.parquet"
        ia_annot = goldai_dir / "ia" / "merged_all_dates_annotated.parquet"
        ia_labelled = goldai_dir / "ia" / "gold_ia_labelled.parquet"
        app_input = goldai_dir / "app" / "gold_app_input.parquet"
        pred_files = (
            sorted((goldai_dir / "predictions").glob("date=*/run=*/predictions.parquet"), key=lambda p: p.stat().st_mtime, reverse=True)
            if (goldai_dir / "predictions").exists()
            else []
        )
        pred_latest = pred_files[0] if pred_files else None
        n_ia_train = _parquet_row_count_cached(str(ia_train)) if ia_train.exists() else 0
        n_ia_val = _parquet_row_count_cached(str(ia_val)) if ia_val.exists() else 0
        n_ia_test = _parquet_row_count_cached(str(ia_test)) if ia_test.exists() else 0
        n_ia_annot = _parquet_row_count_cached(str(ia_annot)) if ia_annot.exists() else 0
        n_ia_labelled = _parquet_row_count_cached(str(ia_labelled)) if ia_labelled.exists() else 0
        n_app_input = _parquet_row_count_cached(str(app_input)) if app_input.exists() else 0
        n_pred_latest = _parquet_row_count_cached(str(pred_latest)) if pred_latest and pred_latest.exists() else 0

        clarity_rows = [
            {"Étape": "1) GOLD SQLite du jour", "Objet": f"data/gold/date={selected_date}/articles.parquet", "Lignes": n_gold},
            {"Étape": "2) GoldAI fusion long terme", "Objet": "data/goldai/merged_all_dates.parquet", "Lignes": n_goldai},
            {"Étape": "3) GOLD_APP_INPUT (inférence, sans label)", "Objet": "data/goldai/app/gold_app_input.parquet", "Lignes": n_app_input},
            {"Étape": "4) GOLD_IA_LABELLED (entraînement)", "Objet": "data/goldai/ia/gold_ia_labelled.parquet", "Lignes": n_ia_labelled},
            {"Étape": "5) IA annoté (compat historique)", "Objet": "data/goldai/ia/merged_all_dates_annotated.parquet", "Lignes": n_ia_annot},
            {"Étape": "6) IA split train", "Objet": "data/goldai/ia/train.parquet", "Lignes": n_ia_train},
            {"Étape": "7) IA split val", "Objet": "data/goldai/ia/val.parquet", "Lignes": n_ia_val},
            {"Étape": "8) IA split test", "Objet": "data/goldai/ia/test.parquet", "Lignes": n_ia_test},
            {
                "Étape": "9) GOLD_APP_PREDICTIONS (dernier run)",
                "Objet": (
                    str(pred_latest.relative_to(PROJECT_ROOT)).replace("\\", "/")
                    if pred_latest is not None
                    else "data/goldai/predictions/date=*/run=*/predictions.parquet"
                ),
                "Lignes": n_pred_latest,
            },
        ]
        st.dataframe(pd.DataFrame(clarity_rows), use_container_width=True, hide_index=True)
        st.code(
            "\n".join(
                [
                    f"Partition GOLD du jour: {n_gold:,} lignes",
                    f"GoldAI courant: {n_goldai:,} lignes (stock long terme, dédupliqué)",
                    f"Branche inférence: app_input={n_app_input:,} -> predictions(last)={n_pred_latest:,}",
                    f"Branche entraînement: ia_labelled={n_ia_labelled:,} -> split={n_ia_train + n_ia_val + n_ia_test:,}",
                    f"IA split total: {n_ia_train + n_ia_val + n_ia_test:,} = {n_ia_train:,} + {n_ia_val:,} + {n_ia_test:,}",
                ]
            ),
            language="text",
        )

        def _stable_keys_local(df: pd.DataFrame) -> pd.Series:
            if "id" in df.columns:
                s = df["id"]
            elif "fingerprint" in df.columns:
                s = df["fingerprint"]
            elif "url" in df.columns:
                s = df["url"]
            else:
                s = pd.Series([None] * len(df), index=df.index, dtype="object")
            s = s.astype("string").str.strip()
            return s.fillna("").replace({"<NA>": "", "nan": "", "None": ""})

        if st.button("Fusionner GoldAI", type="primary", use_container_width=True):
            with st.spinner("Fusion en cours…"):
                proc = subprocess.run(
                    [sys.executable, "scripts/merge_parquet_goldai.py"],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    timeout=600,
                )
            if proc.returncode == 0 and meta_path.exists():
                import json

                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                apres = meta.get("total_rows", n_goldai + n_gold)
                st.session_state["fusion_success"] = {
                    "avant": n_goldai,
                    "apres": apres,
                    "ajoutes": apres - n_goldai,
                    "date": selected_date or "—",
                }
            elif proc.returncode != 0:
                st.session_state["fusion_error"] = (proc.stderr or proc.stdout or "")[-500:]
            st.rerun()

        n_new, df_new = 0, None
        keys_gold = keys_goldai = pd.Series(dtype="string")
        ids = set()
        keys_gold_set = set()
        n_overlap = 0
        n_gold_missing_keys = 0
        n_goldai_missing_keys = 0
        n_gold_keys = 0
        n_goldai_keys = 0
        if (
            df_gold is not None
            and df_goldai is not None
        ):
            keys_gold = _stable_keys_local(df_gold)
            keys_goldai = _stable_keys_local(df_goldai)
            ids = set(keys_goldai[keys_goldai != ""])
            keys_gold_set = set(keys_gold[keys_gold != ""])
            n_gold_missing_keys = int((keys_gold == "").sum())
            n_goldai_missing_keys = int((keys_goldai == "").sum())
            n_gold_keys = len(keys_gold_set)
            n_goldai_keys = len(ids)
            n_overlap = len(keys_gold_set.intersection(ids))
            df_new = df_gold[(keys_gold != "") & (~keys_gold.isin(ids))]
            n_new = len(df_new)

        w1, w2, w3 = st.columns(3)
        with w1:
            st.markdown("#### 1. GOLD quotidien")
            if df_gold is not None:
                st.metric("Lignes", f"{n_gold:,}")
                st.caption("Lot source du jour à fusionner.")
            else:
                st.info("—")
        with w2:
            st.markdown("#### 2. GoldAI")
            if df_goldai is not None:
                st.metric("Lignes", f"{n_goldai:,}")
                st.caption("Stock long terme déjà fusionné.")
                if "raw_data_id" in df_goldai.columns:
                    n_null_raw_data_id = int(df_goldai["raw_data_id"].isna().sum())
                    if n_null_raw_data_id > 0:
                        st.caption(
                            f"Note: {n_null_raw_data_id:,} valeurs `raw_data_id` vides = normal "
                            "pour des lignes historiques / schémas hérités."
                        )
            else:
                st.info("—")
        with w3:
            st.markdown("#### 3. Nouveaux IDs à fusionner")
            st.metric("IDs nouveaux", f"{n_new:,}")
            if df_gold is not None and df_goldai is not None:
                st.caption(f"Doublons détectés (IDs déjà en GoldAI): {n_overlap:,}")
            if n_new == 0 and df_gold is not None and df_goldai is not None:
                if already_merged_selected:
                    st.caption("Date déjà fusionnée: +0 est normal.")
                else:
                    st.caption("Aucun ID nouveau détecté: lot 100% doublons.")
        st.markdown("#### 4. Résultat (1 + 2 + 3)")
        if df_gold is not None and df_goldai is not None:
            n_concat = n_goldai + n_gold
            n_res_keys = len(ids.union(keys_gold_set))
            n_dedup_keys = n_gold_keys - n_new
            n_added = n_new

            if already_merged_selected:
                st.caption("Date déjà intégrée dans GoldAI (simulation informative).")
            st.markdown("**Preuve du calcul (séparée par unité)**")
            st.code(
                "\n".join(
                    [
                        f"Rows bruts: {n_goldai:,} + {n_gold:,} = {n_concat:,}",
                        f"IDs stables: {n_goldai_keys:,} + {n_new:,} = {n_res_keys:,}",
                        f"Contrôle doublons IDs: {n_gold_keys:,} - {n_new:,} = {n_dedup_keys:,}",
                    ]
                ),
                language="text",
            )

            r1, r2, r3 = st.columns(3)
            r1.metric("Concat brut (1+2)", f"{n_concat:,}")
            r2.metric("Résultat après dédup (IDs)", f"{n_res_keys:,}")
            r3.metric("Lignes ajoutées nettes", f"{n_added:,}", delta=f"+{n_added:,}")
            st.caption(
                f"Clés vides ignorées dans la preuve IDs: GOLD={n_gold_missing_keys:,}, GoldAI={n_goldai_missing_keys:,}."
            )

            proof_df = pd.DataFrame(
                [
                    {"Preuve": "IDs GoldAI existants (avant)", "Valeur": n_goldai_keys},
                    {"Preuve": "IDs GOLD du jour", "Valeur": n_gold_keys},
                    {"Preuve": "Recouvrement (doublons IDs)", "Valeur": n_overlap},
                    {"Preuve": "Nouveaux IDs", "Valeur": n_new},
                    {"Preuve": "Total IDs attendus après fusion", "Valeur": n_res_keys},
                ]
            )
            st.dataframe(proof_df, use_container_width=True, hide_index=True)

            tab_new, tab_gold_prev, tab_goldai_prev = st.tabs(
                ["Nouvelles lignes (+)", "Aperçu GOLD", "Aperçu GoldAI"]
            )
            with tab_new:
                if df_new is not None and not df_new.empty:
                    cols_focus = [c for c in ["id", "title", "source", "collected_at"] if c in df_new.columns]
                    preview_new = df_new[cols_focus].copy().head(120) if cols_focus else df_new.copy().head(120)
                    if "id" in preview_new.columns:
                        preview_new["id"] = (
                            preview_new["id"]
                            .astype("string")
                            .fillna("ID_HARMONISE_MANQUANT")
                            .replace({"<NA>": "ID_HARMONISE_MANQUANT", "": "ID_HARMONISE_MANQUANT"})
                        )
                    st.success(f"{n_new:,} ligne(s) nouvelle(s) détectée(s).")
                    st.dataframe(preview_new, use_container_width=True, height=300)
                elif df_new is not None:
                    st.info("Aucune nouvelle ligne à afficher.")
                else:
                    st.info("—")
            with tab_gold_prev:
                cols_focus = [c for c in ["id", "title", "source", "collected_at"] if c in df_gold.columns]
                gold_view = df_gold[cols_focus].copy().head(220) if cols_focus else df_gold.copy().head(220)
                if not gold_view.empty:
                    key_series = _stable_keys_local(gold_view)
                    gold_view.insert(
                        0,
                        "Statut preuve",
                        key_series.apply(
                            lambda v: "NOUVEAU" if v != "" and v not in ids else "DEJA_PRESENT" if v != "" else "SANS_CLE"
                        ),
                    )
                    gold_view = gold_view.sort_values(by="Statut preuve", ascending=True)
                st.dataframe(gold_view.head(120), use_container_width=True, height=320)
            with tab_goldai_prev:
                cols_focus_goldai = [c for c in ["id", "title", "source", "collected_at", "sentiment"] if c in df_goldai.columns]
                preview_goldai = df_goldai[cols_focus_goldai].copy().head(120) if cols_focus_goldai else df_goldai.copy().head(120)
                st.dataframe(preview_goldai, use_container_width=True, height=320)
        elif df_goldai is not None:
            st.metric("Lignes", f"{n_goldai:,}")
        else:
            st.info("—")

        st.divider()
        st.markdown("### Datasets par étape")
        st.caption("RAW → SILVER → GOLD → GoldAI → Copie IA")

        def _load_df_sample(path: Path, max_rows: int = 100) -> pd.DataFrame | None:
            """Charge un DataFrame à partir d'un CSV ou Parquet, limité à max_rows."""
            if not path.exists():
                return None
            try:
                if path.suffix.lower() == ".parquet":
                    return pd.read_parquet(path).head(max_rows)
                if path.suffix.lower() == ".csv":
                    return pd.read_csv(path, nrows=max_rows, encoding="utf-8", on_bad_lines="skip")
                return None
            except Exception:
                return None

        def _load_df_full(path: Path) -> pd.DataFrame | None:
            """Charge un DataFrame complet (pour count uniquement)."""
            if not path.exists():
                return None
            try:
                if path.suffix.lower() == ".parquet":
                    return pd.read_parquet(path)
                if path.suffix.lower() == ".csv":
                    return pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
                return None
            except Exception:
                return None

        def _render_stage_block(
            title: str,
            desc: str,
            paths: list[Path],
            primary_idx: int = 0,
            exclude_zzdb: bool = False,
        ) -> None:
            """Affiche un bloc pour une étape."""
            primary = (
                paths[primary_idx] if primary_idx < len(paths) else (paths[0] if paths else None)
            )
            if not primary or not primary.exists():
                with st.expander(f"**{title}** – données absentes", expanded=True):
                    st.caption(desc)
                    st.info("Aucun fichier trouvé.")
                    return
            df_full = _load_df_full(primary)
            if df_full is None:
                with st.expander(f"**{title}** – erreur lecture", expanded=True):
                    st.caption(desc)
                    st.error(f"Impossible de lire {primary.name}")
                    return
            if exclude_zzdb and "source" in df_full.columns:
                mask = ~df_full["source"].astype(str).str.lower().str.contains("zzdb", na=False)
                df_full = df_full[mask]
            n_rows = len(df_full)
            cols = list(df_full.columns)
            if n_rows == 0 and exclude_zzdb:
                with st.expander(f"**{title}**", expanded=True):
                    st.caption(desc)
                    st.info("Aucune donnée hors sources synthétiques dans les exports.")
                return
            df_preview = df_full.head(50)
            with st.expander(f"**{title}** · {n_rows:,} lignes · {len(cols)} col.", expanded=True):
                st.caption(desc)
                st.caption(f"`{primary.relative_to(PROJECT_ROOT)}`")
                st.dataframe(df_preview, use_container_width=True, height=320)

        exports_dir = PROJECT_ROOT / "exports"
        raw_dir = PROJECT_ROOT / "data" / "raw"
        silver_dir = PROJECT_ROOT / "data" / "silver"
        gold_dir = PROJECT_ROOT / "data" / "gold"
        goldai_dir = PROJECT_ROOT / "data" / "goldai"
        ia_dir = goldai_dir / "ia"

        # Déterminer les fichiers sources par étape
        raw_paths = []
        if (exports_dir / "raw.csv").exists():
            raw_paths.append(exports_dir / "raw.csv")
        for d in sorted(raw_dir.iterdir(), reverse=True):
            if d.is_dir() and "sources" in d.name:
                for f in [d / "raw_articles.csv", d / "raw_articles.json"]:
                    if f.exists() and f.suffix == ".csv":
                        raw_paths.append(f)
                        break
                if raw_paths:
                    break

        silver_paths = []
        if (exports_dir / "silver.csv").exists():
            silver_paths.append(exports_dir / "silver.csv")
        for d in sorted(silver_dir.iterdir(), reverse=True):
            if d.is_dir():
                for f in d.rglob("*.parquet"):
                    silver_paths.append(f)
                    break
            if silver_paths:
                break

        gold_paths = []
        if (exports_dir / "gold.parquet").exists():
            gold_paths.append(exports_dir / "gold.parquet")
        if (exports_dir / "gold.csv").exists():
            gold_paths.append(exports_dir / "gold.csv")
        for d in sorted(gold_dir.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("date="):
                p = d / "articles.parquet"
                if p.exists():
                    gold_paths.append(p)
                    break

        _render_stage_block(
            "1. RAW",
            "Sources brutes (RSS, agrégateurs).",
            raw_paths or [exports_dir / "raw.csv"],
            exclude_zzdb=True,
        )
        _render_stage_block(
            "2. SILVER",
            "Nettoyage, fusion, topics.",
            silver_paths or [exports_dir / "silver.csv"],
            exclude_zzdb=True,
        )
        _render_stage_block(
            "3. GOLD",
            "Parquet quotidien, sentiment IA.",
            gold_paths or [goldai_dir / "merged_all_dates.parquet"],
        )
        _render_stage_block(
            "4. GoldAI",
            "Fusion long terme des GOLD.",
            [goldai_dir / "merged_all_dates.parquet"],
        )
        # Copie IA : merged_all_dates_annotated ou train comme fallback
        ia_paths = [
            ia_dir / "merged_all_dates_annotated.parquet",
            ia_dir / "train.parquet",
            ia_dir / "val.parquet",
            ia_dir / "test.parquet",
        ]
        ia_existing = [p for p in ia_paths if p.exists()]
        ia_primary = (
            ia_existing[0] if ia_existing else ia_dir / "merged_all_dates_annotated.parquet"
        )
        if not ia_primary.exists():
            with st.expander("**5. Copie IA** – données absentes", expanded=True):
                st.caption("Split train/val/test pour l'entraînement.")
                st.info("Pilotage → bouton « Créer copie IA (split) »")
        else:
            _render_stage_block(
                "5. Copie IA",
                "Split train/val/test.",
                ia_existing,
            )

        for idx, (name, path) in enumerate(
            [
                ("train", ia_dir / "train.parquet"),
                ("val", ia_dir / "val.parquet"),
                ("test", ia_dir / "test.parquet"),
            ]
        ):
            if path.exists():
                substep = chr(ord("a") + idx)
                with st.expander(f"5{substep}. {name}", expanded=False):
                    df = _load_df_full(path)
                    if df is not None:
                        st.dataframe(df.head(30), use_container_width=True, height=280)

        # ── Tableau d'enrichissement ─────────────────────────────────────────────
        st.divider()
        st.markdown("### Enrichissement étape par étape")
        st.caption(
            "Ce tableau montre comment les données s'enrichissent à chaque étape du pipeline. "
            "Les colonnes **sentiment** et **topics** sont ajoutées progressivement."
        )
        enrich_rows = _build_enrichment_table(PROJECT_ROOT)
        if enrich_rows:
            STAGE_COLS = {
                "1. RAW": [],
                "2. SILVER": ["topic_1", "topic_2", "quality_score"],
                "3. GOLD": ["sentiment", "sentiment_score"],
                "4. GoldAI": ["(fusion toutes dates)"],
                "5. Copie IA (train)": ["(split 70/15/15)"],
            }
            display_rows = []
            prev_cols: set = set()
            for p in enrich_rows:
                new_cols = set(p["cols_list"]) - prev_cols
                key_new = [c for c in ["sentiment", "topic_1", "topic_2", "sentiment_score", "quality_score"] if c in new_cols]
                display_rows.append({
                    "Étape": p["stage"],
                    "Lignes": f"{p['lignes']:,}",
                    "Colonnes": p["colonnes"],
                    "Nouvelles colonnes clés": ", ".join(key_new) if key_new else "—",
                    "Sentiment ✓": "Oui" if p["has_sentiment"] else "Non",
                    "Topics ✓": "Oui" if p["has_topic"] else "Non",
                    "Couv. sentiment": f"{p['sentiment_coverage']:.0%}" if p["has_sentiment"] else "—",
                    "Couv. topics": f"{p['topic_coverage']:.0%}" if p["has_topic"] else "—",
                })
                prev_cols = set(p["cols_list"])
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

            # Graphe des lignes par étape
            df_enrich = pd.DataFrame([{"Étape": r["Étape"], "Lignes": p["lignes"]} for r, p in zip(display_rows, enrich_rows)])
            st.bar_chart(df_enrich.set_index("Étape")["Lignes"], use_container_width=True)
        else:
            st.info("Aucune donnée disponible. Lancez d'abord le pipeline E1.")

    with tab_flux:
        _inject_css()

        # CSS additionnel pour cet onglet
        st.markdown("""
        <style>
        .flux-stage-header {
            background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
            border-left: 4px solid #42a5f5;
            border-radius: 6px;
            padding: 10px 16px;
            margin: 12px 0 8px 0;
        }
        .flux-stage-header h4 { color: #e3f2fd; margin: 0; font-size: 1rem; }
        .flux-stage-header p  { color: #90caf9; margin: 4px 0 0 0; font-size: 0.8rem; }
        .kpi-box {
            background: #1e1e2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px 16px;
            text-align: center;
        }
        .kpi-box .kpi-val { color: #fff; font-size: 1.6rem; font-weight: 700; }
        .kpi-box .kpi-lbl { color: #90caf9; font-size: 0.75rem; margin-top: 2px; }
        .kpi-box .kpi-sub { color: #a5d6a7; font-size: 0.75rem; }
        .success-banner {
            background: #1b5e20;
            border: 1px solid #43a047;
            border-radius: 6px;
            padding: 8px 16px;
            color: #c8e6c9;
            margin: 8px 0;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Header ──────────────────────────────────────────────────────────────
        st.markdown("""
        <div class="flux-stage-header">
        <h4>Pipeline DataSens : RAW → SILVER → GOLD → GoldAI → Copie IA</h4>
        <p>Chaque étape enrichit les données. Chargez une étape pour inspecter son contenu et ses métriques.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Ce pipeline réalise :**
        1. Collecte depuis les sources (RSS, CSV, bases de données) → **RAW**
        2. Nettoyage, fusion, ajout des topics IA → **SILVER**
        3. Analyse de sentiment (positif / négatif / neutre) → **GOLD**
        4. Fusion long terme, stockage MongoDB → **GoldAI**
        5. Split train / val / test pour l'entraînement → **Copie IA**
        """)

        # ── Helpers locaux ───────────────────────────────────────────────────────
        SENT_COLORS = {
            "positif":  ("#1b5e20", "#e8f5e9", "positif"),
            "positive": ("#1b5e20", "#e8f5e9", "positif"),
            "négatif":  ("#b71c1c", "#ffebee", "négatif"),
            "negatif":  ("#b71c1c", "#ffebee", "négatif"),
            "negative": ("#b71c1c", "#ffebee", "négatif"),
            "neutre":   ("#37474f", "#eceff1", "neutre"),
            "neutral":  ("#37474f", "#eceff1", "neutre"),
        }

        def _badge(label: str) -> str:
            key = str(label).strip().lower()
            color, bg, display = SENT_COLORS.get(key, ("#37474f", "#eceff1", label))
            return (
                f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:10px;'
                f'font-weight:700;font-size:0.85rem;border:1px solid {color}33;">{display}</span>'
            )

        def _kpis(df: pd.DataFrame, label: str) -> None:
            n = len(df)
            n_sent = int(df["sentiment"].notna().sum()) if "sentiment" in df.columns else 0
            n_top = int(df["topic_1"].notna().sum()) if "topic_1" in df.columns else 0
            n_src = df["source"].nunique() if "source" in df.columns else 0
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(f'<div class="kpi-box"><div class="kpi-val">{n:,}</div><div class="kpi-lbl">Lignes chargées</div><div class="kpi-sub">{label}</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="kpi-box"><div class="kpi-val">{len(df.columns)}</div><div class="kpi-lbl">Colonnes</div><div class="kpi-sub">{", ".join(list(df.columns)[:3])}…</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="kpi-box"><div class="kpi-val">{n_sent/n:.0%}" if n else "—"</div><div class="kpi-lbl">Couv. sentiment</div><div class="kpi-sub">{n_sent:,} articles</div></div>'.replace('"', '') if n else f'<div class="kpi-box"><div class="kpi-val">—</div><div class="kpi-lbl">Couv. sentiment</div></div>', unsafe_allow_html=True)
            k4.markdown(f'<div class="kpi-box"><div class="kpi-val">{n_top/n:.0%}" if n else "—"</div><div class="kpi-lbl">Couv. topics</div><div class="kpi-sub">{n_src} sources</div></div>'.replace('"', '') if n else f'<div class="kpi-box"><div class="kpi-val">—</div><div class="kpi-lbl">Couv. topics</div></div>', unsafe_allow_html=True)

        def _show_table(df: pd.DataFrame, key: str, max_rows: int = 200) -> None:
            priority = [c for c in ["title", "sentiment", "sentiment_score", "topic_1", "topic_2", "source", "published_at", "url", "content"] if c in df.columns]
            others = [c for c in df.columns if c not in priority]
            cols = priority + others
            cfg: dict = {}
            if "sentiment_score" in cols:
                cfg["sentiment_score"] = st.column_config.ProgressColumn("Score", min_value=-1.0, max_value=1.0, format="%.3f")
            if "topic_1_confidence" in cols:
                cfg["topic_1_confidence"] = st.column_config.ProgressColumn("Conf. topic", min_value=0.0, max_value=1.0, format="%.2f")
            if "url" in cols:
                cfg["url"] = st.column_config.LinkColumn("URL", display_text="Ouvrir")
            if "quality_score" in cols:
                cfg["quality_score"] = st.column_config.ProgressColumn("Qualite", min_value=0.0, max_value=1.0, format="%.2f")
            st.dataframe(df[cols].head(max_rows), use_container_width=True, height=380, column_config=cfg, hide_index=True, key=key)

        def _load_stage(paths: list[Path], suffix_priority: list[str] | None = None) -> tuple[pd.DataFrame | None, str]:
            for p in paths:
                if not p.exists():
                    continue
                try:
                    if p.suffix == ".parquet":
                        return pd.read_parquet(p), str(p.name)
                    if p.suffix == ".csv":
                        return pd.read_csv(p, encoding="utf-8", on_bad_lines="skip"), str(p.name)
                except Exception:
                    pass
            return None, ""

        def _load_stage_many(paths: list[Path]) -> tuple[pd.DataFrame | None, int]:
            frames: list[pd.DataFrame] = []
            loaded = 0
            for p in paths:
                if not p.exists():
                    continue
                try:
                    if p.suffix == ".parquet":
                        df_i = pd.read_parquet(p)
                    elif p.suffix == ".csv":
                        df_i = pd.read_csv(p, encoding="utf-8", on_bad_lines="skip")
                    else:
                        continue
                    frames.append(df_i)
                    loaded += 1
                except Exception:
                    continue
            if not frames:
                return None, 0
            try:
                return pd.concat(frames, ignore_index=True, sort=False), loaded
            except Exception:
                return frames[0], loaded

        # ── ETAPE 1 : RAW ────────────────────────────────────────────────────────
        st.markdown("""
        <div class="flux-stage-header">
        <h4>ETAPE 1 — RAW : Articles bruts collectes</h4>
        <p>Colonnes : title, content, url, source, published_at, quality_score</p>
        </div>
        """, unsafe_allow_html=True)

        raw_dir_v = PROJECT_ROOT / "data" / "raw"
        raw_candidates: list[Path] = []
        if raw_dir_v.exists():
            date_dirs = sorted([d for d in raw_dir_v.iterdir() if d.is_dir() and "sources" in d.name], reverse=True)
            date_options_raw = [d.name for d in date_dirs]
        else:
            date_dirs, date_options_raw = [], []

        cr1, cr2 = st.columns([3, 1])
        with cr1:
            sel_raw_date = st.selectbox("Date RAW", date_options_raw or ["(aucune date disponible)"], key="sel_raw_date")
        with cr2:
            load_raw = st.button(
                "Charger RAW" if not history_mode else "Charger RAW (historique)",
                type="primary",
                use_container_width=True,
                key="btn_raw",
            )

        if load_raw and date_dirs:
            if history_mode:
                paths_raw: list[Path] = []
                loaded_dates: list[str] = []
                for d in date_dirs:
                    cand = [d / "raw_articles.csv", d / "raw_articles.json"]
                    picked = next((p for p in cand if p.exists()), None)
                    if picked is not None:
                        paths_raw.append(picked)
                        loaded_dates.append(d.name)
                df_raw_loaded, n_files = _load_stage_many(paths_raw)
                meta_raw = {
                    "mode": "history",
                    "files": n_files,
                    "range": (
                        min(loaded_dates).replace("sources_", ""),
                        max(loaded_dates).replace("sources_", ""),
                    )
                    if loaded_dates
                    else ("—", "—"),
                }
                fn_raw = f"{n_files} fichier(s)"
            else:
                raw_dir_sel = next((d for d in date_dirs if d.name == sel_raw_date), None)
                paths_raw = [raw_dir_sel / "raw_articles.csv", raw_dir_sel / "raw_articles.json"] if raw_dir_sel else []
                df_raw_loaded, fn_raw = _load_stage(paths_raw)
                meta_raw = {"mode": "single"}
            if df_raw_loaded is not None:
                st.session_state["flux_raw"] = (df_raw_loaded, fn_raw, sel_raw_date, meta_raw)
            else:
                st.warning("Fichier RAW introuvable pour cette date.")

        if "flux_raw" in st.session_state:
            fr_val = st.session_state["flux_raw"]
            if isinstance(fr_val, tuple) and len(fr_val) >= 4:
                df_r, fn_r, date_r, meta_r = fr_val
            else:
                df_r, fn_r, date_r = fr_val
                meta_r = {"mode": "single"}
            if isinstance(meta_r, dict) and meta_r.get("mode") == "history":
                dmin, dmax = meta_r.get("range", ("—", "—"))
                st.markdown(
                    f'<div class="success-banner">  {len(df_r):,} articles charges depuis RAW historique '
                    f'({meta_r.get("files", 0)} fichier(s), période {dmin} → {dmax})</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="success-banner">  {len(df_r):,} articles charges depuis {fn_r} (date: {date_r})</div>',
                    unsafe_allow_html=True,
                )
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("Lignes", f"{len(df_r):,}")
            rc2.metric("Colonnes", len(df_r.columns))
            rc3.metric("Sources distinctes", df_r["source"].nunique() if "source" in df_r.columns else "—")
            try:
                date_min = str(pd.to_datetime(df_r["published_at"], errors="coerce").min())[:10] if "published_at" in df_r.columns else "—"
            except Exception:
                date_min = "—"
            rc4.metric("Date min", date_min)
            st.caption("Apercu donnees brutes (RAW) :")
            _show_table(df_r, key="tbl_raw")

        # ── ETAPE 2 : SILVER ─────────────────────────────────────────────────────
        st.markdown("""
        <div class="flux-stage-header">
        <h4>ETAPE 2 — SILVER : Nettoyage + enrichissement</h4>
        <p>Colonnes selon version : quality_score, tags/tag_scores (ancien) ou topic_1/topic_2 (actuel)</p>
        </div>
        """, unsafe_allow_html=True)

        silver_dir_v = PROJECT_ROOT / "data" / "silver"
        # Support deux formats : date=YYYY-MM-DD (nouveau) et v_YYYY-MM-DD (ancien)
        silver_dirs = sorted(
            [d for d in silver_dir_v.iterdir() if d.is_dir()] if silver_dir_v.exists() else [],
            key=lambda d: d.name.replace("date=", "").replace("v_", ""),
            reverse=True,
        )
        silver_options = [d.name for d in silver_dirs]

        if not silver_dirs:
            st.info("Aucun SILVER disponible. Lancez `python main.py` pour générer le pipeline complet.")
        elif all(not d.name.startswith("date=") for d in silver_dirs):
            st.info(
                "SILVER en ancien format (`v_YYYY-MM-DD`). "
                "Apres le prochain run de `python main.py`, il sera partitionné comme le GOLD (`date=YYYY-MM-DD`)."
            )

        cs1, cs2 = st.columns([3, 1])
        with cs1:
            sel_silver = st.selectbox("Date SILVER", silver_options or ["(aucune)"], key="sel_silver")
        with cs2:
            load_silver = st.button(
                "Charger SILVER" if not history_mode else "Charger SILVER (historique)",
                type="primary",
                use_container_width=True,
                key="btn_silver",
            )

        if load_silver and silver_dirs:
            if history_mode:
                paths_silver: list[Path] = []
                silver_period: list[str] = []
                for sd in silver_dirs:
                    candidates = (
                        [sd / "silver_articles.csv"]
                        + [sd / "silver_articles.parquet"]
                        + list(sd.rglob("*.parquet"))
                        + list(sd.rglob("*.csv"))
                    )
                    picked = next((p for p in candidates if p.exists()), None)
                    if picked is not None:
                        paths_silver.append(picked)
                        silver_period.append(sd.name.replace("date=", "").replace("v_", ""))
                df_s, n_files = _load_stage_many(paths_silver)
                if df_s is not None:
                    st.session_state["flux_silver"] = (
                        df_s,
                        f"{n_files} fichier(s)",
                        "historique",
                        {"mode": "history", "files": n_files, "range": (min(silver_period), max(silver_period)) if silver_period else ("—", "—")},
                    )
                else:
                    st.warning("Aucun fichier SILVER trouve.")
            else:
                sd = next((d for d in silver_dirs if d.name == sel_silver), None)
                if sd:
                    # Nouveau format : CSV partitionné  |  Ancien format : Parquet v_YYYY-MM-DD
                    candidates = (
                        [sd / "silver_articles.csv"]
                        + [sd / "silver_articles.parquet"]
                        + list(sd.rglob("*.parquet"))
                        + list(sd.rglob("*.csv"))
                    )
                    df_s, fn_s = _load_stage([p for p in candidates if p.exists()][:1])
                    if df_s is not None:
                        st.session_state["flux_silver"] = (df_s, fn_s, sel_silver, {"mode": "single"})
                    else:
                        st.warning("Aucun fichier SILVER trouve.")

        if "flux_silver" in st.session_state:
            fs_val = st.session_state["flux_silver"]
            if isinstance(fs_val, tuple) and len(fs_val) >= 4:
                df_s, fn_s, ver_s, meta_s = fs_val
            else:
                df_s, fn_s, ver_s = fs_val
                meta_s = {"mode": "single"}
            if isinstance(meta_s, dict) and meta_s.get("mode") == "history":
                dmin, dmax = meta_s.get("range", ("—", "—"))
                st.markdown(
                    f'<div class="success-banner">  {len(df_s):,} articles charges depuis SILVER historique '
                    f'({meta_s.get("files", 0)} fichier(s), période {dmin} → {dmax})</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="success-banner">  {len(df_s):,} articles charges depuis SILVER ({ver_s})</div>',
                    unsafe_allow_html=True,
                )

            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Lignes", f"{len(df_s):,}")
            sc2.metric("Colonnes", len(df_s.columns))

            # Gestion ancien format (tags) vs nouveau (topic_1)
            has_topic1 = "topic_1" in df_s.columns
            has_tags = "tags" in df_s.columns
            if has_topic1:
                n_top_s = int(df_s["topic_1"].notna().sum())
                sc3.metric("Avec topic_1", f"{n_top_s:,}", f"{n_top_s/len(df_s):.0%}" if len(df_s) else "—")
            elif has_tags:
                n_tagged = int((df_s["tags"].astype(str).str.strip() != "Untagged").sum())
                sc3.metric("Articles tagues", f"{n_tagged:,}", f"{n_tagged/len(df_s):.0%}" if len(df_s) else "—")
            else:
                sc3.metric("Topics", "—")

            n_qual = int(df_s["quality_score"].notna().sum()) if "quality_score" in df_s.columns else 0
            sc4.metric("Avec quality_score", f"{n_qual:,}")

            # Avertissement format ancien
            if has_tags and not has_topic1:
                st.warning(
                    "Format SILVER ancien (dec. 2025) : colonne `tags` au lieu de `topic_1/topic_2`. "
                    "Le GOLD et GoldAI utilisent le format actuel avec `topic_1/topic_2/sentiment`."
                )
                # Afficher distribution des tags
                if "tags" in df_s.columns:
                    tag_vals = df_s["tags"].astype(str).str.split("|").explode().str.strip()
                    tag_vals = tag_vals[tag_vals.str.lower() != "untagged"]
                    if len(tag_vals) > 0:
                        top_tags = tag_vals.value_counts().head(10)
                        st.caption("Distribution des tags (SILVER ancien format) :")
                        st.bar_chart(
                            pd.DataFrame({"Tag": top_tags.index, "Articles": top_tags.values}).set_index("Tag"),
                            use_container_width=True, height=180,
                        )

            st.caption(f"Apercu donnees SILVER ({ver_s}) — {len(df_s.columns)} colonnes :")
            _show_table(df_s, key="tbl_silver")

        # ── ETAPE 3 : GOLD ────────────────────────────────────────────────────────
        st.markdown("""
        <div class="flux-stage-header">
        <h4>ETAPE 3 — GOLD : Sentiment IA ajoute</h4>
        <p>Nouvelles colonnes : sentiment (positif/negatif/neutre), sentiment_score [-1, +1]</p>
        </div>
        """, unsafe_allow_html=True)

        gold_dir_v = PROJECT_ROOT / "data" / "gold"
        gold_dates_v = sorted(
            [d.name.replace("date=", "") for d in gold_dir_v.iterdir() if d.is_dir() and d.name.startswith("date=")],
            reverse=True,
        ) if gold_dir_v.exists() else []

        cg1, cg2 = st.columns([3, 1])
        with cg1:
            sel_gold_date = st.selectbox("Date GOLD", gold_dates_v or ["(aucune)"], key="sel_gold_date")
        with cg2:
            load_gold = st.button(
                "Charger GOLD" if not history_mode else "Charger GOLD (historique)",
                type="primary",
                use_container_width=True,
                key="btn_gold",
            )

        if load_gold and gold_dates_v:
            if history_mode:
                paths_gold: list[Path] = []
                for dt in gold_dates_v:
                    gold_part = gold_dir_v / f"date={dt}"
                    picked = next(
                        (p for p in [gold_part / "articles.parquet", gold_part / "articles.csv"] if p.exists()),
                        None,
                    )
                    if picked is not None:
                        paths_gold.append(picked)
                df_g, n_files = _load_stage_many(paths_gold)
                if df_g is not None:
                    st.session_state["flux_gold"] = (
                        df_g,
                        f"{n_files} fichier(s)",
                        "historique",
                        {"mode": "history", "files": n_files, "range": (min(gold_dates_v), max(gold_dates_v))},
                    )
                else:
                    st.warning("Fichier GOLD introuvable.")
            else:
                gold_part = gold_dir_v / f"date={sel_gold_date}"
                # Parquet en priorité, CSV en fallback (les deux sont maintenant générés)
                df_g, fn_g = _load_stage([
                    gold_part / "articles.parquet",
                    gold_part / "articles.csv",
                ])
                if df_g is not None:
                    st.session_state["flux_gold"] = (df_g, fn_g, sel_gold_date, {"mode": "single"})
                else:
                    st.warning("Fichier GOLD introuvable.")

        if "flux_gold" in st.session_state:
            fg_val = st.session_state["flux_gold"]
            if isinstance(fg_val, tuple) and len(fg_val) >= 4:
                df_g, fn_g, date_g, meta_g = fg_val
            else:
                df_g, fn_g, date_g = fg_val
                meta_g = {"mode": "single"}
            if isinstance(meta_g, dict) and meta_g.get("mode") == "history":
                dmin, dmax = meta_g.get("range", ("—", "—"))
                st.markdown(
                    f'<div class="success-banner">  {len(df_g):,} articles charges depuis GOLD historique '
                    f'({meta_g.get("files", 0)} partition(s), période {dmin} → {dmax})</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="success-banner">  {len(df_g):,} articles charges depuis GOLD (date={date_g})</div>',
                    unsafe_allow_html=True,
                )
            gc1, gc2, gc3, gc4 = st.columns(4)
            gc1.metric("Lignes", f"{len(df_g):,}")
            gc2.metric("Colonnes", len(df_g.columns))
            n_sent_g = int(df_g["sentiment"].notna().sum()) if "sentiment" in df_g.columns else 0
            gc3.metric("Labellises sentiment", f"{n_sent_g:,}", f"{n_sent_g/len(df_g):.0%}" if len(df_g) else "—")
            if "sentiment_score" in df_g.columns:
                gc4.metric("Score moyen", f"{df_g['sentiment_score'].mean():+.3f}")
            if "sentiment" in df_g.columns:
                sv = df_g["sentiment"].value_counts()
                sent_html = " &nbsp; ".join(_badge(str(k)) + f' <span style="color:#ccc">{v:,}</span>' for k, v in sv.items())
                st.markdown(f"Distribution : {sent_html}", unsafe_allow_html=True)
            st.caption("Apercu donnees enrichies (GOLD) :")
            _show_table(df_g, key="tbl_gold")

            # Mini graphe sentiment
            if "sentiment" in df_g.columns:
                sv2 = df_g["sentiment"].value_counts().reset_index()
                sv2.columns = ["Sentiment", "Articles"]
                st.bar_chart(sv2.set_index("Sentiment"), use_container_width=True, height=180)

        # ── ETAPE 4 : GoldAI ─────────────────────────────────────────────────────
        st.markdown("""
        <div class="flux-stage-header">
        <h4>ETAPE 4 — GoldAI : Fusion long terme (stockage MongoDB)</h4>
        <p>Toutes les dates fusionnees. Dataset complet pour l'IA et les clients.</p>
        </div>
        """, unsafe_allow_html=True)

        goldai_merged_v = PROJECT_ROOT / "data" / "goldai" / "merged_all_dates.parquet"
        cga1, cga2 = st.columns([3, 1])
        with cga1:
            st.caption(f"Fichier : `data/goldai/merged_all_dates.parquet` {'(existe)' if goldai_merged_v.exists() else '(absent — lancez Fusion GoldAI)'}")
        with cga2:
            load_goldai = st.button("Charger GoldAI", type="primary", use_container_width=True, key="btn_goldai")

        if load_goldai:
            df_ga, fn_ga = _load_stage([goldai_merged_v])
            if df_ga is not None:
                st.session_state["flux_goldai"] = (df_ga, fn_ga)
            else:
                st.warning("GoldAI absent. Allez dans Pipeline & Fusion → Fusionner GoldAI.")

        if "flux_goldai" in st.session_state:
            df_ga, fn_ga = st.session_state["flux_goldai"]
            st.markdown(f'<div class="success-banner">  {len(df_ga):,} articles charges depuis GoldAI (fusion complete)</div>', unsafe_allow_html=True)
            if "published_at" in df_ga.columns:
                try:
                    dmin = pd.to_datetime(df_ga["published_at"], errors="coerce").min()
                    dmax = pd.to_datetime(df_ga["published_at"], errors="coerce").max()
                    if pd.notna(dmin) and pd.notna(dmax):
                        st.caption(f"Période couverte (preuve): {dmin.date()} → {dmax.date()}")
                except Exception:
                    pass
            ga1, ga2, ga3, ga4 = st.columns(4)
            ga1.metric("Total articles", f"{len(df_ga):,}")
            ga2.metric("Colonnes", len(df_ga.columns))
            n_sent_ga = int(df_ga["sentiment"].notna().sum()) if "sentiment" in df_ga.columns else 0
            ga3.metric("Taux enrichissement", f"{n_sent_ga/len(df_ga):.0%}" if len(df_ga) else "—")
            n_src_ga = df_ga["source"].nunique() if "source" in df_ga.columns else 0
            ga4.metric("Sources", n_src_ga)

            # Filtres
            fga1, fga2, fga3 = st.columns(3)
            with fga1:
                f_sent = st.selectbox("Sentiment", ["Tous"] + (list(df_ga["sentiment"].dropna().unique()) if "sentiment" in df_ga.columns else []), key="f_sent_ga")
            with fga2:
                f_top = st.selectbox("Topic", ["Tous"] + (list(df_ga["topic_1"].dropna().value_counts().head(20).index) if "topic_1" in df_ga.columns else []), key="f_top_ga")
            with fga3:
                f_src = st.selectbox("Source", ["Toutes"] + (list(df_ga["source"].dropna().value_counts().head(20).index) if "source" in df_ga.columns else []), key="f_src_ga")

            df_ga_f = df_ga.copy()
            if f_sent != "Tous" and "sentiment" in df_ga_f.columns:
                df_ga_f = df_ga_f[df_ga_f["sentiment"] == f_sent]
            if f_top != "Tous" and "topic_1" in df_ga_f.columns:
                df_ga_f = df_ga_f[df_ga_f["topic_1"] == f_top]
            if f_src != "Toutes" and "source" in df_ga_f.columns:
                df_ga_f = df_ga_f[df_ga_f["source"] == f_src]

            st.caption(f"{len(df_ga_f):,} articles affiches sur {len(df_ga):,} apres filtre")
            _show_table(df_ga_f, key="tbl_goldai")

            # Distributions cote a cote
            dc1, dc2 = st.columns(2)
            with dc1:
                if "sentiment" in df_ga.columns:
                    sv_ga = df_ga["sentiment"].value_counts().reset_index()
                    sv_ga.columns = ["Sentiment", "Articles"]
                    st.caption("Repartition sentiment")
                    st.bar_chart(sv_ga.set_index("Sentiment"), use_container_width=True, height=200)
            with dc2:
                if "topic_1" in df_ga.columns:
                    tv_ga = df_ga["topic_1"].dropna().value_counts().head(12).reset_index()
                    tv_ga.columns = ["Topic", "Articles"]
                    st.caption("Top topics")
                    st.bar_chart(tv_ga.set_index("Topic"), use_container_width=True, height=200)

            # Evolution temporelle
            date_col_ga = "published_at" if "published_at" in df_ga.columns else ("date" if "date" in df_ga.columns else None)
            if date_col_ga:
                try:
                    df_time_ga = df_ga.copy()
                    df_time_ga["_d"] = pd.to_datetime(df_time_ga[date_col_ga], errors="coerce").dt.date.astype(str)
                    daily_ga = df_time_ga.dropna(subset=["_d"]).groupby("_d").size().reset_index(name="n").sort_values("_d").tail(60)
                    if len(daily_ga) > 1:
                        st.caption("Evolution du volume par jour (60 derniers jours)")
                        st.line_chart(daily_ga.set_index("_d")["n"], use_container_width=True, height=160)
                    if "sentiment" in df_time_ga.columns:
                        piv = df_time_ga.dropna(subset=["_d"]).groupby(["_d", "sentiment"]).size().unstack(fill_value=0).tail(30)
                        if not piv.empty:
                            st.caption("Evolution sentiment par jour (30 derniers jours)")
                            st.area_chart(piv, use_container_width=True, height=180)
                except Exception:
                    pass

        # ── ETAPE 5 : Copie IA ────────────────────────────────────────────────────
        st.markdown("""
        <div class="flux-stage-header">
        <h4>ETAPE 5 — Copie IA : Datasets Train / Val / Test</h4>
        <p>Split 70 / 15 / 15 — pret pour l'entrainement du modele de sentiment</p>
        </div>
        """, unsafe_allow_html=True)

        ia_dir_v = PROJECT_ROOT / "data" / "goldai" / "ia"
        cia1, cia2 = st.columns([3, 1])
        with cia1:
            sel_split = st.selectbox("Split", ["train", "val", "test"], key="sel_split_ia")
        with cia2:
            load_ia = st.button("Charger Copie IA", type="primary", use_container_width=True, key="btn_ia")

        if load_ia:
            df_ia_l, fn_ia = _load_stage([ia_dir_v / f"{sel_split}.parquet"])
            if df_ia_l is not None:
                st.session_state["flux_ia"] = (df_ia_l, fn_ia, sel_split)
            else:
                st.warning("Copie IA absente. Allez dans Pilotage → Copie IA.")

        if "flux_ia" in st.session_state:
            df_ia_l, fn_ia, split_ia = st.session_state["flux_ia"]
            st.markdown(f'<div class="success-banner">  {len(df_ia_l):,} exemples charges (split: {split_ia})</div>', unsafe_allow_html=True)
            ia1, ia2, ia3, ia4 = st.columns(4)
            ia1.metric("Exemples", f"{len(df_ia_l):,}")
            ia2.metric("Colonnes", len(df_ia_l.columns))
            n_sent_ia = int(df_ia_l["sentiment"].notna().sum()) if "sentiment" in df_ia_l.columns else 0
            ia3.metric("Labellises", f"{n_sent_ia:,}", f"{n_sent_ia/len(df_ia_l):.0%}" if len(df_ia_l) else "—")
            ia4.metric("Split", split_ia)
            if "sentiment" in df_ia_l.columns:
                sv_ia = df_ia_l["sentiment"].value_counts()
                sent_ia_html = " &nbsp; ".join(_badge(str(k)) + f' <span style="color:#ccc">{v:,}</span>' for k, v in sv_ia.items())
                st.markdown(f"Distribution : {sent_ia_html}", unsafe_allow_html=True)
            st.caption(f"Apercu dataset {split_ia} (pret pour entrainement) :")
            _show_table(df_ia_l, key="tbl_ia")

        # ── Suivi d'un article ────────────────────────────────────────────────────
        if "flux_goldai" in st.session_state:
            df_master = st.session_state["flux_goldai"][0]
            st.divider()
            st.subheader("Suivre un article — du RAW au GoldAI")
            col_s1, col_s2 = st.columns([4, 1])
            with col_s1:
                q = st.text_input("Rechercher (titre, mot-cle)", placeholder="Ex: inflation, BCE, Macron...", key="flux_search2")
            with col_s2:
                rnd = st.button("Article aleatoire", use_container_width=True, key="flux_rnd2")
            if rnd or "flux_art_idx" not in st.session_state:
                st.session_state.flux_art_idx = int(pd.Series(range(len(df_master))).sample(1).iloc[0])
            if q:
                mask2 = pd.Series([False] * len(df_master))
                for col2 in ["title", "content"]:
                    if col2 in df_master.columns:
                        mask2 |= df_master[col2].astype(str).str.contains(q, case=False, na=False)
                hits = df_master[mask2].index.tolist()
                if hits:
                    st.session_state.flux_art_idx = hits[0]
                    st.caption(f"{len(hits)} article(s) trouve(s)")
                else:
                    st.warning("Aucun article trouve.")
            row = df_master.iloc[st.session_state.flux_art_idx]
            title_v = str(row.get("title", row.get("headline", "—")) or "—")
            content_v = str(row.get("content", row.get("text", "—")) or "—")
            url_v = str(row.get("url", "—") or "—")
            pub_v = str(row.get("published_at", row.get("date", "—")) or "—")[:10]
            src_v = str(row.get("source", "—") or "—")
            sent_v = str(row.get("sentiment", "") or "")
            score_v = float(row.get("sentiment_score", 0) or 0)
            top1_v = str(row.get("topic_1", "—") or "—")
            top2_v = str(row.get("topic_2", "—") or "—")
            top1c_v = float(row.get("topic_1_confidence", 0) or 0)

            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.markdown('<div class="ds-card"><div class="ds-card-title">1. RAW</div></div>', unsafe_allow_html=True)
                st.markdown(f"**{title_v[:70]}{'…' if len(title_v)>70 else ''}**")
                st.caption(f"Source : {src_v}  |  Date : {pub_v}")
                st.text_area("Contenu brut", content_v[:250] + "…", height=110, disabled=True, key="art_raw", label_visibility="visible")
                st.progress(0.0, text="0% enrichi")
            with s2:
                st.markdown('<div class="ds-card"><div class="ds-card-title">2. SILVER</div></div>', unsafe_allow_html=True)
                st.markdown(f"**{title_v[:70]}{'…' if len(title_v)>70 else ''}**")
                if top1_v != "—":
                    st.markdown(f'<div class="ds-card" style="margin:6px 0"><div class="ds-card-title">Topic 1</div><div class="ds-card-value">{top1_v}</div></div>', unsafe_allow_html=True)
                    if top2_v != "—":
                        st.caption(f"Topic 2 : {top2_v}")
                    if top1c_v > 0:
                        st.progress(top1c_v, text=f"Confiance : {top1c_v:.0%}")
                else:
                    st.caption("Topics non disponibles")
                st.progress(0.5, text="50% enrichi")
            with s3:
                st.markdown('<div class="ds-card"><div class="ds-card-title">3. GOLD</div></div>', unsafe_allow_html=True)
                st.markdown(f"**{title_v[:70]}{'…' if len(title_v)>70 else ''}**")
                if sent_v:
                    pct_bar = int((score_v + 1) / 2 * 100)
                    bar_color = "#43a047" if score_v > 0.1 else ("#e53935" if score_v < -0.1 else "#90a4ae")
                    st.markdown(
                        f'<div class="ds-card" style="margin:6px 0">'
                        f'<div class="ds-card-title">Sentiment IA</div>'
                        f'<div style="margin:6px 0">{_badge(sent_v)}</div>'
                        f'<div style="background:#111;border-radius:4px;height:10px;"><div style="background:{bar_color};width:{pct_bar}%;height:10px;border-radius:4px;"></div></div>'
                        f'<div style="color:{bar_color};font-size:0.75rem;margin-top:3px;">Score : {score_v:+.3f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.progress(0.75, text="75% enrichi")
            with s4:
                st.markdown('<div class="ds-card"><div class="ds-card-title">4. GoldAI — Pret IA</div></div>', unsafe_allow_html=True)
                if sent_v:
                    st.markdown(
                        f'<div class="ds-card" style="margin:6px 0;border-color:#42a5f5">'
                        f'{_badge(sent_v)}'
                        f'<div style="color:#81d4fa;margin-top:6px;font-size:0.8rem;">Topic : {top1_v}</div>'
                        f'<div style="color:#81d4fa;font-size:0.8rem;">Score : {score_v:+.3f}</div>'
                        f'<div style="color:#a5d6a7;font-size:0.8rem;">Source : {src_v}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                if url_v.startswith("http"):
                    st.markdown(f"[Voir l'article original]({url_v})")
                st.progress(1.0, text="100% enrichi")

            with st.expander("Toutes les colonnes de cet article", expanded=False):
                article_d = {k: [v] for k, v in row.items() if pd.notna(v) and str(v).strip() not in ("", "nan")}
                st.dataframe(pd.DataFrame(article_d), use_container_width=True)

    with tab_pilotage:
        view_mode = st.radio(
            "Mode cockpit",
            ["Focus", "Expert"],
            horizontal=True,
            help="Focus: vue claire et guidée. Expert: détails techniques complets.",
            key="cockpit_view_mode",
        )
        show_advanced = view_mode == "Expert"

        def _resolve_db_path() -> str:
            db = os.getenv("DB_PATH")
            if db and Path(db).exists():
                return db
            default = str(Path.home() / "datasens_project" / "datasens.db")
            if Path(default).exists():
                return default
            return (
                str(PROJECT_ROOT / "datasens.db")
                if (PROJECT_ROOT / "datasens.db").exists()
                else default
            )

        db_path = _resolve_db_path()
        n_raw, n_silver, n_gold = 0, 0, 0
        if Path(db_path).exists():
            try:
                import sqlite3

                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                has_raw = cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='raw_data'"
                ).fetchone()
                conn.close()
                if has_raw:
                    from src.e1.aggregator import DataAggregator

                    agg = DataAggregator(db_path)
                    n_raw = len(agg.aggregate_raw())
                    n_silver = len(agg.aggregate_silver())
                    n_gold = len(agg.aggregate())
                    agg.close()
            except Exception:
                pass

        m1, m2, m3 = st.columns(3)
        m1.metric("RAW", f"{n_raw:,}")
        m2.metric("SILVER", f"{n_silver:,}")
        m3.metric("GOLD", f"{n_gold:,}")

        # Cockpit de lineage/transformation (pilotage opérationnel)
        try:
            lineage = LineageService(db_path=db_path, project_root=PROJECT_ROOT).get_daily_lineage()
        except Exception:
            lineage = {}

        if lineage:
            st.markdown(
                """
                <div class="ds-panel-title">
                  Cockpit lineage quotidien
                  <div class="ds-panel-sub">Traçabilité complète: collecte, transformation, enrichissement, stockage.</div>
                </div>
                <span class="ds-chip">SOURCE → RAW</span>
                <span class="ds-chip">RAW → SILVER</span>
                <span class="ds-chip">SILVER → GOLD</span>
                <span class="ds-chip">GOLD → GoldAI</span>
                """,
                unsafe_allow_html=True,
            )
            s = lineage.get("summary", {})
            f = lineage.get("formulas", {})
            l = lineage.get("layers", {})

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Avant ingestion", f"{int(s.get('before_total', 0)):,}")
            c2.metric("Collectés aujourd'hui", f"{int(s.get('collected_today', 0)):,}")
            c3.metric("Doublons", f"{int(s.get('duplicates_today', 0)):,}")
            c4.metric("Ajoutés (réels)", f"{int(s.get('added_today', 0)):,}")
            c5.metric("Après merge", f"{int(s.get('after_total', 0)):,}")

            st.caption(
                f"Formule collecte → insert: `{f.get('collection_to_insert', 'n/a')}` | "
                f"Formule stock: `{f.get('before_to_after', 'n/a')}`"
            )

            d1, d2, d3 = st.columns(3)
            d1.metric("SQLite RAW (buffer)", f"{int(l.get('raw_sqlite', 0)):,}")
            d2.metric("GoldAI (Parquet long terme)", f"{int(l.get('goldai_parquet') or 0):,}")
            mongo_files = l.get("mongo_gridfs_files")
            d3.metric("MongoDB GridFS (fichiers)", "n/a" if mongo_files is None else f"{int(mongo_files):,}")

            with st.expander("Nouvelles lignes du jour (exactes)", expanded=False):
                rows = lineage.get("new_rows_today", [])
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.caption("Aucune nouvelle ligne aujourd'hui.")

            with st.expander("Flux réel (article) : RAW → SILVER → GOLD → GoldAI", expanded=False):
                samples = lineage.get("transformed_samples_today", [])
                if not samples:
                    st.caption("Aucun échantillon de transformation disponible aujourd'hui.")
                else:
                    idx_label = [
                        f"#{r.get('id')} · {str(r.get('source', ''))} · {str(r.get('title', ''))[:60]}"
                        for r in samples
                    ]
                    pick = st.selectbox("Choisir un article ajouté aujourd'hui", idx_label, index=0)
                    chosen = samples[idx_label.index(pick)]

                    title = str(chosen.get("title", "") or "")
                    content = str(chosen.get("content", "") or "")
                    topic_1 = str(chosen.get("topic_1", "") or "")
                    topic_2 = str(chosen.get("topic_2", "") or "")
                    sent = str(chosen.get("sentiment", "") or "")
                    score = chosen.get("sentiment_score")
                    url = str(chosen.get("url", "") or "")

                    b1, b2, b3, b4 = st.columns(4)
                    with b1:
                        st.markdown("**RAW (buffer SQLite)**")
                        st.caption("Donnée brute ingérée")
                        st.write(f"ID: `{chosen.get('id')}`")
                        st.write(f"Source: `{chosen.get('source')}`")
                        st.write(f"Titre: {title[:120]}")
                        st.caption((content[:220] + "…") if len(content) > 220 else content)
                    with b2:
                        st.markdown("**SILVER**")
                        st.caption("Nettoyage + topics")
                        st.write(f"Topic 1: `{topic_1 or 'n/a'}`")
                        st.write(f"Topic 2: `{topic_2 or 'n/a'}`")
                        st.write("Transformations: normalisation texte, harmonisation schéma")
                    with b3:
                        st.markdown("**GOLD**")
                        st.caption("Ajout sentiment IA")
                        if sent:
                            st.markdown(_badge(sent), unsafe_allow_html=True)
                        st.write(f"Score sentiment: `{float(score):+.3f}`" if score is not None else "Score sentiment: `n/a`")
                        st.write("Transformations: enrichissement IA, scoring")
                    with b4:
                        st.markdown("**GoldAI (long terme)**")
                        st.caption("Fusion historique et conservation")
                        st.write(f"Article fusionné par `id={chosen.get('id')}`")
                        st.write("Règle: keep='last' sur `collected_at`")
                        if url.startswith("http"):
                            st.markdown(f"[URL source]({url})")

            with st.expander("Collecte vs ajoutés par source", expanded=False):
                src_rows = lineage.get("by_source", [])
                if src_rows:
                    st.dataframe(pd.DataFrame(src_rows), use_container_width=True, hide_index=True)
                else:
                    st.caption("Aucune donnée source.")

            with st.expander("Qualité ingestion : doublons / rejets / enrichissement", expanded=False):
                t1, t2, t3 = st.tabs(
                    ["Doublons/Non-ajoutés", "Rejets validation", "Enrichissement du jour"]
                )

                with t1:
                    dups = lineage.get("duplicates_rows_today_table", [])
                    if dups:
                        st.dataframe(pd.DataFrame(dups), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Aucun non-ajouté détecté aujourd'hui.")

                with t2:
                    rej = lineage.get("rejected_rows_today_table", [])
                    if rej:
                        st.dataframe(pd.DataFrame(rej), use_container_width=True, hide_index=True)
                        st.info(
                            "Le pipeline ne persiste pas chaque ligne rejetée individuellement. "
                            "La colonne `non_added_today` agrège doublons + rejets."
                        )
                    else:
                        st.caption("Aucune info rejet disponible.")

                with t3:
                    enr = lineage.get("enriched_rows_today_table", [])
                    if enr:
                        st.dataframe(pd.DataFrame(enr), use_container_width=True, hide_index=True)
                    else:
                        st.caption("Aucune ligne ajoutée aujourd'hui, donc pas d'enrichissement du jour.")

            with st.expander("Évolution quotidienne (40 jours)", expanded=False):
                hist = lineage.get("history_daily", [])
                if hist:
                    df_hist = pd.DataFrame(hist).sort_values("day")
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)
                    st.line_chart(
                        df_hist.set_index("day")[["collected_rows", "added_rows", "duplicates_rows"]],
                        use_container_width=True,
                    )
                else:
                    st.caption("Historique indisponible.")

            with st.expander("Diagnostic modèles sentiment (benchmark)", expanded=False):
                df_diag = _sentiment_benchmark_diagnosis(PROJECT_ROOT)
                if df_diag.empty:
                    st.caption("Aucun benchmark disponible dans docs/e2/AI_BENCHMARK_RESULTS.json")
                else:
                    st.dataframe(df_diag, use_container_width=True, hide_index=True)
                    best = df_diag.iloc[0]
                    worst = df_diag.iloc[-1]
                    st.info(
                        f"Meilleur modèle actuel: `{best['model']}` "
                        f"(F1 macro={best['f1_macro']:.3f}, acc={best['accuracy']:.3f}). "
                        f"Modèle le plus faible: `{worst['model']}` "
                        f"(F1 macro={worst['f1_macro']:.3f})."
                    )
                    st.caption(
                        "Indice stabilité classes: `f1_gap_max` (plus bas = performances plus homogènes entre neg/neu/pos)."
                    )
                    st.caption(
                        "Note nomenclature: `xlm_roberta_twitter` est la clé canonique "
                        "(ancien alias: `flaubert_multilingual`)."
                    )

        # Cockpit pilotage: buffer SQLite vs long terme GoldAI / MongoDB
        if show_advanced:
            latest_state, prev_state = _latest_db_state_reports(PROJECT_ROOT)
            if latest_state:
                st.markdown(
                    """
                    <div class="ds-panel-title">
                      Supervision buffer vs long terme
                      <div class="ds-panel-sub">SQLite journalier, Parquet long terme, MongoDB GridFS et disponibilité IA.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                raw_total = int(latest_state.get("raw_data", {}).get("total_rows", 0) or 0)
                goldai_meta = latest_state.get("goldai_metadata") or {}
                goldai_total = int(goldai_meta.get("total_rows", 0) or 0)
                delta_prev = latest_state.get("run_progress", {}).get(
                    "raw_data_delta_since_previous_report"
                )
                coh = latest_state.get("coherence_checks", {})

                p1, p2, p3, p4 = st.columns(4)
                p1.metric("Buffer SQLite (raw_data)", f"{raw_total:,}", delta=None)
                p2.metric(
                    "Long terme GoldAI",
                    f"{goldai_total:,}",
                    delta=f"{goldai_total - raw_total:+,} vs buffer",
                )
                p3.metric(
                    "Croissance depuis dernier snapshot",
                    f"{(delta_prev if isinstance(delta_prev, int) else 0):+,}",
                )
                p4.metric(
                    "Statut cohérence",
                    str(coh.get("status", "n/a")),
                    delta=None,
                )
                coh_status = str(coh.get("status", "n/a")).upper()
                coh_reasons = coh.get("reasons") or []
                if coh_status == "WARNING":
                    reason_txt = " | ".join(str(r) for r in coh_reasons) if coh_reasons else "Motif non renseigné"
                    st.warning(
                        "Incohérence détectée: "
                        f"{reason_txt}. "
                        "Interprétation: GoldAI contient un historique supérieur au buffer SQLite."
                    )
                    st.caption(
                        "Action de réalignement recommandée: "
                        "`python scripts/merge_parquet_goldai.py --force-full`"
                    )
                elif coh_status == "OK":
                    st.success("Cohérence buffer/long terme: OK.")

                with st.expander("Détail évolution collecte (par source)", expanded=False):
                    deltas = latest_state.get("run_progress", {}).get(
                        "source_deltas_since_previous_report", []
                    )
                    if deltas:
                        df_d = pd.DataFrame(deltas)
                        st.dataframe(df_d, use_container_width=True, hide_index=True)
                    else:
                        st.caption("Aucun delta source disponible (ou premier rapport).")

                with st.expander("Actions recommandées", expanded=False):
                    recos = latest_state.get("recommendations", [])
                    if recos:
                        for r in recos:
                            st.markdown(f"- {r}")
                    else:
                        st.caption("Aucune recommandation.")

                # Vue rapide MongoDB si déjà vérifié, sinon information claire
                mongo_cached = st.session_state.get("mongo_status_cache")
                if mongo_cached and mongo_cached.get("connected"):
                    st.success(
                        f"MongoDB long terme connecté: {len(mongo_cached.get('files', []))} fichiers, "
                        f"{_fmt_size(mongo_cached.get('total_size', 0))}."
                    )
                else:
                    st.info(
                        "Long terme MongoDB: cliquez sur 'Vérifier MongoDB' plus bas pour compléter "
                        "le cockpit de pilotage."
                    )

        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Pipeline E1", type="primary", use_container_width=True):
                env = {"FORCE_ZZDB_REIMPORT": "false"}
                _run_command("pipeline", [sys.executable, "main.py"], extra_env=env)
        with b2:
            if st.button("Fusion GoldAI", type="primary", use_container_width=True):
                _run_command("goldai", [sys.executable, "scripts/merge_parquet_goldai.py"])
        with b3:
            copie_ia_topics = st.checkbox(
                "Copie IA (experimental): filtrer finance+politique (peut biaiser l'entrainement)",
                value=False,
                key="copie_ia_topics",
            )
            if copie_ia_topics:
                st.warning(
                    "Mode slice metier active: utile pour test rapide, mais a eviter pour le modele principal. "
                    "Bonne pratique: entrainer global, puis filtrer au niveau des insights."
                )
            if st.button("Copie IA", type="primary", use_container_width=True):
                cmd = [sys.executable, "scripts/create_ia_copy.py"]
                if copie_ia_topics:
                    cmd += ["--topics", "finance,politique"]
                _run_command("copie IA", cmd)

        # Rapport d'exécution (affiché juste après les boutons principaux)
        _render_last_report("pilotage")

        b4, b5, _ = st.columns(3)
        with b4:
            if st.button("Lancer API E2", use_container_width=True):
                _launch_api_in_new_window()
        with b5:
            if st.button(
                "Backup MongoDB",
                use_container_width=True,
                help="Parquet vers MongoDB GridFS. Lancer start_mongo.bat avant (Docker).",
            ):
                _run_command(
                    "backup",
                    [sys.executable, "scripts/backup_parquet_to_mongo.py"],
                    extra_env={"MONGO_STORE_PARQUET": "true"},
                )

        with st.expander("Injecter un CSV (à la demande)", expanded=False):
            st.caption(
                "Le CSV parcourt le pipeline E1 complet (RAW → SILVER → GOLD). "
                "Colonnes: title, content (obligatoires), url, published_at (optionnels)"
            )
            csv_file = st.file_uploader("Fichier CSV", type=["csv"], key="inject_csv")
            source_name = st.text_input("Nom de la source", value="csv_inject", key="inject_source")
            if st.button("Injecter dans le pipeline E1"):
                if csv_file:
                    import tempfile
                    with tempfile.NamedTemporaryFile(
                        suffix=".csv", delete=False, mode="wb"
                    ) as tmp:
                        tmp.write(csv_file.getvalue())
                        tmp_path = tmp.name
                    try:
                        _run_command(
                            "inject CSV (pipeline complet)",
                            [
                                sys.executable,
                                "main.py",
                                "--inject-csv",
                                tmp_path,
                                "--source-name",
                                source_name or "csv_inject",
                            ],
                        )
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass
                else:
                    st.warning("Déposez un fichier CSV.")

        st.caption("Fine-tuning : améliore le modèle IA avec les données GoldAI")

        # Auto-suggestion du meilleur backbone basée sur le benchmark
        _bench_for_ft = _load_benchmark_results(PROJECT_ROOT)
        _best_backbone_suggestion = "sentiment_fr"
        if _bench_for_ft:
            _pretrained_only = {
                k: v for k, v in _bench_for_ft.items()
                if k != "finetuned_local" and "error" not in v
            }
            _backbone_map = {
                "bert_multilingual": "bert_multilingual",
                "sentiment_fr": "sentiment_fr",
                "xlm_roberta_twitter": "flaubert",
                "flaubert_multilingual": "flaubert",
            }
            if _pretrained_only:
                _best_bench_key = max(_pretrained_only, key=lambda k: _pretrained_only[k].get("accuracy", 0))
                _best_backbone_suggestion = _backbone_map.get(_best_bench_key, "sentiment_fr")
                _best_acc = _pretrained_only[_best_bench_key].get("accuracy", 0)
                f1_best = _pretrained_only[_best_bench_key].get("f1_macro", 0)
                st.info(
                    f"**Recommandation** : fine-tuner **{_best_bench_key}** "
                    f"(F1 macro {f1_best:.1%}). Évitez CamemBERT distil (le plus faible). "
                    f"Un bon pré-entraîné donne un meilleur fine-tuné."
                )

        ft_col1, ft_col2, ft_col3 = st.columns(3)
        with ft_col1:
            _backbone_choices = ["sentiment_fr", "bert_multilingual", "camembert", "flaubert"]
            _default_idx = _backbone_choices.index(_best_backbone_suggestion) if _best_backbone_suggestion in _backbone_choices else 0
            ft_backbone = st.selectbox(
                "Backbone à entraîner",
                _backbone_choices,
                index=_default_idx,
                format_func=lambda x: {
                    "camembert": "CamemBERT distil (léger, CPU rapide)",
                    "bert_multilingual": "BERT multilingue 5★ (nlptown) — pas CamemBERT",
                    "sentiment_fr": "sentiment_fr (RECOMMANDÉ — meilleur bench) ★",
                    "flaubert": "FlauBERT base uncased (FR)",
                }.get(x, x),
                key="ft_backbone",
                help="sentiment_fr est le meilleur pré-entraîné sur le benchmark. Fine-tuner le meilleur backbone donne le meilleur résultat final.",
            )
        with ft_col2:
            ft_mode = st.selectbox(
                "Mode",
                ["quick", "full"],
                format_func=lambda x: "Quick (1 epoch, ~3000 ex.)" if x == "quick" else "Full (3 epochs, toutes données)",
                key="ft_mode",
            )
        with ft_col3:
            ft_epochs = 1 if ft_mode == "quick" else 3
            ft_max_train = 3000 if ft_mode == "quick" else None
            ft_max_val = 800 if ft_mode == "quick" else None
            st.caption(f"Epochs: {ft_epochs}")
            if ft_max_train:
                st.caption(f"Max train: {ft_max_train} · Max val: {ft_max_val}")

        ft_topics = st.checkbox(
            "Filtrer finance + politique uniquement",
            value=False,
            key="ft_topics_filter",
            help="Entraîne sur les articles avec topic_1 ou topic_2 = finance/politique. Meilleure restitution veille.",
        )
        ft_pos_ratio = st.slider(
            "Recalibrage classe positif (train)",
            min_value=0.0,
            max_value=0.40,
            value=0.25,
            step=0.01,
            help="0 = off. Augmente la part de la classe positif dans le train via sur-échantillonnage contrôlé.",
            key="ft_target_pos_ratio",
        )
        ft_pos_mult = st.slider(
            "Limite sur-échantillonnage positif (x)",
            min_value=1.0,
            max_value=6.0,
            value=3.0,
            step=0.5,
            help="Garde-fou pour éviter de dupliquer excessivement la classe positif.",
            key="ft_pos_oversample_multiplier",
        )

        b6, b7, _ = st.columns(3)
        with b6:
            if st.button(
                "Lancer le fine-tuning",
                type="primary",
                use_container_width=True,
                help="Entraîne le backbone choisi sur train.parquet (Copie IA).",
            ):
                cmd = [
                    sys.executable,
                    "scripts/finetune_sentiment.py",
                    "--model", ft_backbone,
                    "--epochs", str(ft_epochs),
                ]
                if ft_max_train:
                    cmd += ["--max-train-samples", str(ft_max_train)]
                if ft_max_val:
                    cmd += ["--max-val-samples", str(ft_max_val)]
                if ft_topics:
                    cmd += ["--topics", "finance,politique"]
                if ft_pos_ratio > 0:
                    cmd += ["--target-pos-ratio", str(ft_pos_ratio)]
                    cmd += ["--pos-oversample-max-multiplier", str(ft_pos_mult)]
                _run_command("finetune", cmd)
        with b7:
            if st.button(
                "Évaluer modèle fine-tuné",
                use_container_width=True,
                help="Calcule accuracy/F1 sur val.parquet (modèle fine-tuné)",
            ):
                _run_command(
                    "eval", [sys.executable, "scripts/finetune_sentiment.py", "--eval-only"]
                )
        finetuned_path = getattr(settings, "sentiment_finetuned_model_path", None)
        if finetuned_path:
            st.caption(f"Modèle fine-tuné actif : `{finetuned_path}`")
        else:
            _expected_path = f"models/{ft_backbone}-sentiment-finetuned" if "ft_backbone" in dir() else "models/sentiment_fr-sentiment-finetuned"
            st.caption(
                f"Après fine-tuning, activez le modèle dans **Modèles & Sélection** "
                f"ou ajoutez dans `.env` : `SENTIMENT_FINETUNED_MODEL_PATH={_expected_path}`"
            )

        with st.expander("Paramètres & détails", expanded=False):
            force_reimport = st.checkbox("FORCE_ZZDB_REIMPORT (zzdb_csv)", value=False)
            env = {"FORCE_ZZDB_REIMPORT": "true" if force_reimport else "false"}
            if st.button("Pipeline E1 (avec params)"):
                _run_command("pipeline", [sys.executable, "main.py"], extra_env=env)
            st.caption(f"Base : {db_path}")
            if Path(db_path).exists():
                try:
                    import sqlite3

                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = []
                    for r in cur.fetchall():
                        if r[0] != "sqlite_sequence":
                            try:
                                cur.execute(f"SELECT COUNT(*) FROM [{r[0]}]")
                                tables.append((r[0], cur.fetchone()[0]))
                            except Exception:
                                pass
                    conn.close()
                    st.caption("Tables : " + ", ".join(f"{t}={c}" for t, c in tables[:8]))
                except Exception:
                    pass
            if st.button("Veille IA"):
                _run_command("veille", [sys.executable, "scripts/veille_digest.py"])
            if st.button("Benchmark IA (rapide 200 ex.)"):
                _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py", "--max-samples", "200"])
            if st.button("Benchmark IA (complet)"):
                _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])
            if st.button("Lister Parquet MongoDB"):
                _run_command("mongo", [sys.executable, "scripts/list_mongo_parquet.py"])
            st.divider()
            st.caption("Après fine-tuning, le chemin du modèle :")
            st.code("SENTIMENT_FINETUNED_MODEL_PATH=models/sentiment_fr-sentiment-finetuned")

    with tab_ia:
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

    with tab_modeles:
        st.markdown("### Modèles IA — Benchmark, Fine-tuning & Sélection")
        st.caption(
            "Ici vous comparez tous les modèles (pré-entraînés et fine-tunés sur vos données), "
            "choisissez le meilleur, et l'activez pour la production (API sentiment + Mistral)."
        )

        active_model = _get_active_model(PROJECT_ROOT)
        if active_model:
            st.success(f"Modèle actif en production : `{active_model}`")
        else:
            st.warning(
                "Aucun modèle fine-tuné activé. Le modèle par défaut (`sentiment_fr`) est utilisé. "
                "Activez un modèle fine-tuné ci-dessous pour améliorer la précision sur vos données."
            )

        # Vision claire pour l'utilisateur: entraînement (validation) vs inférence (production)
        bench_results_modeles = _load_benchmark_results(PROJECT_ROOT)
        trained_models_modeles = _scan_trained_models(PROJECT_ROOT)
        gate = _go_no_go_snapshot(active_model, bench_results_modeles, trained_models_modeles)

        st.divider()
        st.subheader("Lecture métier : entraînement vs inférence")
        st.caption(
            "Entraînement = qualité d'apprentissage interne (train/validation). "
            "Inférence = qualité réelle en production (benchmark/test + latence)."
        )
        explain_rows = [
            {
                "Étape": "Entraînement (offline)",
                "Objectif": "Apprendre le modèle",
                "Mesures clés": "eval_accuracy, eval_f1_macro, eval_f1_pos, eval_loss",
                "Source": "trainer_state.json / runs fine-tuning",
            },
            {
                "Étape": "Inférence (online)",
                "Objectif": "Prédire vite et bien pour l'utilisateur",
                "Mesures clés": "accuracy, f1_macro, f1_pos, latency_ms",
                "Source": "AI_BENCHMARK_RESULTS.json + API /ai/predict",
            },
        ]
        st.dataframe(pd.DataFrame(explain_rows), use_container_width=True, hide_index=True)

        c_train, c_inf, c_gate = st.columns(3)
        with c_train:
            st.markdown("**Entraînement (validation)**")
            st.metric("Modèle entraîné de référence", gate.get("train_model_name") or "n/a")
            tr_acc = gate.get("train_accuracy")
            tr_f1 = gate.get("train_f1_macro")
            tr_pos = gate.get("train_f1_pos")
            st.caption(
                f"Acc={float(tr_acc):.3f} | F1_macro={float(tr_f1):.3f} | F1_pos={float(tr_pos):.3f}"
                if tr_acc is not None and tr_f1 is not None and tr_pos is not None
                else "Métriques entraînement incomplètes."
            )
        with c_inf:
            st.markdown("**Inférence (production/test)**")
            st.metric("Modèle évalué en inférence", gate.get("inference_model_key") or "n/a")
            inf_acc = gate.get("inference_accuracy")
            inf_f1 = gate.get("inference_f1_macro")
            inf_pos = gate.get("inference_f1_pos")
            inf_lat = gate.get("inference_latency_ms")
            st.caption(
                f"Acc={float(inf_acc):.3f} | F1_macro={float(inf_f1):.3f} | "
                f"F1_pos={float(inf_pos):.3f} | Lat={float(inf_lat):.1f} ms"
                if inf_acc is not None and inf_f1 is not None and inf_pos is not None and inf_lat is not None
                else "Métriques inférence incomplètes."
            )
        with c_gate:
            st.markdown("**Décision Go/No-Go prod**")
            gate_status = str(gate.get("status", "NO-GO"))
            if gate_status == "GO":
                st.success("GO")
            elif gate_status == "GO avec vigilance":
                st.warning("GO avec vigilance")
            else:
                st.error("NO-GO")

        with st.expander("Règles de décision (explicites)", expanded=False):
            checks = gate.get("checks", [])
            for label, ok in checks:
                st.markdown(f"- {'✅' if ok else '❌'} {label}")

        # ── Section 0 : Évolution des datasets ─────────────────────────────────────
        st.divider()
        st.subheader("0. Évolution du volume de données")
        st.caption(
            "Plus vous collectez, plus le modèle s'améliore. "
            "Cette courbe montre la croissance cumulative des articles labellisés dans GoldAI."
        )

        df_hist = _ia_history(PROJECT_ROOT)
        if not df_hist.empty:
            col_h1, col_h2, col_h3 = st.columns(3)
            ia_dir_path = PROJECT_ROOT / "data" / "goldai" / "ia"
            n_train = len(pd.read_parquet(ia_dir_path / "train.parquet")) if (ia_dir_path / "train.parquet").exists() else 0
            n_val = len(pd.read_parquet(ia_dir_path / "val.parquet")) if (ia_dir_path / "val.parquet").exists() else 0
            n_test = len(pd.read_parquet(ia_dir_path / "test.parquet")) if (ia_dir_path / "test.parquet").exists() else 0
            col_h1.metric("Train", f"{n_train:,}")
            col_h2.metric("Validation", f"{n_val:,}")
            col_h3.metric("Test", f"{n_test:,}")
            st.line_chart(df_hist.set_index("date")["lignes_cumulées"], use_container_width=True)
            st.caption("Données collectées par date → plus de données = meilleur fine-tuning.")
        else:
            st.info("Aucun historique disponible. Lancez le pipeline et la fusion GoldAI.")

        # Évolution des runs d'entraînement (si plusieurs modèles fine-tunés)
        trained_models_hist = _scan_trained_models(PROJECT_ROOT)
        if len(trained_models_hist) >= 1:
            st.caption("**Historique des runs de fine-tuning**")
            run_rows = []
            for m in trained_models_hist:
                if m.get("eval_accuracy"):
                    run_rows.append({
                        "Run": m["name"],
                        "Date": m.get("trained_at", "—"),
                        "Accuracy": round(m["eval_accuracy"], 4),
                        "F1": round(m.get("eval_f1") or 0, 4),
                        "Epochs": m.get("epochs", "—"),
                    })
            if run_rows:
                df_runs = pd.DataFrame(run_rows)
                st.dataframe(df_runs, use_container_width=True, hide_index=True)
                if len(run_rows) > 1:
                    st.line_chart(df_runs.set_index("Run")[["Accuracy", "F1"]], use_container_width=True)

        # ── Section 1 : Benchmark ───────────────────────────────────────────────────
        st.divider()
        st.subheader("1. Benchmark — Modèles pré-entraînés")
        st.caption(
            "Compare les modèles HuggingFace sur votre dataset de test (data/goldai/ia/test.parquet). "
            "**Relancez le benchmark après chaque grosse collecte** car les métriques évoluent avec les données."
        )

        bench_results = _load_benchmark_results(PROJECT_ROOT)
        _backbone_from_bench_key = {
            "bert_multilingual": "bert_multilingual",
            "sentiment_fr": "sentiment_fr",
            "xlm_roberta_twitter": "flaubert",
            "flaubert_multilingual": "flaubert",
        }
        _best_pretrained_backbone = "sentiment_fr"
        if bench_results:
            rows_b = []
            for key, r in bench_results.items():
                if "error" in r:
                    continue
                pc = r.get("per_class", {})
                f1_pos_val = pc.get("pos", {}).get("f1", pc.get("positif", {}).get("f1", 0))
                rows_b.append({
                    "Modèle": key,
                    "Accuracy": f"{r.get('accuracy', 0):.1%}",
                    "F1 macro": f"{r.get('f1_macro', 0):.3f}",
                    "F1 positif": f"{f1_pos_val:.3f}",
                    "F1 négatif": f"{pc.get('neg', {}).get('f1', 0):.3f}",
                    "Latence (ms)": f"{r.get('avg_latency_ms', 0):.0f}",
                })
            if rows_b:
                # Trier par accuracy décroissante
                rows_b_sorted = sorted(
                    rows_b,
                    key=lambda x: bench_results.get(x["Modèle"], {}).get("accuracy", 0),
                    reverse=True,
                )
                # Ajouter médaille
                for i, row in enumerate(rows_b_sorted):
                    row["Rang"] = ["🥇", "🥈", "🥉", "4"][min(i, 3)]
                df_bench = pd.DataFrame(rows_b_sorted)[["Rang", "Modèle", "Accuracy", "F1 macro", "F1 positif", "F1 négatif", "Latence (ms)"]]
                st.dataframe(df_bench, use_container_width=True, hide_index=True)

                best_key = rows_b_sorted[0]["Modèle"]
                best_acc = bench_results.get(best_key, {}).get("accuracy", 0)

                # Exclure finetuned_local pour suggérer un backbone pré-entraîné
                pretrained_sorted = [r for r in rows_b_sorted if r["Modèle"] != "finetuned_local"]
                if pretrained_sorted:
                    _best_pretrained_backbone = _backbone_from_bench_key.get(
                        pretrained_sorted[0]["Modèle"], "sentiment_fr"
                    )
                    best_pt_key = pretrained_sorted[0]["Modèle"]
                    best_pt_acc = bench_results.get(best_pt_key, {}).get("accuracy", 0)

                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.success(
                            f"**Meilleur pré-entraîné : {best_pt_key}** ({best_pt_acc:.1%} accuracy) "
                            f"→ Recommandé comme backbone pour le fine-tuning."
                        )
                    with col_btn:
                        if st.button(
                            f"Fine-tuner {_best_pretrained_backbone} maintenant",
                            use_container_width=True,
                            type="primary",
                            help=f"Lance le fine-tuning du meilleur backbone ({best_pt_key}) avec class weights",
                        ):
                            _run_command(
                                "finetune",
                                [sys.executable, "scripts/finetune_sentiment.py",
                                 "--model", _best_pretrained_backbone, "--epochs", "3",
                                 "--target-pos-ratio", "0.25",
                                 "--pos-oversample-max-multiplier", "3.0"],
                            )
                            st.info("Fine-tuning lancé. Suivez la progression dans **Pilotage**.")
        else:
            st.info(
                "Aucun résultat de benchmark disponible. "
                "Lancez le benchmark ci-dessous pour comparer les modèles et obtenir une recommandation automatique."
            )

        col_bench1, col_bench2 = st.columns(2)
        with col_bench1:
            if st.button("Lancer Benchmark (rapide 200 ex.)", use_container_width=True,
                         help="Compare tous les modèles sur 200 exemples (~5 min)"):
                _run_command(
                    "benchmark",
                    [sys.executable, "scripts/ai_benchmark.py", "--max-samples", "200"],
                )
        with col_bench2:
            if st.button("Lancer Benchmark (complet)", use_container_width=True,
                         help="Compare sur toutes les données — résultats définitifs"):
                _run_command("benchmark", [sys.executable, "scripts/ai_benchmark.py"])

        _render_last_report("monitoring")

        # ── Section 2 : Modèles fine-tunés ─────────────────────────────────────────
        st.divider()
        st.subheader("2. Modèles fine-tunés — Entraînés sur vos données")
        st.caption(
            "Chaque fine-tuning produit un modèle adapté à vos articles (politique / économie FR). "
            "Plus il y a de données collectées, plus le modèle sera précis."
        )

        trained_models = _scan_trained_models(PROJECT_ROOT)
        if trained_models:
            rows_t: list[dict] = []
            for m in trained_models:
                # Certains anciens runs peuvent avoir eval_f1_macro=None mais eval_f1 défini.
                raw_f1_macro = m.get("eval_f1_macro")
                fallback_f1 = m.get("eval_f1")
                f1_macro_display_val = raw_f1_macro if raw_f1_macro is not None else fallback_f1
                f1_pos_ft = m.get("eval_f1_pos")
                rows_t.append(
                    {
                        "Modèle": m["name"],
                        "Accuracy val.": f"{m['eval_accuracy']:.1%}" if m.get("eval_accuracy") else "—",
                        "F1 macro": f"{f1_macro_display_val:.3f}" if f1_macro_display_val is not None else "—",
                        "F1 positif": f"{f1_pos_ft:.3f}" if f1_pos_ft is not None else "⚠ non calculé",
                        "Epochs": f"{m.get('epochs', '—')}",
                        "Entraîné le": m.get("trained_at", "—"),
                        "Chemin": m["path"],
                    }
                )
            df_trained = pd.DataFrame(rows_t)
            st.dataframe(df_trained.drop(columns=["Chemin"]), use_container_width=True, hide_index=True)
            if any(r.get("F1 positif", "").startswith("⚠") for r in rows_t):
                st.warning(
                    "**F1 positif non calculé** pour certains modèles → anciens runs sans class weights. "
                    "Re-lancez le fine-tuning avec le nouveau script pour corriger (class weights automatiques activés)."
                )

            # Courbe de loss pour le modèle sélectionné
            selected_model_name = st.selectbox(
                "Voir la courbe d'apprentissage",
                [m["name"] for m in trained_models],
                key="sel_loss_curve",
            )
            selected_model = next((m for m in trained_models if m["name"] == selected_model_name), None)
            if selected_model and selected_model.get("log_history"):
                log = selected_model["log_history"]
                train_steps = [e["step"] for e in log if "loss" in e]
                train_loss = [e["loss"] for e in log if "loss" in e]
                eval_entries = [e for e in log if "eval_loss" in e]
                if train_steps:
                    df_loss = pd.DataFrame({"step": train_steps, "Train Loss": train_loss})
                    df_loss = df_loss.set_index("step")
                    if eval_entries:
                        for ev in eval_entries:
                            step = ev.get("step", train_steps[-1])
                            df_loss.loc[step, "Val Loss"] = ev["eval_loss"]
                    st.line_chart(df_loss, use_container_width=True)
        else:
            st.info(
                "Aucun modèle fine-tuné trouvé dans `models/`. "
                "Allez dans **Pilotage** → choisissez un backbone → **Lancer le fine-tuning**."
            )

        # ── Section 3 : Sélection & Activation ─────────────────────────────────────
        st.divider()
        st.subheader("3. Sélection & Activation pour la production")
        st.caption(
            "Activez le meilleur modèle ici. Il sera utilisé automatiquement par l'API `/ai/predict` "
            "et pour les analyses Mistral (insights clients politique / économie)."
        )

        all_model_options: dict[str, str] = {
            "sentiment_fr (pré-entraîné — défaut)": "",
            "camembert (pré-entraîné — DistilCamemBERT)": "camembert_pretrained",
        }
        for m in trained_models:
            label = (
                f"{m['name']} — Accuracy {m['eval_accuracy']:.1%}" if m.get("eval_accuracy")
                else m["name"]
            )
            all_model_options[label] = m["path"]

        current_label = next(
            (lbl for lbl, path in all_model_options.items() if path == (active_model or "")),
            list(all_model_options.keys())[0],
        )
        chosen_label = st.selectbox(
            "Modèle à activer pour la production",
            list(all_model_options.keys()),
            index=list(all_model_options.keys()).index(current_label),
            key="activate_model_select",
        )
        chosen_path = all_model_options[chosen_label]

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Activer ce modèle", type="primary", use_container_width=True):
                if chosen_path:
                    ok = _activate_model(PROJECT_ROOT, chosen_path)
                    if ok:
                        st.success(
                            f"Modèle activé : `{chosen_path}`\n\n"
                            "Redémarrez l'API E2 pour prendre en compte le changement."
                        )
                        st.rerun()
                    else:
                        st.error("Impossible d'écrire dans .env — vérifiez les permissions.")
                else:
                    ok = _activate_model(PROJECT_ROOT, "")
                    if ok:
                        st.success("Modèle par défaut (`sentiment_fr`) restauré.")
                        st.rerun()
        with col_act2:
            if trained_models and st.button("Activer le meilleur automatiquement", use_container_width=True,
                                             help="Active le modèle fine-tuné avec la meilleure accuracy"):
                best = max(trained_models, key=lambda m: m.get("eval_accuracy") or 0)
                if best.get("eval_accuracy"):
                    ok = _activate_model(PROJECT_ROOT, best["path"])
                    if ok:
                        st.success(f"Meilleur modèle activé : `{best['name']}` ({best['eval_accuracy']:.1%})")
                        st.rerun()

        # ── Section 4 : Dataset IA prêt pour Mistral ───────────────────────────────
        st.divider()
        st.subheader("4. Dataset IA — Prêt pour Mistral")
        st.caption(
            "Ce dataset (labellisé sentiment + topics) est ce que vous vendez à vos clients : "
            "il alimente l'assistant Mistral pour les analyses politique / économie."
        )

        ia_dir = PROJECT_ROOT / "data" / "goldai" / "ia"
        splits_info = []
        for split in ["train", "val", "test"]:
            p = ia_dir / f"{split}.parquet"
            if p.exists():
                try:
                    n = len(pd.read_parquet(p))
                    splits_info.append({"Split": split, "Lignes": n, "Chemin": str(p.relative_to(PROJECT_ROOT))})
                except Exception:
                    splits_info.append({"Split": split, "Lignes": "?", "Chemin": str(p.relative_to(PROJECT_ROOT))})

        if splits_info:
            df_splits = pd.DataFrame(splits_info)
            total = sum(r["Lignes"] for r in splits_info if isinstance(r["Lignes"], int))
            c1, c2, c3 = st.columns(3)
            c1.metric("Total exemples étiquetés", f"{total:,}")
            c2.metric("Modèle actif (inférence)", active_model.split("/")[-1] if active_model else "sentiment_fr")
            c3.metric("Splits disponibles", len(splits_info))
            st.dataframe(df_splits, use_container_width=True, hide_index=True)
            st.caption(
                "Pour Mistral : le dataset `data/goldai/ia/` contient `sentiment` (positif/négatif/neutre) "
                "+ `topic_1/topic_2` pour chaque article. L'assistant peut s'en servir pour les insights clients."
            )
        else:
            st.info(
                "Dataset IA absent. Lancez : **Pilotage** → Copie IA → Fine-tuning → revenir ici."
            )

    with tab_monitoring:
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
                    st.caption("Distribution sentiment (normalisée)")
                    for label, count in list(sent.items())[:5]:
                        pct = ia.get("sentiment_pct", {}).get(label, 0)
                        st.caption(f"  • {label}: {count} ({pct}%)")
                    alias_rows = int(ia.get("sentiment_alias_rows", 0) or 0)
                    if alias_rows > 0:
                        st.warning(
                            f"{alias_rows:,} lignes avec labels hétérogènes (ex: neutral/positive) "
                            "ont été reclassées en labels canoniques FR."
                        )
                    lsrc = ia.get("label_source_breakdown", {})
                    n_lex = int(lsrc.get("lexical", 0))
                    n_ml = int(lsrc.get("ml_model", 0))
                    tot_src = int(lsrc.get("total", n_lex + n_ml)) or 1
                    if n_ml > 0:
                        st.info(
                            f"**Source des labels** — "
                            f"Lexical (moteur de règles) : {n_lex:,} ({n_lex/tot_src*100:.1f}%)  |  "
                            f"ML (modèle fine-tuné) : {n_ml:,} ({n_ml/tot_src*100:.1f}%)"
                        )
                    else:
                        st.caption(
                            f"Source des labels : lexical uniquement ({n_lex:,} lignes). "
                            "Lancez `bootstrap_ml_labels.py` pour substituer avec les prédictions ML."
                        )

            with st.expander("Annotation / reclassement des sentiments", expanded=False):
                map_rows = ia.get("sentiment_mapping_table", [])
                if map_rows:
                    st.dataframe(pd.DataFrame(map_rows), use_container_width=True, hide_index=True)
                raw_dist = ia.get("sentiment_distribution_raw", {})
                if raw_dist:
                    st.caption("Labels bruts observés (avant normalisation) :")
                    for lbl, n in list(raw_dist.items())[:10]:
                        st.caption(f"  • {lbl}: {n}")
                st.caption(
                    "Lecture: cette table montre comment les labels bruts sont reclassés "
                    "vers les 3 classes canoniques (négatif / neutre / positif)."
                )

            with st.expander("Qualité dataset IA pour Mistral", expanded=False):
                st.caption(ia.get("mistral_dataset_reco", ""))
                splits = ia.get("ia_splits", {})
                if splits:
                    st.dataframe(
                        pd.DataFrame(
                            [{"split": k, "lignes": v} for k, v in splits.items()]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                st.caption(
                    f"IDs manquants: {int(ia.get('id_missing', 0)):,} · "
                    f"IDs dupliqués: {int(ia.get('id_duplicates', 0)):,}."
                )

            with st.expander("Distribution des topics (pour rééquilibrer le modèle)"):
                if "topic_distribution" in ia:
                    for topic, count in list(ia["topic_distribution"].items())[:20]:
                        st.text(f"  {topic}: {count}")
                else:
                    st.caption("Colonne topic_1 absente dans le dataset.")

            with st.expander("Top sources (volume)"):
                if "top_sources" in ia:
                    for src, count in list(ia["top_sources"].items())[:10]:
                        st.text(f"  {src}: {count}")
                else:
                    st.caption("Colonne source absente.")

            st.caption(
                "Surveiller déséquilibres et confiance ; fine-tuner CamemBERT/FlauBERT sur la copie IA."
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


if __name__ == "__main__":
    main()
