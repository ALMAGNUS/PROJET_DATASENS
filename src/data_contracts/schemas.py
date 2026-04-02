"""
Core data contracts for training/inference split.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CommonFeatures(BaseModel):
    id: str | int | None = None
    source: str | None = None
    title: str = Field(default="", max_length=1000)
    content: str = Field(default="", max_length=20000)
    collected_at: str | None = None
    topic_1: str | None = None
    topic_2: str | None = None


class TrainingRecord(CommonFeatures):
    sentiment_label: str


class InferenceInput(CommonFeatures):
    pass


class PredictionOutput(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str | int | None = None
    predicted_sentiment: str
    predicted_sentiment_score: float
    model_version: str
    inference_run_id: str
    prediction_timestamp: str

