"""
Page cockpit : onglet pipeline.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st

from src.observability.lineage_service import LineageService
from src.streamlit._cockpit_helpers import (
    PageContext,
    activate_model as _activate_model,
    csv_row_count_cached as _csv_row_count_cached,
    get_active_model as _get_active_model,
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
    run_command as _run_command,
)
from src.streamlit.auth_plug import (
    get_token,
    init_session_auth,
    is_logged_in,
    render_login_form,
    render_user_and_logout,
)
from src.streamlit.pipeline_proof import render_last_run_proof_full
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

    gold_dir = PROJECT_ROOT / "data" / "gold"
    goldai_dir = PROJECT_ROOT / "data" / "goldai"
    merged_path = goldai_dir / "merged_all_dates.parquet"
    meta_path = goldai_dir / "metadata.json"

    # Preuve d'enrichissement du dernier run (audit / traçabilité pipeline).
    render_last_run_proof_full(ctx)
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
            st.caption("Stock long terme consolidé.")
        else:
            st.info("—")
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
                st.info("—")
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
        "Progression du pipeline de bout en bout. À chaque étape, on ajoute "
        "de la structure (colonnes) ou de la valeur métier (sentiment, topics)."
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
