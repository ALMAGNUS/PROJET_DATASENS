"""ML Models E3 - FlauBERT & CamemBERT (GoldAI)"""
from .inference.goldai_loader import load_goldai, get_goldai_texts
from .inference.sentiment import run_sentiment_inference

__all__ = ["load_goldai", "get_goldai_texts", "run_sentiment_inference"]
