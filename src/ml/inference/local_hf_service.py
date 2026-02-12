"""
Local HF inference service (CamemBERT / FlauBERT).
"""

from __future__ import annotations

from dataclasses import dataclass

from transformers import pipeline

from src.config import get_settings


@dataclass
class LocalHFService:
    model_name: str
    task: str

    def __post_init__(self) -> None:
        settings = get_settings()
        self._pipe = pipeline(
            task=self.task,
            model=self.model_name,
            device=0 if settings.model_device == "cuda" else -1,
        )

    def predict(self, text: str) -> list[dict]:
        return self._pipe(text)
