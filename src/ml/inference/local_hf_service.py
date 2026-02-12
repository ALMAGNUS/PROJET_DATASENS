"""
Local HF inference service (CamemBERT / FlauBERT).
Optimisé CPU: micro-batch, truncation, torch threads.
"""

from __future__ import annotations

from dataclasses import dataclass

from transformers import pipeline

from src.config import get_settings


def _setup_cpu_optimization() -> None:
    """Config CPU: torch threads + TOKENIZERS_PARALLELISM=false (Windows)."""
    import os
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    try:
        import torch
        if not torch.cuda.is_available():
            n = getattr(get_settings(), "torch_num_threads", 6)
            torch.set_num_threads(n)
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
        self._pipe = pipeline(
            task=self.task,
            model=self.model_name,
            device=device,
        )

    def predict(self, text: str) -> list[dict]:
        return self._pipe(text, truncation=True, max_length=self._max_length)
