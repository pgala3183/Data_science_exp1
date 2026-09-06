"""Capstone runtime configuration — NYC Taxi CRISP-DM Audit Platform."""

from __future__ import annotations

from pathlib import Path

PORT = 8013
EXPERIMENT_ID = 13
RANDOM_STATE = 42
TEST_FRACTION = 0.2
N_CLUSTERS = 8
TARGET = "trip_duration"

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "trips.parquet"
DOCS_DIR = ROOT / "docs"
ARTIFACTS_DIR = BACKEND_DIR / "artifacts"

BUNDLE_PATH = ARTIFACTS_DIR / "model_bundle.joblib"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
EDA_PATH = ARTIFACTS_DIR / "eda.json"
EVAL_PATH = ARTIFACTS_DIR / "evaluation.json"
META_PATH = ARTIFACTS_DIR / "meta.json"
TRAIN_REF_PATH = ARTIFACTS_DIR / "train_feature_ref.joblib"

FEATURE_COLUMNS = [
    "haversine_km",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_rush_hour",
    "passenger_count",
    "pickup_cluster",
    "dropoff_cluster",
    "pickup_latitude",
    "pickup_longitude",
    "dropoff_latitude",
    "dropoff_longitude",
]

# Drift monitoring thresholds (PSI / KS)
PSI_YELLOW = 0.10
PSI_RED = 0.25
KS_YELLOW = 0.10
KS_RED = 0.20
