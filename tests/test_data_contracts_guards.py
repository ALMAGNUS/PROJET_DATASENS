import pytest

from src.data_contracts import assert_no_target_leakage, assert_training_label_present


def test_assert_no_target_leakage_ok() -> None:
    assert_no_target_leakage(["id", "title", "content", "source"])


def test_assert_no_target_leakage_raises_on_label() -> None:
    with pytest.raises(ValueError, match="Target leakage detected"):
        assert_no_target_leakage(["id", "title", "sentiment_label"])


def test_assert_training_label_present_ok() -> None:
    assert_training_label_present(["id", "title", "sentiment_label"])


def test_assert_training_label_present_raises_when_missing() -> None:
    with pytest.raises(ValueError, match="must contain `sentiment_label`"):
        assert_training_label_present(["id", "title", "content"])

