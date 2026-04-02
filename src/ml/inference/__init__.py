"""ML Inference - GoldAI"""
from .goldai_loader import get_goldai_texts, load_goldai
from .sentiment import (
    build_prediction_frame,
    run_sentiment_inference,
    write_inference_to_model_output,
    write_predictions_parquet,
)

__all__ = [
    "get_goldai_texts",
    "load_goldai",
    "run_sentiment_inference",
    "write_inference_to_model_output",
    "build_prediction_frame",
    "write_predictions_parquet",
]
