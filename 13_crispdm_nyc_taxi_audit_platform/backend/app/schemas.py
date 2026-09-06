"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    pickup_latitude: float = Field(..., ge=40.4, le=41.1)
    pickup_longitude: float = Field(..., ge=-74.3, le=-73.5)
    dropoff_latitude: float = Field(..., ge=40.4, le=41.1)
    dropoff_longitude: float = Field(..., ge=-74.3, le=-73.5)
    pickup_datetime: datetime
    passenger_count: int = Field(1, ge=1, le=6)

    @field_validator("pickup_datetime", mode="before")
    @classmethod
    def parse_dt(cls, v: Any) -> Any:
        return v


class FeatureContribution(BaseModel):
    feature: str
    importance: float


class PredictResponse(BaseModel):
    predicted_duration_seconds: float
    predicted_duration_minutes: float
    confidence_interval_95_seconds: tuple[float, float]
    model_name: str
    top_features: list[FeatureContribution]
    haversine_km: float


class MonitoringRequest(BaseModel):
    drift_mode: Literal["none", "moderate", "severe"] = "moderate"
    n: int = Field(3000, ge=200, le=20_000)
