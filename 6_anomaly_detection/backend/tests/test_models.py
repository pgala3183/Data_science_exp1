import numpy as np
import pandas as pd

from app.models import fit_backbones, score_matrix
from app.pipeline import time_split


def test_time_split_ordered():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=100, freq="min"),
            "is_anomaly": [0] * 100,
        }
    )
    tr, te = time_split(df, 0.2)
    assert tr["timestamp"].max() <= te["timestamp"].min()


def test_backbones_score_shape():
    rng = np.random.default_rng(0)
    Xn = rng.normal(size=(200, 8))
    Xt = np.vstack([Xn[:50], rng.normal(loc=5, size=(20, 8))])
    bb = fit_backbones(Xn, [f"f{i}" for i in range(8)], seed=0)
    scores = score_matrix(bb, Xt)
    assert scores["ensemble"].shape == (70,)
    assert 0 <= scores["ensemble"].min() <= scores["ensemble"].max() <= 1
