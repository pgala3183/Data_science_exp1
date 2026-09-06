"""Data validation presence checks."""

from __future__ import annotations

import re
from pathlib import Path

from app.fsutil import SourceFile
from app.schemas import Finding

VALIDATOR_LIBS = re.compile(
    r"\b(pandera|great_expectations|pydantic|cerberus|jsonschema|"
    r"tensorflow_data_validation|evidently|expectations)\b",
    re.IGNORECASE,
)

SCHEMA_HINTS = re.compile(
    r"\b(schema|validate_schema|check_schema|column.?dtype|dtype.?check|"
    r"assert_frame|BaseModel|Field\()\b",
    re.IGNORECASE,
)

NULL_CHECKS = re.compile(
    r"\b(isna|isnull|notna|dropna|fillna|null.?check|missing.?value)\b",
    re.IGNORECASE,
)

ASSERT_CHECKS = re.compile(r"\bassert\b")


def check(_root: Path, files: list[SourceFile]) -> list[Finding]:
    findings: list[Finding] = []
    has_lib = False
    has_schema = False
    has_null = False
    has_assert = False
    lib_hit: tuple[str, int] | None = None

    for sf in files:
        if VALIDATOR_LIBS.search(sf.text):
            has_lib = True
            m = VALIDATOR_LIBS.search(sf.text)
            if m and lib_hit is None:
                line = sf.text[: m.start()].count("\n") + 1
                lib_hit = (sf.relative, line)
        if SCHEMA_HINTS.search(sf.text):
            has_schema = True
        if NULL_CHECKS.search(sf.text):
            has_null = True
        if ASSERT_CHECKS.search(sf.text):
            has_assert = True

    if not has_lib and not has_schema:
        findings.append(
            Finding(
                dimension="validation",
                severity="high",
                rule_id="VAL_NO_SCHEMA",
                message=(
                    "No schema/validation library or schema-check pattern detected "
                    "(pandera, pydantic models, great_expectations, etc.)."
                ),
            )
        )
    elif has_lib and lib_hit:
        findings.append(
            Finding(
                dimension="validation",
                severity="info",
                rule_id="VAL_LIB_FOUND",
                message="Validation-related library usage detected.",
                file=lib_hit[0],
                line=lib_hit[1],
            )
        )

    if not has_null:
        findings.append(
            Finding(
                dimension="validation",
                severity="medium",
                rule_id="VAL_NO_NULL_HANDLING",
                message="No null/missing-value handling patterns (isna/dropna/fillna) found.",
            )
        )

    if not has_assert and not has_lib:
        findings.append(
            Finding(
                dimension="validation",
                severity="low",
                rule_id="VAL_NO_ASSERTS",
                message="No `assert` guards found in Python sources for data invariants.",
            )
        )

    if not findings:
        findings.append(
            Finding(
                dimension="validation",
                severity="info",
                rule_id="VAL_OK",
                message="Basic validation signals present.",
            )
        )
    return findings
