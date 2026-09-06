"""Pydantic schemas for AutoML API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    record: dict[str, Any] = Field(..., description="Feature dict matching training schema")
    include_base_models: bool = True


class PredictResponse(BaseModel):
    prediction: str
    probabilities: dict[str, float]
    best_model: str
    per_model_predictions: dict[str, str]
