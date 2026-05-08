"""
Onglet "Pipeline & Données" — regroupe la synthèse pipeline et l'exploration flux.

Wrapper léger : aucune logique métier ici, on délègue aux modules existants
`page_modules/pipeline.py` (synthèse run + preuve fusion) et
`page_modules/flux.py` (exploration RAW -> SILVER -> GOLD -> GoldAI).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext
from src.streamlit.page_modules import flux as page_flux
from src.streamlit.page_modules import pipeline as page_pipeline


def render(ctx: PageContext) -> None:
    """Affiche les deux vues sous forme de sous-onglets."""
    sub_run, sub_explore = st.tabs(
        ["Run & Fusion (synthèse)", "Exploration des étapes (détail)"]
    )
    with sub_run:
        page_pipeline.render(ctx)
    with sub_explore:
        page_flux.render(ctx)
