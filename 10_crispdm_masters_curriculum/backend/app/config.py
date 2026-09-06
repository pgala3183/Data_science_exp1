"""Paths and training knobs for CRISP-DM Adult Income curriculum."""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "adult.parquet"
DOCS_DIR = PROJECT_ROOT / "docs"
ARTIFACTS = BACKEND_DIR / "artifacts"

META_PATH = ARTIFACTS / "meta.json"
EDA_PATH = ARTIFACTS / "eda.json"
EVAL_PATH = ARTIFACTS / "evaluation.json"
PIPELINE_PATH = ARTIFACTS / "pipeline.joblib"
MODELS_PATH = ARTIFACTS / "models.joblib"
LSH_PATH = ARTIFACTS / "lsh.joblib"
TRAIN_META_PATH = ARTIFACTS / "train_index.joblib"

LABEL = "income"
POSITIVE_LABEL = ">50K"
SENSITIVE_ATTRS = ("sex", "race")

NUMERIC_FEATURES = [
    "age",
    "fnlwgt",
    "education-num",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
]
CATEGORICAL_FEATURES = [
    "workclass",
    "education",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "native-country",
]
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

PORT = 8010
RANDOM_STATE = 42
TEST_FRACTION = 0.2
CV_FOLDS = 5

# LSH (cosine via random hyperplanes)
LSH_N_BITS = 16
LSH_N_TABLES = 8
LSH_CANDIDATE_MULT = 20
