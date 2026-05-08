"""
Page cockpit : onglet ia.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import os
from pathlib import Path

import requests
import streamlit as st

from src.streamlit._cockpit_helpers import (
    PageContext,
)
from src.streamlit._cockpit_helpers import (
    get_active_model as _get_active_model,
)
from src.streamlit.auth_plug import (
    get_token,
)
from src.streamlit.metrics import (
    scan_trained_models as _scan_trained_models,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def render(ctx: PageContext) -> None:
    PROJECT_ROOT = ctx.project_root
    settings = ctx.settings
    api_base = ctx.api_base

    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    api_v1 = f"{api_base}{settings.api_v1_prefix}"

    st.markdown("### IA – Modèles & Assistant")
    try:
        api_ok = requests.get(f"{api_base}/health", timeout=2).ok
    except Exception:
        api_ok = False
    api_warning = (
        "API indisponible. Ouvrez **Pilotage** puis lancez *API E2* avant d'utiliser "
        "la prédiction ou l'assistant."
    )
    if not api_ok:
        st.warning(api_warning)
    help_seen = st.session_state.get("ia_help_seen", False)
    with st.expander("Comment utiliser cet onglet ?", expanded=not help_seen):
        st.markdown("""
        **1. Prédiction** : Testez l’analyse de sentiment sur un texte (ex. « Le marché affiche une hausse »).
        → Saisissez un texte, choisissez un modèle, cliquez sur *Prédire*. Si un modèle fine-tuné est configuré (SENTIMENT_FINETUNED_MODEL_PATH), il est utilisé automatiquement.

        **2. Assistant** : Posez des questions par domaine (Politique, Financier, Utilisateurs).
        → Sélectionnez un thème, tapez votre question dans le champ en bas. L’assistant répond en fonction des données du projet.
        """)
    st.session_state["ia_help_seen"] = True

    st.subheader("1. Classification sentiment (brique ML)")
    st.caption(
        "Analysez le sentiment (positif / négatif / neutre) d’un texte avec FlauBERT ou CamemBERT."
    )
    pred_text = st.text_area(
        "Texte à analyser",
        "Le marché affiche une hausse.",
        height=70,
        help="Ex. une phrase ou un paragraphe",
    )
    active_model = _get_active_model(PROJECT_ROOT)
    trained_models = _scan_trained_models(PROJECT_ROOT)
    trained_by_path = {
        str(m.get("path", "")).replace("\\", "/"): m for m in trained_models if m.get("path")
    }
    (
        trained_by_path.get(str(active_model or "").replace("\\", "/"))
        if active_model
        else None
    )

    best_local = None
    if trained_models:
        ranked = sorted(
            trained_models,
            key=lambda m: (
                float(m.get("eval_f1_macro") or m.get("eval_f1") or 0.0),
                float(m.get("eval_accuracy") or 0.0),
            ),
            reverse=True,
        )
        best_local = ranked[0]

    effective_model_path = active_model or (best_local or {}).get("path")
    effective_meta = (
        trained_by_path.get(str(effective_model_path).replace("\\", "/"))
        if effective_model_path
        else None
    )

    # UX produit: un seul modèle exposé à l'utilisateur (le meilleur courant).
    # Le backend reste piloté par SENTIMENT_FINETUNED_MODEL_PATH.
    pred_model = "sentiment_fr"
    st.markdown("**Modèle utilisé**")
    if effective_model_path:
        f1_local = effective_meta.get("eval_f1_macro") if effective_meta else None
        acc_local = effective_meta.get("eval_accuracy") if effective_meta else None
        perf = "métriques non lues"
        if f1_local is not None:
            perf = f"F1 macro val {float(f1_local):.1%}"
        elif acc_local is not None:
            perf = f"accuracy val {float(acc_local):.1%}"
        st.success(f"Fine-tuné local (meilleur courant) — {effective_model_path} · {perf}")
        if active_model:
            st.caption(
                "Inférence via backend avec modèle fine-tuné actif "
                "(SENTIMENT_FINETUNED_MODEL_PATH)."
            )
        else:
            st.caption(
                "Fine-tuné local détecté. Pour l'activer côté backend, définissez "
                "SENTIMENT_FINETUNED_MODEL_PATH sur ce chemin."
            )
    else:
        st.info("Aucun fine-tuné local détecté. Fallback sur sentiment_fr.")
    if st.button("Prédire le sentiment"):
        token = get_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            r = requests.post(
                f"{api_v1}/ai/predict",
                json={"text": pred_text, "model": pred_model, "task": "sentiment-analysis"},
                headers=headers,
                timeout=120,
            )
            if r.ok:
                data = r.json()
                res = data.get("result", data)
                if res and isinstance(res, list) and res[0].get("sentiment_score") is not None:
                    r0 = res[0]
                    label_raw = str(r0.get("label", "-")).upper()
                    label_fr = {
                        "POSITIVE": "Positif",
                        "NEGATIVE": "Négatif",
                        "NEUTRAL": "Neutre",
                    }.get(label_raw, str(r0.get("label", "-")))
                    confidence = float(r0.get("confidence", 0.0) or 0.0)
                    intensity = float(r0.get("sentiment_score", 0.0) or 0.0)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Sentiment", label_fr)
                    c2.metric("Confiance du modèle", f"{confidence:.1%}")
                    c3.metric("Intensité [-1,+1]", f"{intensity:+.2f}")
                    tone_map = {
                        "Positif": ("#1b5e20", "#e8f5e9"),
                        "Neutre": ("#37474f", "#eceff1"),
                        "Négatif": ("#b71c1c", "#ffebee"),
                    }
                    fg, bg = tone_map.get(label_fr, ("#263238", "#eceff1"))
                    st.markdown(
                        (
                            f"<div style='display:inline-block;padding:6px 12px;border-radius:999px;"
                            f"background:{bg};color:{fg};font-weight:700;'>"
                            f"Sentiment détecté : {label_fr}"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                    polarity = (
                        "très positive"
                        if intensity >= 0.6
                        else "positive"
                        if intensity >= 0.2
                        else "neutre"
                        if intensity > -0.2
                        else "négative"
                        if intensity > -0.6
                        else "très négative"
                    )
                    st.caption(
                        f"Lecture : sentiment **{label_fr.lower()}**, confiance "
                        f"**{confidence:.1%}**, intensité **{intensity:+.2f}** ({polarity})."
                    )
                    with st.expander("Détail technique (probabilités brutes)", expanded=False):
                        st.json(res)
                else:
                    st.json(res)
            else:
                err_detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
                st.error(f"Erreur {r.status_code}: {err_detail[:300]}")
        except requests.exceptions.ConnectionError:
            st.warning(api_warning)
        except Exception as e:
            st.error(str(e)[:150])

    st.divider()
    st.subheader("2. Insights métier assistés (Mistral + GoldAI)")

    # Statut Mistral
    mistral_ok = False
    try:
        r_status = requests.get(
            f"{api_v1}/ai/status",
            headers={"Authorization": f"Bearer {get_token()}"} if get_token() else {},
            timeout=3,
        )
        mistral_ok = r_status.ok and r_status.json().get("configured", False)
    except Exception:
        pass

    if mistral_ok:
        st.success(
            "Mistral connecte — L'assistant s'appuie sur vos donnees GoldAI pour repondre."
        )
    elif api_ok:
        st.warning(
            "Mistral non configure. Verifiez `MISTRAL_API_KEY` dans `.env`."
        )
    else:
        st.warning(api_warning)

    st.caption(
        "Posez des questions métier sur vos données. Mistral répond en s'appuyant sur le contexte réel "
        "(distribution sentiment, topics, sources, tendances) extrait de votre dataset GoldAI."
    )

    theme_options = {
        "Politique": "politique",
        "Financier": "financier",
        "Utilisateurs": "utilisateurs",
    }
    theme_display_to_api = theme_options  # clé affichée -> valeur API

    assist_col1, assist_col2 = st.columns([2, 1])
    with assist_col1:
        theme_display = st.selectbox(
            "Theme d'analyse",
            list(theme_options.keys()),
            key="ia_theme",
            help="Politique : veille, tendances | Financier : marche, indicateurs | Utilisateurs : comportement",
        )
        theme = theme_display_to_api[theme_display]
    with assist_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Effacer la conversation", key="ia_clear", use_container_width=True):
            st.session_state.ia_chat_messages = []
            st.rerun()

    # Exemples de questions
    with st.expander("Exemples de questions clients", expanded=False):
        ex_cols = st.columns(3)
        examples = {
            "Politique": [
                "Quelles sont les tendances politiques cette semaine ?",
                "Quel est le sentiment dominant sur le gouvernement ?",
                "Résume les sujets politiques les plus couverts.",
            ],
            "Financier": [
                "Quelle est la tendance sur l'inflation ?",
                "Le sentiment sur les marchés est-il positif ou négatif ?",
                "Quels indicateurs économiques ressortent le plus ?",
            ],
            "Utilisateurs": [
                "Quelles sources génèrent le plus de contenu négatif ?",
                "Quel est le volume de collecte par source ?",
                "Y a-t-il un déséquilibre dans les données ?",
            ],
        }
        # Utiliser theme_display (Politique/Financier/Utilisateurs) pour les exemples
        examples_for_theme = examples.get(theme_display, [])
        for i, ex in enumerate(examples_for_theme):
            with ex_cols[i]:
                if st.button(ex, key=f"ex_{theme_display}_{i}", use_container_width=True):
                    st.session_state.ia_prefill = ex

    if "ia_chat_messages" not in st.session_state:
        st.session_state.ia_chat_messages = []

    for msg in st.session_state.ia_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Prefill depuis les exemples
    prefill_val = st.session_state.pop("ia_prefill", "")
    prompt = st.chat_input("Votre question d'analyse client...", key="ia_chat_input")
    if not prompt and prefill_val:
        prompt = prefill_val

    if prompt:
        st.session_state.ia_chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"), st.spinner("Mistral analyse vos donnees..."):
            token = get_token()
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            try:
                r = requests.post(
                    f"{api_v1}/ai/insight",
                    json={"theme": theme, "message": prompt},
                    headers=headers,
                    timeout=60,
                )
                if r.ok:
                    reply = r.json().get("reply", "—")
                else:
                    detail = r.json().get("detail", r.text) if "application/json" in r.headers.get("content-type", "") else r.text
                    reply = f"Erreur {r.status_code} : {detail[:200]}"
            except requests.exceptions.ConnectionError:
                reply = api_warning
            except Exception as e:
                reply = f"Erreur : {e!s}"[:200]
            st.markdown(reply)
        st.session_state.ia_chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()
