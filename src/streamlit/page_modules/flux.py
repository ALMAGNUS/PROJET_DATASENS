"""
Page cockpit : onglet flux.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
)
from src.streamlit._cockpit_helpers import (
    inject_css as _inject_css,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    PROJECT_ROOT = ctx.project_root
    history_mode = ctx.history_mode

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

    st.caption(
        "Inspectez une couche (RAW, SILVER, GOLD…) et chargez les fichiers manuellement. "
        "La synthèse run + fusion est dans l'autre sous-onglet."
    )

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
        k3.markdown(f'<div class="kpi-box"><div class="kpi-val">{n_sent/n:.0%}" if n else "—"</div><div class="kpi-lbl">Couv. sentiment</div><div class="kpi-sub">{n_sent:,} articles</div></div>'.replace('"', '') if n else '<div class="kpi-box"><div class="kpi-val">—</div><div class="kpi-lbl">Couv. sentiment</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-box"><div class="kpi-val">{n_top/n:.0%}" if n else "—"</div><div class="kpi-lbl">Couv. topics</div><div class="kpi-sub">{n_src} sources</div></div>'.replace('"', '') if n else '<div class="kpi-box"><div class="kpi-val">—</div><div class="kpi-lbl">Couv. topics</div></div>', unsafe_allow_html=True)

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
            cfg["quality_score"] = st.column_config.ProgressColumn("Qualité", min_value=0.0, max_value=1.0, format="%.2f")
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

    def _render_stage_header(title: str, subtitle: str) -> None:
        st.markdown(
            f"""
            <div class="flux-stage-header">
            <h4>{title}</h4>
            <p>{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── ETAPE 1 : RAW ────────────────────────────────────────────────────────
    _render_stage_header(
        "ETAPE 1 — RAW : Articles bruts collectés",
        "Colonnes : title, content, url, source, published_at, quality_score",
    )

    raw_dir_v = PROJECT_ROOT / "data" / "raw"
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
                f'<div class="success-banner">  {len(df_r):,} articles chargés depuis RAW historique '
                f'({meta_r.get("files", 0)} fichier(s), période {dmin} → {dmax})</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="success-banner">  {len(df_r):,} articles chargés depuis {fn_r} (date: {date_r})</div>',
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
        st.caption("Aperçu des données brutes (RAW) :")
        _show_table(df_r, key="tbl_raw")

    # ── ETAPE 2 : SILVER ─────────────────────────────────────────────────────
    _render_stage_header(
        "ETAPE 2 — SILVER : Nettoyage + enrichissement",
        "Colonnes selon version : quality_score, tags/tag_scores (ancien) ou topic_1/topic_2 (actuel)",
    )

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
            "Après le prochain run de `python main.py`, il sera partitionné comme le GOLD (`date=YYYY-MM-DD`)."
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
                    [sd / "silver_articles.csv", sd / "silver_articles.parquet", *list(sd.rglob("*.parquet")), *list(sd.rglob("*.csv"))]
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
                st.warning("Aucun fichier SILVER trouvé.")
        else:
            sd = next((d for d in silver_dirs if d.name == sel_silver), None)
            if sd:
                # Nouveau format : CSV partitionné  |  Ancien format : Parquet v_YYYY-MM-DD
                candidates = (
                    [sd / "silver_articles.csv", sd / "silver_articles.parquet", *list(sd.rglob("*.parquet")), *list(sd.rglob("*.csv"))]
                )
                df_s, fn_s = _load_stage([p for p in candidates if p.exists()][:1])
                if df_s is not None:
                    st.session_state["flux_silver"] = (df_s, fn_s, sel_silver, {"mode": "single"})
                else:
                    st.warning("Aucun fichier SILVER trouvé.")

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
                f'<div class="success-banner">  {len(df_s):,} articles chargés depuis SILVER historique '
                f'({meta_s.get("files", 0)} fichier(s), période {dmin} → {dmax})</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="success-banner">  {len(df_s):,} articles chargés depuis SILVER ({ver_s})</div>',
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
            sc3.metric("Articles tagués", f"{n_tagged:,}", f"{n_tagged/len(df_s):.0%}" if len(df_s) else "—")
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

        st.caption(f"Aperçu des données SILVER ({ver_s}) — {len(df_s.columns)} colonnes :")
        _show_table(df_s, key="tbl_silver")

    # ── ETAPE 3 : GOLD ────────────────────────────────────────────────────────
    _render_stage_header(
        "ETAPE 3 — GOLD : Sentiment IA ajouté",
        "Nouvelles colonnes : sentiment (positif/negatif/neutre), sentiment_score [-1, +1]",
    )

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
                f'<div class="success-banner">  {len(df_g):,} articles chargés depuis GOLD historique '
                f'({meta_g.get("files", 0)} partition(s), période {dmin} → {dmax})</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="success-banner">  {len(df_g):,} articles chargés depuis GOLD (date={date_g})</div>',
                unsafe_allow_html=True,
            )
        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("Lignes", f"{len(df_g):,}")
        gc2.metric("Colonnes", len(df_g.columns))
        n_sent_g = int(df_g["sentiment"].notna().sum()) if "sentiment" in df_g.columns else 0
        gc3.metric("Labellisés sentiment", f"{n_sent_g:,}", f"{n_sent_g/len(df_g):.0%}" if len(df_g) else "—")
        if "sentiment_score" in df_g.columns:
            gc4.metric("Score moyen", f"{df_g['sentiment_score'].mean():+.3f}")
        if "sentiment" in df_g.columns:
            sv = df_g["sentiment"].value_counts()
            sent_html = " &nbsp; ".join(_badge(str(k)) + f' <span style="color:#ccc">{v:,}</span>' for k, v in sv.items())
            st.markdown(f"Distribution : {sent_html}", unsafe_allow_html=True)
        st.caption("Aperçu des données enrichies (GOLD) :")
        _show_table(df_g, key="tbl_gold")

        # Mini graphe sentiment
        if "sentiment" in df_g.columns:
            sv2 = df_g["sentiment"].value_counts().reset_index()
            sv2.columns = ["Sentiment", "Articles"]
            st.bar_chart(sv2.set_index("Sentiment"), use_container_width=True, height=180)

    # ── ETAPE 4 : GoldAI ─────────────────────────────────────────────────────
    _render_stage_header(
        "ETAPE 4 — GoldAI : Fusion long terme (stockage MongoDB)",
        "Toutes les dates fusionnées. Dataset complet pour l'IA et les clients.",
    )

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
        st.markdown(f'<div class="success-banner">  {len(df_ga):,} articles chargés depuis GoldAI (fusion complète)</div>', unsafe_allow_html=True)
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

        st.caption(f"{len(df_ga_f):,} articles affichés sur {len(df_ga):,} après filtre")
        _show_table(df_ga_f, key="tbl_goldai")

        with st.expander("Analyse avancée GoldAI (distributions et tendances)", expanded=False):
            # Distributions cote a cote
            dc1, dc2 = st.columns(2)
            with dc1:
                if "sentiment" in df_ga.columns:
                    sv_ga = df_ga["sentiment"].value_counts().reset_index()
                    sv_ga.columns = ["Sentiment", "Articles"]
                    st.caption("Répartition sentiment")
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
                        st.caption("Évolution du volume par jour (60 derniers jours)")
                        st.line_chart(daily_ga.set_index("_d")["n"], use_container_width=True, height=160)
                    if "sentiment" in df_time_ga.columns:
                        piv = df_time_ga.dropna(subset=["_d"]).groupby(["_d", "sentiment"]).size().unstack(fill_value=0).tail(30)
                        if not piv.empty:
                            st.caption("Évolution sentiment par jour (30 derniers jours)")
                            st.area_chart(piv, use_container_width=True, height=180)
                except Exception:
                    pass

    # ── ETAPE 5 : Copie IA ────────────────────────────────────────────────────
    _render_stage_header(
        "ETAPE 5 — Copie IA : Datasets Train / Val / Test",
        "Split 70 / 15 / 15 — prêt pour l'entraînement du modèle de sentiment",
    )

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
        st.markdown(f'<div class="success-banner">  {len(df_ia_l):,} exemples chargés (split: {split_ia})</div>', unsafe_allow_html=True)
        ia1, ia2, ia3, ia4 = st.columns(4)
        ia1.metric("Exemples", f"{len(df_ia_l):,}")
        ia2.metric("Colonnes", len(df_ia_l.columns))
        n_sent_ia = int(df_ia_l["sentiment"].notna().sum()) if "sentiment" in df_ia_l.columns else 0
        ia3.metric("Labellisés", f"{n_sent_ia:,}", f"{n_sent_ia/len(df_ia_l):.0%}" if len(df_ia_l) else "—")
        ia4.metric("Split", split_ia)
        if "sentiment" in df_ia_l.columns:
            sv_ia = df_ia_l["sentiment"].value_counts()
            sent_ia_html = " &nbsp; ".join(_badge(str(k)) + f' <span style="color:#ccc">{v:,}</span>' for k, v in sv_ia.items())
            st.markdown(f"Distribution : {sent_ia_html}", unsafe_allow_html=True)
        st.caption(f"Aperçu du dataset {split_ia} (prêt pour entraînement) :")
        _show_table(df_ia_l, key="tbl_ia")

    # ── Suivi d'un article ────────────────────────────────────────────────────
    if "flux_goldai" in st.session_state:
        df_master = st.session_state["flux_goldai"][0]
        st.divider()
        st.subheader("Suivre un article — du RAW au GoldAI")
        col_s1, col_s2 = st.columns([4, 1])
        with col_s1:
            q = st.text_input("Rechercher (titre, mot-clé)", placeholder="Ex: inflation, BCE, Macron...", key="flux_search2")
        with col_s2:
            rnd = st.button("Article aléatoire", use_container_width=True, key="flux_rnd2")
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
                st.caption(f"{len(hits)} article(s) trouvé(s)")
            else:
                st.warning("Aucun article trouvé.")
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
            st.markdown('<div class="ds-card"><div class="ds-card-title">4. GoldAI — Prêt IA</div></div>', unsafe_allow_html=True)
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
