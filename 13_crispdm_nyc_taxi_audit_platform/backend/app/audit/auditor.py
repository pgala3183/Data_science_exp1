"""Orchestrate all static checks into an AuditResponse."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from app.audit.checks import ALL_CHECKS
from app.audit.config import ALLOWED_ROOTS, WORKSPACE_ROOT
from app.audit.fsutil import iter_python_files
from app.audit.schemas import AuditResponse, Finding
from app.audit.scoring import build_dimension_scores, letter_grade, overall_from_dimensions


LIMITATIONS = [
    "Static analysis cannot prove absence of leakage — cross-file fit-then-split flows may be missed.",
    "Seed checks cover common sklearn/numpy/torch patterns only; custom RNGs may be invisible.",
    "Fairness scoring looks for libraries/keywords; it does not measure disparate impact.",
    "Test 'coverage' here is file presence/ratio, not line- or branch-coverage from a runner.",
    "README section detection is regex-based and can false-positive/false-negative on unusual docs.",
]


def resolve_project_path(raw: str) -> Path:
    """Resolve a user path and ensure it stays under an allowed workspace root."""
    p = Path(raw).expanduser()
    if not p.is_absolute():
        # Prefer workspace sibling, then CWD
        candidate = (WORKSPACE_ROOT / raw).resolve()
        if candidate.exists():
            p = candidate
        else:
            p = Path.cwd().joinpath(raw).resolve()
    else:
        p = p.resolve()

    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")
    if not p.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {p}")

    if not any(_is_relative_to(p, root) for root in ALLOWED_ROOTS):
        raise PermissionError(
            f"Path {p} is outside allowed workspace roots: "
            + ", ".join(str(r) for r in ALLOWED_ROOTS)
        )
    return p


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def run_audit(project_root: Path, *, exclude_globs: tuple[str, ...] = ()) -> AuditResponse:
    root = project_root.resolve()
    files = iter_python_files(root)
    if exclude_globs:
        files = [
            f
            for f in files
            if not any(g.replace("\\", "/") in f.relative.replace("\\", "/") for g in exclude_globs)
        ]
    findings: list[Finding] = []
    for check_fn in ALL_CHECKS:
        findings.extend(check_fn(root, files))

    # Drop pure-info findings from penalty math is already handled in scoring;
    # keep them for the UI.
    dimensions = build_dimension_scores(findings)
    overall = overall_from_dimensions(dimensions)

    return AuditResponse(
        project_path=str(root),
        project_name=root.name,
        overall_score=overall,
        letter_grade=letter_grade(overall),
        dimensions=dimensions,
        findings=findings,
        files_scanned=len(files),
        notes=LIMITATIONS,
    )


def extract_zip_to_temp(zip_bytes: bytes) -> Path:
    """Extract an uploaded zip into a temp dir under the workspace uploads area."""
    upload_root = WORKSPACE_ROOT / "11_enterprise_ds_audit" / "backend" / "uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="ds_audit_", dir=str(upload_root)))
    zip_path = tmp / "upload.zip"
    zip_path.write_bytes(zip_bytes)
    with zipfile.ZipFile(zip_path, "r") as zf:
        _safe_extract(zf, tmp / "project")
    project = tmp / "project"
    # If zip contained a single top-level folder, use that
    children = [c for c in project.iterdir() if c.name != "__MACOSX"]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return project


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts:
            raise ValueError(f"Unsafe zip entry: {name}")
        target = dest / name
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
