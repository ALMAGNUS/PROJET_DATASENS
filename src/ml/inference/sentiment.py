"""
Sentiment Inference — Windows natif CPU (i7 / 15 Go)
=====================================================
Pipeline HF avec return_all_scores: 3 classes + confidence + sentiment_score.
Modèle: cmarkea/distilcamembert-base-sentiment (5★ → pos/neu/neg).
"""

import os
import time

from src.config import get_settings

from .goldai_loader import get_goldai_texts, load_goldai

settings = get_settings()
MODEL_ID = "cmarkea/distilcamembert-base-sentiment"
MODEL_ML_NAME = "sentiment_ml_distilcamembert"


def _setup_cpu_env() -> None:
    """Config CPU: threads + TOKENIZERS_PARALLELISM (évite soucis Windows)."""
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    try:
        import torch
        if not torch.cuda.is_available():
            n = getattr(settings, "torch_num_threads", 6)
            torch.set_num_threads(n)
    except Exception:
        pass


def _scores_to_output(scores: list[dict], model_id: str) -> dict:
    """
    Convertit sortie pipeline (return_all_scores) en label_3c, confidence, p_pos/neu/neg, sentiment_score.
    Gère: 5★ (cmarkea), POSITIVE/NEUTRAL/NEGATIVE, LABEL_0/1/2.
    """
    d = {str(x["label"]).strip(): float(x["score"]) for x in scores}
    # cmarkea: "1 star", "2 stars", "3 stars", "4 stars", "5 stars"
    p_1 = d.get("1 star", d.get("1 STAR", 0.0))
    p_2 = d.get("2 stars", d.get("2 STARS", 0.0))
    p_3 = d.get("3 stars", d.get("3 STARS", 0.0))
    p_4 = d.get("4 stars", d.get("4 STARS", 0.0))
    p_5 = d.get("5 stars", d.get("5 STARS", 0.0))
    if p_1 + p_2 + p_3 + p_4 + p_5 > 0:
        p_neg = p_1 + p_2
        p_neu = p_3
        p_pos = p_4 + p_5
    else:
        p_pos = d.get("POSITIVE", d.get("LABEL_2", d.get("POS", 0.0)))
        p_neu = d.get("NEUTRAL", d.get("LABEL_1", d.get("NEU", 0.0)))
        p_neg = d.get("NEGATIVE", d.get("LABEL_0", d.get("NEG", 0.0)))
        s = p_pos + p_neu + p_neg
        if s > 0:
            p_pos, p_neu, p_neg = p_pos / s, p_neu / s, p_neg / s
    best = max([("POSITIVE", p_pos), ("NEUTRAL", p_neu), ("NEGATIVE", p_neg)], key=lambda x: x[1])
    label_3c = best[0]
    confidence = best[1]
    sentiment_score = round(p_pos - p_neg, 4)  # [-1, +1] finance-friendly
    return {
        "model_id": model_id,
        "label_3c": label_3c,
        "confidence": round(confidence, 4),
        "p_pos": round(p_pos, 4),
        "p_neu": round(p_neu, 4),
        "p_neg": round(p_neg, 4),
        "sentiment_score": sentiment_score,
    }


def _label_3c_to_fr(label_3c: str) -> str:
    """POSITIVE/NEUTRAL/NEGATIVE → positif/neutre/négatif."""
    m = {"POSITIVE": "positif", "NEUTRAL": "neutre", "NEGATIVE": "négatif"}
    return m.get(str(label_3c).upper(), "neutre")


def predict_one(text: str, model_id: str | None = None, max_length: int = 256) -> dict:
    """
    Prédit sentiment d'un texte. Retourne label_3c, confidence, p_pos/neu/neg, sentiment_score, inference_ms.
    """
    _setup_cpu_env()
    model_id = model_id or settings.camembert_model_path or MODEL_ID
    max_length = max_length or getattr(settings, "inference_max_length", 256)
    try:
        import torch
        from transformers import pipeline
    except ImportError as e:
        raise ImportError("transformers and torch required") from e
    device = -1 if not (torch.cuda.is_available() and settings.model_device == "cuda") else 0
    clf = pipeline(
        "text-classification",
        model=model_id,
        tokenizer=model_id,
        device=device,
        truncation=True,
        max_length=max_length,
        top_k=None,  # toutes les classes (équivalent return_all_scores=True)
    )
    t0 = time.perf_counter()
    scores = clf(text[:800], batch_size=1)[0]
    ms = int((time.perf_counter() - t0) * 1000)
    out = _scores_to_output(scores, model_id)
    out["inference_ms"] = ms
    out["sentiment_ml"] = _label_3c_to_fr(out["label_3c"])
    out["confidence"] = out["confidence"]
    return out


def run_sentiment_inference(
    limit: int = 100,
    model_name: str | None = None,
    use_merged: bool = True,
    date: str | None = None,
    batch_size: int | None = None,
    max_length: int | None = None,
) -> list[dict]:
    """
    Inférence batch sur GoldAI. return_all_scores → label_3c, confidence, sentiment_score.
    """
    _setup_cpu_env()
    model_id = model_name or settings.camembert_model_path or MODEL_ID
    batch_size = batch_size or getattr(settings, "inference_batch_size", 4)
    max_length = max_length or getattr(settings, "inference_max_length", 256)
    try:
        import torch
        from transformers import pipeline
    except ImportError as e:
        raise ImportError("transformers and torch required") from e
    device = -1 if not (torch.cuda.is_available() and settings.model_device == "cuda") else 0
    try:
        clf = pipeline(
            "text-classification",
            model=model_id,
            tokenizer=model_id,
            device=device,
            truncation=True,
            max_length=max_length,
            top_k=None,  # toutes les classes (équivalent return_all_scores=True)
        )
    except Exception:
        clf = pipeline(
            "text-classification",
            model=MODEL_ID,
            tokenizer=MODEL_ID,
            device=device,
            truncation=True,
            max_length=max_length,
            top_k=None,  # toutes les classes (équivalent return_all_scores=True)
        )
    df = load_goldai(limit=limit, use_merged=use_merged, date=date)
    texts = get_goldai_texts(df)
    if not texts:
        return []
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = [(t[1] + " " + t[2]).strip()[:800] for t in batch]
        if not inputs:
            continue
        t0 = time.perf_counter()
        try:
            outs = clf(inputs, batch_size=len(inputs))
        except Exception:
            outs = [[{"label": "3 stars", "score": 1.0}]] * len(inputs)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        n = len(batch)
        per_ms = elapsed_ms // n if n else 0
        for j, (aid, title, _) in enumerate(batch):
            if j < len(outs) and isinstance(outs[j], list) and outs[j]:
                out = _scores_to_output(outs[j], model_id)
            else:
                out = {"label_3c": "NEUTRAL", "confidence": 0.5, "p_pos": 0.33, "p_neu": 0.34, "p_neg": 0.33, "sentiment_score": 0.0}
            results.append({
                "id": aid,
                "title": title[:100],
                "sentiment_ml": _label_3c_to_fr(out["label_3c"]),
                "label_3c": out["label_3c"],
                "confidence": out["confidence"],
                "p_pos": out["p_pos"],
                "p_neu": out["p_neu"],
                "p_neg": out["p_neg"],
                "sentiment_score": out["sentiment_score"],
                "score": out["confidence"],
                "inference_ms": per_ms,
                "model_id": model_id,
            })
    return results


def write_inference_to_model_output(
    results: list[dict],
    db_path: str | None = None,
    model_name: str = MODEL_ML_NAME,
) -> int:
    """
    Persiste dans MODEL_OUTPUT : label_3c, confidence, p_pos/neu/neg, sentiment_score, inference_ms.
    """
    from datetime import datetime

    settings = get_settings()
    db_path = db_path or settings.db_path
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(model_output)")
        cols = {r[1] for r in cur.fetchall()}
        has_ml_cols = "label_3c" in cols and "sentiment_score" in cols
        count = 0
        for r in results:
            raw_id = r.get("id")
            if raw_id is None:
                continue
            model_id = r.get("model_id", model_name)
            label_3c = r.get("label_3c", "NEUTRAL")
            confidence = float(r.get("confidence", r.get("score", 0.5)))
            p_pos = float(r.get("p_pos", 0.33))
            p_neu = float(r.get("p_neu", 0.34))
            p_neg = float(r.get("p_neg", 0.33))
            sentiment_score = float(r.get("sentiment_score", 0.0))
            inference_ms = int(r.get("inference_ms", 0))
            label = r.get("sentiment_ml", _label_3c_to_fr(label_3c))
            cur.execute(
                "DELETE FROM model_output WHERE raw_data_id = ? AND model_name = ?",
                (raw_id, model_name),
            )
            if has_ml_cols:
                cur.execute(
                    """INSERT INTO model_output (raw_data_id, model_name, model_id, label, label_3c,
                       confidence, score, p_pos, p_neu, p_neg, sentiment_score, inference_ms, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (raw_id, model_name, model_id, label, label_3c, confidence, confidence,
                     p_pos, p_neu, p_neg, sentiment_score, inference_ms, datetime.now().isoformat()),
                )
            else:
                cur.execute(
                    "INSERT INTO model_output (raw_data_id, model_name, label, score, created_at) VALUES (?, ?, ?, ?, ?)",
                    (raw_id, model_name, label, round(confidence, 3), datetime.now().isoformat()),
                )
            count += 1
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        raise RuntimeError(f"Écriture MODEL_OUTPUT échouée: {e}") from e
