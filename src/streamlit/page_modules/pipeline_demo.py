"""
Vue Pipeline & Données — Mode démo jury (simplifiée).

Charts + lineage article. Pas de fusion ops, pas d'exploration expert.
Le mode Expert conserve pipeline.py + flux.py inchangés.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
    latest_run_summary_reports,
    parquet_row_count_cached,
)
from src.streamlit.cockpit_ux import (
    altair_status_scale,
    latest_db_state_cached,
    render_data_journey_strip,
    run_summary_history_cached,
)
from src.streamlit.page_modules.overview import (
    _count_raw_sqlite,
    _latest_gold,
    _latest_silver,
    _resolve_db_path,
)
from src.streamlit.pipeline_proof import render_article_journey, render_last_run_proof_full

_DEMO_FONT = "Segoe UI, system-ui, sans-serif"
_BAR_H = 34
_BAR_PAD = 0.28


def _fmt_num(value: int | float) -> str:
    return f"{int(value):,}".replace(",", "\u202f")


def _style_chart(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeWidth=0, fill="#121a32", fillOpacity=1)
        .configure_axis(
            gridColor="#334155",
            domainColor="#475569",
            labelColor="#cbd5e1",
            titleColor="#e2e8f0",
            labelFont=_DEMO_FONT,
            titleFont=_DEMO_FONT,
            labelFontSize=12,
            titleFontSize=12,
            tickColor="#475569",
        )
        .configure_legend(
            labelColor="#cbd5e1",
            titleColor="#e2e8f0",
            labelFont=_DEMO_FONT,
            titleFont=_DEMO_FONT,
        )
    )


def _horizontal_bars(
    df: pd.DataFrame,
    *,
    x_field: str = "Lignes",
    y_field: str = "Label",
    color_field: str = "Label",
    colors: list[str],
    x_scale: alt.Scale | None = None,
    x_title: str = "Nombre de lignes",
    height: int | None = None,
) -> alt.Chart:
    """Barres horizontales lisibles (catégories à gauche, valeurs à droite des barres)."""
    chart_h = height or max(180, int((_BAR_H + 18) * len(df) / (1 - _BAR_PAD)))
    y_sort = list(df[y_field])
    max_v = float(df[x_field].max()) if not df.empty else 1.0
    if x_scale is None:
        x_scale = alt.Scale(domain=[0, max(max_v * 1.22, 1)], nice=False)

    base = alt.Chart(df).encode(
        y=alt.Y(
            f"{y_field}:N",
            sort=y_sort,
            title=None,
            axis=alt.Axis(
                labelLimit=200,
                labelOverlap=False,
                labelPadding=12,
                labelFontSize=12,
                ticks=False,
            ),
            scale=alt.Scale(padding=_BAR_PAD),
        ),
    )
    x_enc = alt.X(
        f"{x_field}:Q",
        title=x_title,
        scale=x_scale,
        axis=alt.Axis(format="~s", grid=True, tickCount=5),
    )
    bars = base.mark_bar(cornerRadiusEnd=5, height=_BAR_H).encode(
        x=x_enc,
        color=alt.Color(
            f"{color_field}:N",
            scale=alt.Scale(domain=y_sort, range=colors[: len(y_sort)]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(f"{y_field}:N", title="Élément"),
            alt.Tooltip(f"{x_field}:Q", title="Lignes", format=","),
            alt.Tooltip("Detail:N", title="Détail"),
        ],
    )
    # Valeurs à droite de la barre (évite le chevauchement avec les labels Y)
    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        fontSize=11,
        fontWeight=600,
        color="#cbd5e1",
    ).encode(
        x=x_enc,
        text=alt.Text("ValueLabel:N"),
    )
    return _style_chart((bars + labels).properties(height=chart_h))


def _load_latest_db_state(root: Path) -> dict | None:
    rep = root / "reports"
    if not rep.exists():
        return None
    files = sorted(rep.glob("db_state_*.json"))
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_run_kpis(last_run: dict | None) -> dict:
    if not last_run:
        return {
            "extracted": 0,
            "cleaned": 0,
            "loaded": 0,
            "deduped": 0,
            "status": "—",
            "n_sources": 0,
            "generated_at": "—",
            "clean_ratio": 0.0,
            "enriched_ratio": 0.0,
        }
    kpi = last_run.get("kpis", {}) if isinstance(last_run, dict) else {}
    source_trace = last_run.get("source_traceability", {}) if isinstance(last_run, dict) else {}
    return {
        "extracted": int(float(kpi.get("extracted", 0) or 0)),
        "cleaned": int(float(kpi.get("cleaned", 0) or 0)),
        "loaded": int(float(kpi.get("loaded", 0) or 0)),
        "deduped": int(float(kpi.get("deduplicated", 0) or 0)),
        "status": str(last_run.get("status", "—") or "—"),
        "n_sources": len(source_trace) if isinstance(source_trace, dict) else 0,
        "generated_at": str(last_run.get("generated_at_utc", "—") or "—"),
        "clean_ratio": float(kpi.get("clean_ratio", 0) or 0),
        "enriched_ratio": float(kpi.get("enriched_ratio", 0) or 0),
    }


def _pipeline_snapshot(ctx: PageContext, db_state: dict | None, kpis: dict) -> dict:
    """Volumes avec périmètre explicite (cumul vs partition du jour)."""
    db_path = _resolve_db_path(ctx.project_root)
    raw_total = _count_raw_sqlite(db_path)
    silver_part, silver_label = _latest_silver(ctx.silver_dir)
    gold_part, gold_label = _latest_gold(ctx.gold_dir)
    merged = ctx.goldai_dir / "merged_all_dates.parquet"
    goldai_total = parquet_row_count_cached(str(merged)) if merged.exists() else 0

    enrichment = (db_state or {}).get("enrichment", {})
    enriched_topics = int(enrichment.get("articles_with_at_least_one_topic", 0) or 0)
    enriched_sentiment = int(enrichment.get("articles_with_sentiment_keyword", 0) or 0)

    run_day = silver_label if silver_label != "—" else gold_label
    silver_daily = int(kpis.get("loaded", 0) or silver_part)

    return {
        "raw_cumulative": raw_total,
        "enriched_topics": enriched_topics or raw_total,
        "enriched_sentiment": enriched_sentiment or raw_total,
        "goldai_cumulative": goldai_total,
        "silver_daily": silver_daily,
        "silver_partition_rows": silver_part,
        "gold_partition_rows": gold_part,
        "run_day": run_day,
        "silver_label": silver_label,
        "gold_label": gold_label,
    }



def _chart_consolidated_stocks(snapshot: dict) -> alt.Chart:
    rows = [
        ("RAW (SQLite)", int(snapshot["raw_cumulative"]), "Stock historique en base"),
        ("Enrichis DB", int(snapshot["enriched_topics"]), "Topics + sentiment en base"),
        ("GoldAI fusion", int(snapshot["goldai_cumulative"]), "Parquet merged_all_dates"),
    ]
    df = pd.DataFrame(
        [
            {
                "Label": label,
                "Lignes": value,
                "ValueLabel": _fmt_num(value),
                "Detail": detail,
            }
            for label, value, detail in rows
        ]
    )
    return _horizontal_bars(
        df,
        colors=["#42a5f5", "#26c6da", "#ab47bc"],
        x_title="Lignes",
    )


def _chart_run_incremental(kpis: dict) -> alt.Chart | None:
    """Run du jour — grain comparable (extraits → nouveaux → doublons)."""
    extracted = int(kpis.get("extracted", 0))
    cleaned = int(kpis.get("cleaned", 0))
    loaded = int(kpis.get("loaded", 0))
    deduped = int(kpis.get("deduped", 0))
    if max(extracted, loaded, deduped) <= 0:
        return None

    rows = [
        ("1 · Extraits (sources)", extracted, "Articles bruts collectés"),
        ("2 · Validés (cleaned)", cleaned, "Après nettoyage qualité"),
        ("3 · Nouveaux → SILVER", loaded, "Lignes réellement chargées"),
        ("4 · Doublons exclus", deduped, "Déjà présents en base"),
    ]
    df = pd.DataFrame(
        [
            {
                "Label": label,
                "Lignes": value,
                "ValueLabel": _fmt_num(value),
                "Detail": detail,
            }
            for label, value, detail in rows
            if value > 0
        ]
    )
    if df.empty:
        return None
    return _horizontal_bars(
        df,
        colors=["#38bdf8", "#22d3ee", "#34d399", "#94a3b8"],
        x_title="Lignes du run (échelle linéaire)",
    )


def _day_label(iso_day: str) -> str:
    if len(iso_day) >= 10:
        parts = iso_day[:10].split("-")
        return f"{parts[2]}/{parts[1]}"
    return iso_day


def _merge_run_status(statuses: list[str]) -> str:
    upper = [str(s).upper() for s in statuses]
    if "FAIL" in upper:
        return "FAIL"
    if "WARN" in upper:
        return "WARN"
    return statuses[0] if statuses else "—"


def _aggregate_runs_by_day(hist: list[dict]) -> dict[str, dict]:
    """Regroupe les run_summary par jour calendaire (somme loaded, statut le plus sévère)."""
    buckets: dict[str, list[dict]] = {}
    for item in hist:
        day = str(item.get("generated_at_utc", ""))[:10]
        if len(day) < 10:
            continue
        buckets.setdefault(day, []).append(item)

    merged: dict[str, dict] = {}
    for day, items in buckets.items():
        loaded_total = 0
        statuses: list[str] = []
        reasons: list[str] = []
        for item in items:
            kpi = item.get("kpis", {}) if isinstance(item, dict) else {}
            loaded_total += int(float(kpi.get("loaded", 0) or 0))
            statuses.append(str(item.get("status", "—")))
            reasons.extend(item.get("reasons", []) or [])
        uniq_reasons = list(dict.fromkeys(str(r) for r in reasons))
        merged[day] = {
            "loaded": loaded_total,
            "status": _merge_run_status(statuses),
            "reasons": uniq_reasons,
            "run_count": len(items),
        }
    return merged


def _build_runs_history_df(
    root: Path, limit: int = 14, hist: list[dict] | None = None
) -> pd.DataFrame | None:
    """DataFrame calendaire : runs + jours sans collecte (ABSENT)."""
    if hist is None:
        hist = run_summary_history_cached(str(root), limit=limit)
    if not hist:
        return None

    by_day = _aggregate_runs_by_day(hist)
    if not by_day:
        return None

    days_sorted = sorted(by_day.keys())
    start = datetime.strptime(days_sorted[0], "%Y-%m-%d").date()
    end = datetime.strptime(days_sorted[-1], "%Y-%m-%d").date()

    rows: list[dict] = []
    prev_absent = False
    cur = start
    while cur <= end:
        iso = cur.isoformat()
        if iso in by_day:
            info = by_day[iso]
            loaded = int(info["loaded"])
            alertes = (
                " · ".join(info["reasons"])
                if info["reasons"]
                else "Aucune alerte"
            )
            if info["run_count"] > 1:
                alertes = f"{info['run_count']} runs ce jour · {alertes}"
            if prev_absent and loaded > 0:
                alertes = f"Rattrapage après jour sans run · {alertes}"
            rows.append(
                {
                    "Date": _day_label(iso),
                    "Ordre": iso,
                    "Lignes": loaded,
                    "ValueLabel": _fmt_num(loaded),
                    "Statut": info["status"],
                    "Alertes": alertes,
                }
            )
            prev_absent = False
        else:
            rows.append(
                {
                    "Date": _day_label(iso),
                    "Ordre": iso,
                    "Lignes": 0,
                    "ValueLabel": "—",
                    "Statut": "ABSENT",
                    "Alertes": "Aucun run — collecte non lancée ce jour.",
                }
            )
            prev_absent = True
        cur += timedelta(days=1)

    df = pd.DataFrame(rows)
    return df if not df.empty else None


def _chart_runs_history(df: pd.DataFrame) -> alt.Chart | None:
    if df is None or df.empty:
        return None

    df = df.copy()
    df["Statut"] = df["Statut"].replace("", "—").fillna("—")

    df_active = df[df["Statut"] != "ABSENT"]
    df_absent = df[df["Statut"] == "ABSENT"]

    chart_h = max(220, 36 * len(df) + 56)
    y_enc = alt.Y(
        "Date:N",
        sort=alt.EncodingSortField(field="Ordre", order="ascending"),
        title=None,
        axis=alt.Axis(labelFontSize=12, labelOverlap=False, ticks=False),
        scale=alt.Scale(padding=0.25),
    )

    layers: list[alt.Chart] = []
    if not df_active.empty:
        base = alt.Chart(df_active).encode(y=y_enc)
        bars = base.mark_bar(cornerRadiusEnd=4, height=22).encode(
            x=alt.X("Lignes:Q", title="Nouvelles lignes chargées", axis=alt.Axis(format=",")),
            color=alt.Color(
                "Statut:N",
                scale=altair_status_scale(),
                legend=alt.Legend(title="Quality gate", orient="bottom", labelLimit=100),
            ),
            tooltip=[
                alt.Tooltip("Ordre:N", title="Date"),
                alt.Tooltip("Lignes:Q", title="Lignes chargées", format=","),
                alt.Tooltip("Statut:N", title="Statut"),
                alt.Tooltip("Alertes:N", title="Alertes / reasons"),
            ],
        )
        labels = base.mark_text(
            align="left", baseline="middle", dx=6, fontSize=11, color="#f1f5f9"
        ).encode(
            x="Lignes:Q",
            text="ValueLabel:N",
        )
        layers.extend([bars, labels])

    if not df_absent.empty:
        absent_base = alt.Chart(df_absent).encode(y=y_enc)
        absent_text = absent_base.mark_text(
            align="left",
            baseline="middle",
            dx=4,
            fontSize=11,
            color="#94a3b8",
            fontStyle="italic",
        ).encode(
            text=alt.value("Aucun run"),
            tooltip=[
                alt.Tooltip("Ordre:N", title="Date"),
                alt.Tooltip("Alertes:N", title="Détail"),
            ],
        )
        layers.append(absent_text)

    if not layers:
        return None

    chart = alt.layer(*layers).properties(height=chart_h)
    return _style_chart(chart)


def _runs_with_alerts(hist: list[dict]) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    for item in hist:
        reasons = item.get("reasons", []) if isinstance(item, dict) else []
        status = str(item.get("status", "—"))
        if status != "WARN" and not reasons:
            continue
        kpi = item.get("kpis", {}) if isinstance(item, dict) else {}
        day = str(item.get("generated_at_utc", ""))[:10]
        rows.append(
            {
                "Date": day or "—",
                "Statut": status,
                "Lignes": int(float(kpi.get("loaded", 0) or 0)),
                "Alertes": " · ".join(str(r) for r in reasons) if reasons else "—",
            }
        )
    return pd.DataFrame(rows)


def render(ctx: PageContext) -> None:
    root = ctx.project_root
    db_state = latest_db_state_cached(str(root))
    last_run, _ = latest_run_summary_reports(root)
    kpis = _parse_run_kpis(last_run)
    snapshot = _pipeline_snapshot(ctx, db_state, kpis)
    run_day = snapshot["run_day"] or "jour"

    st.markdown(
        """
        <div class="ds-hero">
          <h3>Pipeline des données</h3>
          <p>Collecte → nettoyage → enrichissement → stock consolidé</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_data_journey_strip(
        lead="Même empreinte, même article — de la collecte à l'enrichissement IA."
    )
    render_article_journey(ctx, demo_mode=True)

    st.markdown('<p class="ds-section">Volumes</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RAW", f"{snapshot['raw_cumulative']:,}")
    c2.metric("Enrichis", f"{snapshot['enriched_topics']:,}")
    c3.metric("GoldAI", f"{snapshot['goldai_cumulative']:,}")
    c4.metric(f"Nouveaux ({run_day})", f"{snapshot['silver_daily']:,}")

    st.altair_chart(_chart_consolidated_stocks(snapshot), use_container_width=True)

    st.markdown('<p class="ds-section">Run du jour</p>', unsafe_allow_html=True)
    inc_chart = _chart_run_incremental(kpis)
    if inc_chart:
        st.altair_chart(inc_chart, use_container_width=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Extraits", f"{kpis['extracted']:,}")
    m2.metric("Doublons filtrés", f"{kpis['deduped']:,}")
    m3.metric("Statut", kpis["status"])

    render_last_run_proof_full(ctx, demo_mode=True)

    with st.expander("Historique des runs", expanded=False):
        hist = run_summary_history_cached(str(root), limit=14)
        hist_df = _build_runs_history_df(root, limit=14, hist=hist)
        hist_chart = _chart_runs_history(hist_df) if hist_df is not None else None
        if hist_chart and hist:
            st.altair_chart(hist_chart, use_container_width=True)
            counts: dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0}
            for item in hist:
                status = str(item.get("status", "—")).upper()
                if status in counts:
                    counts[status] += 1
            absent_n = 0
            catch_up_n = 0
            if hist_df is not None and not hist_df.empty:
                absent_n = int((hist_df["Statut"] == "ABSENT").sum())
                catch_up_n = int(
                    hist_df["Alertes"]
                    .astype(str)
                    .str.startswith("Rattrapage")
                    .sum()
                )
            st.caption(
                f"Période {hist_df['Ordre'].min()} → {hist_df['Ordre'].max()} · "
                f"{counts['PASS']} PASS · {counts['WARN']} WARN · {counts['FAIL']} FAIL · "
                f"{absent_n} jour(s) sans run (*Aucun run*) · "
                f"survolez une barre pour le détail."
            )
            if catch_up_n > 0:
                st.caption(
                    f"{catch_up_n} run(s) marqué(s) *Rattrapage* : collecte le lendemain "
                    f"d'un jour sans run — le volume chargé permet de vérifier la reprise."
                )
            alerts_df = _runs_with_alerts(hist)
            if not alerts_df.empty:
                st.markdown("**Alertes quality gate**")
                st.caption(
                    "WARN = le pipeline a tourné et a chargé des données, "
                    "mais un seuil ou une source mérite attention."
                )
                st.dataframe(alerts_df, use_container_width=True, hide_index=True)
            else:
                st.caption("Aucune alerte sur les runs affichés.")
        else:
            st.caption("Historique indisponible.")
