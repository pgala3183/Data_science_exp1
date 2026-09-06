"""Pydantic request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    record: dict[str, Any]


class PredictResponse(BaseModel):
    prediction: str
    probability_gt_50k: float
    model: str
    probabilities: dict[str, float]


class SimilarRequest(BaseModel):
    record: dict[str, Any]
    k: int = Field(default=5, ge=1, le=25)
    model: str = "hist_gradient_boosting"


class SimilarNeighbor(BaseModel):
    rank: int
    cosine_similarity: float
    income: str
    record: dict[str, Any]


class SimilarResponse(BaseModel):
    query_prediction: str | None = None
    query_probability_gt_50k: float | None = None
    neighbors: list[SimilarNeighbor]
    lsh_candidates_scanned: int
    method: str = "cosine_lsh"
