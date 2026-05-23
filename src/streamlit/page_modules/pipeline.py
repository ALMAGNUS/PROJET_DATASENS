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
from src.streamlit.pipeline_proof import (
    render_article_journey,
    render_last_run_proof_full,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    PROJECT_ROOT = ctx.project_root
    show_advanced = ctx.show_advanced
    gold_dir = ctx.gold_dir
    goldai_dir = ctx.goldai_dir

    gold_dir = PROJECT_ROOT / "data" / "gold"
    goldai_dir = PROJECT_ROOT / "data" / "goldai"
    merged_path = goldai_dir / "merged_all_dates.parquet"
    meta_path = goldai_dir / "metadata.json"

    # Suivi visuel d'un article à travers les 5 étapes du lineage.
    # Placé en tête : audit visuel direct de l'enrichissement et de la persistance.
    render_article_journey(ctx)
    st.divider()

    # Trace par les lignes : MEMES articles dans SQLite, GOLD, GoldAI, GridFS.
    render_row_trace(ctx)
    st.divider()

    # Preuve chiffrée du dernier run (deltas par étape + lignes réelles).
    render_last_run_proof_full(ctx)
    st.divider()

    run_summary, _run_summary_prev = _latest_run_summary_reports(PROJECT_ROOT)
    if run_summary:
        k = run_summary.get("kpis", {}) if isinstance(run_summary, dict) else {}
        reasons = run_summary.get("reasons", []) if isinstance(run_summary, dict) else []
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Statut", str(run_summary.get("status", "—")))
        c2.metric("Chargées", f"{int(k.get('loaded', 0)):,}")
        c3.metric("Ratio net", f"{float(k.get('clean_ratio', 0.0)) * 100:.1f}%")
        c4.metric("Durée", f"{float(k.get('run_duration_sec', 0.0)):.1f}s")
        if reasons:
            with st.expander("WARN_REASONS (run summary)", expanded=False):
                for r in reasons:
                    st.write(f"- {r}")
        hist = _run_summary_history(PROJECT_ROOT, limit=10)
        if hist:
            rows = []
            pass_count = 0
            warn_rows = []
            for item in hist:
                status = str(item.get("status", "—"))
                if status == "PASS":
                    pass_count += 1
                kpi = item.get("kpis", {}) if isinstance(item, dict) else {}
                reasons_item = item.get("reasons", []) if isinstance(item, dict) else []
                rows.append(
                    {
                        "execution_file": item.get("_file", "—"),
                        "status": status,
                        "loaded": int(float(kpi.get("loaded", 0.0) or 0.0)),
                        "clean_ratio_%": round(float(kpi.get("clean_ratio", 0.0) or 0.0) * 100, 1),
                        "enriched_ratio_%": round(
                            float(kpi.get("enriched_ratio", 0.0) or 0.0) * 100, 1
                        ),
                        "duration_s": round(float(kpi.get("run_duration_sec", 0.0) or 0.0), 1),
                    }
                )
                if status == "WARN":
                    warn_rows.append(
                        {
                            "execution_file": item.get("_file", "—"),
                            "loaded": int(float(kpi.get("loaded", 0.0) or 0.0)),
                            "reasons": " | ".join(str(r) for r in reasons_item) if reasons_item else "—",
                        }
                    )
            pass_rate = (pass_count / len(hist)) * 100 if hist else 0.0
            st.caption(f"Stabilité quality gate (10 derniers runs max): {pass_rate:.0f}% PASS")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown("#### Vue anomalies (quality gates)")
            if warn_rows:
                st.warning(f"{len(warn_rows)} run(s) en WARN détecté(s) dans l'historique.", icon="⚠️")
                st.dataframe(pd.DataFrame(warn_rows), use_container_width=True, hide_index=True)
            else:
                st.success("Aucune anomalie quality gate détectée dans l'historique chargé.", icon="✅")
    else:
        st.info("Aucun `run_summary_*.json` trouvé dans `reports/`.")
    st.divider()

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
    cols_min = ("id", "fingerprint", "url", "title", "source", "collected_at", "sentiment")
    cols_goldai = ("id", "fingerprint", "url", "title", "source", "collected_at", "sentiment", "raw_data_id")
    if gold_file and gold_file.exists():
        df_gold = _read_parquet_cached(str(gold_file), cols_min)
    if merged_path.exists():
        df_goldai = _read_parquet_cached(str(merged_path), cols_goldai)
    n_gold = _parquet_row_count_cached(str(gold_file)) if (gold_file and gold_file.exists()) else 0
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
            st.info("Aucun lot GOLD chargé pour la date sélectionnée.")
    with w2:
        st.markdown("#### 2. GoldAI")
        if df_goldai is not None:
            st.metric("Lignes", f"{n_goldai:,}")
            st.caption("Stock long terme consolidé.")
        else:
            st.info("Stock GoldAI indisponible. Lancez une fusion pour le créer.")
    with w3:
        st.markdown("#### 3. À ajouter")
        st.metric("Nouvelles lignes", f"{n_new:,}")
        if df_gold is not None and df_goldai is not None:
            if n_overlap > 0:
                st.caption(f"{n_overlap:,} déjà présentes (non ajoutées).")
            if n_new == 0:
                st.caption(
                    "Date déjà intégrée."
                    if already_merged_selected
                    else "Lot entièrement dédupliqué."
                )
    st.markdown("#### Preuve d'enrichissement GOLD -> GoldAI")
    if df_gold is not None and df_goldai is not None:
        added_pct = (n_new / n_gold * 100.0) if n_gold > 0 else 0.0
        c_proof1, c_proof2, c_proof3, c_proof4 = st.columns(4)
        c_proof1.metric("GOLD du jour", f"{n_gold:,}")
        c_proof2.metric("Déjà présents", f"{n_overlap:,}")
        c_proof3.metric("Nouvelles lignes", f"{n_new:,}", delta=f"{added_pct:.1f}% du lot")
        c_proof4.metric("GoldAI actuel", f"{n_goldai:,}")
        if n_new > 0:
            st.success(
                f"Enrichissement visible: le lot GOLD du jour apporte **{n_new:,}** nouvelles lignes "
                "au stock GoldAI consolidé."
            )
        else:
            st.info(
                "Aucune nouvelle ligne détectée sur ce lot: la date est déjà fusionnée "
                "ou le lot est entièrement dédupliqué."
            )
        st.markdown("**Lignes incrémentales (échantillon)**")
        if df_new is not None and not df_new.empty:
            cols_lineage = [c for c in ["id", "title", "source", "collected_at", "sentiment"] if c in df_new.columns]
            preview_new_lines = (
                df_new[cols_lineage].copy().head(30)
                if cols_lineage
                else df_new.copy().head(30)
            )
            st.caption(
                "Ces lignes sont réellement absentes de GoldAI avant fusion "
                "(comparaison par identifiant stable id/fingerprint/url)."
            )
            st.dataframe(preview_new_lines, use_container_width=True, hide_index=True)
        else:
            st.caption(
                "Aucune ligne nouvelle à afficher sur ce lot "
                "(déjà fusionné ou entièrement en doublon)."
            )
    else:
        st.info("Preuve indisponible: chargez un lot GOLD et le stock GoldAI.")
    st.markdown("#### Résultat de la fusion")
    if df_gold is not None and df_goldai is not None:
        n_res_keys = len(ids.union(keys_gold_set))
        n_added = n_new

        if already_merged_selected:
            st.info(
                "Cette date est déjà intégrée dans le stock consolidé GoldAI. "
                "Relancer la fusion n'ajoutera aucune nouvelle ligne."
            )
        elif n_added == 0:
            st.info("Lot entièrement constitué de doublons — aucune ligne à ajouter.")
        else:
            st.success(
                f"Fusion prévisionnelle : **{n_added:,}** nouvelle(s) ligne(s) "
                "seront ajoutées à GoldAI."
            )

        if show_advanced:
            with st.expander("Détail technique (administrateurs)", expanded=False):
                proof_df = pd.DataFrame(
                    [
                        {"Indicateur": "IDs GoldAI existants (avant fusion)", "Valeur": n_goldai_keys},
                        {"Indicateur": "IDs GOLD du jour", "Valeur": n_gold_keys},
                        {"Indicateur": "Recouvrement (doublons détectés)", "Valeur": n_overlap},
                        {"Indicateur": "Nouveaux IDs", "Valeur": n_new},
                        {"Indicateur": "Total attendu après fusion", "Valeur": n_res_keys},
                    ]
                )
                st.dataframe(proof_df, use_container_width=True, hide_index=True)
                if n_gold_missing_keys or n_goldai_missing_keys:
                    st.caption(
                        f"Lignes sans identifiant stable ignorées dans le contrôle : "
                        f"GOLD {n_gold_missing_keys:,} · GoldAI {n_goldai_missing_keys:,}."
                    )

            tab_new, tab_gold_prev, tab_goldai_prev = st.tabs(
                ["Nouvelles lignes", "Aperçu GOLD du jour", "Aperçu GoldAI"]
            )
            with tab_new:
                if df_new is not None and not df_new.empty:
                    cols_focus = [c for c in ["id", "title", "source", "collected_at"] if c in df_new.columns]
                    preview_new = df_new[cols_focus].copy().head(120) if cols_focus else df_new.copy().head(120)
                    if "id" in preview_new.columns:
                        preview_new["id"] = (
                            preview_new["id"]
                            .astype("string")
                            .fillna("—")
                            .replace({"<NA>": "—", "": "—"})
                        )
                    st.dataframe(preview_new, use_container_width=True, height=300)
                elif df_new is not None:
                    st.info("Aucune nouvelle ligne à afficher.")
                else:
                    st.info("Aucun aperçu disponible: chargez GOLD puis GoldAI.")
            with tab_gold_prev:
                cols_focus = [c for c in ["id", "title", "source", "collected_at"] if c in df_gold.columns]
                gold_view = df_gold[cols_focus].copy().head(220) if cols_focus else df_gold.copy().head(220)
                if not gold_view.empty:
                    key_series = _stable_keys_local(gold_view)
                    gold_view.insert(
                        0,
                        "Statut",
                        key_series.apply(
                            lambda v: "Nouveau" if v != "" and v not in ids
                            else "Déjà présent" if v != ""
                            else "Sans identifiant"
                        ),
                    )
                    gold_view = gold_view.sort_values(by="Statut", ascending=True)
                st.dataframe(gold_view.head(120), use_container_width=True, height=320)
            with tab_goldai_prev:
                cols_focus_goldai = [c for c in ["id", "title", "source", "collected_at", "sentiment"] if c in df_goldai.columns]
                preview_goldai = df_goldai[cols_focus_goldai].copy().head(120) if cols_focus_goldai else df_goldai.copy().head(120)
                st.dataframe(preview_goldai, use_container_width=True, height=320)
        else:
            st.caption("Aperçus détaillés et preuve technique complète disponibles en mode Expert.")
    elif df_goldai is not None:
        st.metric("Lignes", f"{n_goldai:,}")
    else:
        st.info("Aucune donnée GoldAI disponible pour afficher le résultat de fusion.")

    st.divider()
    st.markdown("### Pipeline du jour")
    st.caption(
        "Lecture cohérente du run courant : volumes par étape, même grain (jour), "
        "même direction (filtrage / déduplication). À ne pas confondre avec les stocks cumulés ci-dessus."
    )

    last_run, _prev_run = _latest_run_summary_reports(PROJECT_ROOT)
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

    goldai_total_after = (
        _parquet_row_count_cached(str(merged_path)) if merged_path.exists() else 0
    )
    goldai_growth = loaded

    def _pct(num: int, denom: int) -> str:
        if denom <= 0:
            return "—"
        return f"{(num/denom)*100:.1f}%"

    journey_steps = [
        {
            "etape": "1. Extraits (sources)",
            "lignes": extracted,
            "lecture": (
                f"articles bruts collectés sur {n_sources} sources actives"
                if n_sources
                else "articles bruts collectés sur les sources actives"
            ),
        },
        {
            "etape": "2. Validés (cleaned)",
            "lignes": cleaned,
            "lecture": f"après nettoyage, ratio {_pct(cleaned, extracted)}",
        },
        {
            "etape": "3. Nouveaux (dédupliqués)",
            "lignes": loaded,
            "lecture": (
                f"déjà connus filtrés : {deduped:,} | "
                f"taux de nouveauté {_pct(loaded, cleaned)}"
            ),
        },
        {
            "etape": "4. Ajoutés à GoldAI",
            "lignes": goldai_growth,
            "lecture": "lignes incrémentales fusionnées dans le stock historique",
        },
    ]

    cols_steps = st.columns(len(journey_steps))
    for col, step in zip(cols_steps, journey_steps, strict=False):
        with col, st.container(border=True):
            st.caption(step["etape"])
            st.metric(
                label=" ",
                value=f"{step['lignes']:,}",
                label_visibility="collapsed",
            )
            st.caption(step["lecture"])

    st.caption(
        f"Statut du run : **{run_status}** · "
        f"Stock GoldAI cumulé après fusion : **{goldai_total_after:,} lignes** "
        f"(le run du jour ajoute +{goldai_growth:,})."
    )

    journey_df = pd.DataFrame(
        [
            {"Étape": s["etape"], "Lignes": s["lignes"]}
            for s in journey_steps
            if s["lignes"] > 0
        ]
    )
    if not journey_df.empty:
        chart_journey = (
            alt.Chart(journey_df)
            .mark_bar(cornerRadiusEnd=4, height=28, color="#06b6d4")
            .encode(
                y=alt.Y("Étape:N", sort=None, title=None),
                x=alt.X("Lignes:Q", title="Lignes du jour"),
                tooltip=[alt.Tooltip("Étape:N"), alt.Tooltip("Lignes:Q", format=",")],
            )
            .properties(height=max(180, 56 * len(journey_df)))
        )
        labels_journey = (
            alt.Chart(journey_df)
            .mark_text(align="left", baseline="middle", dx=6, fontSize=13, fontWeight=600, color="#e2e8f0")
            .encode(
                y=alt.Y("Étape:N", sort=None),
                x=alt.X("Lignes:Q"),
                text=alt.Text("Lignes:Q", format=","),
            )
        )
        st.altair_chart(chart_journey + labels_journey, use_container_width=True)
    else:
        if last_run:
            st.info(
                "Run détecté mais aucune ligne incrémentale ce jour "
                f"(statut {run_status}). Relancez `python main.py` si vous attendez de nouvelles données."
            )
        else:
            st.info("Aucun run récent détecté. Lancez `python main.py` pour produire le run du jour.")

    if not show_advanced:
        return

    st.divider()
    st.markdown("### Détail technique : enrichissement étape par étape (Expert)")
    st.caption(
        "Vue brute des stocks par couche. Attention : les périmètres sont hétérogènes "
        "(RAW/SILVER = partition du jour, GOLD/GoldAI = stocks cumulés)."
    )
    enrich_rows = _build_enrichment_table(PROJECT_ROOT)
    if enrich_rows:
        # Indique le périmètre réel de chaque mesure pour éviter les lectures trompeuses :
        # RAW/SILVER observent la dernière partition journalière, GOLD est l'export enrichi
        # du jour, GoldAI est la fusion historique, et Copie IA est le split d'entraînement.
        STAGE_SCOPE = {
            "1. RAW": "Partition du jour",
            "2. SILVER": "Partition du jour",
            "3. GOLD": "Export du jour (stock enrichi)",
            "4. GoldAI": "Stock consolidé (toutes dates)",
            "5. Copie IA (train)": "Split d'entraînement 70 %",
        }

        display_rows: list[dict] = []
        prev_cols: set = set()
        prev_count: int | None = None
        for p in enrich_rows:
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
                    "Périmètre": STAGE_SCOPE.get(p["stage"], "—"),
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
                    "_lignes": int(p["lignes"]),
                    "_key_cols": ", ".join(key_new) if key_new else "—",
                }
            )
            prev_cols = set(p["cols_list"])
            prev_count = p["lignes"]

        df_display = pd.DataFrame(display_rows).drop(columns=["_lignes", "_key_cols"])
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.info(
            "**Lecture** — RAW et SILVER reflètent la **partition du jour** "
            "(quelques centaines à quelques milliers de lignes). "
            "GOLD, GoldAI et Copie IA sont des **stocks consolidés** "
            "(dizaines de milliers de lignes). Les volumes ne sont donc pas "
            "directement comparables : on regarde plutôt l'enrichissement "
            "des colonnes et la couverture sentiment/topics.",
            icon="ℹ️",
        )

        # ── Graphique volumétrie + enrichissement ────────────────────────────
        col_scale, col_metric = st.columns([1, 1])
        with col_scale:
            scale_type = st.radio(
                "Échelle",
                ["Logarithmique (recommandée)", "Linéaire"],
                index=0,
                horizontal=True,
                key="pipeline_enrich_scale",
                help="L'échelle logarithmique permet de voir RAW/SILVER "
                "malgré les volumes très supérieurs des étapes suivantes.",
            )
        with col_metric:
            st.caption(
                "Colorisation par périmètre : violet = partition du jour, "
                "turquoise = stock consolidé, doré = split d'entraînement."
            )

        chart_df = pd.DataFrame(
            [
                {
                    "Étape": r["Étape"],
                    "Lignes": r["_lignes"],
                    "Périmètre": r["Périmètre"],
                    "Label": f"{r['_lignes']:,}".replace(",", " "),
                }
                for r in display_rows
            ]
        )
        x_scale = (
            alt.Scale(type="log", domainMin=max(1, chart_df["Lignes"].min()))
            if scale_type.startswith("Log")
            else alt.Scale(type="linear")
        )
        color_domain = [
            "Partition du jour",
            "Export du jour (stock enrichi)",
            "Stock consolidé (toutes dates)",
            "Split d'entraînement 70 %",
        ]
        color_range = ["#8b5cf6", "#06b6d4", "#14b8a6", "#f59e0b"]

        base = alt.Chart(chart_df).encode(
            y=alt.Y(
                "Étape:N",
                sort=None,
                title=None,
                axis=alt.Axis(
                    labelLimit=220,
                    labelOverlap=False,
                    labelPadding=6,
                    labelFontSize=12,
                ),
            ),
        )
        bars = base.mark_bar(cornerRadiusEnd=4, height=28).encode(
            x=alt.X("Lignes:Q", scale=x_scale, title="Nombre de lignes"),
            color=alt.Color(
                "Périmètre:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Étape:N"),
                alt.Tooltip("Périmètre:N"),
                alt.Tooltip("Lignes:Q", format=","),
            ],
        )
        labels = base.mark_text(
            align="left",
            baseline="middle",
            dx=6,
            fontSize=13,
            fontWeight=600,
            color="#e2e8f0",
        ).encode(
            x=alt.X("Lignes:Q", scale=x_scale),
            text="Label:N",
        )
        chart_height = max(260, 56 * len(chart_df))
        st.altair_chart(
            (bars + labels).properties(height=chart_height),
            use_container_width=True,
        )
    else:
        st.info("Aucune donnée disponible. Lancez d'abord le pipeline E1.")
