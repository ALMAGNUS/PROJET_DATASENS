"""
Qualité du jeu de données IA — distribution sentiment, topics, splits train/val/test.

Affiché dans l'onglet **IA → Modèles**, pas dans Pilotage (infra / Mongo).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.streamlit._cockpit_helpers import PageContext
from src.streamlit.cockpit_ux import render_section_title
from src.streamlit.metrics import ia_metrics_from_parquet as _ia_metrics_from_parquet


def render_dataset_quality(ctx: PageContext) -> None:
    project_root = ctx.project_root
    show_advanced = ctx.show_advanced

    render_section_title("Qualité du jeu de données")
    st.caption(
        "Distribution sentiment/topics et splits d'entraînement — "
        "pour choisir et valider un modèle."
    )
    ia = _ia_metrics_from_parquet(project_root)
    if ia is None:
        st.warning("Aucune donnée Parquet (GOLD/GoldAI). Lancez le pipeline puis la fusion GoldAI.")
        return

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
                    f"Origine labels : lexical {n_lex/tot_src*100:.0f}% · "
                    f"modèle IA {n_ml/tot_src*100:.0f}%"
                )
            elif n_lex > 0:
                st.caption("Origine labels : règles lexicales uniquement.")

    if not show_advanced:
        st.caption("Analyses détaillées (mapping labels, topics, sources) ci-dessous si Expert.")
        return

    with st.expander("Reclassement des sentiments", expanded=False):
        alias_rows = int(ia.get("sentiment_alias_rows", 0) or 0)
        if alias_rows > 0:
            st.caption(
                f"**{alias_rows:,}** lignes multilingues normalisées "
                "vers négatif / neutre / positif."
            )
        map_rows = ia.get("sentiment_mapping_table", [])
        if map_rows:
            st.dataframe(pd.DataFrame(map_rows), use_container_width=True, hide_index=True)
        raw_dist = ia.get("sentiment_distribution_raw", {})
        if raw_dist:
            st.caption("Labels bruts avant normalisation :")
            for lbl, n in list(raw_dist.items())[:10]:
                st.caption(f"  • {lbl} : {n:,}")

    with st.expander("Splits train / val / test", expanded=False):
        reco = ia.get("mistral_dataset_reco", "")
        if reco:
            st.caption(reco)
        splits = ia.get("ia_splits", {})
        if splits:
            st.dataframe(
                pd.DataFrame([{"Jeu": k, "Lignes": v} for k, v in splits.items()]),
                use_container_width=True,
                hide_index=True,
            )
        id_missing = int(ia.get("id_missing", 0))
        id_duplicates = int(ia.get("id_duplicates", 0))
        if id_missing or id_duplicates:
            st.caption(f"IDs manquants : {id_missing:,} · doublons : {id_duplicates:,}.")

    with st.expander("Distribution des topics", expanded=False):
        full_topics = ia.get("topic_distribution_full") or ia.get("topic_distribution")
        if full_topics:
            total_topics = int(ia.get("topic_total_rows", sum(full_topics.values())))
            topic_rows = [
                {
                    "Topic": topic,
                    "Articles": count,
                    "%": round(count / total_topics * 100, 1) if total_topics else 0.0,
                }
                for topic, count in full_topics.items()
            ]
            st.dataframe(
                pd.DataFrame(topic_rows),
                use_container_width=True,
                hide_index=True,
                height=min(420, 40 + 35 * len(topic_rows)),
            )
        else:
            st.caption("Aucune donnée topic.")

    with st.expander("Principales sources (volume)", expanded=False):
        if "top_sources" in ia:
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Source": src, "Articles": count}
                        for src, count in list(ia["top_sources"].items())[:10]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Aucune donnée source.")
