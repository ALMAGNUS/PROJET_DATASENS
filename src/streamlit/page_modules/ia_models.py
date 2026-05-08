"""
Onglet "IA & Modèles" — regroupe la prédiction live et la gouvernance modèles.

Wrapper léger : on délègue aux modules existants
`page_modules/ia.py` (prédiction sentiment + insight Mistral) et
`page_modules/modeles.py` (benchmark, fine-tuning, GO/NO-GO).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext
from src.streamlit.page_modules import ia as page_ia
from src.streamlit.page_modules import modeles as page_modeles


def render(ctx: PageContext) -> None:
    """Affiche prédiction et benchmark sous forme de sous-onglets."""
    sub_predict, sub_models = st.tabs(
        ["Prédiction & Insights", "Benchmark & Fine-tuning"]
    )
    with sub_predict:
        page_ia.render(ctx)
    with sub_models:
        page_modeles.render(ctx)
