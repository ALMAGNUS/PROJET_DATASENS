"""
Onglet "IA & Modèles" — regroupe la prédiction live et la gouvernance modèles.

Wrapper léger : on délègue aux modules existants
`page_modules/ia.py` (prédiction sentiment + insight Mistral) et
`page_modules/modeles.py` (benchmark, fine-tuning, GO/NO-GO).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext
from src.streamlit.cockpit_ux import render_expert_breadcrumb
from src.streamlit.page_modules import ia as page_ia
from src.streamlit.page_modules import modeles as page_modeles


def render(ctx: PageContext) -> None:
    """Affiche prédiction et benchmark sous forme de sous-onglets."""
    st.caption(
        "Prédiction live, benchmark sentiment et gouvernance des modèles entraînés."
    )
    sub_predict, sub_models = st.tabs(["Sentiment", "Modèles"])
    with sub_predict:
        render_expert_breadcrumb("IA & Modèles", "Sentiment")
        page_ia.render(ctx)
    with sub_models:
        render_expert_breadcrumb("IA & Modèles", "Modèles")
        page_modeles.render(ctx)
