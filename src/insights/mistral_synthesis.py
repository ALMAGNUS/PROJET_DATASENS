"""Synthèse croisée Mistral — ancrée sur le contexte GoldAI."""

from __future__ import annotations

import re

from src.config import get_settings
from src.e3.mistral import get_mistral_service


def _clean_mistral_analysis(text: str) -> str:
    out = (text or "").strip()
    for pat in (
        r"\n\s*Recommandation",
        r"\n\s*Limite",
        r"\n\s*Points clés",
        r"\n\s*---",
        r"il faudrait enrichir",
        r"Pour une analyse robuste",
        r"API comme",
    ):
        m = re.search(pat, out, flags=re.IGNORECASE)
        if m:
            out = out[: m.start()].strip()
    out = re.sub(r"\*\*([^*]+)\*\*", r"\1", out)
    out = re.sub(r"\*([^*]+)\*", r"\1", out)
    words = out.split()
    if len(words) > 160:
        out = " ".join(words[:160]).rstrip(".,;") + "…"
    return out


def mistral_cross_analysis(context: str, question: str, theme_label: str) -> str | None:
    """
    Mistral croise météo, politique, économie, signaux crise — uniquement sur les faits fournis.
    """
    settings = get_settings()
    if not settings.mistral_api_key:
        return None
    service = get_mistral_service()
    if not service.is_available():
        return None

    system = (
        "Tu es analyste de veille DataSens. On te fournit des FAITS issus du dataset GoldAI "
        "(articles réels : politique, météo OpenWeather, finance Yahoo/INSEE, signaux crise).\n\n"
        "MISSION : répondre à la question en croisant les dimensions quand c'est pertinent "
        "(ex. intempéries → tension politique ; épidémie → sentiment santé ; marchés → climat économique).\n\n"
        "RÈGLES STRICTES :\n"
        "- Appuie-toi UNIQUEMENT sur les faits ci-dessous — n'invente pas de chiffres.\n"
        "- Cite des chiffres et titres d'exemple du contexte.\n"
        "- Si hantavirus/épidémie/inondation absent du contexte, dis-le clairement en une phrase.\n"
        "- 4 à 6 phrases, français, analytique et professionnel.\n"
        "- INTERDIT : Recommandation, Limite, Points clés, listes numérotées, markdown **, "
        "conseils pour enrichir le dataset, coaching technique.\n"
        "- Pas d'introduction du type « D'après le dataset »."
    )
    user_msg = (
        f"Thème : {theme_label}\n"
        f"Question : {question}\n\n"
        f"FAITS GOLDAI :\n{context[:5500]}"
    )
    try:
        raw = service.chat(
            message=user_msg,
            system_prompt=system,
            temperature=0.35,
            max_tokens=320,
        )
        cleaned = _clean_mistral_analysis(raw)
        return cleaned if len(cleaned.split()) >= 15 else None
    except Exception:
        return None
