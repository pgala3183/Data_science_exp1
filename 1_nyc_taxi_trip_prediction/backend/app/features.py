"""Feature engineering — only information available at trip start."""

from __future__ import annotations

import numpy as np
import pandas as pd


def haversine_km(
    lat1: np.ndarray | pd.Series,
    lon1: np.ndarray | pd.Series,
    lat2: np.ndarray | pd.Series,
    lon2: np.ndarray | pd.Series,
) -> np.ndarray:
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def add_time_and_distance_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ts = pd.to_datetime(out["pickup_datetime"])
    out["hour"] = ts.dt.hour.astype(int)
    out["day_of_week"] = ts.dt.dayofweek.astype(int)
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["is_rush_hour"] = (
        ((out["hour"] >= 7) & (out["hour"] <= 9) | (out["hour"] >= 16) & (out["hour"] <= 19))
        & (out["is_weekend"] == 0)
    ).astype(int)
    out["haversine_km"] = haversine_km(
        out["pickup_latitude"].to_numpy(),
        out["pickup_longitude"].to_numpy(),
        out["dropoff_latitude"].to_numpy(),
        out["dropoff_longitude"].to_numpy(),
    )
    return out


def filter_valid_trips(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning without using target-derived thresholds from the test set."""
    out = df.copy()
    out = out[
        (out["passenger_count"] >= 1)
        & (out["passenger_count"] <= 6)
        & (out["pickup_latitude"].between(40.5, 41.0))
        & (out["pickup_longitude"].between(-74.3, -73.6))
        & (out["dropoff_latitude"].between(40.5, 41.0))
        & (out["dropoff_longitude"].between(-74.3, -73.6))
    ]
    if "trip_duration" in out.columns:
        # Target hygiene only — applied before split on full frame is OK for
        # removing impossible labels; we do NOT engineer features from duration.
        out = out[(out["trip_duration"] >= 60) & (out["trip_duration"] <= 7200)]
    out = out[out["haversine_km"] > 0.05]
    return out.reset_index(drop=True)
