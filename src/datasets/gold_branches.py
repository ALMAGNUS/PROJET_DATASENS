"""
Builders for separated GoldAI datasets:
- gold_app_input (inference branch, unlabeled)
- gold_ia_labelled (training branch, labeled)
"""

from __future__ import annotations

import unicodedata

import pandas as pd

from src.data_contracts import assert_no_target_leakage, assert_training_label_present


def _ascii_fold(s: str) -> str:
    """Strip diacritics -> ASCII lowercase. Makes label matching encoding-agnostic."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    ).lower()


def normalize_sentiment_label(value: object) -> str:
    """
    Normalize sentiment label to one of: negatif / neutre / positif.

    Handles all encoding variants produced by Windows/Spark/CSV round-trips:
      negatif, negative, n\\xefegatif (mojibake U+00EF), n\\ufffdgatif, etc.
    The comparison uses ASCII-folded strings (diacritics stripped) so that
    any encoding corruption of e/e accent/i is transparent.
    """
    s = str(value or "").strip()
    folded = _ascii_fold(s)

    if folded in ("negatif", "negative", "neg"):
        return "negatif"
    # Catch corrupted variants after ASCII fold: niegatif, n?egatif, nagatif, etc.
    # They all start with 'n' and end with 'gatif' while not being 'neutre'.
    if folded.endswith("gatif") and folded.startswith("n"):
        return "negatif"
    if folded in ("positif", "positive", "pos"):
        return "positif"
    if folded in ("neutre", "neutral", "neu"):
        return "neutre"
    return "neutre"


def build_gold_ia_labelled(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build training dataset with explicit `sentiment_label`.
    Keeps `sentiment` for backward compatibility with existing trainers.
    """
    out = df.copy()
    if "sentiment_label" in out.columns:
        out["sentiment_label"] = out["sentiment_label"].apply(normalize_sentiment_label)
        if "sentiment" not in out.columns:
            out["sentiment"] = out["sentiment_label"]
    elif "sentiment" in out.columns:
        out["sentiment"] = out["sentiment"].apply(normalize_sentiment_label)
        out["sentiment_label"] = out["sentiment"]
    else:
        raise ValueError("Missing sentiment columns. Expected `sentiment` or `sentiment_label`.")

    assert_training_label_present(out.columns, label_col="sentiment_label")
    return out


def build_gold_app_input(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build inference input dataset without any training target columns.
    """
    out = df.copy()
    for col in ("sentiment_label", "label", "target", "y_true", "sentiment"):
        if col in out.columns:
            out = out.drop(columns=[col])
    assert_no_target_leakage(out.columns)
    return out
