"""
UX cockpit DataSens — fil d'Ariane, KPI strip, palette, cache, parcours démo.

Innovations cockpit (2026-05) : harmonisation Standard / Démo / Expert.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    check_api_health,
    get_active_model,
    latest_run_summary_reports,
    run_summary_history,
)
from src.streamlit.metrics import load_benchmark_results, scan_trained_models

# ---------------------------------------------------------------------------
# Palette unifiée PASS / WARN / FAIL / ABSENT (#7)
# ---------------------------------------------------------------------------

STATUS_COLORS: dict[str, str] = {
    "PASS": "#34d399",
    "WARN": "#fbbf24",
    "FAIL": "#f87171",
    "ABSENT": "#64748b",
    "—": "#94a3b8",
    "OK": "#34d399",
    "WARNING": "#fbbf24",
    "ERROR": "#f87171",
}

STATUS_CHIP_CLASS: dict[str, str] = {
    "PASS": "ds-mode-chip-ok",
    "OK": "ds-mode-chip-ok",
    "WARN": "ds-mode-chip-warn",
    "WARNING": "ds-mode-chip-warn",
    "FAIL": "ds-mode-chip-ko",
    "ERROR": "ds-mode-chip-ko",
    "ABSENT": "ds-mode-chip-ko",
}

STATUS_ORDER: list[str] = ["PASS", "WARN", "FAIL", "ABSENT", "—"]

LAYER_ICONS: dict[str, str] = {
    "RAW": "🗄️",
    "SILVER": "🧹",
    "GOLD": "✨",
    "GoldAI": "🤖",
}

DEMO_TOUR_STEPS: list[dict[str, str]] = [
    {
        "tab": "IA",
        "title": "1/5 — Sentiment",
        "body": "Onglet **IA** : saisissez un texte ou choisissez un exemple, puis analysez le sentiment.",
    },
    {
        "tab": "IA",
        "title": "2/5 — Insights",
        "body": "Passez sur **Insights** : posez une question métier (API requise).",
    },
    {
        "tab": "Pipeline",
        "title": "3/5 — Volumes",
        "body": "Onglet **Pipeline** : volumes RAW → GoldAI et run du jour.",
    },
    {
        "tab": "Pipeline",
        "title": "4/5 — Preuve de run",
        "body": "Scrollez jusqu'à **Preuve du run** — deltas, exports PDF/MD.",
    },
    {
        "tab": "Pipeline",
        "title": "5/5 — Historique",
        "body": "Ouvrez **Historique des runs** — PASS/WARN et alertes quality gate.",
    },
]


def status_chip_class(status: str) -> str:
    return STATUS_CHIP_CLASS.get(str(status or "").upper(), "")


def status_color(status: str) -> str:
    return STATUS_COLORS.get(str(status or "").upper(), STATUS_COLORS["—"])


def altair_status_scale():
    import altair as alt

    present = [s for s in STATUS_ORDER if s in STATUS_COLORS]
    return alt.Scale(
        domain=present,
        range=[STATUS_COLORS[s] for s in present],
    )


# ---------------------------------------------------------------------------
# CSS UX (#1 #2 #8)
# ---------------------------------------------------------------------------


def inject_cockpit_ux_css() -> None:
    st.markdown(
        """
<style>
.ds-breadcrumb {
  font-size: 0.82rem;
  color: #8fa8e8;
  margin: 0 0 0.65rem 0;
  letter-spacing: 0.02em;
}
.ds-breadcrumb strong { color: #dce6ff; font-weight: 600; }
.ds-kpi-strip {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.55rem 0.75rem;
  margin: 0 0 1rem 0;
  border-radius: 12px;
  border: 1px solid rgba(116, 149, 255, 0.35);
  background: rgba(12, 18, 38, 0.92);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
}
.ds-kpi-item {
  flex: 1 1 140px;
  min-width: 120px;
  padding: 0.35rem 0.55rem;
  border-radius: 8px;
  border: 1px solid rgba(126, 158, 255, 0.22);
  background: rgba(31, 47, 99, 0.35);
}
.ds-kpi-label { font-size: 0.72rem; color: #9cb4f0; text-transform: uppercase; letter-spacing: 0.04em; }
.ds-kpi-value { font-size: 0.92rem; color: #f0f4ff; font-weight: 600; margin-top: 0.1rem; }
.ds-layer-tile {
  border: 1px solid rgba(116, 149, 255, 0.28);
  border-radius: 12px;
  padding: 0.75rem 0.85rem;
  background: linear-gradient(160deg, rgba(27, 37, 72, 0.78) 0%, rgba(19, 27, 56, 0.78) 100%);
  min-height: 108px;
}
.ds-layer-head { display: flex; align-items: center; gap: 0.4rem; color: #9dc0ff; font-weight: 600; font-size: 0.88rem; }
.ds-layer-value { font-size: 1.35rem; color: #fff; font-weight: 700; margin: 0.35rem 0 0.2rem 0; }
.ds-layer-meta { font-size: 0.78rem; color: #94a8d8; }
.ds-sparkline-wrap { margin-top: 0.35rem; opacity: 0.9; }
.ds-section-title {
  color: #c5d7ff;
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0.85rem 0 0.45rem 0;
}
.ds-demo-tour {
  border: 1px solid rgba(251, 191, 36, 0.45);
  background: rgba(120, 80, 10, 0.25);
  border-radius: 10px;
  padding: 0.65rem 0.85rem;
  margin-bottom: 0.85rem;
  color: #fde68a;
  font-size: 0.9rem;
}
.ds-demo-tour strong { color: #fef3c7; }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_expert_breadcrumb(*parts: str) -> None:
    """Fil d'Ariane Expert (#1)."""
    if not parts:
        return
    trail = " › ".join(f"<strong>{p}</strong>" if i == len(parts) - 1 else p for i, p in enumerate(parts))
    st.markdown(f'<div class="ds-breadcrumb">Expert › {trail}</div>', unsafe_allow_html=True)


def render_section_title(title: str) -> None:
    """Titre de section sans H3/H4 supplémentaire (#9)."""
    st.markdown(f'<p class="ds-section-title">{title}</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Backend OK — prefetch login (#6)
# ---------------------------------------------------------------------------


def prefetch_backend_ok(api_base: str) -> None:
    ok = check_api_health(api_base)
    st.session_state["backend_ok"] = ok
    st.session_state["backend_ok_ts"] = time.time()


def resolve_backend_ok(api_base: str) -> bool:
    ts = st.session_state.get("backend_ok_ts")
    if ts and time.time() - float(ts) < 20:
        return bool(st.session_state.get("backend_ok", False))
    ok = check_api_health(api_base)
    st.session_state["backend_ok"] = ok
    st.session_state["backend_ok_ts"] = time.time()
    return ok


# ---------------------------------------------------------------------------
# Cache (#4)
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False, ttl=30)
def run_summary_history_cached(root_str: str, limit: int = 10) -> list[dict]:
    return run_summary_history(Path(root_str), limit=limit)


@st.cache_data(show_spinner=False, ttl=30)
def latest_db_state_cached(root_str: str) -> dict | None:
    rep = Path(root_str) / "reports"
    if not rep.exists():
        return None
    files = sorted(rep.glob("db_state_*.json"))
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=30)
def growth_timeline_cached(root_str: str) -> list[dict[str, Any]]:
    from src.streamlit.pipeline_proof import build_growth_timeline

    df = build_growth_timeline(Path(root_str))
    if df.empty:
        return []
    return df.reset_index().rename(columns={"index": "date"}).to_dict(orient="records")


# ---------------------------------------------------------------------------
# KPI strip Expert (#2)
# ---------------------------------------------------------------------------


def _mongo_label(ctx: PageContext) -> tuple[str, str]:
    cache = st.session_state.get("mongo_status_cache")
    if isinstance(cache, dict) and cache.get("connected"):
        n = len(cache.get("files", []) or [])
        return f"Mongo · {n} fichiers", "ds-mode-chip-ok"
    if isinstance(cache, dict):
        return "Mongo · hors ligne", "ds-mode-chip-ko"
    return "Mongo · non vérifié", ""


def get_active_model_summary(root: Path) -> dict[str, Any]:
    """Synthèse modèle actif (#12)."""
    active_path = get_active_model(root)
    name = "—"
    if active_path:
        name = Path(active_path).name if "/" in active_path or "\\" in active_path else active_path
        if len(name) > 40:
            name = "…" + name[-37:]

    trained = scan_trained_models(root)
    trained_at = "—"
    train_f1 = None
    if active_path:
        for m in trained:
            if m.get("path") == active_path or m.get("name") in active_path:
                trained_at = m.get("trained_at", "—")
                train_f1 = m.get("eval_f1_macro") or m.get("eval_f1")
                name = m.get("name", name)
                break

    bench = load_benchmark_results(root)
    inf_f1 = None
    if bench:
        for key in ("finetuned_local", "sentiment_fr"):
            if key in bench and isinstance(bench[key], dict):
                inf_f1 = bench[key].get("f1_macro")
                break
        if inf_f1 is None and bench:
            first = next(iter(bench.values()))
            if isinstance(first, dict):
                inf_f1 = first.get("f1_macro")

    f1_display = "—"
    if inf_f1 is not None:
        f1_display = f"{float(inf_f1):.3f} (bench)"
    elif train_f1 is not None:
        f1_display = f"{float(train_f1):.3f} (train)"

    return {
        "name": name,
        "trained_at": trained_at,
        "f1_display": f1_display,
        "active_path": active_path,
    }


def render_expert_kpi_strip(ctx: PageContext) -> None:
    """Bandeau KPI sticky en mode Expert (#2)."""
    api_cls = "ds-mode-chip-ok" if ctx.backend_ok else "ds-mode-chip-ko"
    api_val = "En ligne" if ctx.backend_ok else "Hors ligne"

    latest, _ = latest_run_summary_reports(ctx.project_root)
    run_val = "Aucun run"
    run_cls = ""
    if latest:
        status = str(latest.get("status", "—"))
        kpi = latest.get("kpis", {}) if isinstance(latest, dict) else {}
        loaded = int(float(kpi.get("loaded", 0) or 0))
        day = str(latest.get("generated_at_utc", ""))[:10]
        run_val = f"{day} · {status} · {loaded:,}"
        run_cls = status_chip_class(status)

    mongo_val, mongo_cls = _mongo_label(ctx)
    model = get_active_model_summary(ctx.project_root)

    nav_hint = ""
    filter_date = st.session_state.get("monitoring_filter_date")
    if filter_date:
        nav_hint = (
            f'<div class="ds-kpi-item" style="flex:2 1 220px;border-color:rgba(251,191,36,0.45)">'
            f'<div class="ds-kpi-label">Alerte quality gate</div>'
            f'<div class="ds-kpi-value">Filtre Monitoring · {filter_date}</div></div>'
        )

    st.markdown(
        f"""
<div class="ds-kpi-strip">
  <div class="ds-kpi-item"><div class="ds-kpi-label">API E2</div>
    <div class="ds-kpi-value"><span class="ds-mode-chip {api_cls}">{api_val}</span></div></div>
  <div class="ds-kpi-item"><div class="ds-kpi-label">Dernier run</div>
    <div class="ds-kpi-value"><span class="ds-mode-chip {run_cls}">{run_val}</span></div></div>
  <div class="ds-kpi-item"><div class="ds-kpi-label">MongoDB</div>
    <div class="ds-kpi-value"><span class="ds-mode-chip {mongo_cls}">{mongo_val}</span></div></div>
  <div class="ds-kpi-item"><div class="ds-kpi-label">Modèle actif</div>
    <div class="ds-kpi-value">{model["name"]} · F1 {model["f1_display"]}</div></div>
  {nav_hint}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_active_model_card(root: Path) -> None:
    """Carte synthèse modèle dans Vue d'ensemble (#12)."""
    model = get_active_model_summary(root)
    if not model.get("active_path"):
        st.info("Aucun modèle fine-tuné activé (.env). Benchmark CamemBERT par défaut.")
        return
    st.success(
        f"**Modèle actif** : `{model['name']}` · F1 **{model['f1_display']}** · "
        f"entraîné {model['trained_at']}"
    )


# ---------------------------------------------------------------------------
# Sparklines tuiles (#8)
# ---------------------------------------------------------------------------


def _sparkline_svg(values: list[int], color: str = "#74a3ff") -> str:
    if not values or len(values) < 2:
        return ""
    w, h = 88, 26
    mn, mx = min(values), max(values)
    rng = max(mx - mn, 1)
    pts: list[str] = []
    for i, v in enumerate(values):
        x = i * (w - 4) / max(len(values) - 1, 1) + 2
        y = h - 2 - (v - mn) / rng * (h - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg width="{w}" height="{h}" class="ds-sparkline">'
        f'<polyline fill="none" stroke="{color}" stroke-width="1.6" '
        f'points="{" ".join(pts)}"/></svg>'
    )


def layer_sparkline_values(root: Path, layer: str, days: int = 7) -> list[int]:
    layer = layer.upper()
    if layer == "SILVER":
        hist = run_summary_history_cached(str(root), limit=days * 3)
        by_day: dict[str, int] = {}
        for item in reversed(hist):
            day = str(item.get("generated_at_utc", ""))[:10]
            if len(day) < 10:
                continue
            kpi = item.get("kpis", {}) if isinstance(item, dict) else {}
            by_day[day] = by_day.get(day, 0) + int(float(kpi.get("loaded", 0) or 0))
        vals = [by_day[d] for d in sorted(by_day.keys())][-days:]
        return vals if len(vals) >= 2 else vals + [vals[-1]] if vals else []

    rows = growth_timeline_cached(str(root))
    if not rows:
        return []
    col = {"RAW": "raw_data", "GOLD": "goldai", "GOLDAI": "goldai"}.get(layer, "raw_data")
    vals = [int(r.get(col, 0) or 0) for r in rows[-days:]]
    return vals


def render_layer_tile(
    layer: str,
    value: str,
    meta: str,
    sparkline: list[int],
    *,
    color: str = "#74a3ff",
) -> None:
    icon = LAYER_ICONS.get(layer, "📊")
    spark = _sparkline_svg(sparkline, color=color)
    st.markdown(
        f"""
<div class="ds-layer-tile">
  <div class="ds-layer-head"><span>{icon}</span><span>{layer}</span></div>
  <div class="ds-layer-value">{value}</div>
  <div class="ds-layer-meta">{meta}</div>
  <div class="ds-sparkline-wrap">{spark}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Lazy load (#5)
# ---------------------------------------------------------------------------


def lazy_panel(session_key: str, loader: Callable[[], None], *, label: str = "Charger le contenu") -> None:
    """Charge un bloc lourd uniquement après action utilisateur (#5)."""
    if st.session_state.get(session_key):
        loader()
        return
    st.caption("Contenu chargé à la demande pour réduire la latence initiale.")
    if st.button(label, key=f"lazy_{session_key}"):
        st.session_state[session_key] = True
        st.rerun()


# ---------------------------------------------------------------------------
# Navigation Monitoring (#10)
# ---------------------------------------------------------------------------


def set_monitoring_filter(date: str, *, reason: str = "") -> None:
    st.session_state["monitoring_filter_date"] = date[:10]
    st.session_state["monitoring_filter_reason"] = reason


def render_warn_monitoring_link(ctx: PageContext) -> None:
    """Bouton lien croisé WARN → Monitoring (#10)."""
    latest, _ = latest_run_summary_reports(ctx.project_root)
    if not latest:
        return
    status = str(latest.get("status", "")).upper()
    reasons = latest.get("reasons", []) or []
    if status != "WARN" and not reasons:
        return
    day = str(latest.get("generated_at_utc", ""))[:10]
    st.warning(
        f"Quality gate **{status}** le {day}"
        + (f" — {' · '.join(str(r) for r in reasons[:2])}" if reasons else "")
    )
    if st.button(
        f"Voir le détail Monitoring ({day})",
        key="warn_to_monitoring",
        help="Ouvre le filtre date dans Pilotage → Santé & MongoDB",
    ):
        set_monitoring_filter(day, reason="; ".join(str(r) for r in reasons))
        st.session_state["expert_goto_hint"] = "Pilotage › Santé & MongoDB"
        st.rerun()
    hint = st.session_state.get("expert_goto_hint")
    if hint and st.session_state.get("monitoring_filter_date"):
        st.info(f"→ Allez dans **{hint}** (filtre `{st.session_state['monitoring_filter_date']}` actif).")


def render_monitoring_date_filter() -> str | None:
    """Applique le filtre date en Monitoring (#10)."""
    filt = st.session_state.get("monitoring_filter_date")
    if not filt:
        return None
    reason = st.session_state.get("monitoring_filter_reason", "")
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.info(
            f"Filtre actif depuis une alerte quality gate · date **{filt}**"
            + (f" · {reason[:120]}" if reason else "")
        )
    with col_b:
        if st.button("Effacer filtre", key="clear_monitoring_filter"):
            st.session_state.pop("monitoring_filter_date", None)
            st.session_state.pop("monitoring_filter_reason", None)
            st.session_state.pop("expert_goto_hint", None)
            st.rerun()
    return str(filt)


# ---------------------------------------------------------------------------
# Parcours démo guidé (#3)
# ---------------------------------------------------------------------------


def render_demo_tour_sidebar() -> None:
    st.markdown("##### Parcours jury")
    active = st.session_state.get("demo_tour_active", False)
    step = int(st.session_state.get("demo_tour_step", 0) or 0)

    if not active:
        if st.button("▶ Parcours jury 5 min", key="demo_tour_start", use_container_width=True):
            st.session_state.demo_tour_active = True
            st.session_state.demo_tour_step = 1
            st.rerun()
        return

    total = len(DEMO_TOUR_STEPS)
    st.progress(min(step, total) / total)
    if step >= 1 and step <= total:
        info = DEMO_TOUR_STEPS[step - 1]
        st.caption(f"Étape {step}/{total} · onglet **{info['tab']}**")
    c1, c2 = st.columns(2)
    with c1:
        if step > 1 and st.button("← Préc.", key="demo_tour_prev"):
            st.session_state.demo_tour_step = step - 1
            st.rerun()
    with c2:
        if step < total and st.button("Suiv. →", key="demo_tour_next"):
            st.session_state.demo_tour_step = step + 1
            st.rerun()
    if st.button("Terminer le parcours", key="demo_tour_stop", use_container_width=True):
        st.session_state.demo_tour_active = False
        st.session_state.demo_tour_step = 0
        st.rerun()


def render_demo_tour_banner(expected_tab: str) -> None:
    if not st.session_state.get("demo_tour_active"):
        return
    step = int(st.session_state.get("demo_tour_step", 0) or 0)
    if step < 1 or step > len(DEMO_TOUR_STEPS):
        return
    info = DEMO_TOUR_STEPS[step - 1]
    if info["tab"] != expected_tab:
        st.markdown(
            f'<div class="ds-demo-tour">Étape en cours sur l’onglet <strong>{info["tab"]}</strong> '
            f"— basculez d’onglet pour continuer.</div>",
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f'<div class="ds-demo-tour"><strong>{info["title"]}</strong> — {info["body"]}</div>',
        unsafe_allow_html=True,
    )


def demo_tour_expand(key: str, default: bool = False) -> bool:
    """Auto-ouvre un expander si le parcours démo le demande (#3)."""
    if not st.session_state.get("demo_tour_active"):
        return default
    step = int(st.session_state.get("demo_tour_step", 0) or 0)
    if step == 5 and key == "hist_runs":
        return True
    if step == 4 and key == "proof_run":
        return True
    return default
