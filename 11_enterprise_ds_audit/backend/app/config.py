"""Runtime configuration."""

from __future__ import annotations

from pathlib import Path

PORT = 8011
EXPERIMENT_ID = 11

# Workspace root containing sibling experiments (…/data_science_exp1)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PROJECT_ROOT.parent

# Paths the auditor may scan (absolute, resolved). Keeps /audit from reading arbitrary disks.
ALLOWED_ROOTS: tuple[Path, ...] = (
    WORKSPACE_ROOT.resolve(),
    PROJECT_ROOT.resolve(),
)

UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".vite",
    "htmlcov",
    ".tox",
    "site-packages",
}

PYTHON_GLOBS = ("*.py",)
DOC_NAMES = ("readme.md", "readme.rst", "readme.txt")
ENV_SPEC_NAMES = (
    "requirements.txt",
    "requirements-dev.txt",
    "environment.yml",
    "environment.yaml",
    "conda.yml",
    "Pipfile",
    "poetry.lock",
    "pyproject.toml",
)

DIMENSIONS = (
    "leakage",
    "reproducibility",
    "validation",
    "tests",
    "documentation",
    "fairness",
)

DIMENSION_LABELS = {
    "leakage": "Train/Test Leakage",
    "reproducibility": "Reproducibility / Seeds",
    "validation": "Data Validation",
    "tests": "Test Coverage",
    "documentation": "Documentation",
    "fairness": "Fairness / Bias",
}

SEVERITY_PENALTY = {
    "critical": 35,
    "high": 22,
    "medium": 12,
    "low": 5,
    "info": 0,
}
