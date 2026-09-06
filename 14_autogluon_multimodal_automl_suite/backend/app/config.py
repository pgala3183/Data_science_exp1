"""Paths and training knobs for multimodal AutoGluon demo."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "products.csv"
IMAGES_DIR = PROJECT_ROOT / "data" / "images"

# Prefer D: when present (room for AutoGluon checkpoints). Override via AG_MM_ARTIFACTS.
_artifacts_env = os.environ.get("AG_MM_ARTIFACTS")
if _artifacts_env:
    ARTIFACTS = Path(_artifacts_env)
elif Path("D:/").exists():
    ARTIFACTS = Path("D:/ag-mm-artifacts")
else:
    ARTIFACTS = BACKEND_DIR / "artifacts"
UPLOADS = ARTIFACTS / "uploads"
META_PATH = ARTIFACTS / "meta.json"

MM_DIR = ARTIFACTS / "multimodal"
TABULAR_DIR = ARTIFACTS / "tabular"
TEXT_DIR = ARTIFACTS / "text"
IMAGE_DIR = ARTIFACTS / "image"

LABEL = "category"
IMAGE_COL = "image"
TEXT_COL = "description"
TABULAR_COLS = ["price", "rating", "brand_tier", "weight_oz", "is_fragile"]

PORT = 8014
RANDOM_STATE = 42
TEST_FRACTION = 0.25
N_SAMPLES = 400

# Wall-clock budgets — multimodal is the slow path on CPU
MM_TIME_LIMIT_SEC = 180
IMAGE_TIME_LIMIT_SEC = 120
TABULAR_TIME_LIMIT_SEC = 60
TEXT_TIME_LIMIT_SEC = 60
TABULAR_PRESETS = "medium_quality"
