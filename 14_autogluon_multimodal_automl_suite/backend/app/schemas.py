"""Pydantic schemas for multimodal AutoML API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ModalityScore(BaseModel):
    name: str
    accuracy: float
    n_test: int


class PredictResponse(BaseModel):
    multimodal: dict[str, Any]
    baselines: dict[str, dict[str, Any]]
    holdout_accuracies: dict[str, float]
    lift_vs_best_baseline: float
    best_baseline: str


class MetricsResponse(BaseModel):
    label: str
    n_train: int
    n_test: int
    class_labels: list[str]
    accuracies: dict[str, float]
    best_baseline: str
    best_baseline_accuracy: float
    multimodal_accuracy: float
    lift_vs_best_baseline: float
    modalities: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
