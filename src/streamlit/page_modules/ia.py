"""
Page cockpit : onglet ia.
Extrait depuis src/streamlit/app.py (phase C, audit 2026-04).
"""

from __future__ import annotations

import html
import json
import os
import time

import requests
import streamlit as st

from src.ml.inference.sentiment_postprocess import finalize_sentiment
from src.streamlit._cockpit_helpers import (
    PageContext,
    cockpit_tab_is_active,
    record_click,
    record_run,
)
from src.insights.goldai_data import load_enriched_goldai
from src.insights.builder import build_insight_pack
from src.streamlit.auth_plug import (
    get_token,
)

_DEMO_SENTIMENT_MODEL = "ac0hik/Sentiment_Analysis_French"

# Thèmes uniquement — pas de libellé de sentiment (c'est l'IA qui décide à l'analyse).
_DEMO_EXAMPLES = [
    ("Marché boursier", "Le marché boursier affiche une forte hausse cette semaine."),
    ("Inflation", "L'inflation inquiète les investisseurs et freine la croissance."),
    ("Cotation CAC 40", "Le CAC 40 clôture à 7 850 points en fin de séance."),
    ("Mesures sociales", "Le gouvernement annonce de nouvelles mesures sociales controversées."),
]

_EXAMPLE_LABELS = ["Texte libre"] + [label for label, _ in _DEMO_EXAMPLES]
_EXAMPLE_TEXTS = {label: text for label, text in _DEMO_EXAMPLES}

_INSIGHT_EXAMPLES = {
    "Politique": "Quel sentiment domine en politique ?",
    "Financier": "Quel sentiment domine sur les marchés ?",
    "Utilisateurs": "Quelles sources dominent dans le corpus ?",
}

_THEME_OPTIONS = {"Politique": "politique", "Financier": "financier", "Utilisateurs": "utilisateurs"}

_TONE_COLORS = {
    "Positif": "#66bb6a",
    "Neutre": "#90a4ae",
    "Négatif": "#ef5350",
}


def _ia_key(ctx: PageContext, name: str) -> str:
    """Clés widgets isolées par profil (Standard vs Démo) — évite page blanche au changement de mode."""
    scope = "demo" if ctx.ux_mode == "Mode démo" else "std"
    return f"ia_{scope}_{name}"


def _label_fr(label_raw: str) -> str:
    return {
        "POSITIVE": "Positif",
        "NEGATIVE": "Négatif",
        "NEUTRAL": "Neutre",
    }.get(str(label_raw).upper(), str(label_raw))


def _render_sentiment_result(last: dict | None, *, demo_mode: bool = False) -> None:
    if not last:
        if demo_mode:
            st.markdown(
                '<div class="ds-ia-result ds-ia-result--empty"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="ds-ia-result ds-ia-result--empty">
                  <div class="ds-ia-result-label">Résultat</div>
                  <div class="ds-ia-result-placeholder">Lancez l'analyse.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    label_fr = _label_fr(last.get("label", "-"))
    confidence = float(last.get("confidence", 0.0) or 0.0)
    intensity = float(last.get("sentiment_score", 0.0) or 0.0)
    accent = _TONE_COLORS.get(label_fr, "#78909c")
    pct = int(max(0.0, min(1.0, (intensity + 1.0) / 2.0)) * 100)

    if demo_mode:
        st.markdown(
            f"""
            <div class="ds-ia-result">
              <div class="ds-ia-result-value" style="color:{accent};">{html.escape(label_fr)}</div>
              <div class="ds-ia-bar"><span style="width:{pct}%;background:{accent};"></span></div>
              <div class="ds-ia-meta"><span>{confidence:.0%}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="ds-ia-result">
          <div class="ds-ia-result-label">Résultat</div>
          <div class="ds-ia-result-value" style="color:{accent};">{html.escape(label_fr)}</div>
          <div class="ds-ia-bar"><span style="width:{pct}%;background:{accent};"></span></div>
          <div class="ds-ia-meta">
            <span>Intensité {intensity:+.2f}</span>
            <span>Confiance {confidence:.0%}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_model_chip() -> None:
    st.markdown(
        '<span class="ds-chip">ac0hik · inférence locale (cockpit)</span>',
        unsafe_allow_html=True,
    )


def _call_predict(api_v1: str, text: str, model: str = "sentiment_fr") -> tuple[bool, dict | str]:
    token = get_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(
            f"{api_v1}/ai/predict",
            json={"text": text, "model": model, "task": "sentiment-analysis"},
            headers=headers,
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        return False, "API indisponible — lancez l'API E2."
    except Exception as e:
        return False, str(e)[:150]

    if not r.ok:
        if r.headers.get("content-type", "").startswith("application/json"):
            detail = r.json().get("detail", r.text)
        else:
            detail = r.text
        return False, f"Erreur {r.status_code}: {str(detail)[:300]}"
    return True, r.json()


@st.cache_resource(show_spinner="Chargement du modèle…")
def _demo_sentiment_service():
    from src.ml.inference.local_hf_service import LocalHFService

    return LocalHFService(model_name=_DEMO_SENTIMENT_MODEL, task="text-classification")


def _predict_demo_local(text: str) -> dict:
    service = _demo_sentiment_service()
    raw = service.predict(text, return_all_scores=True)
    scores = raw[0] if raw and isinstance(raw[0], list) else raw
    out = finalize_sentiment(text, scores)
    return {
        "model": "sentiment_fr",
        "task": "sentiment-analysis",
        "result": [out],
        "resolved_model": _DEMO_SENTIMENT_MODEL,
    }


def _clear_sentiment_result() -> None:
    st.session_state.pop("ia_last_result", None)
    st.session_state.pop("ia_last_resolved_model", None)


def _render_sentiment_examples(*, ctx: PageContext, text_key: str, ex_label_key: str, demo_mode: bool) -> None:
    """Exemples 1-clic — selectbox."""
    key_prefix = _ia_key(ctx, "ex")
    pick_key = f"{key_prefix}_pick"
    current = st.session_state.get(ex_label_key)
    if pick_key not in st.session_state:
        st.session_state[pick_key] = current if current in _EXAMPLE_LABELS else _EXAMPLE_LABELS[0]

    def _on_example_change() -> None:
        pick = st.session_state.get(pick_key)
        if not pick or pick == "Texte libre":
            st.session_state[ex_label_key] = None
            return
        st.session_state[text_key] = _EXAMPLE_TEXTS[pick]
        st.session_state[ex_label_key] = pick
        _clear_sentiment_result()

    st.selectbox(
        "Exemple",
        _EXAMPLE_LABELS,
        key=pick_key,
        on_change=_on_example_change,
        label_visibility="collapsed" if demo_mode else "visible",
    )


def _run_sentiment(text: str, api_v1: str, *, allow_api_fallback: bool) -> tuple[bool, dict | str]:
    """Toujours ac0hik en local dans le cockpit (évite le mauvais modèle Hub via API)."""
    try:
        return True, _predict_demo_local(text)
    except Exception as local_err:
        if not allow_api_fallback:
            return False, f"Modèle local indisponible : {local_err!s}"[:200]
        ok, payload = _call_predict(api_v1, text, "sentiment_fr")
        if ok and isinstance(payload, dict):
            payload.setdefault("resolved_model", "API /predict")
        return ok, payload


def _store_sentiment_result(payload: dict) -> None:
    res = payload.get("result", [])
    resolved = payload.get("resolved_model")
    if resolved:
        st.session_state.ia_last_resolved_model = resolved
    if res and res[0].get("sentiment_score") is not None:
        st.session_state.ia_last_result = res[0]
    else:
        st.session_state.ia_last_result = None


def _render_sentiment_tab(
    ctx: PageContext,
    api_v1: str,
    api_ok: bool,
    api_warning: str,
    demo_mode: bool,
) -> None:
    if not demo_mode and not api_ok:
        st.warning(api_warning)

    col_in, col_out = st.columns([1.05, 0.95], gap="large")

    text_key = _ia_key(ctx, "text")
    ex_label_key = _ia_key(ctx, "ex_label")
    analyze_key = _ia_key(ctx, "analyze_pending")

    with col_in:
        if not demo_mode:
            st.markdown('<p class="ds-ia-section">Texte</p>', unsafe_allow_html=True)
        with st.container(border=True):
            if text_key not in st.session_state:
                st.session_state[text_key] = ""

            _render_sentiment_examples(
                ctx=ctx, text_key=text_key, ex_label_key=ex_label_key, demo_mode=demo_mode
            )

            pred_text = st.text_area(
                "Texte à analyser",
                height=110,
                key=text_key,
                label_visibility="collapsed",
            )
            if not demo_mode:
                _render_model_chip()
            if st.button(
                "Analyser",
                type="primary",
                use_container_width=True,
                key=_ia_key(ctx, "run_sentiment"),
            ):
                st.session_state[analyze_key] = True

    with col_out:
        if not demo_mode:
            st.markdown('<p class="ds-ia-section">Sentiment</p>', unsafe_allow_html=True)

        pred_text = st.session_state.get(text_key, "")
        if st.session_state.pop(analyze_key, False) and str(pred_text).strip():
            _clear_sentiment_result()
            record_click("IA · Analyser sentiment")
            started = time.time()
            with st.spinner("Analyse…"):
                ok, payload = _run_sentiment(
                    str(pred_text).strip(),
                    api_v1,
                    allow_api_fallback=not demo_mode,
                )
            record_run("IA · Sentiment", time.time() - started, ok)
            if ok:
                _store_sentiment_result(payload)
            else:
                _clear_sentiment_result()
                st.error(str(payload))

        _render_sentiment_result(st.session_state.get("ia_last_result"), demo_mode=demo_mode)

        if not demo_mode:
            resolved = st.session_state.get("ia_last_resolved_model")
            if resolved and st.session_state.get("ia_last_result"):
                short = resolved if len(resolved) < 56 else "…" + resolved[-53:]
                st.caption(f"Modèle · `{short}`")
                if "datasens-sentiment-fr" in short.lower():
                    st.warning(
                        "Ancien modèle Hub détecté — rafraîchissez la page (F5) puis relancez l'analyse."
                    )

            if st.session_state.get("ia_last_result"):
                with st.expander("Détail technique", expanded=False):
                    st.json([st.session_state.ia_last_result])


def _render_insight_cards(cards: list[dict]) -> None:
    if not cards:
        return
    small = [c for c in cards if c.get("type") != "cross_analysis"][:6]
    parts = ['<div class="ds-insight-grid">']
    for card in small:
        title = html.escape(str(card.get("title", "")))
        summary = html.escape(str(card.get("summary", "")))
        parts.append(
            f'<div class="ds-insight-card">'
            f'<div class="ds-insight-card-title">{title}</div>'
            f'<div class="ds-insight-card-summary">{summary}</div>'
            f"</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _render_cross_analysis_bubble(cards: list[dict]) -> None:
    cross = next((c for c in cards if c.get("type") == "cross_analysis"), None)
    if not cross:
        return
    title = html.escape(str(cross.get("title", "Analyse croisée")))
    summary = html.escape(str(cross.get("summary", "")))
    st.markdown(
        f"""
        <div class="ds-insight-grid" style="margin-bottom:0.65rem;">
          <div class="ds-insight-card ds-insight-card-cross">
            <div class="ds-insight-card-title">{title}</div>
            <div class="ds-insight-card-summary">{summary}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _purge_legacy_insight_chat() -> None:
    """Supprime les anciennes réponses Mistral (texte long sans cartes ni engine)."""
    msgs = st.session_state.get("ia_chat_messages", [])
    if not msgs:
        return
    cleaned = []
    for msg in msgs:
        if msg.get("role") != "assistant":
            cleaned.append(msg)
            continue
        if msg.get("cards") or "engine" in msg:
            cleaned.append(msg)
            continue
        content = str(msg.get("content", ""))
        if len(content) > 400:
            continue
        cleaned.append(msg)
    if len(cleaned) != len(msgs):
        st.session_state.ia_chat_messages = cleaned


@st.cache_data(show_spinner=False, ttl=3600)
def _warm_goldai_cache() -> bool:
    load_enriched_goldai()
    return True


@st.cache_data(show_spinner=False, ttl=600)
def _cached_insight_pack(theme: str, message: str) -> tuple[str, list[dict], str]:
    """Calcul GoldAI + synthèse Mistral (cache 10 min)."""
    pack = build_insight_pack(theme, message)
    cards = json.loads(json.dumps(pack.insights, default=str))
    return pack.reply, cards, "goldai_mistral_v4_macro"


def _fetch_insights_cockpit(theme: str, message: str) -> tuple[str, list[dict], str]:
    try:
        return _cached_insight_pack(theme, message)
    except Exception as e:
        return f"Erreur analyse locale : {e!s}"[:200], [], "error"


def _render_insight_messages(messages: list[dict]) -> None:
    if not messages:
        return

    parts = ['<div class="ds-ia-chat">']
    for msg in messages[-6:]:
        role = msg.get("role", "assistant")
        if role == "user":
            content = html.escape(str(msg.get("content", ""))).replace("\n", "<br>")
            parts.append(
                f'<div class="ds-ia-bubble ds-ia-bubble-user">{content}</div>'
            )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

    assistant_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            assistant_msg = msg
            break

    if assistant_msg:
        cards = assistant_msg.get("cards") or []
        if cards:
            _render_cross_analysis_bubble(cards)
            _render_insight_cards(cards)
        elif assistant_msg.get("content"):
            content = str(assistant_msg.get("content", ""))
            if content.startswith("Erreur") or content.startswith("Aucune"):
                st.error(content)
            elif not demo_mode:
                st.warning(
                    "Ancienne réponse texte détectée. Cliquez **Effacer**, puis relancez."
                )


def _render_insights_tab(
    ctx: PageContext,
    api_v1: str,
    api_ok: bool,
    api_warning: str,
    *,
    demo_mode: bool = False,
) -> None:
    question_key = _ia_key(ctx, "insight_question")
    theme_key = _ia_key(ctx, "theme")
    theme_prev_key = _ia_key(ctx, "theme_prev")
    clear_chat_key = _ia_key(ctx, "clear_chat")
    _purge_legacy_insight_chat()
    _warm_goldai_cache()

    if "ia_chat_messages" not in st.session_state:
        st.session_state.ia_chat_messages = []

    compute_payload = st.session_state.pop("ia_insight_compute_payload", None)
    if compute_payload:
        reply = "—"
        cards: list[dict] = []
        engine = ""
        try:
            insight_started = time.time()
            with st.spinner("Analyse…"):
                reply, cards, engine = _fetch_insights_cockpit(
                    compute_payload["theme"],
                    compute_payload["message"],
                )
            insight_ok = not (not cards and reply.startswith("Erreur"))
            record_run("IA · Insights", time.time() - insight_started, insight_ok)
            if not cards and not reply.startswith("Erreur"):
                reply = (
                    "Aucune carte insight générée. Vérifiez les données GoldAI "
                    "ou relancez start_full.bat."
                )
        except Exception as e:
            reply = f"Erreur : {e!s}"[:200]
            engine = "error"
        st.session_state.ia_chat_messages.append(
            {"role": "assistant", "content": reply, "cards": cards, "engine": engine}
        )
        st.session_state.ia_clear_insight_question = True

    if st.session_state.pop("ia_clear_insight_question", False):
        st.session_state[question_key] = ""

    theme = "politique"
    with st.container(border=True):
        theme_display = st.radio(
            "Domaine",
            list(_THEME_OPTIONS.keys()),
            horizontal=True,
            key=theme_key,
            label_visibility="collapsed",
        )
        theme = _THEME_OPTIONS[theme_display]

        prev_theme = st.session_state.get(theme_prev_key)
        msgs = st.session_state.get("ia_chat_messages", [])
        awaiting = msgs and msgs[-1].get("role") == "user"
        if prev_theme is not None and prev_theme != theme_display and not awaiting:
            st.session_state.ia_chat_messages = []
            st.session_state[question_key] = ""
        st.session_state[theme_prev_key] = theme_display

        example_q = _INSIGHT_EXAMPLES.get(theme_display, "")
        if demo_mode:
            if st.button("Effacer", key=clear_chat_key, use_container_width=True):
                st.session_state.ia_chat_messages = []
                st.session_state.ia_clear_insight_question = True
                st.rerun()
        else:
            c1, c2 = st.columns([3, 1])
            with c1:
                if st.button(
                    "Question exemple",
                    key=_ia_key(ctx, "insight_ex"),
                    use_container_width=True,
                ):
                    st.session_state[question_key] = example_q
                    st.rerun()
            with c2:
                if st.button("Effacer", key=clear_chat_key, use_container_width=True):
                    st.session_state.ia_chat_messages = []
                    st.session_state.ia_clear_insight_question = True
                    st.rerun()

        _render_insight_messages(st.session_state.ia_chat_messages)

        question = st.text_area(
            "Votre question",
            height=72,
            key=question_key,
            label_visibility="collapsed",
            placeholder=(
                example_q if demo_mode else "Posez votre question…"
            ),
        )
        send = st.button(
            "Envoyer",
            type="primary",
            use_container_width=True,
            key=_ia_key(ctx, "send_insight"),
        )

    if send and question.strip():
        record_click("IA · Insights")
        st.session_state.ia_chat_messages.append({"role": "user", "content": question.strip()})
        st.session_state.ia_insight_compute_payload = {
            "theme": theme,
            "message": question.strip(),
        }
        st.rerun()


def render(ctx: PageContext) -> None:
    if not cockpit_tab_is_active(ctx, "🤖 IA"):
        return
    settings = ctx.settings
    api_base = os.getenv("API_BASE", f"http://localhost:{settings.fastapi_port}")
    api_v1 = f"{api_base}{settings.api_v1_prefix}"
    api_ok = ctx.backend_ok
    api_warning = (
        "API indisponible. Lancez l'API E2 (`python run_e2_api.py`) avant l'assistant."
    )
    demo_mode = ctx.ux_mode == "Mode démo"

    # Purge d'un ancien résultat API (Hub +0.96) encore en session
    stale = st.session_state.get("ia_last_result")
    if stale and float(stale.get("sentiment_score", 0) or 0) > 0.9:
        resolved = str(st.session_state.get("ia_last_resolved_model", ""))
        if "ac0hik" not in resolved:
            _clear_sentiment_result()

    ia_view = st.radio(
        "Vue IA",
        ["Sentiment", "Insights"],
        horizontal=True,
        key=_ia_key(ctx, "view"),
        label_visibility="collapsed",
    )

    if ia_view == "Sentiment":
        _render_sentiment_tab(ctx, api_v1, api_ok, api_warning, demo_mode)
    else:
        _render_insights_tab(
            ctx, api_v1, api_ok, api_warning, demo_mode=demo_mode
        )
