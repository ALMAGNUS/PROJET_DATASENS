"""
Anti-leakage guards for training vs inference separation.
"""

from __future__ import annotations

from collections.abc import Iterable


TARGET_LABEL_COLUMNS = {
    "sentiment_label",
    "label",
    "target",
    "y_true",
}


def assert_no_target_leakage(columns: Iterable[str]) -> None:
    """
    Fail fast if a target/label-like column is present in inference inputs.
    """
    cols = {str(c).strip() for c in columns}
    leaked = sorted(c for c in cols if c in TARGET_LABEL_COLUMNS)
    if leaked:
        raise ValueError(
            "Target leakage detected in inference inputs. "
            f"Forbidden columns present: {', '.join(leaked)}"
        )


def assert_training_label_present(columns: Iterable[str], label_col: str = "sentiment_label") -> None:
    """
    Ensure the training branch contains the expected supervised label.
    """
    cols = {str(c).strip() for c in columns}
    if label_col not in cols:
        raise ValueError(
            f"Training dataset must contain `{label_col}` but columns are: {sorted(cols)}"
        )

