"""
Onglet "Pipeline & Données" — regroupe la synthèse pipeline et l'exploration flux.

- **Mode démo** : vue jury simplifiée (`pipeline_demo.py`) — charts + lineage.
- **Mode Expert** : synthèse complète + exploration (inchangé).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext
from src.streamlit.cockpit_ux import render_expert_breadcrumb
from src.streamlit.page_modules import flux as page_flux
from src.streamlit.page_modules import pipeline as page_pipeline
from src.streamlit.page_modules import pipeline_demo as page_pipeline_demo


def render(ctx: PageContext) -> None:
    if ctx.ux_mode == "Mode démo":
        page_pipeline_demo.render(ctx)
        return

    st.caption(
        "Synthèse des runs, fusion GOLD→GoldAI et exploration étape par étape."
    )
    sub_run, sub_explore = st.tabs(
        ["Run & Fusion (synthèse)", "Exploration des étapes (détail)"]
    )
    with sub_run:
        render_expert_breadcrumb("Pipeline", "Run & Fusion")
        page_pipeline.render(ctx)
    with sub_explore:
        render_expert_breadcrumb("Pipeline", "Exploration")
        page_flux.render(ctx)
