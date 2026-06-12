"""
Page cockpit : aide rapide (mode Expert / référence interne).

En mode démo, cet onglet n'est plus affiché — parcours IA puis Pipeline suffit.
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext


def render(ctx: PageContext) -> None:
    st.subheader("Aide rapide")
    st.markdown(
        """
        **Par où commencer**

        1. **IA** — saisir un texte, voir le sentiment et les insights.
        2. **Pipeline** — volumes du jour et parcours d'un article dans les couches de données.
        """
    )
    if ctx.ux_mode == "Expert":
        st.caption(
            "Mode Expert : onglets Pilotage et exploration complète du pipeline disponibles."
        )
