"""
Onglet "Pipeline & Données" — regroupe la synthèse pipeline et l'exploration flux.

- **Mode démo** : vue jury simplifiée (`pipeline_demo.py`) — charts + lineage.
- **Mode Expert** : synthèse complète + exploration (inchangé).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext, cockpit_tab_is_active
from src.streamlit.cockpit_ux import render_expert_breadcrumb
from src.streamlit.page_modules import flux as page_flux
from src.streamlit.page_modules import pipeline as page_pipeline
from src.streamlit.page_modules import pipeline_demo as page_pipeline_demo


def render(ctx: PageContext) -> None:
    if not cockpit_tab_is_active(ctx, "🔁 Pipeline"):
        return
    if ctx.ux_mode == "Mode démo":
        page_pipeline_demo.render(ctx)
        return

    st.caption(
        "Synthèse du run, preuves et fusion. "
        "Pour ouvrir fichier par fichier → sous-onglet **Explorer les fichiers**."
    )
    sub_run, sub_explore = st.tabs(
        ["Synthèse & run", "Explorer les fichiers"]
    )
    with sub_run:
        render_expert_breadcrumb("Pipeline", "Synthèse & run")
        page_pipeline.render(ctx)
    with sub_explore:
        render_expert_breadcrumb("Pipeline", "Explorer les fichiers")
        page_flux.render(ctx)
