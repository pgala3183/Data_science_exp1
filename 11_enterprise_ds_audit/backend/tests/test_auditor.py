"""Auditor unit + API smoke tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.auditor import run_audit  # noqa: E402
from main import app  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_leaky_fixture_flags_fit_before_split():
    result = run_audit(FIXTURES / "sample_leaky")
    assert result.overall_score < 80
    rules = {f.rule_id for f in result.findings}
    assert "LEAK_FIT_BEFORE_SPLIT" in rules
    assert "TEST_NONE" in rules
    assert "DOC_NO_ENV_SPEC" in rules
    leak = next(d for d in result.dimensions if d.dimension == "leakage")
    assert leak.score < 100


def test_clean_fixture_scores_higher():
    leaky = run_audit(FIXTURES / "sample_leaky")
    clean = run_audit(FIXTURES / "sample_clean")
    assert clean.overall_score > leaky.overall_score
    assert clean.letter_grade in {"A", "B", "C"}
    rules = {f.rule_id for f in clean.findings}
    assert "LEAK_FIT_BEFORE_SPLIT" not in rules
    assert "TEST_FILES_FOUND" in rules


def test_audit_endpoint_on_fixture():
    path = str((FIXTURES / "sample_clean").resolve())
    r = client.post("/audit", json={"path": path})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["files_scanned"] >= 1
    assert len(body["dimensions"]) == 6
    assert body["letter_grade"] in list("ABCDF")
