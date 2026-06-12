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

import base64
import csv
import io
import json
import os
import re
import sqlite3
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

# (connect, read) — l'API peut mettre >5 s au 1er hit (reload uvicorn, poste chargé).
HTTP_PROBE_TIMEOUT: tuple[float, float] = (3.0, 20.0)


def get_api_base(settings: Any | None = None) -> str:
    """URL API E2 — 127.0.0.1 par défaut (évite latences localhost/IPv6 sous Windows)."""
    from src.config import get_settings

    s = settings or get_settings()
    return os.getenv("API_BASE", f"http://127.0.0.1:{s.fastapi_port}").rstrip("/")


def probe_http_get(
    url: str,
    timeout: tuple[float, float] | float = HTTP_PROBE_TIMEOUT,
) -> dict[str, Any]:
    """GET HTTP avec durée mesurée — utilisé par les checks cockpit."""
    import time

    import requests

    t0 = time.time()
    try:
        resp = requests.get(url, timeout=timeout)
        elapsed = time.time() - t0
        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "text": resp.text,
            "elapsed_s": round(elapsed, 2),
            "error": None,
        }
    except Exception as exc:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "text": "",
            "elapsed_s": round(elapsed, 2),
            "error": str(exc),
        }


_METRIC_LINE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>[-+eE0-9.]+)$"
)
_LABEL_RE = re.compile(r'(\w+)="((?:\\.|[^"\\])*)"')


def _parse_prometheus_samples(body: str) -> list[tuple[str, dict[str, str], float]]:
    samples: list[tuple[str, dict[str, str], float]] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _METRIC_LINE_RE.match(line)
        if not match:
            continue
        name = match.group("name")
        if name.endswith("_created") or name.endswith("_bucket"):
            continue
        labels = {m.group(1): m.group(2) for m in _LABEL_RE.finditer(match.group("labels") or "")}
        try:
            value = float(match.group("value"))
        except ValueError:
            continue
        samples.append((name, labels, value))
    return samples


def _fmt_int(n: float) -> str:
    return f"{int(n):,}".replace(",", " ")


def summarize_prometheus_metrics(body: str, *, max_request_lines: int = 8) -> str:
    """Résumé lisible des métriques E2 (sans bruit *_created)."""
    samples = _parse_prometheus_samples(body)
    by_name: dict[str, list[tuple[dict[str, str], float]]] = {}
    for name, labels, value in samples:
        by_name.setdefault(name, []).append((labels, value))

    lines: list[str] = ["=== API E2 — Résumé Prometheus ===", ""]

    # Auth
    auth_rows = by_name.get("datasens_e2_api_authentications_total", [])
    if auth_rows:
        lines.append("Authentification")
        for labels, value in sorted(auth_rows, key=lambda x: x[0].get("status", "")):
            status = labels.get("status", "?")
            lines.append(f"  {status:7} : {_fmt_int(value)}")
        lines.append("")

    # HTTP requests
    req_rows = [
        (labels, value)
        for labels, value in by_name.get("datasens_e2_api_requests_total", [])
        if value > 0
    ]
    if req_rows:
        lines.append("Requêtes HTTP (top endpoints)")
        req_rows.sort(key=lambda x: x[1], reverse=True)
        for labels, value in req_rows[:max_request_lines]:
            method = labels.get("method", "?")
            endpoint = labels.get("endpoint", "?")
            status = labels.get("status_code", "?")
            lines.append(f"  {method:4} {endpoint} -> {_fmt_int(value)} ({status})")
        if len(req_rows) > max_request_lines:
            lines.append(f"  … +{len(req_rows) - max_request_lines} autres combinaisons")
        lines.append("")

    # Zone RBAC
    zone_rows = [
        (labels, value)
        for labels, value in by_name.get("datasens_e2_api_zone_access_total", [])
        if value > 0
    ]
    if zone_rows:
        lines.append("Accès par zone (RBAC)")
        zone_rows.sort(key=lambda x: (x[0].get("zone", ""), x[0].get("method", "")))
        for labels, value in zone_rows:
            zone = labels.get("zone", "?")
            method = labels.get("method", "?")
            lines.append(f"  {zone:6} {method:4} : {_fmt_int(value)}")
        lines.append("")

    # Errors
    err_rows = [
        (labels, value)
        for labels, value in by_name.get("datasens_e2_api_errors_total", [])
        if value > 0
    ]
    lines.append("Erreurs HTTP")
    if err_rows:
        err_rows.sort(key=lambda x: x[1], reverse=True)
        for labels, value in err_rows[:6]:
            endpoint = labels.get("endpoint", "?")
            status = labels.get("status_code", "?")
            lines.append(f"  {status} {endpoint} -> {_fmt_int(value)}")
    else:
        lines.append("  (aucune)")
    lines.append("")

    # Live gauges
    lines.append("Etat courant (instantane — 0 entre deux requetes = normal)")
    for gauge, label in (
        ("datasens_e2_api_active_connections", "connexions HTTP en cours"),
        ("datasens_e2_api_active_users", "sessions JWT actives (API)"),
    ):
        rows = by_name.get(gauge, [])
        val = rows[0][1] if rows else 0.0
        lines.append(f"  {label:28} : {_fmt_int(val)}")
    if (
        not by_name.get("datasens_e2_api_active_users")
        or by_name["datasens_e2_api_active_users"][0][1] == 0
    ):
        lines.append("  (login cockpit seul : refaire login ou appeler une route API authentifiee)")
    lines.append("")

    # Drift
    drift_map = {
        "datasens_drift_score": "score composite (0=stable, 1=élevé)",
        "datasens_drift_sentiment_entropy": "entropie sentiment",
        "datasens_drift_topic_dominance": "dominance topic dominants",
        "datasens_drift_articles_total": "articles GoldAI analysés",
    }
    drift_rows = [key for key in drift_map if by_name.get(key)]
    if drift_rows:
        lines.append("Drift modèle / données (GoldAI)")
        for key in drift_rows:
            val = by_name[key][0][1]
            if key == "datasens_drift_articles_total":
                lines.append(f"  {drift_map[key]:28} : {_fmt_int(val)}")
            else:
                lines.append(f"  {drift_map[key]:28} : {val:.4f}")
        if drift_rows and by_name.get("datasens_drift_articles_total", [[None, 0]])[0][1] == 0:
            lines.append(
                "  (drift a 0 : Modèles > Rafraichir drift ou GET /api/v1/analytics/drift-metrics)"
            )
        lines.append("")

    if len(lines) <= 2:
        return "Aucune métrique datasens_e2_* trouvée dans la réponse /metrics."

    lines.append("Source : GET /metrics · Grafana : http://localhost:3000")
    return "\n".join(lines)


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
    cockpit_tab: str = ""

    @property
    def root(self) -> Path:
        return self.project_root


def cockpit_tab_is_active(ctx: PageContext, *labels: str) -> bool:
    """Vrai si l'onglet principal affiché correspond (Standard = toujours vrai)."""
    if ctx.ux_mode == "Standard":
        return True
    return ctx.cockpit_tab in labels


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
        radial-gradient(circle at 15% 12%, rgba(76, 110, 245, 0.16), transparent 34%),
        radial-gradient(circle at 85% 8%, rgba(156, 123, 255, 0.14), transparent 36%),
        linear-gradient(180deg, var(--ds-bg-0) 0%, var(--ds-bg-1) 100%);
    }
    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, rgba(10, 16, 33, 0.95) 0%, rgba(16, 25, 49, 0.92) 100%);
      border-right: 1px solid rgba(116, 149, 255, 0.2);
    }
    .ds-logo-shell {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
    }
    .ds-logo-shell--login {
      margin: 1.75rem auto 1.1rem;
      max-width: 380px;
    }
    .ds-logo-shell--sidebar {
      margin: 0.15rem 0 0.85rem;
      padding: 0 0.15rem;
    }
    .ds-logo-shell--header-main {
      margin: 0.15rem 0 0.85rem;
      max-width: 320px;
      min-height: 72px;
    }
    .ds-logo-img {
      display: block;
      margin: 0 auto;
      height: auto;
      object-fit: contain;
      object-position: center;
      background: transparent;
    }
    .ds-hero { background: linear-gradient(135deg, #1f2f63 0%, #2b3f89 55%, #4a3ea5 100%); padding: 1.5rem; border-radius: 14px; margin-bottom: 1.2rem; border: 1px solid rgba(143, 168, 255, 0.35); box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35); }
    .ds-hero h3 { color: #e8eaf6; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .ds-hero p { color: #c5cae9; margin: 0; font-size: 0.9rem; }
    .ds-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 0.3rem; margin: 1rem 0; font-size: 0.85rem; }
    .ds-flow span { color: #90caf9; }
    .ds-flow .arrow { color: #64b5f6; }
    .ds-card { background: var(--ds-card); border: 1px solid var(--ds-border); border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; backdrop-filter: blur(5px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    .ds-card-title { color: #9dc0ff; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.3rem; }
    .ds-card-value { color: #fff; font-size: 1.1rem; }
    .ds-card-empty { color: #78909c; }
    .ds-panel-title { margin: 0.2rem 0 0.6rem 0; padding: 0.9rem 1rem; border-radius: 12px; border: 1px solid var(--ds-border); background: linear-gradient(135deg, rgba(26, 39, 76, 0.9) 0%, rgba(41, 52, 99, 0.9) 100%); color: #d6e1ff; font-weight: 700; letter-spacing: 0.2px; }
    .ds-panel-sub { color: var(--ds-text-soft); font-size: 0.88rem; margin-top: 0.2rem; font-weight: 400; }
    .ds-mode-intro {
      color: #a8bdf6;
      font-size: 0.92rem;
      margin: -0.35rem 0 1rem 0;
      line-height: 1.45;
      min-height: 2.6rem;
    }
    .ds-mode-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      margin: -0.25rem 0 1rem 0;
    }
    .ds-mode-chip {
      display: inline-block;
      padding: 0.22rem 0.65rem;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
      border: 1px solid rgba(126, 158, 255, 0.35);
      background: rgba(31, 47, 99, 0.45);
      color: #dce6ff;
    }
    .ds-mode-chip-ok { border-color: rgba(102, 187, 106, 0.55); color: #a5d6a7; }
    .ds-mode-chip-warn { border-color: rgba(255, 183, 77, 0.55); color: #ffcc80; }
    .ds-mode-chip-ko { border-color: rgba(239, 83, 80, 0.55); color: #ef9a9a; }
    .ds-chip { display: inline-block; border: 1px solid rgba(138, 166, 255, 0.45); color: #c7d7ff; border-radius: 999px; padding: 0.24rem 0.7rem; margin: 0.15rem 0.3rem 0.15rem 0; font-size: 0.76rem; background: rgba(65, 84, 150, 0.28); }
    [data-testid="stMetric"] {
      background: linear-gradient(160deg, rgba(27, 37, 72, 0.78) 0%, rgba(19, 27, 56, 0.78) 100%);
      border: 1px solid rgba(126, 158, 255, 0.35);
      border-radius: 12px;
      padding: 0.45rem 0.7rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.18);
    }
    [data-testid="stMetricLabel"] p { color: #a9c3ff !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #f4f7ff !important; }
    .stButton > button {
      border: 1px solid rgba(122, 161, 255, 0.45) !important;
      color: #eaf0ff !important;
      background: linear-gradient(135deg, rgba(55, 86, 189, 0.85) 0%, rgba(91, 68, 198, 0.85) 100%) !important;
      border-radius: 11px !important;
      font-weight: 600 !important;
      box-shadow: 0 3px 10px rgba(0,0,0,0.2) !important;
    }
    .stButton > button:hover {
      transform: translateY(-1px);
      filter: brightness(1.08);
      border-color: rgba(170, 192, 255, 0.8) !important;
    }
    [data-baseweb="tab-list"] {
      gap: 0.45rem;
      background: rgba(23, 32, 64, 0.68);
      border: 1px solid rgba(109, 139, 237, 0.28);
      border-radius: 12px;
      padding: 0.45rem;
      overflow-x: auto;
      flex-wrap: nowrap;
    }
    [data-baseweb="tab"] {
      border-radius: 10px !important;
      font-weight: 600;
      flex-shrink: 0;
      min-width: max-content;
      white-space: nowrap;
      overflow: visible;
      font-size: 1rem !important;
      padding: 0.62rem 1.35rem !important;
      line-height: 1.35 !important;
      height: auto !important;
    }
    [data-baseweb="tab"] p {
      font-size: 1rem !important;
      line-height: 1.35 !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
      background: linear-gradient(135deg, rgba(65, 94, 201, 0.85), rgba(126, 84, 220, 0.85)) !important;
      color: #f4f6ff !important;
    }
    [data-testid="stTabs"] [role="tabpanel"] {
      background: rgba(13, 20, 39, 0.72);
      border: 1px solid rgba(106, 138, 238, 0.24);
      border-radius: 12px;
      padding: 0.85rem 1rem 1rem 1rem;
      margin-top: 0.55rem;
      overflow: visible;
      isolation: isolate;
    }
    [data-testid="stTabs"] [role="tabpanel"] > div {
      row-gap: 0.85rem;
    }
    /* Onglets inactifs : pas de fantôme en bas de page (hidden natif Streamlit uniquement) */
    [data-testid="stTabs"] [role="tabpanel"][hidden] {
      display: none !important;
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


def inject_ia_css() -> None:
    """Styles dédiés à l'onglet IA — layout épuré, panneau résultat stable."""
    st.markdown(
        """
    <style>
    .ds-ia-section {
      color: #9eb8ff;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin: 0 0 0.65rem 0;
    }
    .ds-ia-panel {
      background: rgba(15, 22, 44, 0.55);
      border: 1px solid rgba(116, 149, 255, 0.22);
      border-radius: 14px;
      padding: 1.15rem 1.2rem;
      min-height: 320px;
    }
    .ds-ia-result {
      background: linear-gradient(160deg, rgba(22, 32, 62, 0.92) 0%, rgba(16, 24, 48, 0.88) 100%);
      border: 1px solid rgba(116, 149, 255, 0.28);
      border-radius: 14px;
      padding: 1.25rem 1.3rem;
      min-height: 220px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .ds-ia-result--empty { align-items: center; text-align: center; }
    .ds-ia-result-label {
      font-size: 0.7rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #8ea2d8;
      margin-bottom: 0.5rem;
    }
    .ds-ia-result-placeholder {
      color: #6b7fa8;
      font-size: 0.92rem;
      line-height: 1.5;
    }
    .ds-ia-result-value {
      font-size: 2rem;
      font-weight: 800;
      line-height: 1.1;
      margin: 0.15rem 0 0.85rem 0;
    }
    .ds-ia-bar {
      height: 6px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      overflow: hidden;
      margin-bottom: 0.75rem;
    }
    .ds-ia-bar > span {
      display: block;
      height: 100%;
      border-radius: 999px;
      transition: width 0.35s ease;
    }
    .ds-ia-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      color: #a8bdf6;
    }
    .ds-ia-chat {
      background: rgba(12, 18, 36, 0.65);
      border: 1px solid rgba(106, 138, 238, 0.2);
      border-radius: 12px;
      padding: 0.85rem 1rem;
      max-height: 340px;
      overflow-y: auto;
      margin-bottom: 0.85rem;
    }
    .ds-ia-bubble {
      border-radius: 12px;
      padding: 0.65rem 0.85rem;
      margin-bottom: 0.55rem;
      font-size: 0.88rem;
      line-height: 1.45;
    }
    .ds-ia-bubble-user {
      background: rgba(65, 94, 201, 0.35);
      border: 1px solid rgba(122, 161, 255, 0.35);
      color: #e8eeff;
      margin-left: 1.5rem;
    }
    .ds-ia-bubble-assistant {
      background: rgba(26, 36, 68, 0.85);
      border: 1px solid rgba(106, 138, 238, 0.22);
      color: #c5d4ff;
      margin-right: 1.5rem;
    }
    .ds-ia-bubble-role {
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      opacity: 0.75;
      margin-bottom: 0.25rem;
    }
    div[data-testid="stVerticalBlock"] div:has(> div > .ds-ia-panel) {
      gap: 0.5rem;
    }
    [data-testid="stTabs"] [role="tabpanel"]:not([hidden]) [data-testid="stVerticalBlockBorderWrapper"] {
      background: rgba(15, 22, 44, 0.55) !important;
      border-color: rgba(116, 149, 255, 0.22) !important;
      border-radius: 14px !important;
      padding: 0.85rem 1rem !important;
    }
    .ds-ia-examples .stButton > button,
    [data-testid="stPopover"] .stButton > button {
      white-space: normal !important;
      line-height: 1.3 !important;
      min-height: 2.75rem !important;
      font-size: 0.84rem !important;
      padding: 0.45rem 0.65rem !important;
    }
    [data-testid="stPopover"] > button {
      font-size: 0.88rem !important;
      justify-content: space-between !important;
    }
    .ds-insight-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 0.65rem;
      margin: 0.5rem 0 0.85rem 0;
    }
    .ds-insight-card {
      background: rgba(18, 28, 54, 0.88);
      border: 1px solid rgba(106, 138, 238, 0.28);
      border-radius: 12px;
      padding: 0.75rem 0.85rem;
      min-height: 88px;
    }
    .ds-insight-card-type {
      font-size: 0.65rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #7fa0e8;
      margin-bottom: 0.25rem;
    }
    .ds-insight-card-title {
      font-size: 0.88rem;
      font-weight: 700;
      color: #dce6ff;
      margin-bottom: 0.35rem;
      line-height: 1.25;
    }
    .ds-insight-card-summary {
      font-size: 0.8rem;
      color: #a8bdf6;
      line-height: 1.4;
    }
    .ds-insight-card-cross {
      border-color: rgba(156, 123, 255, 0.55) !important;
      background: linear-gradient(145deg, rgba(40, 32, 72, 0.95) 0%, rgba(22, 28, 54, 0.92) 100%);
      grid-column: 1 / -1;
    }
    .ds-insight-card-cross .ds-insight-card-summary {
      color: #d4c8ff;
      font-size: 0.86rem;
      line-height: 1.5;
    }
    .ds-insight-loading {
      min-height: 320px;
      margin: 0.5rem 0 0.85rem 0;
      padding: 1.25rem 1rem;
      border-radius: 12px;
      border: 1px dashed rgba(106, 138, 238, 0.35);
      background: rgba(18, 28, 54, 0.55);
      color: #9eb8f5;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.88rem;
    }
    .ds-ia-busy .stButton > button,
    .ds-ia-busy [data-baseweb="radio"] label {
      opacity: 0.55;
      pointer-events: none;
    }
    /* Navigation Sentiment / Insights — radio horizontal (évite onglets Streamlit 1/2) */
    [data-testid="stRadio"] > div[role="radiogroup"] {
      gap: 0.35rem;
      background: rgba(23, 32, 64, 0.68);
      border: 1px solid rgba(109, 139, 237, 0.28);
      border-radius: 12px;
      padding: 0.35rem;
      width: fit-content;
      margin-bottom: 0.75rem;
    }
    [data-testid="stRadio"] label {
      background: transparent !important;
      border-radius: 10px !important;
      padding: 0.5rem 1.25rem !important;
      margin: 0 !important;
      font-weight: 600 !important;
      color: #b8c9f5 !important;
    }
    [data-testid="stRadio"] label:has(input:checked) {
      background: linear-gradient(135deg, rgba(65, 94, 201, 0.85), rgba(126, 84, 220, 0.85)) !important;
      color: #f4f6ff !important;
    }
    [data-testid="stRadio"] label > div:first-child {
      display: none !important;
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
    """Mode démo : typographie, contrastes, espacements, graphiques."""
    if not enabled:
        return
    st.markdown(
        """
    <style>
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"] {
      font-family: "Segoe UI", system-ui, sans-serif !important;
    }
    [data-testid="stHeader"] { background: transparent; }
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
      font-family: "Segoe UI", system-ui, sans-serif !important;
      letter-spacing: -0.02em;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] p,
    label, .stMetric label {
      line-height: 1.5 !important;
    }

    /* Navigation principale mode démo / expert (radio horizontal) */
    .element-container:has(.ds-demo-main-nav) + .element-container [data-testid="stRadio"] > div[role="radiogroup"],
    .element-container:has(.ds-expert-main-nav) + .element-container [data-testid="stRadio"] > div[role="radiogroup"] {
      width: 100% !important;
      max-width: 100%;
      margin-bottom: 1rem !important;
    }
    .ds-demo-lead {
      color: #a8bdf6;
      font-size: 0.92rem;
      margin: -0.5rem 0 1rem 0;
      min-height: 2.6rem;
    }
    .ds-section {
      color: #dce6ff;
      font-size: 1.05rem;
      font-weight: 700;
      margin: 1.25rem 0 0.65rem 0;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid rgba(116, 149, 255, 0.22);
    }
    .ds-hero {
      padding: 1.1rem 1.25rem !important;
      margin-bottom: 1rem !important;
    }
    .ds-hero h3 { font-size: 1.15rem !important; }
    .ds-hero p { font-size: 0.88rem !important; opacity: 0.92; }

    .ds-journey-strip {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.35rem 0.5rem;
      margin: 0.75rem 0 1.1rem 0;
      padding: 0.85rem 1rem;
      border-radius: 12px;
      border: 1px solid rgba(116, 149, 255, 0.28);
      background: linear-gradient(90deg, rgba(30, 41, 79, 0.55), rgba(18, 26, 50, 0.35));
      font-size: 0.88rem;
      color: #c5d4f7;
    }
    .ds-journey-strip strong { color: #eef3ff; font-weight: 600; }
    .ds-journey-step {
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      white-space: nowrap;
    }
    .ds-journey-arrow { opacity: 0.55; user-select: none; }

    [data-testid="stMetric"] {
      min-height: 96px;
      padding: 0.65rem 0.85rem !important;
      border-radius: 14px !important;
    }
    [data-testid="stMetricLabel"] p {
      font-size: 0.78rem !important;
      text-transform: none !important;
    }
    [data-testid="stMetricValue"] {
      font-size: 1.45rem !important;
      font-weight: 700 !important;
    }

    [data-baseweb="tab-list"] {
      gap: 0.5rem !important;
      padding: 0.5rem !important;
      border-radius: 14px !important;
    }
    [data-baseweb="tab"] {
      font-size: 1.02rem !important;
      padding: 0.7rem 1.5rem !important;
    }
    [data-testid="stTabs"] [role="tabpanel"] {
      padding: 1.1rem 1.15rem 1.25rem !important;
      border-radius: 14px !important;
    }

    div[data-testid="stAlert"] {
      border-radius: 12px !important;
      border-width: 1px !important;
    }
    [data-testid="stAlertContainer"] div[data-baseweb="notification"] {
      background: rgba(22, 32, 62, 0.92) !important;
    }

    .stExpander { margin-bottom: 0.75rem !important; }
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
      border-radius: 12px !important;
      font-size: 0.95rem !important;
    }
    [data-testid="stCaptionContainer"] p {
      color: #9eb0d9 !important;
      font-size: 0.84rem !important;
    }
    [data-testid="stVerticalBlock"] > div { row-gap: 0.75rem; }

    /* Graphiques Altair — fond sombre cohérent */
    [data-testid="stArrowVegaLiteChart"] {
      background: rgba(14, 20, 40, 0.65);
      border: 1px solid rgba(106, 138, 238, 0.2);
      border-radius: 14px;
      padding: 0.5rem 0.35rem;
    }

    /* Sidebar démo : plus aérée */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
      font-size: 0.88rem;
    }
    .ds-sidebar-compact .backend-ok { color: #66bb6a; font-weight: 600; }
    .ds-sidebar-compact .backend-ko { color: #ffb74d; font-weight: 600; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def inject_presentation_css(enabled: bool) -> None:
    """Mode présentation : masque le chrome Streamlit (menu, header, footer)."""
    if not enabled:
        return
    st.markdown(
        """
    <style>
    header[data-testid="stHeader"] { display: none !important; }
    footer { visibility: hidden !important; height: 0 !important; }
    #MainMenu { visibility: hidden !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    .stAppDeployButton { display: none !important; }
    div[data-testid="stToolbarActions"] { display: none !important; }

    [data-testid="stAppViewContainer"] > section.main {
      padding-top: 0.75rem !important;
    }
    [data-testid="stAppViewContainer"] .block-container {
      padding-top: 1rem !important;
      max-width: 100% !important;
    }
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
      top: 0.35rem !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


_LOGO_PREFERRED = (
    "datasens_logo_vintage_exact.svg",
    "datasens_logo_vintage_transparent.png",
    "datasens_logo.png",
    "datasens_logo.jpg",
    "logo.png",
)

_LOGO_RASTER_PREFERRED = (
    "datasens_logo_vintage_transparent.png",
    "datasens_logo.png",
    "datasens_logo.jpg",
    "logo.png",
)


def brand_logo_path(project_root: Path) -> Path | None:
    """Logo principal (SVG prioritaire) — en-tête, sidebar, login."""
    branding = project_root / "assets" / "branding"
    if not branding.is_dir():
        return None
    for name in _LOGO_PREFERRED:
        candidate = branding / name
        if candidate.is_file():
            return candidate
    for pattern in ("*.svg", "*.png", "*.jpg", "*.jpeg"):
        files = sorted(
            branding.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if files:
            return files[0]
    return None


def brand_logo_raster_path(project_root: Path) -> Path | None:
    """Logo raster (PNG/JPG) — favicon et export PDF (fpdf2 ne lit pas le SVG)."""
    branding = project_root / "assets" / "branding"
    if not branding.is_dir():
        return None
    for name in _LOGO_RASTER_PREFERRED:
        candidate = branding / name
        if candidate.is_file():
            return candidate
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        files = sorted(
            branding.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if files:
            return files[0]
    return None


_LOGO_PLACEMENTS: dict[str, dict[str, Any]] = {
    "login": {
        "prefer_raster": True,
        "width_px": 340,
        "max_height_px": 92,
        "shell_class": "ds-logo-shell ds-logo-shell--login",
    },
    "sidebar": {
        "prefer_raster": True,
        "width_px": 118,
        "max_height_px": 42,
        "shell_class": "ds-logo-shell ds-logo-shell--sidebar",
    },
    "header_main": {
        "prefer_raster": True,
        "width_px": 272,
        "max_height_px": 74,
        "shell_class": "ds-logo-shell ds-logo-shell--header-main",
    },
}


def _resolve_logo_path(project_root: Path, *, prefer_raster: bool) -> Path | None:
    if prefer_raster:
        return brand_logo_raster_path(project_root) or brand_logo_path(project_root)
    return brand_logo_path(project_root) or brand_logo_raster_path(project_root)


@st.cache_data(show_spinner=False)
def _logo_data_uri(path_str: str, mtime_ns: int) -> str:
    """Data-URI cache (invalidé si le fichier logo change)."""
    _ = mtime_ns
    raw = Path(path_str).read_bytes()
    suffix = Path(path_str).suffix.lower()
    if suffix == ".svg":
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(suffix, "image/png")
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _render_logo_image(
    logo: Path,
    *,
    shell_class: str = "ds-logo-shell",
    width_px: int | None = None,
    width_pct: int | None = None,
    max_height_px: int | None = None,
) -> None:
    uri = _logo_data_uri(str(logo), logo.stat().st_mtime_ns)
    img_styles = [
        "display:block",
        "margin:0 auto",
        "height:auto",
        "object-fit:contain",
        "object-position:center",
        "background:transparent",
    ]
    if width_px is not None:
        img_styles.append(f"width:{width_px}px")
        img_styles.append("max-width:100%")
    elif width_pct is not None:
        img_styles.append(f"width:{width_pct}%")
        img_styles.append("max-width:100%")
    if max_height_px is not None:
        img_styles.append(f"max-height:{max_height_px}px")
    style = ";".join(img_styles)
    st.markdown(
        f'<div class="{shell_class}">'
        f'<img class="ds-logo-img" src="{uri}" alt="DataSens" style="{style}" />'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_brand_logo(
    project_root: Path,
    *,
    placement: str = "sidebar",
    width: int | None = None,
) -> bool:
    """Affiche le logo avec dimensions adaptées au contexte (login, sidebar, en-têtes)."""
    spec = _LOGO_PLACEMENTS.get(placement, _LOGO_PLACEMENTS["sidebar"])
    logo = _resolve_logo_path(project_root, prefer_raster=bool(spec.get("prefer_raster")))
    if not logo:
        return False
    _render_logo_image(
        logo,
        shell_class=str(spec.get("shell_class", "ds-logo-shell")),
        width_px=width if width is not None else spec.get("width_px"),
        width_pct=None if width is not None else spec.get("width_pct"),
        max_height_px=spec.get("max_height_px"),
    )
    return True


def render_demo_header(project_root: Path) -> None:
    """En-tête mode démo — logo seul."""
    if not render_brand_logo(project_root, placement="header_main"):
        st.title("DataSens Cockpit")


@st.cache_data(show_spinner=False, ttl=30)
def check_api_health(api_base: str) -> bool:
    """Health check API avec cache court (évite plusieurs appels par rerun)."""
    result = probe_http_get(
        f"{api_base.rstrip('/')}/health",
        timeout=(2.0, 12.0),
    )
    return bool(result["ok"])


def _run_status_chip_class(status: str) -> str:
    s = str(status or "").upper()
    if s == "PASS":
        return "ds-mode-chip-ok"
    if s == "WARN":
        return "ds-mode-chip-warn"
    if s in ("FAIL", "ABSENT", "KO"):
        return "ds-mode-chip-ko"
    return ""


def _render_status_strip(ctx: PageContext) -> None:
    """Pastilles API + dernier run (partagées Standard / Expert / Démo)."""
    api_cls = "ds-mode-chip-ok" if ctx.backend_ok else "ds-mode-chip-ko"
    api_label = "API connectée" if ctx.backend_ok else "API hors ligne"

    latest, _ = latest_run_summary_reports(ctx.project_root)
    run_chip = ""
    run_label = "Aucun run enregistré"
    if latest:
        status = str(latest.get("status", "—"))
        kpi = latest.get("kpis", {}) if isinstance(latest, dict) else {}
        loaded = int(float(kpi.get("loaded", 0) or 0))
        day = str(latest.get("generated_at_utc", ""))[:10]
        run_label = f"Dernier run · {day or '?'} · {status} · {loaded:,} lignes"
        run_chip = _run_status_chip_class(status)

    st.markdown(
        f"""
        <div class="ds-mode-strip">
          <span class="ds-mode-chip {api_cls}">{api_label}</span>
          <span class="ds-mode-chip {run_chip}">{run_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mode_intro(ctx: PageContext) -> None:
    """Bandeau profil (sans statut API/run — voir sidebar)."""
    if ctx.ux_mode == "Standard":
        intro = "Lecture seule — analyse de sentiment et insights métier."
    elif ctx.ux_mode == "Expert":
        intro = "Cockpit complet — pipeline, modèles, pilotage et monitoring."
    else:
        return

    st.markdown(f'<p class="ds-mode-intro">{intro}</p>', unsafe_allow_html=True)


def render_demo_status_strip(ctx: PageContext) -> None:
    """Deprecated — statut dans la sidebar."""
    _ = ctx


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


def _build_mongo_uri_from_env(default_uri: str) -> str:
    """
    Construit une URI Mongo prenant en compte les credentials de `.env`.

    Priorité :
      1. `MONGO_URI` complète si définie (avec ou sans credentials).
      2. `settings.mongo_uri` si elle contient déjà des credentials (`@`).
      3. Reconstruction depuis `MONGO_HOST/PORT/USER/PASSWORD/AUTH_SOURCE`
         si ces variables sont présentes dans `.env`.
      4. Fallback : la valeur par défaut fournie.

    Évite l'erreur classique "Authentication failed" quand `.env` définit
    les credentials par variables séparées mais pas `MONGO_URI`.
    """
    env_uri = os.getenv("MONGO_URI", "").strip()
    if env_uri:
        return env_uri
    if "@" in default_uri:
        return default_uri
    user = os.getenv("MONGO_USER", "").strip()
    pwd = os.getenv("MONGO_PASSWORD", "").strip()
    if not (user and pwd):
        return default_uri
    host = os.getenv("MONGO_HOST", "localhost").strip() or "localhost"
    port = os.getenv("MONGO_PORT", "27017").strip() or "27017"
    auth_source = os.getenv("MONGO_AUTH_SOURCE", "admin").strip() or "admin"
    from urllib.parse import quote_plus

    return (
        f"mongodb://{quote_plus(user)}:{quote_plus(pwd)}"
        f"@{host}:{port}/?authSource={auth_source}"
    )


def mongo_status(root: Path) -> dict:
    """Teste la connexion MongoDB et retourne le statut + liste des fichiers GridFS."""
    result: dict = {
        "connected": False,
        "error": None,
        "files": [],
        "total_size": 0,
        "db_name": "",
        "bucket": "",
    }
    try:
        import sys as _sys

        _sys.path.insert(0, str(root))
        _sys.path.insert(0, str(root / "src"))
        from src.config import get_settings

        settings = get_settings()
        default_uri = getattr(settings, "mongo_uri", "mongodb://localhost:27017")
        mongo_uri = _build_mongo_uri_from_env(default_uri)
        mongo_db = os.getenv("MONGO_DB_NAME", getattr(settings, "mongo_db", "datasens"))
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
        for f in coll.find({}, {"filename": 1, "metadata": 1, "length": 1, "uploadDate": 1}).sort(
            "uploadDate", -1
        ):
            size = f.get("length", 0)
            total_size += size
            meta = f.get("metadata", {})
            upload_dt = f.get("uploadDate")
            files.append(
                {
                    "file_id": str(f.get("_id", "")),
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


def mongo_get_file_bytes(root: Path, file_id: str) -> tuple[bytes | None, dict | None, str | None]:
    """Retourne (bytes, metadata, filename) d'un fichier GridFS par _id."""
    try:
        import sys as _sys

        import gridfs
        from bson import ObjectId
        from pymongo import MongoClient

        _sys.path.insert(0, str(root))
        _sys.path.insert(0, str(root / "src"))
        from src.config import get_settings

        settings = get_settings()
        default_uri = getattr(settings, "mongo_uri", "mongodb://localhost:27017")
        mongo_uri = _build_mongo_uri_from_env(default_uri)
        mongo_db = os.getenv("MONGO_DB_NAME", getattr(settings, "mongo_db", "datasens"))
        bucket = getattr(settings, "mongo_gridfs_bucket", "parquet_fs")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        db = client[mongo_db]
        fs = gridfs.GridFS(db, collection=bucket)
        gf = fs.get(ObjectId(file_id))
        payload = gf.read()
        meta = getattr(gf, "metadata", {}) or {}
        filename = getattr(gf, "filename", None)
        client.close()
        return payload, meta, filename
    except Exception:
        return None, None, None


def mongo_read_parquet_preview(root: Path, file_id: str, limit: int = 100) -> pd.DataFrame:
    """Charge un aperçu DataFrame depuis un fichier parquet stocké dans GridFS."""
    payload, _meta, _filename = mongo_get_file_bytes(root, file_id)
    if not payload:
        return pd.DataFrame()
    try:
        df = pd.read_parquet(io.BytesIO(payload))
        if limit > 0:
            return df.head(limit)
        return df
    except Exception:
        return pd.DataFrame()


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
        return pd.DataFrame(columns=pd.Index(["date", "lignes_cumulées"]))
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


def latest_run_summary_reports(root: Path) -> tuple[dict | None, dict | None]:
    """Retourne (dernier, precedent) run_summary JSON."""
    rep = root / "reports"
    files = sorted(rep.glob("run_summary_*.json"))
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


def run_summary_history(root: Path, limit: int = 10) -> list[dict]:
    """Retourne l'historique des run_summary (du plus récent au plus ancien)."""
    rep = root / "reports"
    files = sorted(rep.glob("run_summary_*.json"), reverse=True)
    if limit > 0:
        files = files[:limit]
    out: list[dict] = []
    for p in files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_file"] = p.name
                out.append(data)
        except Exception:
            continue
    return out


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


def ensure_telemetry_session() -> None:
    """Initialise le chrono session des le login (pas seulement a l'ouverture du panneau)."""
    _telemetry_state()


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
    """Affiche le dernier rapport d'exécution (persisté après rerun)."""
    report = st.session_state.get("last_command_report")
    if not report:
        return
    status = "OK" if report.get("ok") else "KO"
    duration_s = float(report.get("duration_s", 0.0) or 0.0)
    st.caption(
        f"Dernière exécution: {report.get('label', 'Commande')} " f"({status}, {duration_s:.2f}s)"
    )
    with st.expander("📋 Rapport d'exécution détaillé", expanded=False):
        st.code(report.get("command", "Commande inconnue"), language="bash")
        st.text_area(
            "Sortie",
            value=report.get("out", "OK"),
            height=220,
            disabled=True,
            label_visibility="collapsed",
            key=f"last_report_output_{panel_key}",
        )
        if report.get("err"):
            st.error(report.get("err", "Erreur inconnue"))


def resolve_sqlite_db_path(project_root: Path) -> Path:
    """Chemin SQLite opérationnel (aligné overview / monitoring)."""
    db_candidate = os.getenv("DB_PATH")
    if db_candidate and Path(db_candidate).exists():
        return Path(db_candidate)
    default_db = Path.home() / "datasens_project" / "datasens.db"
    return default_db if default_db.exists() else project_root / "datasens.db"


def fetch_user_audit_log(
    project_root: Path,
    *,
    limit: int = 50,
    role_filter: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Lit user_action_log joint à profils (journal actions utilisateurs)."""
    db_path = resolve_sqlite_db_path(project_root)
    if not db_path.exists():
        return [], f"Base SQLite introuvable : `{db_path}`"

    role_filter = (role_filter or "").strip().lower()
    if role_filter in ("tous", "all", ""):
        role_filter = ""

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_action_log'"
        )
        if not cursor.fetchone():
            conn.close()
            return [], "Table `user_action_log` absente — lancer le pipeline E1 ou l'API E2."

        query = """
            SELECT
                ual.action_date,
                ual.profil_id,
                p.email,
                p.role,
                ual.action_type,
                ual.resource_type,
                ual.resource_id,
                ual.ip_address,
                ual.details
            FROM user_action_log ual
            LEFT JOIN profils p ON p.profil_id = ual.profil_id
        """
        params: list[Any] = []
        if role_filter:
            query += " WHERE LOWER(COALESCE(p.role, '')) = ?"
            params.append(role_filter)
        query += " ORDER BY ual.action_date DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        rows = [dict(r) for r in cursor.execute(query, params).fetchall()]
        conn.close()
        return rows, None
    except Exception as exc:
        return [], str(exc)[:200]
