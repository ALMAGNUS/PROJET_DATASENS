"""
Local HF inference service (CamemBERT / sentiment_fr).
Optimisé CPU: batch=1, truncation courte, torch threads limités.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from transformers import pipeline

from src.config import get_settings
from src.ml.inference.sentiment_postprocess import compute_sentiment_output, finalize_sentiment

__all__ = ["LocalHFService", "compute_sentiment_output", "finalize_sentiment"]


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
