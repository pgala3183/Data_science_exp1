"""Pydantic request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
Dimension = Literal[
    "leakage",
    "reproducibility",
    "validation",
    "tests",
    "documentation",
    "fairness",
]


class AuditRequest(BaseModel):
    """Audit a project already on disk under the workspace."""

    path: str = Field(
        ...,
        description="Absolute or workspace-relative path to a data science project root",
        examples=["1_nyc_taxi_trip_prediction", "../3_customer_segmentation_clustering"],
    )


class Finding(BaseModel):
    dimension: Dimension
    severity: Severity
    rule_id: str
    message: str
    file: str | None = None
    line: int | None = None
    evidence: str | None = None


class DimensionScore(BaseModel):
    dimension: Dimension
    label: str
    score: int = Field(ge=0, le=100)
    finding_count: int


class AuditResponse(BaseModel):
    project_path: str
    project_name: str
    overall_score: int = Field(ge=0, le=100)
    letter_grade: str
    dimensions: list[DimensionScore]
    findings: list[Finding]
    files_scanned: int
    notes: list[str] = Field(default_factory=list)
