"""Filesystem helpers for scanning a project tree."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.audit.config import SKIP_DIR_NAMES


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative: str
    text: str


def iter_python_files(root: Path) -> list[SourceFile]:
    files: list[SourceFile] = []
    root = root.resolve()
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        files.append(SourceFile(path=path, relative=rel, text=text))
    return files


def find_readme(root: Path) -> Path | None:
    for name in ("README.md", "README.rst", "README.txt", "Readme.md"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    # case-insensitive fallback
    for path in root.iterdir():
        if path.is_file() and path.name.lower().startswith("readme"):
            return path
    return None


def has_env_spec(root: Path) -> tuple[bool, str | None]:
    names = (
        "requirements.txt",
        "requirements-dev.txt",
        "environment.yml",
        "environment.yaml",
        "Pipfile",
        "poetry.lock",
        "pyproject.toml",
        "conda.yml",
    )
    for name in names:
        for path in root.rglob(name):
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            return True, str(path.relative_to(root)).replace("\\", "/")
    return False, None


def collect_test_files(root: Path) -> list[str]:
    found: list[str] = []
    root = root.resolve()
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        rel_path = path.relative_to(root)
        rel = str(rel_path).replace("\\", "/")
        name = path.name.lower()
        # Only inspect path parts under the project root (not parents like …/tests/fixtures/…)
        parts = {p.lower() for p in rel_path.parts}
        if name.startswith("test_") or name.endswith("_test.py") or "tests" in parts:
            if name == "__init__.py":
                continue
            found.append(rel)
    return sorted(set(found))
