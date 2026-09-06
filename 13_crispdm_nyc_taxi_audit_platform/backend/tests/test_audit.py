from pathlib import Path

from app.audit import run_audit
from app.audit.config import PROJECT_ROOT


def test_self_audit_returns_scores():
    result = run_audit(
        PROJECT_ROOT,
        exclude_globs=("backend/app/audit/checks/",),
    )
    assert result.files_scanned >= 5
    assert 0 <= result.overall_score <= 100
    assert result.letter_grade in {"A", "B", "C", "D", "F"}
    assert len(result.dimensions) == 6
    assert Path(result.project_path).name == "13_crispdm_nyc_taxi_audit_platform"
