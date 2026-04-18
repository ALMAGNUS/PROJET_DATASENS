"""
Helpers partagés du cockpit Streamlit DataSens.

Ce module centralise :
- Les injections CSS (ds-panel, hero, readability, mode démo).
- Les lectures parquet/CSV en cache (`st.cache_data`).
- Les helpers de lecture d'état (Mongo, db_state, modèle actif).
- Les utilitaires d'exécution de commandes (`_run_command`, `_render_last_report`).
- La telemetrie cockpit (compteurs clics, chrono session, erreurs).
- Le dataclass `PageContext` transporté vers chaque module de `pages/`.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover
    pq = None  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class PageContext:
    """État partagé propagé à chaque page du cockpit."""

    project_root: Path
    api_base: str
    backend_ok: bool
    ux_mode: str
    show_advanced: bool
    history_mode: bool
    raw_dir: Path
    silver_dir: Path
    gold_dir: Path
    goldai_dir: Path
    ia_dir: Path
    settings: Any

    @property
    def root(self) -> Path:
        return self.project_root


def inject_css() -> None:
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


def inject_readability_css(enabled: bool) -> None:
    """Mode accessibilite: contraste et lisibilite renforces."""
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


def inject_demo_css(enabled: bool) -> None:
    """Mode demo: interface allegee et focus narration."""
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


@st.cache_data(show_spinner=False, ttl=60)
def read_parquet_cached(path_str: str, columns: tuple[str, ...] | None = None) -> pd.DataFrame:
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
def parquet_row_count_cached(path_str: str) -> int:
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
def csv_row_count_cached(path_str: str) -> int:
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


def mongo_status(root: Path) -> dict:
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
            files.append(
                {
                    "filename": f.get("filename", "?"),
                    "logical_name": meta.get("logical_name", "—"),
                    "partition_date": meta.get("partition_date", "—"),
                    "stored_at": meta.get("stored_at", "—"),
                    "upload_date": upload_dt.isoformat() if upload_dt else "—",
                    "size_bytes": size,
                    "sha256": meta.get("sha256", "")[:12] + "…" if meta.get("sha256") else "—",
                }
            )
        result["files"] = files
        result["total_size"] = total_size
        client.close()
    except Exception as exc:
        result["error"] = str(exc)
    return result


def ia_history(root: Path) -> pd.DataFrame:
    """Construit l'historique des snapshots GoldAI (evolution du volume de donnees)."""
    import json as _json

    goldai_dir = root / "data" / "goldai"
    meta_path = goldai_dir / "metadata.json"
    rows: list[dict] = []
    if meta_path.exists():
        try:
            meta = _json.loads(meta_path.read_text(encoding="utf-8"))
            dates = sorted(meta.get("dates_included", []))
            total = meta.get("total_rows", 0)
            step = total // max(len(dates), 1) if dates else 0
            for i, d in enumerate(dates):
                rows.append({"date": d, "lignes_cumulées": step * (i + 1)})
            if rows:
                rows[-1]["lignes_cumulées"] = total
        except Exception:
            pass
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


def latest_db_state_reports(root: Path) -> tuple[dict | None, dict | None]:
    """Retourne (dernier, precedent) rapports db_state JSON."""
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


def get_active_model(root: Path) -> str | None:
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


def activate_model(root: Path, model_path: str) -> bool:
    """Ecrit SENTIMENT_FINETUNED_MODEL_PATH dans .env."""
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


def launch_api_in_new_window() -> None:
    """Lance l'API E2 dans une nouvelle fenetre (ne bloque pas le Cockpit)."""
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


TELEMETRY_KEY = "cockpit_telemetry"


def _telemetry_state() -> dict:
    """Retourne (et initialise) le conteneur de telemetrie en session."""
    if TELEMETRY_KEY not in st.session_state:
        st.session_state[TELEMETRY_KEY] = {
            "session_started_at": time.time(),
            "clicks": {},
            "runs": [],
            "errors": 0,
        }
    return st.session_state[TELEMETRY_KEY]


def record_click(label: str) -> None:
    """Incremente le compteur de clics pour un label donne."""
    state = _telemetry_state()
    state["clicks"][label] = state["clicks"].get(label, 0) + 1


def record_run(label: str, duration_s: float, ok: bool) -> None:
    """Enregistre la duree et le resultat d'une commande subprocess."""
    state = _telemetry_state()
    state["runs"].append(
        {
            "label": label,
            "duration_s": round(float(duration_s), 3),
            "ok": bool(ok),
            "at": time.time(),
        }
    )
    # Garde seulement les 200 derniers runs pour borner la memoire session
    if len(state["runs"]) > 200:
        del state["runs"][:-200]
    if not ok:
        state["errors"] += 1


def record_error() -> None:
    """Incremente le compteur d'erreurs UI (exceptions signalees par l'utilisateur)."""
    state = _telemetry_state()
    state["errors"] += 1


def get_telemetry_snapshot() -> dict:
    """Retourne un snapshot (agrege) de la telemetrie cockpit."""
    state = _telemetry_state()
    runs = state["runs"]
    total_duration = sum(r["duration_s"] for r in runs)
    avg_duration = (total_duration / len(runs)) if runs else 0.0
    success = sum(1 for r in runs if r["ok"])
    failures = sum(1 for r in runs if not r["ok"])
    return {
        "session_age_s": int(time.time() - state["session_started_at"]),
        "clicks": dict(state["clicks"]),
        "total_runs": len(runs),
        "success_runs": success,
        "failure_runs": failures,
        "avg_run_duration_s": round(avg_duration, 3),
        "total_run_duration_s": round(total_duration, 3),
        "errors": int(state["errors"]),
        "recent_runs": runs[-20:],
    }


def reset_telemetry() -> None:
    """Reinitialise la telemetrie cockpit (bouton admin)."""
    st.session_state[TELEMETRY_KEY] = {
        "session_started_at": time.time(),
        "clicks": {},
        "runs": [],
        "errors": 0,
    }


def run_command(label: str, command: list[str], extra_env: dict | None = None) -> None:
    st.write(f"Commande: `{' '.join(command)}`")
    record_click(label)
    out, err = "", None
    started = time.time()
    ok = False
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
            ok = proc.returncode == 0
        except subprocess.TimeoutExpired:
            out = ""
            err = None
            ok = False
            st.warning("Timeout: commande trop longue")

        record_run(label, time.time() - started, ok)

        if "last_command_report" not in st.session_state:
            st.session_state.last_command_report = {}
        st.session_state.last_command_report = {
            "label": label,
            "out": out or "OK",
            "err": err,
            "command": " ".join(command),
            "duration_s": round(time.time() - started, 3),
            "ok": ok,
        }


SENT_COLORS: dict[str, tuple[str, str, str]] = {
    "positif": ("#1b5e20", "#e8f5e9", "positif"),
    "positive": ("#1b5e20", "#e8f5e9", "positif"),
    "négatif": ("#b71c1c", "#ffebee", "négatif"),
    "negatif": ("#b71c1c", "#ffebee", "négatif"),
    "negative": ("#b71c1c", "#ffebee", "négatif"),
    "neutre": ("#37474f", "#eceff1", "neutre"),
    "neutral": ("#37474f", "#eceff1", "neutre"),
}


def sentiment_badge(label: str) -> str:
    """Rend un badge HTML colorise pour un label de sentiment."""
    key = str(label).strip().lower()
    color, bg, display = SENT_COLORS.get(key, ("#37474f", "#eceff1", label))
    return (
        f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:10px;'
        f'font-weight:700;font-size:0.85rem;border:1px solid {color}33;">{display}</span>'
    )


def render_last_report(panel_key: str) -> None:
    """Affiche le dernier rapport d'execution (persiste apres rerun)."""
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
