"""Phase 3 — Data Preparation: imputation, encoding, scaling."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.config import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """Reusable sklearn preprocessor (fit on train only)."""
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric, list(NUMERIC_FEATURES)),
            ("cat", categorical, list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
    )


def pipeline_diagram() -> dict[str, Any]:
    """Structured steps for the frontend pipeline diagram."""
    return {
        "name": "AdultIncomePreprocessor",
        "steps": [
            {
                "id": "split",
                "title": "Train / test split",
                "detail": "Stratified 80/20 on income; fit transformer on train only",
            },
            {
                "id": "num_impute",
                "title": "Numeric imputation",
                "detail": f"Median fill for {', '.join(NUMERIC_FEATURES)}",
            },
            {
                "id": "num_scale",
                "title": "Numeric scaling",
                "detail": "StandardScaler (zero mean, unit variance)",
            },
            {
                "id": "cat_impute",
                "title": "Categorical imputation",
                "detail": f"Most-frequent fill for {', '.join(CATEGORICAL_FEATURES)}",
            },
            {
                "id": "cat_encode",
                "title": "One-hot encoding",
                "detail": "OneHotEncoder(handle_unknown='ignore')",
            },
            {
                "id": "model",
                "title": "Classifier",
                "detail": "LogisticRegression or HistGradientBoosting on dense matrix",
            },
        ],
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
    }


def transform_record(preprocessor: ColumnTransformer, record: dict[str, Any]) -> np.ndarray:
    """Transform a single raw feature dict to model space."""
    row = {c: record.get(c) for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES}
    df = pd.DataFrame([row])
    return np.asarray(preprocessor.transform(df), dtype=np.float64)
