"""Tests for the preprocessing pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import CATEGORICAL_FEATURES, FEATURE_COLS, NUMERIC_FEATURES
from app.preparation import build_preprocessor, pipeline_diagram, transform_record


def _toy_frame(n: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    data = {
        "age": rng.integers(18, 70, n),
        "fnlwgt": rng.integers(10_000, 400_000, n),
        "education-num": rng.integers(1, 16, n),
        "capital-gain": rng.integers(0, 5000, n),
        "capital-loss": rng.integers(0, 1000, n),
        "hours-per-week": rng.integers(10, 60, n),
        "workclass": rng.choice(["Private", "Self-emp", None], n),
        "education": rng.choice(["Bachelors", "HS-grad", "Masters"], n),
        "marital-status": rng.choice(["Never-married", "Married"], n),
        "occupation": rng.choice(["Tech", "Sales", "Other"], n),
        "relationship": rng.choice(["Husband", "Not-in-family"], n),
        "race": rng.choice(["White", "Black", "Asian-Pac-Islander"], n),
        "sex": rng.choice(["Male", "Female"], n),
        "native-country": rng.choice(["United-States", "Mexico", None], n),
    }
    return pd.DataFrame(data)


def test_preprocessor_fit_transform_shape():
    df = _toy_frame()
    prep = build_preprocessor()
    Xt = prep.fit_transform(df[FEATURE_COLS])
    assert Xt.ndim == 2
    assert Xt.shape[0] == len(df)
    assert Xt.shape[1] > len(NUMERIC_FEATURES)  # one-hot expands cats
    assert np.isfinite(Xt).all()


def test_preprocessor_handles_missing_and_unknown():
    df = _toy_frame()
    prep = build_preprocessor()
    prep.fit(df[FEATURE_COLS])
    row = {c: df.iloc[0][c] for c in FEATURE_COLS}
    row["workclass"] = None
    row["occupation"] = "Brand-New-Job"  # unseen category
    x = transform_record(prep, row)
    assert x.shape[0] == 1
    assert np.isfinite(x).all()


def test_pipeline_diagram_lists_phases():
    diagram = pipeline_diagram()
    ids = [s["id"] for s in diagram["steps"]]
    assert "num_impute" in ids
    assert "cat_encode" in ids
    assert set(diagram["numeric_features"]) == set(NUMERIC_FEATURES)
    assert set(diagram["categorical_features"]) == set(CATEGORICAL_FEATURES)
