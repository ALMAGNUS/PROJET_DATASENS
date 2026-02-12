"""
Sentiment Inference - FlauBERT / CamemBERT
==========================================
Inférence sentiment sur données GoldAI (pas Silver).
"""

from src.config import get_settings
from .goldai_loader import load_goldai, get_goldai_texts

settings = get_settings()


def _label_to_sentiment(label: str) -> str:
    """Mappe label modèle -> positif/négatif/neutre"""
    low = label.lower()
    if "positive" in low or "5" in low or "4" in low:
        return "positif"
    if "negative" in low or "1" in low or "2" in low:
        return "négatif"
    return "neutre"


def run_sentiment_inference(
    limit: int = 100,
    model_name: str = "cmarkea/distilcamembert-base-sentiment",
    use_merged: bool = True,
    date: str | None = None,
) -> list[dict]:
    """
    Exécute l'inférence sentiment sur GoldAI avec un modèle Hugging Face.

    Args:
        limit: Nombre max d'articles à traiter
        model_name: Modèle HF (défaut: distilcamembert-base-sentiment)
        use_merged: Charger merged_all_dates.parquet
        date: Si use_merged=False, date au format YYYY-MM-DD

    Returns:
        Liste de {"id": int, "title": str, "sentiment_ml": str, "score": float}
    """
    try:
        from transformers import pipeline
        import torch
    except ImportError as e:
        raise ImportError(
            "transformers and torch required. pip install transformers torch"
        ) from e

    device = 0 if torch.cuda.is_available() and settings.model_device != "cpu" else -1

    # Charger GoldAI (pas Silver)
    df = load_goldai(limit=limit, use_merged=use_merged, date=date)
    texts = get_goldai_texts(df)

    if not texts:
        return []

    try:
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=device,
        )
    except Exception:
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            device=device,
        )

    results = []
    for aid, title, text in texts:
        inp = (title + " " + text)[:512]
        try:
            out = sentiment_pipeline(inp, truncation=True, max_length=512)
            if out:
                label = out[0]["label"]
                score = float(out[0]["score"])
                sentiment = _label_to_sentiment(label)
                results.append({"id": aid, "title": title[:100], "sentiment_ml": sentiment, "score": score})
            else:
                results.append({"id": aid, "title": title[:100], "sentiment_ml": "neutre", "score": 0.5})
        except Exception:
            results.append({"id": aid, "title": title[:100], "sentiment_ml": "neutre", "score": 0.5})

    return results
