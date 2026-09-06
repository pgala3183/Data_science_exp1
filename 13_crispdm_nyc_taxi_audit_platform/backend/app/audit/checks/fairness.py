"""Fairness / bias check heuristics (intentionally conservative)."""

from __future__ import annotations

import re
from pathlib import Path

from app.audit.fsutil import SourceFile
from app.audit.schemas import Finding

FAIRNESS_LIBS = re.compile(
    r"\b(fairlearn|aif360|aequitas|what.?if.?tool|tensorflow_model_analysis|"
    r"fairness.?indicators|lift)\b",
    re.IGNORECASE,
)

FAIRNESS_METRICS = re.compile(
    r"\b(demographic\s+parity|equalized\s+odds|equal\s+opportunity|"
    r"disparate\s+impact|statistical\s+parity|calibration\s+by\s+group|"
    r"group\s+fairness|bias\s+audit|fairness\s+metric)\b",
    re.IGNORECASE,
)

PROTECTED_ATTRS = re.compile(
    r"\b(gender|sex|race|ethnicity|age_group|disability|religion|"
    r"protected_attribute|sensitive_feature|sensitive_attr)\b",
    re.IGNORECASE,
)


def check(_root: Path, files: list[SourceFile]) -> list[Finding]:
    findings: list[Finding] = []
    has_lib = False
    has_metric = False
    has_protected = False
    protected_hits: list[tuple[str, int, str]] = []

    for sf in files:
        if FAIRNESS_LIBS.search(sf.text):
            has_lib = True
        if FAIRNESS_METRICS.search(sf.text):
            has_metric = True
        for i, line in enumerate(sf.text.splitlines(), start=1):
            m = PROTECTED_ATTRS.search(line)
            if m:
                has_protected = True
                protected_hits.append((sf.relative, i, line.strip()[:160]))

    if not has_lib and not has_metric:
        findings.append(
            Finding(
                dimension="fairness",
                severity="high",
                rule_id="FAIR_NO_CHECKS",
                message=(
                    "No fairness library or fairness-metric language detected. "
                    "Static audit cannot confirm bias evaluation was performed."
                ),
            )
        )

    if has_protected and not (has_lib or has_metric):
        for rel, ln, ev in protected_hits[:3]:
            findings.append(
                Finding(
                    dimension="fairness",
                    severity="medium",
                    rule_id="FAIR_PROTECTED_WITHOUT_AUDIT",
                    message=(
                        "Potential sensitive/protected attribute reference without "
                        "accompanying fairness metrics."
                    ),
                    file=rel,
                    line=ln,
                    evidence=ev,
                )
            )

    if has_lib or has_metric:
        findings.append(
            Finding(
                dimension="fairness",
                severity="info",
                rule_id="FAIR_SIGNALS_OK",
                message="Fairness-related libraries or metric language detected.",
            )
        )

    return findings
