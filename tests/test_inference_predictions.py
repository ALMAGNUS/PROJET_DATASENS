from pathlib import Path

import pandas as pd

from src.ml.inference.sentiment import build_prediction_frame, write_predictions_parquet


def test_build_prediction_frame_schema() -> None:
    results = [
        {
            "id": 1,
            "sentiment_ml": "positif",
            "sentiment_score": 0.42,
            "label_3c": "POSITIVE",
            "confidence": 0.91,
            "p_pos": 0.91,
            "p_neu": 0.07,
            "p_neg": 0.02,
            "inference_ms": 12,
            "title": "titre",
        }
    ]
    df = build_prediction_frame(
        results,
        model_version="test-model",
        inference_run_id="run-1",
        prediction_timestamp="2026-01-01T00:00:00",
    )
    expected = {
        "id",
        "predicted_sentiment",
        "predicted_sentiment_score",
        "model_version",
        "inference_run_id",
        "prediction_timestamp",
    }
    assert expected.issubset(set(df.columns))
    assert df.iloc[0]["predicted_sentiment"] == "positif"


def test_write_predictions_parquet(tmp_path: Path) -> None:
    results = [{"id": 1, "sentiment_ml": "neutre", "sentiment_score": 0.0, "confidence": 0.5}]
    out = write_predictions_parquet(results, base_dir=tmp_path, model_version="m1", inference_run_id="run-test")
    assert out.exists()
    df = pd.read_parquet(out)
    assert len(df) == 1
    assert df.iloc[0]["inference_run_id"] == "run-test"

