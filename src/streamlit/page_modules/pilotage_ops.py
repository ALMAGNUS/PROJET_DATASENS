"""
Onglet "Pilotage & Ops" — regroupe les actions opérationnelles et le monitoring MLOps.

Wrapper léger : on délègue aux modules existants
`page_modules/pilotage.py` (boutons run/fusion/copy IA/API/backup) et
`page_modules/monitoring.py` (santé services, voyage de la donnée, MongoDB).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext
from src.streamlit.page_modules import monitoring as page_monitoring
from src.streamlit.page_modules import pilotage as page_pilotage


def render(ctx: PageContext) -> None:
    """Affiche actions et monitoring sous forme de sous-onglets."""
    sub_actions, sub_health = st.tabs(
        ["Actions (run, fusion, backup)", "Santé & MongoDB"]
    )
    with sub_actions:
        page_pilotage.render(ctx)
    with sub_health:
        page_monitoring.render(ctx)
