"""
Page cockpit : onglet pipeline.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
)
from src.streamlit._cockpit_helpers import (
    latest_run_summary_reports as _latest_run_summary_reports,
)
from src.streamlit._cockpit_helpers import (
    parquet_row_count_cached as _parquet_row_count_cached,
)
from src.streamlit._cockpit_helpers import (
    read_parquet_cached as _read_parquet_cached,
)
from src.streamlit._cockpit_helpers import (
    run_summary_history as _run_summary_history,
)
from src.streamlit.data_lineage import render_row_trace
from src.streamlit.metrics import (
    build_enrichment_table as _build_enrichment_table,
)
from src.streamlit.cockpit_ux import render_section_title
from src.streamlit.pipeline_proof import (
    render_article_journey,
    render_last_run_proof_full,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

_STOCK_LAYER_LABELS: dict[str, str] = {
    "3. GOLD": "GOLD — snapshot du jour",
    "4. GoldAI": "GoldAI — stock fusionné",
    "5. Copie IA (train)": "Copie IA — split entraînement",
}
_STOCK_LAYER_COLORS = ["#06b6d4", "#14b8a6", "#f59e0b"]


def _style_expert_altair(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeWidth=0, fill="transparent", clip=False)
        .configure_axis(
            gridColor="#334155",
            domainColor="#475569",
            labelColor="#cbd5e1",
            titleColor="#e2e8f0",
            tickColor="#475569",
        )
        .configure_title(color="#e2e8f0", fontSize=14, anchor="start")
        .configure_header(
            labelColor="#cbd5e1",
            labelFontSize=12,
            labelFontWeight="normal",
        )
        .configure_facet(spacing=10)
    )


def _bar_chart(
    rows: list[dict],
    title: str,
    *,
    single_color: str | None = None,
    step_colors: list[str] | None = None,
    bar_height: int = 36,
    row_height: int = 58,
    labels_inside_only: bool = False,
    y_key: str = "Étape",
) -> alt.Chart | None:
    if not rows:
        return None
    chart_df = pd.DataFrame(
        [
            {
                "Étape": r.get(y_key, r.get("Étape", "—")),
                "Lignes": r["_lignes"],
                "Label": f"{r['_lignes']:,}".replace(",", "\u202f"),
                "Périmètre": r.get("Périmètre", ""),
            }
            for r in rows
        ]
    )
    max_v = float(chart_df["Lignes"].max()) if not chart_df.empty else 1.0
    label_threshold = 0.0 if labels_inside_only else max(max_v * 0.14, 1.0)
    x_scale = alt.Scale(domain=[0, max(max_v * 1.38, 1)], nice=False, zero=True)
    x_enc = alt.X(
        "Lignes:Q",
        scale=x_scale,
        title="Lignes",
        axis=alt.Axis(format="~s", grid=True, tickCount=5),
    )
    y_enc = alt.Y(
        "Étape:N",
        sort=None,
        title=None,
        axis=alt.Axis(
            labelLimit=280,
            labelOverlap=False,
            labelPadding=8,
            labelFontSize=13,
            ticks=False,
        ),
        scale=alt.Scale(padding=0.28),
    )
    tooltips = [
        alt.Tooltip("Étape:N", title="Couche"),
        alt.Tooltip("Lignes:Q", title="Lignes", format=","),
    ]
    if (chart_df["Périmètre"] != "").any():
        tooltips.insert(1, alt.Tooltip("Périmètre:N", title="Périmètre"))

    base = alt.Chart(chart_df).encode(y=y_enc)
    if single_color:
        bars = base.mark_bar(cornerRadiusEnd=5, height=bar_height, color=single_color).encode(
            x=x_enc,
            tooltip=tooltips,
        )
    else:
        palette = step_colors or ["#06b6d4"] * len(chart_df)
        bars = base.mark_bar(cornerRadiusEnd=5, height=bar_height).encode(
            x=x_enc,
            color=alt.Color(
                "Étape:N",
                sort=None,
                scale=alt.Scale(
                    domain=chart_df["Étape"].tolist(),
                    range=palette[: len(chart_df)],
                ),
                legend=None,
            ),
            tooltip=tooltips,
        )
    labels_in = base.mark_text(
        align="right",
        baseline="middle",
        dx=-10,
        fontSize=13,
        fontWeight=700,
        color="#ffffff",
    ).encode(
        x=x_enc,
        text="Label:N",
    ).transform_filter(alt.datum.Lignes >= label_threshold)
    layers: list[alt.Chart] = [bars, labels_in]
    if not labels_inside_only:
        labels_out = base.mark_text(
            align="left",
            baseline="middle",
            dx=8,
            fontSize=13,
            fontWeight=700,
            color="#f1f5f9",
        ).encode(
            x=x_enc,
            text="Label:N",
        ).transform_filter(alt.datum.Lignes < label_threshold)
        layers.append(labels_out)
    chart = alt.layer(*layers).properties(
        title=title,
        height=max(180, row_height * len(chart_df)),
        padding={"left": 4, "top": 8, "right": 88, "bottom": 4},
    )
    return _style_expert_altair(chart)


def _stock_export_chart(rows: list[dict]) -> list[alt.Chart]:
    """Une barre par couche — même rendu que Run du jour, échelle propre à chaque chart."""
    charts: list[alt.Chart] = []
    for i, row in enumerate(rows):
        short = _STOCK_LAYER_LABELS.get(row["Étape"], row["Étape"])
        chart_row = {**row, "Étape": short}
        color = _STOCK_LAYER_COLORS[i % len(_STOCK_LAYER_COLORS)]
        chart = _bar_chart(
            [chart_row],
            title=short,
            single_color=color,
            bar_height=40,
            row_height=72,
            labels_inside_only=True,
        )
        if chart:
            charts.append(chart)
    return charts


def _render_run_du_jour(project_root: Path, merged_path: Path) -> None:
    """Volumes du dernier run E1 (grain jour)."""
    last_run, _ = _latest_run_summary_reports(project_root)
    if last_run:
        kpi = last_run.get("kpis", {}) if isinstance(last_run, dict) else {}
        extracted = int(float(kpi.get("extracted", 0) or 0))
        cleaned = int(float(kpi.get("cleaned", 0) or 0))
        loaded = int(float(kpi.get("loaded", 0) or 0))
        deduped = int(float(kpi.get("deduplicated", 0) or 0))
        run_status = str(last_run.get("status", "—") or "—")
        source_trace = last_run.get("source_traceability", {}) if isinstance(last_run, dict) else {}
        n_sources = len(source_trace) if isinstance(source_trace, dict) else 0
    else:
        extracted = cleaned = loaded = deduped = 0
        run_status = "—"
        n_sources = 0

    goldai_total = (
        _parquet_row_count_cached(str(merged_path)) if merged_path.exists() else 0
    )

    def _pct(num: int, denom: int) -> str:
        if denom <= 0:
            return "—"
        return f"{(num/denom)*100:.1f}%"

    journey_steps = [
        {"etape": "1. Extraits", "lignes": extracted, "lecture": f"{n_sources} sources"},
        {"etape": "2. Validés", "lignes": cleaned, "lecture": f"nettoyage {_pct(cleaned, extracted)}"},
        {
            "etape": "3. Nouveaux (loaded)",
            "lignes": loaded,
            "lecture": f"dédup {deduped:,} · nouveauté {_pct(loaded, cleaned)}",
        },
        {"etape": "4. → GoldAI", "lignes": loaded, "lecture": "incrément fusion"},
    ]
    cols = st.columns(len(journey_steps))
    for col, step in zip(cols, journey_steps, strict=False):
        with col, st.container(border=True):
            st.caption(step["etape"])
            st.metric(" ", f"{step['lignes']:,}", label_visibility="collapsed")
            st.caption(step["lecture"])

    st.caption(
        f"Statut **{run_status}** · stock GoldAI **{goldai_total:,}** lignes "
        f"(+{loaded:,} ce run)."
    )
    journey_df = pd.DataFrame(
        [{"Étape": s["etape"], "Lignes": s["lignes"]} for s in journey_steps if s["lignes"] > 0]
    )
    if not journey_df.empty:
        chart = (
            alt.Chart(journey_df)
            .mark_bar(cornerRadiusEnd=4, height=28, color="#06b6d4")
            .encode(
                y=alt.Y("Étape:N", sort=None, title=None),
                x=alt.X("Lignes:Q", title="Lignes du jour"),
            )
            .properties(height=max(160, 52 * len(journey_df)))
        )
        st.altair_chart(chart, use_container_width=True)
    elif not last_run:
        st.info("Aucun run récent — lancez le pipeline E1 (Pilotage → Actions).")


def _render_run_history(project_root: Path) -> None:
    """Tableau des 10 derniers run_summary."""
    hist = _run_summary_history(project_root, limit=10)
    if not hist:
        st.info("Aucun `run_summary_*.json` dans reports/.")
        return
    rows = []
    pass_count = warn_rows = 0
    for item in hist:
        status = str(item.get("status", "—"))
        if status == "PASS":
            pass_count += 1
        kpi = item.get("kpis", {}) if isinstance(item, dict) else {}
        reasons_item = item.get("reasons", []) if isinstance(item, dict) else []
        rows.append(
            {
                "Fichier": item.get("_file", "—"),
                "Statut": status,
                "Loaded": int(float(kpi.get("loaded", 0) or 0)),
                "Durée (s)": round(float(kpi.get("run_duration_sec", 0) or 0), 1),
            }
        )
        if status == "WARN":
            warn_rows += 1
    st.caption(f"Stabilité : {pass_count}/{len(hist)} PASS")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if warn_rows:
        st.warning(f"{warn_rows} run(s) en WARN — détail dans Vue d'ensemble ou Infra & MongoDB.")


def _render_fusion_block(
    project_root: Path,
    gold_dir: Path,
    merged_path: Path,
    meta_path: Path,
    show_advanced: bool,
) -> None:
    """Fusion GOLD → GoldAI (sans doublon d'aperçus)."""
    import json

    dates_in_goldai: list = []
    if meta_path.exists():
        dates_in_goldai = json.loads(meta_path.read_text(encoding="utf-8")).get("dates_included", [])

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
    if not gold_dates:
        st.info("Aucune partition GOLD — lancez d'abord le pipeline E1.")
        return

    selected_date = st.select_slider("Date GOLD à fusionner", options=gold_dates, value=gold_dates[0])
    already_merged = selected_date in set(dates_in_goldai)
    gold_file = gold_dir / f"date={selected_date}" / "articles.parquet"

    cols_min = ("id", "fingerprint", "url", "title", "source", "collected_at", "sentiment")
    cols_goldai = ("id", "fingerprint", "url", "title", "source", "collected_at", "sentiment", "raw_data_id")
    df_gold = _read_parquet_cached(str(gold_file), cols_min) if gold_file.exists() else None
    df_goldai = _read_parquet_cached(str(merged_path), cols_goldai) if merged_path.exists() else None
    n_gold = _parquet_row_count_cached(str(gold_file)) if gold_file.exists() else 0
    n_goldai = _parquet_row_count_cached(str(merged_path)) if merged_path.exists() else 0

    def _stable_keys_local(df: pd.DataFrame) -> pd.Series:
        if "id" in df.columns:
            s = df["id"]
        elif "fingerprint" in df.columns:
            s = df["fingerprint"]
        elif "url" in df.columns:
            s = df["url"]
        else:
            s = pd.Series([None] * len(df), index=df.index, dtype="object")
        return s.astype("string").str.strip().fillna("").replace({"<NA>": "", "nan": "", "None": ""})

    n_new, df_new, n_overlap = 0, None, 0
    ids: set = set()
    if df_gold is not None and df_goldai is not None:
        keys_gold = _stable_keys_local(df_gold)
        keys_goldai = _stable_keys_local(df_goldai)
        ids = set(keys_goldai[keys_goldai != ""])
        keys_gold_set = set(keys_gold[keys_gold != ""])
        n_overlap = len(keys_gold_set.intersection(ids))
        df_new = df_gold[(keys_gold != "") & (~keys_gold.isin(ids))]
        n_new = len(df_new)

    c1, c2, c3 = st.columns(3)
    c1.metric("GOLD (date)", f"{n_gold:,}")
    c2.metric("GoldAI (stock)", f"{n_goldai:,}")
    c3.metric("Nouvelles lignes", f"{n_new:,}")

    if already_merged:
        st.info("Cette date est déjà dans GoldAI — relancer n'ajoutera rien.")
    elif n_new == 0 and df_gold is not None:
        st.info("Lot entièrement en doublon.")
    elif n_new > 0:
        st.success(f"Prévision : **{n_new:,}** ligne(s) à ajouter.")

    if st.button("Fusionner GoldAI", type="primary", use_container_width=True, key="fusion_goldai_btn"):
        with st.spinner("Fusion en cours…"):
            proc = subprocess.run(
                [sys.executable, "scripts/merge_parquet_goldai.py"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                timeout=600,
            )
        if proc.returncode == 0 and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            apres = meta.get("total_rows", n_goldai + n_gold)
            st.session_state["fusion_success"] = {
                "avant": n_goldai,
                "apres": apres,
                "ajoutes": apres - n_goldai,
                "date": selected_date,
            }
        elif proc.returncode != 0:
            st.session_state["fusion_error"] = (proc.stderr or proc.stdout or "")[-500:]
        st.rerun()

    if show_advanced and df_gold is not None and df_goldai is not None:
        tab_new, tab_gold, tab_goldai = st.tabs(["Nouvelles lignes", "GOLD du jour", "GoldAI"])
        with tab_new:
            if df_new is not None and not df_new.empty:
                cols = [c for c in ["id", "title", "source", "sentiment"] if c in df_new.columns]
                st.dataframe(df_new[cols].head(80) if cols else df_new.head(80), use_container_width=True)
            else:
                st.caption("Aucune ligne nouvelle.")
        with tab_gold:
            cols = [c for c in ["id", "title", "source", "collected_at"] if c in df_gold.columns]
            st.dataframe(df_gold[cols].head(80) if cols else df_gold.head(80), use_container_width=True)
        with tab_goldai:
            cols = [c for c in ["id", "title", "source", "sentiment"] if c in df_goldai.columns]
            st.dataframe(df_goldai[cols].head(80) if cols else df_goldai.head(80), use_container_width=True)


def render(ctx: PageContext) -> None:
    PROJECT_ROOT = ctx.project_root
    show_advanced = ctx.show_advanced
    gold_dir = ctx.gold_dir
    goldai_dir = ctx.goldai_dir

    gold_dir = PROJECT_ROOT / "data" / "gold"
    goldai_dir = PROJECT_ROOT / "data" / "goldai"
    merged_path = goldai_dir / "merged_all_dates.parquet"
    meta_path = goldai_dir / "metadata.json"

    render_section_title("Run du jour")
    st.caption(
        "Volumes collectés lors du dernier run. Preuves, lineage et fusion → sections repliées. "
        "Fichiers couche par couche → sous-onglet **Explorer les fichiers**."
    )
    _render_run_du_jour(PROJECT_ROOT, merged_path)

    with st.expander("Preuve d'enrichissement (db_state · PDF · CSV)", expanded=False):
        render_last_run_proof_full(ctx, embedded=True)

    with st.expander("Lineage — article & trace IDs", expanded=False):
        render_article_journey(ctx)
        render_row_trace(ctx)

    with st.expander("Historique quality gate", expanded=False):
        _render_run_history(PROJECT_ROOT)

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

    with st.expander("Fusion GOLD → GoldAI", expanded=False):
        st.caption("Compare le lot GOLD sélectionné au stock consolidé et lance la fusion.")
        _render_fusion_block(
            PROJECT_ROOT, gold_dir, merged_path, meta_path, show_advanced
        )

    if not show_advanced:
        return

    st.divider()
    render_section_title("Profil colonnes par couche")
    st.caption(
        "Tableau de profil colonnes + couverture sentiment/topics. "
        "Les volumes ne se comparent pas entre eux sans lire la colonne **Périmètre**."
    )
    enrich_rows = _build_enrichment_table(PROJECT_ROOT)
    if enrich_rows:
        STAGE_META: dict[str, dict[str, str]] = {
            "1. RAW": {
                "perimetre": "Lot du jour (brut)",
                "explain": "Extraits collectés lors du dernier run, avant nettoyage.",
                "group": "run",
            },
            "2. SILVER": {
                "perimetre": "Lot du jour (nettoyé)",
                "explain": "Articles validés du run — même ordre de grandeur que le KPI « loaded ».",
                "group": "run",
            },
            "3. GOLD": {
                "perimetre": "Snapshot enrichi du jour",
                "explain": "Export parquet complet de la partition GOLD (enrichi, régénéré à chaque run).",
                "group": "stock",
            },
            "4. GoldAI": {
                "perimetre": "Stock historique fusionné",
                "explain": "merged_all_dates.parquet — toutes les dates dédupliquées.",
                "group": "stock",
            },
            "5. Copie IA (train)": {
                "perimetre": "Split entraînement 70 %",
                "explain": "Sous-ensemble train.parquet pour le fine-tuning.",
                "group": "stock",
            },
        }
        COLOR_RUN = "#8b5cf6"

        display_rows: list[dict] = []
        prev_cols: set = set()
        prev_count: int | None = None
        for p in enrich_rows:
            meta = STAGE_META.get(p["stage"], {})
            new_cols = set(p["cols_list"]) - prev_cols
            key_new = [
                c
                for c in ["sentiment", "topic_1", "topic_2", "sentiment_score", "quality_score"]
                if c in new_cols
            ]
            added_cols = len(new_cols)
            if prev_count is None:
                delta_rows = "—"
            else:
                diff = p["lignes"] - prev_count
                delta_rows = f"{diff:+,}" if diff != 0 else "0"
            display_rows.append(
                {
                    "Étape": p["stage"],
                    "Périmètre": meta.get("perimetre", "—"),
                    "Lignes": f"{p['lignes']:,}",
                    "Δ lignes vs étape N-1": delta_rows,
                    "Colonnes": p["colonnes"],
                    "Colonnes ajoutées": f"+{added_cols}" if added_cols else "—",
                    "Sentiment": "Oui" if p["has_sentiment"] else "Non",
                    "Topics": "Oui" if p["has_topic"] else "Non",
                    "Couverture sentiment": f"{p['sentiment_coverage']:.0%}"
                    if p["has_sentiment"]
                    else "—",
                    "Couverture topics": f"{p['topic_coverage']:.0%}"
                    if p["has_topic"]
                    else "—",
                    "Ce que compte la ligne": meta.get("explain", "—"),
                    "_lignes": int(p["lignes"]),
                    "_group": meta.get("group", "stock"),
                    "_key_cols": ", ".join(key_new) if key_new else "—",
                }
            )
            prev_cols = set(p["cols_list"])
            prev_count = p["lignes"]

        df_display = pd.DataFrame(display_rows).drop(
            columns=["_lignes", "_group", "_key_cols"]
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        run_chart_rows = [r for r in display_rows if r["_group"] == "run"]
        stock_chart_rows = [r for r in display_rows if r["_group"] == "stock"]

        run_chart = _bar_chart(
            run_chart_rows,
            "Run du jour (RAW → SILVER)",
            single_color=COLOR_RUN,
            bar_height=40,
            row_height=72,
        )
        if run_chart:
            st.altair_chart(run_chart, use_container_width=True)
        else:
            st.caption("Pas de partition RAW/SILVER du jour.")

        if stock_chart_rows:
            st.caption(
                "Stocks / exports — **une échelle par couche** "
                "(snapshot jour, stock fusionné, split IA : périmètres différents)."
            )
            metric_cols = st.columns(min(len(stock_chart_rows), 3))
            for col, row in zip(metric_cols, stock_chart_rows, strict=False):
                short = _STOCK_LAYER_LABELS.get(row["Étape"], row["Étape"])
                with col:
                    st.metric(
                        short,
                        f"{row['_lignes']:,}".replace(",", "\u202f"),
                        help=row.get("Périmètre", ""),
                    )
            for stock_chart in _stock_export_chart(stock_chart_rows):
                st.altair_chart(stock_chart, use_container_width=True)
        else:
            st.caption("Pas de fichier GOLD/GoldAI disponible.")
    else:
        st.info("Aucune donnée disponible. Lancez d'abord le pipeline E1.")
