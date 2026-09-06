"""Audit package configuration (embedded from experiment 11)."""

from __future__ import annotations

from pathlib import Path

# Capstone project root (…/13_crispdm_nyc_taxi_audit_platform)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = PROJECT_ROOT.parent

ALLOWED_ROOTS: tuple[Path, ...] = (
    WORKSPACE_ROOT.resolve(),
    PROJECT_ROOT.resolve(),
)

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
