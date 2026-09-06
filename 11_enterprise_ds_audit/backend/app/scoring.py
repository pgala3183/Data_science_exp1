"""Score aggregation and letter grades."""

from __future__ import annotations

from app.config import DIMENSION_LABELS, DIMENSIONS, SEVERITY_PENALTY
from app.schemas import DimensionScore, Finding


def letter_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def score_dimension(findings: list[Finding], dimension: str) -> int:
    """Start at 100; subtract severity penalties (floored at 0). Info never deducts."""
    penalty = 0
    for f in findings:
        if f.dimension != dimension:
            continue
        penalty += SEVERITY_PENALTY.get(f.severity, 0)
    return max(0, min(100, 100 - penalty))


def build_dimension_scores(findings: list[Finding]) -> list[DimensionScore]:
    scores: list[DimensionScore] = []
    for dim in DIMENSIONS:
        dim_findings = [f for f in findings if f.dimension == dim]
        scores.append(
            DimensionScore(
                dimension=dim,  # type: ignore[arg-type]
                label=DIMENSION_LABELS[dim],
                score=score_dimension(findings, dim),
                finding_count=len(dim_findings),
            )
        )
    return scores


def overall_from_dimensions(dimensions: list[DimensionScore]) -> int:
    if not dimensions:
        return 0
    return int(round(sum(d.score for d in dimensions) / len(dimensions)))
