import pandas as pd
import pytest

from src.datasets import build_gold_app_input, build_gold_ia_labelled


def test_build_gold_ia_labelled_creates_sentiment_label() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "title": ["a", "b"],
            "content": ["x", "y"],
            "sentiment": ["positive", "négatif"],
        }
    )
    out = build_gold_ia_labelled(df)
    assert "sentiment_label" in out.columns
    assert out["sentiment_label"].tolist() == ["positif", "négatif"]


def test_build_gold_app_input_removes_target_columns() -> None:
    df = pd.DataFrame(
        {
            "id": [1],
            "title": ["a"],
            "content": ["x"],
            "sentiment": ["positif"],
            "sentiment_label": ["positif"],
        }
    )
    out = build_gold_app_input(df)
    assert "sentiment" not in out.columns
    assert "sentiment_label" not in out.columns


def test_build_gold_ia_labelled_requires_sentiment_source() -> None:
    with pytest.raises(ValueError, match="Missing sentiment columns"):
        build_gold_ia_labelled(pd.DataFrame({"id": [1], "title": ["a"]}))

