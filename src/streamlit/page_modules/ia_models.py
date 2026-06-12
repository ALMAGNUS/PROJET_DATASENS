"""
Onglet "IA & Modèles" — regroupe la prédiction live et la gouvernance modèles.

Wrapper léger : on délègue aux modules existants
`page_modules/ia.py` (prédiction sentiment + insight Mistral) et
`page_modules/modeles.py` (benchmark, fine-tuning, GO/NO-GO).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext, cockpit_tab_is_active
from src.streamlit.cockpit_ux import render_expert_breadcrumb
from src.streamlit.page_modules import dataset_quality as page_dataset_quality
from src.streamlit.page_modules import ia as page_ia
from src.streamlit.page_modules import modeles as page_modeles


def render(ctx: PageContext) -> None:
    """Affiche prédiction et benchmark sous forme de sous-onglets."""
    if not cockpit_tab_is_active(ctx, "🤖 IA"):
        return
    st.caption(
        "Prédiction live (Sentiment) · benchmark, fine-tuning, drift et qualité dataset (Modèles)."
    )
    sub_predict, sub_models = st.tabs(["Sentiment", "Modèles"])
    with sub_predict:
        render_expert_breadcrumb("IA & Modèles", "Sentiment")
        page_ia.render(ctx)
    with sub_models:
        render_expert_breadcrumb("IA & Modèles", "Modèles")
        page_modeles.render(ctx)
        st.divider()
        page_dataset_quality.render_dataset_quality(ctx)
