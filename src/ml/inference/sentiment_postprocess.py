"""Post-traitement sentiment (sans dépendance transformers)."""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "compute_sentiment_output",
    "finalize_sentiment",
    "refine_factual_neutral",
    "refine_irony_sentiment",
    "refine_mixed_sentiment",
    "refine_understatement_positive",
]


def _normalize_label(label: str) -> str:
    """ASCII lowercase — gère négatif/negatif, accents HF."""
    raw = unicodedata.normalize("NFKD", str(label))
    ascii_lbl = raw.encode("ascii", "ignore").decode("ascii")
    return ascii_lbl.lower().strip()


def _label_to_polarity(label: str) -> str:
    """Mappe un label modèle vers pos/neu/neg."""
    lbl = _normalize_label(label)
    if lbl in {"positive", "pos", "positif", "5", "very_pos", "4", "label_2"}:
        return "pos"
    if lbl in {"negative", "neg", "negatif", "1", "very_neg", "2", "label_0"}:
        return "neg"
    if lbl in {"neutral", "neu", "neutre", "3", "label_1"}:
        return "neu"
    if any(x in lbl for x in ("negative", "negatif", "very_neg")):
        return "neg"
    if any(x in lbl for x in ("positive", "positif", "very_pos")):
        return "pos"
    return "neu"


_CONTRAST_RE = re.compile(
    r"\b(mais|cependant|toutefois|néanmoins|neanmoins|par contre|même si|meme si|malgré|malgre|sans être|sans etre)\b",
    re.I,
)
_IMPROVE_RE = re.compile(
    r"(amélior\w*|amelior\w*|problème|probleme|défaut\w*|defaut\w*|insuffis\w*|faible|manque|corriger|critiqu\w*|confus\w*|exploitable|effort\w*|prêt|pret|convaincant\w*)",
    re.I,
)
_POS_HINT_RE = re.compile(
    r"\b(correct|bon|bien|réussi|reussi|satisf|conforme|acceptabl\w*|adéquat|adequat|intéressant|interessant|prometteur|moderne|joli|pertinent|plutôt bien|plutot bien|presque)\b",
    re.I,
)
_IRONY_OPEN_RE = re.compile(
    r"^(génial|genial|super|formidable|magnifique|excellent|quelle réussite|quelle reussite)\b",
    re.I,
)
_IRONY_NEG_RE = re.compile(
    r"(plante|incohérent|incoherent|trompe|erreur\w*|critique|évite|evite|confus|catastroph|faible|mauvais|lent|déçu|decu)",
    re.I,
)
_UNDERSTATEMENT_POS_RE = re.compile(
    r"pas mal( du tout)?.*(m'attendais à pire|attendais à pire)",
    re.I,
)
_FACTUAL_NEUTRAL_RE = re.compile(
    r"^(le |la |les |l'|un |une |des ).*(présente|classe|collectées|collectees|stockées|stockees|affiche|comprend|utilise|mises à jour|genere|génère|testé|teste|identifie|doivent être|doivent etre|sont stockés|sont stockes)\b",
    re.I,
)


def compute_sentiment_output(scores: list[dict]) -> dict:
    """
    Calcule label 3 classes, confidence et sentiment_score (finance-friendly).

    - label: POSITIVE | NEUTRAL | NEGATIVE (argmax)
    - confidence: max(probs) = probabilité de la classe prédite
    - sentiment_score: p_pos - p_neg ∈ [-1, +1] (stable, quant-friendly)
    """
    p_pos = p_neu = p_neg = 0.0
    for item in scores:
        pol = _label_to_polarity(item.get("label", ""))
        sc = float(item.get("score", 0))
        if pol == "pos":
            p_pos += sc
        elif pol == "neg":
            p_neg += sc
        else:
            p_neu += sc
    total = p_pos + p_neu + p_neg
    if total > 0:
        p_pos, p_neu, p_neg = p_pos / total, p_neu / total, p_neg / total
    probs = [("POSITIVE", p_pos), ("NEUTRAL", p_neu), ("NEGATIVE", p_neg)]
    label_3c = max(probs, key=lambda x: x[1])[0]
    confidence = max(p_pos, p_neu, p_neg)
    sentiment_score = p_pos - p_neg
    return {
        "label": label_3c,
        "confidence": round(confidence, 4),
        "sentiment_score": round(sentiment_score, 4),
        "p_pos": round(p_pos, 4),
        "p_neu": round(p_neu, 4),
        "p_neg": round(p_neg, 4),
    }


def refine_irony_sentiment(text: str, out: dict) -> dict:
    """Ironie explicite (« Super, encore des erreurs… ») → négatif."""
    if not text or not out:
        return out
    if not (_IRONY_OPEN_RE.search(text.strip()) and _IRONY_NEG_RE.search(text)):
        return out
    refined = dict(out)
    refined["label"] = "NEGATIVE"
    refined["sentiment_score"] = round(min(-0.55, float(refined.get("sentiment_score", 0))), 4)
    refined["confidence"] = round(max(float(refined.get("p_neg", 0)), 0.72), 4)
    refined["refined"] = "irony_prefix"
    return refined


def refine_understatement_positive(text: str, out: dict) -> dict:
    """Formulation atténuée positive (« pas mal, je m'attendais à pire »)."""
    if not text or not out:
        return out
    if not _UNDERSTATEMENT_POS_RE.search(text):
        return out
    refined = dict(out)
    refined["label"] = "POSITIVE"
    refined["sentiment_score"] = round(max(0.35, float(refined.get("sentiment_score", 0))), 4)
    refined["confidence"] = round(max(float(refined.get("p_pos", 0)), 0.62), 4)
    refined["refined"] = "understatement_positive"
    return refined


def refine_factual_neutral(text: str, out: dict) -> dict:
    """Descriptions factives sans marqueur affectif → neutre."""
    if not text or not out:
        return out
    if out.get("label") == "NEUTRAL":
        return out
    if _POS_HINT_RE.search(text) or _IMPROVE_RE.search(text):
        return out
    if not _FACTUAL_NEUTRAL_RE.search(text):
        return out
    refined = dict(out)
    refined["label"] = "NEUTRAL"
    refined["sentiment_score"] = round(
        max(-0.2, min(0.2, float(refined.get("sentiment_score", 0)) * 0.15)),
        4,
    )
    refined["confidence"] = round(max(float(refined.get("p_neu", 0)), 0.58), 4)
    refined["refined"] = "factual_neutral"
    return refined


def refine_mixed_sentiment(text: str, out: dict) -> dict:
    """
    Phrases contrastées du type « correct, mais… à améliorer » → neutre.
    Le modèle sur-pèse souvent le premier segment positif (ac0hik).
    """
    if not text or not out:
        return out
    has_contrast = bool(_CONTRAST_RE.search(text))
    has_mixed_signal = bool(_IMPROVE_RE.search(text) and _POS_HINT_RE.search(text))
    lukewarm = bool(
        re.search(r"\b(au moins|presque exploitable|déjà un progrès|deja un progres)\b", text, re.I)
    )
    if not has_contrast and not lukewarm:
        return out
    if not (has_mixed_signal or lukewarm):
        return out
    p_neg = float(out.get("p_neg", 0))
    sentiment_score = float(out.get("sentiment_score", 0))
    if p_neg >= 0.85 and sentiment_score <= -0.55:
        return out
    refined = dict(out)
    refined["label"] = "NEUTRAL"
    refined["sentiment_score"] = round(
        max(-0.35, min(0.35, float(refined.get("sentiment_score", 0)) * 0.25)),
        4,
    )
    p_neu = float(refined.get("p_neu", 0))
    refined["confidence"] = round(max(p_neu, 0.55), 4)
    refined["refined"] = "mixed_contrast"
    return refined


def finalize_sentiment(text: str, scores: list[dict]) -> dict:
    """Scores bruts → sortie métier (+ calibration phrases mitigées)."""
    out = compute_sentiment_output(scores)
    out = refine_irony_sentiment(text, out)
    out = refine_understatement_positive(text, out)
    out = refine_mixed_sentiment(text, out)
    return refine_factual_neutral(text, out)
