"""
Local HF inference service (CamemBERT / sentiment_fr).
Optimisé CPU: batch=1, truncation courte, torch threads limités.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from transformers import pipeline

from src.config import get_settings


def _label_to_polarity(label: str) -> str:
    """Mappe un label modèle vers pos/neu/neg."""
    lbl = str(label).lower()
    if any(x in lbl for x in ["positive", "pos", "positif", "5", "very_pos", "4"]):
        return "pos"
    if any(x in lbl for x in ["negative", "neg", "négatif", "1", "very_neg", "2"]):
        return "neg"
    return "neu"


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
    # Normaliser si somme != 1 (modèles bizarres)
    total = p_pos + p_neu + p_neg
    if total > 0:
        p_pos, p_neu, p_neg = p_pos / total, p_neu / total, p_neg / total
    # Label 3 classes
    probs = [("POSITIVE", p_pos), ("NEUTRAL", p_neu), ("NEGATIVE", p_neg)]
    label_3c = max(probs, key=lambda x: x[1])[0]
    confidence = max(p_pos, p_neu, p_neg)
    sentiment_score = p_pos - p_neg  # ∈ [-1, +1], finance-friendly
    return {
        "label": label_3c,
        "confidence": round(confidence, 4),
        "sentiment_score": round(sentiment_score, 4),
        "p_pos": round(p_pos, 4),
        "p_neu": round(p_neu, 4),
        "p_neg": round(p_neg, 4),
    }


def _setup_cpu_optimization() -> None:
    """Config CPU: torch threads limités + TOKENIZERS_PARALLELISM=false (Windows)."""
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    try:
        import torch
        if not torch.cuda.is_available():
            n = getattr(get_settings(), "torch_num_threads", 8)
            torch.set_num_threads(n)  # 6-8 pour i7, 4-6 pour i5
    except Exception:
        pass


@dataclass
class LocalHFService:
    model_name: str
    task: str

    def __post_init__(self) -> None:
        _setup_cpu_optimization()
        settings = get_settings()
        device = 0 if (settings.model_device == "cuda" and __import__("torch").cuda.is_available()) else -1
        # Conforme spec: max_length=256, batch 4-8, device=-1 (CPU)
        self._max_length = getattr(settings, "inference_max_length", 256)
        self._batch_size = getattr(settings, "inference_batch_size", 4)
        self._pipe = pipeline(
            task=self.task,
            model=self.model_name,
            device=device,
            model_kwargs={"low_cpu_mem_usage": True} if device == -1 else {},
        )

    def predict(self, text: str, return_all_scores: bool = True) -> list[dict]:
        """Prédiction. return_all_scores=True pour avoir p_pos, p_neu, p_neg."""
        return self._pipe(
            text,
            truncation=True,
            max_length=self._max_length,
            return_all_scores=return_all_scores,
        )
