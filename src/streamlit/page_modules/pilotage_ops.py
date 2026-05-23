"""
Onglet "Pilotage & Ops" — regroupe les actions opérationnelles et le monitoring MLOps.

Wrapper léger : on délègue aux modules existants
`page_modules/pilotage.py` (boutons run/fusion/copy IA/API/backup) et
`page_modules/monitoring.py` (santé services, voyage de la donnée, MongoDB).
"""

from __future__ import annotations

import streamlit as st

from src.streamlit._cockpit_helpers import PageContext, cockpit_tab_is_active
from src.streamlit.cockpit_ux import render_expert_breadcrumb
from src.streamlit.page_modules import monitoring as page_monitoring
from src.streamlit.page_modules import pilotage as page_pilotage


def render(ctx: PageContext) -> None:
    """Affiche actions et monitoring sous forme de sous-onglets."""
    if not cockpit_tab_is_active(ctx, "⚙️ Pilotage"):
        return
    st.caption("Lancement des jobs, sauvegardes et monitoring infra (MongoDB, Prometheus).")
    sub_actions, sub_health = st.tabs(
        ["Actions (run, fusion, backup)", "Infra & MongoDB"]
    )
    with sub_actions:
        render_expert_breadcrumb("Pilotage", "Actions")
        page_pilotage.render(ctx)
    with sub_health:
        render_expert_breadcrumb("Pilotage", "Infra & MongoDB")
        page_monitoring.render(ctx)
