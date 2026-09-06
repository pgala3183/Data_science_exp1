import numpy as np
import pandas as pd

from app.features import add_time_and_distance_features, haversine_km
from app.pipeline import assign_clusters, fit_coordinate_clusters, time_based_split


def test_haversine_known_distance():
    # ~5.4 km Times Square → Empire State-ish
    d = haversine_km(
        np.array([40.7580]),
        np.array([-73.9855]),
        np.array([40.7484]),
        np.array([-73.9857]),
    )
    assert 0.5 < float(d[0]) < 2.0


def test_time_based_split_is_ordered():
    df = pd.DataFrame(
        {
            "pickup_datetime": pd.date_range("2016-01-01", periods=100, freq="h"),
            "x": range(100),
        }
    )
    train, test = time_based_split(df, test_fraction=0.2)
    assert train["pickup_datetime"].max() <= test["pickup_datetime"].min()
    assert len(train) == 80
    assert len(test) == 20


def test_clusters_fit_on_train_only_pattern():
    """KMeans is fit on train coordinates; test only receives predict()."""
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame(
        {
            "pickup_datetime": pd.date_range("2016-01-01", periods=n, freq="h"),
            "pickup_latitude": rng.normal(40.75, 0.02, n),
            "pickup_longitude": rng.normal(-73.98, 0.02, n),
            "dropoff_latitude": rng.normal(40.76, 0.02, n),
            "dropoff_longitude": rng.normal(-73.97, 0.02, n),
            "passenger_count": 1,
            "trip_duration": rng.integers(300, 2000, n),
        }
    )
    df = add_time_and_distance_features(df)
    train, test = time_based_split(df, 0.2)
    pk, dk = fit_coordinate_clusters(train, n_clusters=4)
    test2 = assign_clusters(test, pk, dk)
    assert "pickup_cluster" in test2.columns
    assert test2["pickup_cluster"].between(0, 3).all()


def test_no_duration_in_feature_columns():
    from app.config import FEATURE_COLUMNS, TARGET

    assert TARGET not in FEATURE_COLUMNS
    assert "trip_duration" not in FEATURE_COLUMNS
    # Common leakage suspects
    for bad in ("dropoff_datetime", "fare_amount", "tip_amount", "total_amount"):
        assert bad not in FEATURE_COLUMNS
