"""ML Models E3 - FlauBERT & CamemBERT (GoldAI)"""
from .inference.goldai_loader import get_goldai_texts, load_goldai
from .inference.sentiment import run_sentiment_inference, write_inference_to_model_output

__all__ = [
    "get_goldai_texts",
    "load_goldai",
    "run_sentiment_inference",
    "write_inference_to_model_output",
]
