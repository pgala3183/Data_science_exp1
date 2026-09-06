"""Paths and training knobs for AutoGluon Adult Income demo."""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "adult.parquet"
# Keep predictor path on the same drive as the project (Windows AutoGluon
# cannot relpath across C: vs D:). Junction this folder to D: if C: is full:
#   cmd /c mklink /J backend\artifacts D:\cursor-venvs\autogluon-artifacts
ARTIFACTS = BACKEND_DIR / "artifacts"
PREDICTOR_DIR = ARTIFACTS / "predictor"
META_PATH = ARTIFACTS / "meta.json"

LABEL = "income"
PORT = 8007
RANDOM_STATE = 42
# Keep wall-clock modest for demos; still enables bagging + multi-layer stack
TIME_LIMIT_SEC = 90
PRESETS = "medium_quality"
NUM_BAG_FOLDS = 4
NUM_STACK_LEVELS = 2
TEST_FRACTION = 0.2
