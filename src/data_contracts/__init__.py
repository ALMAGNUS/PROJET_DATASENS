"""
Data contracts package: schemas and anti-leakage guards.
"""

from .guards import assert_no_target_leakage, assert_training_label_present
from .schemas import CommonFeatures, InferenceInput, PredictionOutput, TrainingRecord

__all__ = [
    "CommonFeatures",
    "TrainingRecord",
    "InferenceInput",
    "PredictionOutput",
    "assert_no_target_leakage",
    "assert_training_label_present",
]

