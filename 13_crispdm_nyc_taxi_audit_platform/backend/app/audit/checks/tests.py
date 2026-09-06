"""Test file / harness presence checks."""

from __future__ import annotations

import re
from pathlib import Path

from app.audit.fsutil import SourceFile, collect_test_files
from app.audit.schemas import Finding

TEST_IMPORT = re.compile(r"\b(import pytest|from pytest|import unittest|from unittest)\b")


def check(root: Path, files: list[SourceFile]) -> list[Finding]:
    findings: list[Finding] = []
    test_files = collect_test_files(root)
    src_count = max(1, len(files) - len(test_files))

    if not test_files:
        findings.append(
            Finding(
                dimension="tests",
                severity="critical",
                rule_id="TEST_NONE",
                message="No test files found (expected `tests/`, `test_*.py`, or `*_test.py`).",
            )
        )
        return findings

    findings.append(
        Finding(
            dimension="tests",
            severity="info",
            rule_id="TEST_FILES_FOUND",
            message=f"Found {len(test_files)} test file(s).",
            evidence=", ".join(test_files[:8]),
        )
    )

    ratio = len(test_files) / src_count
    if ratio < 0.15:
        findings.append(
            Finding(
                dimension="tests",
                severity="medium",
                rule_id="TEST_LOW_RATIO",
                message=(
                    f"Test-to-source file ratio is low ({len(test_files)} tests / "
                    f"~{src_count} sources)."
                ),
            )
        )

    has_framework = any(TEST_IMPORT.search(sf.text) for sf in files)
    if not has_framework:
        findings.append(
            Finding(
                dimension="tests",
                severity="low",
                rule_id="TEST_NO_FRAMEWORK_IMPORT",
                message="Test files exist but no pytest/unittest import was detected.",
            )
        )

    return findings
