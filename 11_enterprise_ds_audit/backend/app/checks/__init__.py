"""Check package exports."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.fsutil import SourceFile
from app.schemas import Finding

from app.checks import documentation, fairness, leakage, reproducibility, tests, validation

CheckFn = Callable[[Path, list[SourceFile]], list[Finding]]

ALL_CHECKS: list[CheckFn] = [
    leakage.check,
    reproducibility.check,
    validation.check,
    tests.check,
    documentation.check,
    fairness.check,
]
