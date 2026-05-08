"""
Page cockpit : onglet demo.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:

    st.subheader("Parcours de démonstration")
    st.caption("Lecture opérationnelle du cockpit data / IA, structurée en 3 panels.")
    st.markdown("#### Panels actifs en mode Démo")
    st.markdown(
        """
        1. **Vue d'ensemble** : état du pipeline (4 couches) + lineage de la donnée (SQLite → MongoDB) + activité du dernier run.
        2. **Pipeline & Données** : pipeline du jour (extraits → validés → nouveaux → ajoutés), preuve de fusion GOLD → GoldAI, lignes incrémentales.
        3. **IA & Modèles** : prédiction sentiment temps réel, insights Mistral, benchmark + fine-tuning.
        """
    )

    st.info(
        "Le mode Démo masque les outils d'administration (MongoDB ops, Prometheus, fine-tuning lourd) "
        "qui restent accessibles en mode Expert."
    )

    with st.expander("Script de présentation (lecture séquentielle)", expanded=False):
        st.markdown(
            """
            **Introduction**
            « Le cockpit expose le pipeline data en trois lectures complémentaires : état global, run du jour, IA. »

            **Panel 1 — Vue d'ensemble**
            « Volumétrie par couche (RAW / SILVER / GOLD / GoldAI), lineage SQLite → Parquet → GoldAI → GridFS, statut du dernier run. »

            **Panel 2 — Pipeline & Données**
            « Sous-onglet *Run & Fusion* : pipeline du jour à grain constant (extraits, validés, dédupliqués, ajoutés à GoldAI), preuve par les lignes incrémentales.
              Sous-onglet *Exploration* : profil RAW → SILVER → GOLD → GoldAI couche par couche pour audit technique. »

            **Panel 3 — IA & Modèles**
            « Sous-onglet *Prédiction & Insights* : inférence sentiment temps réel + insights Mistral sur requête utilisateur.
              Sous-onglet *Benchmark & Fine-tuning* : comparatif de modèles, décision d'exploitation GO / NO-GO. »
            """
        )
