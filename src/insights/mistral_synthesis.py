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
    if len(words) > 95:
        out = " ".join(words[:95]).rstrip(".,;") + "…"
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
        "Tu es analyste macro DataSens. On te fournit des FAITS GoldAI (politique, météo, économie, sport, crises).\n\n"
        "MISSION : répondre en croisant les dimensions avec un angle « macro → politique/économie/social ».\n"
        "Exemples de liens à exploiter SI les faits le permettent :\n"
        "- canicule / intempéries → tension sociale, ralentissement économique local ;\n"
        "- bulletins météo cléments ≠ canicule (ne pas confondre) ;\n"
        "- sport majeur (Coupe du monde, PSG/LDC) → euphorie, consommation, capital politique ;\n"
        "- économie neutre + politique négatif → découplage, méfiance endogène.\n\n"
        "RÈGLES :\n"
        "- Uniquement les faits fournis — pas de chiffres inventés.\n"
        "- 3 phrases denses, français, sans listes ni markdown.\n"
        "- Cite 1–2 titres ou chiffres du contexte.\n"
        "- INTERDIT : Recommandation, Limite, coaching technique, « il faudrait enrichir ».\n"
        "- Ne recopie pas toutes les cartes : apporte une lecture croisée."
    )
    user_msg = (
        f"Thème : {theme_label}\n" f"Question : {question}\n\n" f"FAITS GOLDAI :\n{context[:5500]}"
    )
    try:
        raw = service.chat(
            message=user_msg,
            system_prompt=system,
            temperature=0.35,
            max_tokens=220,
        )
        cleaned = _clean_mistral_analysis(raw)
        return cleaned if len(cleaned.split()) >= 15 else None
    except Exception:
        return None
