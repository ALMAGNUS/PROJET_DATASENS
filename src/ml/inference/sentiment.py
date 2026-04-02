"""
Sentiment Inference — Windows natif CPU (i7 / 15 Go)
=====================================================
Pipeline HF avec return_all_scores: 3 classes + confidence + sentiment_score.
Modèle: cmarkea/distilcamembert-base-sentiment (5★ → pos/neu/neg).
"""

import os
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from src.config import get_settings
from src.data_contracts import assert_no_target_leakage

from .goldai_loader import get_goldai_texts, load_goldai

settings = get_settings()
MODEL_ID = "cmarkea/distilcamembert-base-sentiment"
MODEL_ML_NAME = "sentiment_ml_distilcamembert"

# Module-level pipeline cache: one loaded model per model_id to avoid reloading on every predict_one() call.
_pipeline_cache: dict[str, object] = {}


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
    Convertit sortie pipeline (return_all_scores) en label_3c, confidence, p_pos/neu/neg.

    Gere tous les formats de labels rencontres dans le projet :
      - 5 etoiles (cmarkea): "1 star" ... "5 stars"
      - Anglais majuscules: POSITIVE / NEUTRAL / NEGATIVE
      - Numeriques HF:      LABEL_0 / LABEL_1 / LABEL_2
      - Francais lowercase: positif / neutre / negatif  (modele fine-tune ALMAGNUS)
    """
    import unicodedata as _ud

    def _fold(t: str) -> str:
        return "".join(c for c in _ud.normalize("NFKD", t) if not _ud.combining(c)).lower()

    d = {str(x["label"]).strip(): float(x["score"]) for x in scores}
    # ASCII-folded lookup — handles négatif/negatif/NÉGATIF and all diacritic variants
    d_fold = {_fold(k): v for k, v in d.items()}

    # --- 5 etoiles (cmarkea/distilcamembert-base-sentiment) ---
    p_1 = d.get("1 star", d.get("1 STAR", 0.0))
    p_2 = d.get("2 stars", d.get("2 STARS", 0.0))
    p_3 = d.get("3 stars", d.get("3 STARS", 0.0))
    p_4 = d.get("4 stars", d.get("4 STARS", 0.0))
    p_5 = d.get("5 stars", d.get("5 STARS", 0.0))
    if p_1 + p_2 + p_3 + p_4 + p_5 > 0.001:
        p_neg = p_1 + p_2
        p_neu = p_3
        p_pos = p_4 + p_5

    # --- Francais (modele fine-tune ALMAGNUS/datasens-sentiment-fr)
    # Labels peuvent etre: positif/neutre/negatif OU positif/neutre/negatif avec accents.
    # On utilise le fold ASCII pour matcher toutes les variantes.
    elif d_fold.get("positif", 0) + d_fold.get("neutre", 0) + d_fold.get("negatif", 0) > 0.001:
        p_pos = d_fold.get("positif", 0.0)
        p_neu = d_fold.get("neutre", 0.0)
        p_neg = d_fold.get("negatif", 0.0)

    # --- Anglais ou numeriques (XLM-RoBERTa, BERT, LABEL_0/1/2) ---
    else:
        p_pos = d_fold.get("positive", d.get("LABEL_2", d.get("pos", 0.0)))
        p_neu = d_fold.get("neutral", d.get("LABEL_1", d.get("neu", 0.0)))
        p_neg = d_fold.get("negative", d.get("LABEL_0", d.get("neg", 0.0)))
        s = p_pos + p_neu + p_neg
        if s > 0:
            p_pos, p_neu, p_neg = p_pos / s, p_neu / s, p_neg / s

    best = max([("POSITIVE", p_pos), ("NEUTRAL", p_neu), ("NEGATIVE", p_neg)], key=lambda x: x[1])
    label_3c = best[0]
    confidence = best[1]
    sentiment_score = round(p_pos - p_neg, 4)
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


def _get_pipeline(model_id: str, max_length: int):
    """
    Retourne (ou charge et met en cache) le pipeline HuggingFace pour un model_id donné.
    Le cache évite de recharger le modèle à chaque appel de predict_one().
    """
    if model_id not in _pipeline_cache:
        try:
            import torch
            from transformers import pipeline as hf_pipeline
        except ImportError as e:
            raise ImportError("transformers and torch required") from e
        device = -1 if not (torch.cuda.is_available() and settings.model_device == "cuda") else 0
        _pipeline_cache[model_id] = hf_pipeline(
            "text-classification",
            model=model_id,
            tokenizer=model_id,
            device=device,
            truncation=True,
            max_length=max_length,
            top_k=None,
        )
    return _pipeline_cache[model_id]


def predict_one(text: str, model_id: str | None = None, max_length: int = 256) -> dict:
    """
    Prédit sentiment d'un texte. Retourne label_3c, confidence, p_pos/neu/neg, sentiment_score, inference_ms.
    Le pipeline est chargé en cache: appels répétés sur le même modèle sont instantanés.
    """
    _setup_cpu_env()
    model_id = (
        model_id
        or settings.sentiment_finetuned_model_path
        or settings.camembert_model_path
        or MODEL_ID
    )
    max_length = max_length or getattr(settings, "inference_max_length", 256)
    clf = _get_pipeline(model_id, max_length)
    t0 = time.perf_counter()
    scores = clf(text[:800], batch_size=1)[0]
    ms = int((time.perf_counter() - t0) * 1000)
    out = _scores_to_output(scores, model_id)
    out["inference_ms"] = ms
    out["sentiment_ml"] = _label_3c_to_fr(out["label_3c"])
    return out


def run_sentiment_inference(
    limit: int = 100,
    model_name: str | None = None,
    use_merged: bool = True,
    date: str | None = None,
    batch_size: int | None = None,
    max_length: int | None = None,
    checkpoint_callback: "Callable[[list[dict]], None] | None" = None,
    checkpoint_every: int = 1000,
) -> list[dict]:
    """
    Inférence batch sur GoldAI. return_all_scores -> label_3c, confidence, sentiment_score.

    checkpoint_callback: appelé tous les `checkpoint_every` résultats accumulés avec la
        liste partielle — permet de sauvegarder les résultats intermédiaires.
    checkpoint_every: nombre de résultats entre deux appels au checkpoint_callback.
    """
    _setup_cpu_env()
    # Priority: explicit arg > fine-tuned model > pre-trained camembert > hard default
    model_id = (
        model_name
        or settings.sentiment_finetuned_model_path
        or settings.camembert_model_path
        or MODEL_ID
    )
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
            top_k=None,
        )
    except Exception as load_err:
        print(f"  WARN: impossible de charger {model_id} ({load_err}), fallback sur {MODEL_ID}")
        model_id = MODEL_ID
        clf = pipeline(
            "text-classification",
            model=MODEL_ID,
            tokenizer=MODEL_ID,
            device=device,
            truncation=True,
            max_length=max_length,
            top_k=None,
        )
    df = load_goldai(limit=limit, use_merged=use_merged, date=date)
    assert_no_target_leakage(df.columns)
    texts = get_goldai_texts(df)
    if not texts:
        return []

    total = len(texts)
    results: list[dict] = []
    last_checkpoint_at = 0
    t_global = time.perf_counter()
    last_checkpoint_n = 0

    print(f"  Modele: {model_id}")
    print(f"  Articles: {total:,}  |  batch_size={batch_size}  |  max_length={max_length}")
    if total > 500:
        print(f"  Checkpoint tous les {checkpoint_every:,} articles.")

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        inputs = [(t[1] + " " + t[2]).strip()[:800] for t in batch]
        if not inputs:
            continue
        t0 = time.perf_counter()
        try:
            outs = clf(inputs, batch_size=len(inputs))
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"\n  WARN batch {i}-{i+len(inputs)}: {exc} -> fallback NEUTRAL")
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

        done = len(results)
        elapsed_total = time.perf_counter() - t_global
        rate = done / elapsed_total if elapsed_total > 0 else 0
        eta_s = int((total - done) / rate) if rate > 0 else 0
        eta_str = f"{eta_s // 3600}h{(eta_s % 3600) // 60:02d}m" if eta_s >= 60 else f"{eta_s}s"
        pct = done / total * 100

        # Progress line (overwrite in place)
        print(
            f"\r  [{done:>{len(str(total))}}/{total}]  {pct:5.1f}%"
            f"  {rate:.1f} art/s  ETA {eta_str}   ",
            end="",
            flush=True,
        )

        # Checkpoint périodique
        if checkpoint_callback and (done - last_checkpoint_n) >= checkpoint_every:
            checkpoint_callback(list(results))
            last_checkpoint_n = done

    print()  # newline after progress line
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
            # SQLite model_output references raw_data.raw_data_id (integer).
            # Some inference IDs are stable text IDs (url/fingerprint), skip those for DB writes.
            try:
                raw_id_int = int(str(raw_id).strip())
            except (TypeError, ValueError):
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
                (raw_id_int, model_name),
            )
            if has_ml_cols:
                cur.execute(
                    """INSERT INTO model_output (raw_data_id, model_name, model_id, label, label_3c,
                       confidence, score, p_pos, p_neu, p_neg, sentiment_score, inference_ms, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (raw_id_int, model_name, model_id, label, label_3c, confidence, confidence,
                     p_pos, p_neu, p_neg, sentiment_score, inference_ms, datetime.now().isoformat()),
                )
            else:
                cur.execute(
                    "INSERT INTO model_output (raw_data_id, model_name, label, score, created_at) VALUES (?, ?, ?, ?, ?)",
                    (raw_id_int, model_name, label, round(confidence, 3), datetime.now().isoformat()),
                )
            count += 1
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        raise RuntimeError(f"Écriture MODEL_OUTPUT échouée: {e}") from e


def build_prediction_frame(
    results: list[dict],
    *,
    model_version: str,
    inference_run_id: str,
    prediction_timestamp: str | None = None,
) -> pd.DataFrame:
    """
    Build normalized inference output frame for GOLD_APP_PREDICTIONS.
    """
    ts = prediction_timestamp or datetime.now(timezone.utc).isoformat()
    rows = []
    for r in results:
        rows.append(
            {
                "id": r.get("id"),
                "predicted_sentiment": r.get("sentiment_ml", "neutre"),
                "predicted_sentiment_score": float(r.get("sentiment_score", 0.0)),
                "model_version": model_version,
                "inference_run_id": inference_run_id,
                "prediction_timestamp": ts,
                # Keep detailed diagnostics for analysis/debug dashboards.
                "label_3c": r.get("label_3c"),
                "confidence": float(r.get("confidence", r.get("score", 0.0))),
                "p_pos": float(r.get("p_pos", 0.0)),
                "p_neu": float(r.get("p_neu", 0.0)),
                "p_neg": float(r.get("p_neg", 0.0)),
                "inference_ms": int(r.get("inference_ms", 0)),
                "title": r.get("title"),
            }
        )
    return pd.DataFrame(rows)


def write_predictions_parquet(
    results: list[dict],
    *,
    base_dir: str | Path | None = None,
    model_version: str | None = None,
    inference_run_id: str | None = None,
) -> Path:
    """
    Persist predictions as partitioned parquet:
    data/goldai/predictions/date=YYYY-MM-DD/run=<run_id>/predictions.parquet
    """
    settings = get_settings()
    root = Path(base_dir or settings.goldai_base_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[3] / root

    run_id = inference_run_id or f"infer_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    model_ver = model_version or settings.sentiment_finetuned_model_path or settings.camembert_model_path
    ts = datetime.now(timezone.utc)
    date_part = ts.strftime("%Y-%m-%d")

    out_dir = root / "predictions" / f"date={date_part}" / f"run={run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "predictions.parquet"

    df = build_prediction_frame(
        results,
        model_version=model_ver,
        inference_run_id=run_id,
        prediction_timestamp=ts.isoformat(),
    )
    df.to_parquet(out_path, index=False)
    return out_path
