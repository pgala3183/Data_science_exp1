"""Data drift monitoring — PSI + Kolmogorov–Smirnov vs training reference."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from app.config import FEATURE_COLUMNS, KS_RED, KS_YELLOW, PSI_RED, PSI_YELLOW, RANDOM_STATE
from app.features import add_time_and_distance_features
from app.pipeline import assign_clusters


def population_stability_index(
    expected: np.ndarray, actual: np.ndarray, bins: int = 10
) -> float:
    """PSI between expected (train) and actual (new batch) distributions."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    expected = expected[np.isfinite(expected)]
    actual = actual[np.isfinite(actual)]
    if len(expected) < 20 or len(actual) < 20:
        return 0.0

    qs = np.linspace(0, 100, bins + 1)
    edges = np.unique(np.percentile(expected, qs))
    if len(edges) < 3:
        edges = np.linspace(expected.min(), expected.max() + 1e-9, min(bins, 5) + 1)

    exp_counts, _ = np.histogram(expected, bins=edges)
    act_counts, _ = np.histogram(actual, bins=edges)

    exp_pct = exp_counts / max(exp_counts.sum(), 1)
    act_pct = act_counts / max(act_counts.sum(), 1)
    # Floor to avoid log(0)
    exp_pct = np.clip(exp_pct, 1e-4, None)
    act_pct = np.clip(act_pct, 1e-4, None)
    # Renormalize after clip
    exp_pct = exp_pct / exp_pct.sum()
    act_pct = act_pct / act_pct.sum()
    psi = float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))
    return abs(psi)


def ks_statistic(expected: np.ndarray, actual: np.ndarray) -> tuple[float, float]:
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    expected = expected[np.isfinite(expected)]
    actual = actual[np.isfinite(actual)]
    if len(expected) < 20 or len(actual) < 20:
        return 0.0, 1.0
    stat, p = stats.ks_2samp(expected, actual)
    return float(stat), float(p)


def _status(psi: float, ks: float) -> str:
    if psi >= PSI_RED or ks >= KS_RED:
        return "red"
    if psi >= PSI_YELLOW or ks >= KS_YELLOW:
        return "yellow"
    return "green"


def simulate_drifted_batch(
    X_train: pd.DataFrame,
    pickup_kmeans,
    dropoff_kmeans,
    *,
    n: int = 3000,
    drift_mode: str = "moderate",
    seed: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Simulate a 'new batch' of taxi trips with controlled distribution shift.

    Modes:
      - none: bootstrap from training (should stay green)
      - moderate: shift pickup coords + inflate rush-hour share
      - severe: larger geo shift + longer distances + more passengers
    """
    rng = np.random.default_rng(seed)
    base = X_train.sample(n=min(n, len(X_train)), replace=True, random_state=seed).copy()

    # Reconstruct a minimal raw frame for re-featurization
    raw = pd.DataFrame(
        {
            "pickup_latitude": base["pickup_latitude"].to_numpy(),
            "pickup_longitude": base["pickup_longitude"].to_numpy(),
            "dropoff_latitude": base["dropoff_latitude"].to_numpy(),
            "dropoff_longitude": base["dropoff_longitude"].to_numpy(),
            "passenger_count": base["passenger_count"].to_numpy(),
            "pickup_datetime": pd.to_datetime("2016-06-01")
            + pd.to_timedelta(rng.integers(0, 30 * 24 * 3600, len(base)), unit="s"),
        }
    )

    if drift_mode == "none":
        pass
    elif drift_mode == "severe":
        raw["pickup_latitude"] = (raw["pickup_latitude"] + 0.04).clip(40.5, 41.0)
        raw["pickup_longitude"] = (raw["pickup_longitude"] - 0.05).clip(-74.3, -73.6)
        raw["dropoff_latitude"] = (raw["dropoff_latitude"] + rng.normal(0.02, 0.01, len(raw))).clip(
            40.5, 41.0
        )
        raw["passenger_count"] = rng.choice([3, 4, 5, 6], size=len(raw))
        # Force more evening / weekend timestamps
        hours = rng.choice([18, 19, 20, 21, 22], size=len(raw))
        raw["pickup_datetime"] = raw["pickup_datetime"].dt.normalize() + pd.to_timedelta(
            hours, unit="h"
        )
    else:  # moderate
        raw["pickup_latitude"] = (raw["pickup_latitude"] + 0.015).clip(40.5, 41.0)
        raw["pickup_longitude"] = (raw["pickup_longitude"] - 0.02).clip(-74.3, -73.6)
        # Bias toward rush hours on weekdays
        rush_mask = rng.random(len(raw)) < 0.55
        rush_hours = rng.choice([7, 8, 9, 16, 17, 18, 19], size=rush_mask.sum())
        dts = raw["pickup_datetime"].copy()
        # Align to weekdays for rush subset
        dts = dts - pd.to_timedelta(dts.dt.dayofweek, unit="D")  # snap toward Monday
        dts.loc[rush_mask] = dts.loc[rush_mask].dt.normalize() + pd.to_timedelta(
            rush_hours, unit="h"
        )
        raw["pickup_datetime"] = dts
        raw.loc[rush_mask, "passenger_count"] = rng.choice([1, 2], size=int(rush_mask.sum()))

    featured = add_time_and_distance_features(raw)
    featured = assign_clusters(featured, pickup_kmeans, dropoff_kmeans)
    return featured[FEATURE_COLUMNS].reset_index(drop=True)


def compute_drift_report(
    X_train: pd.DataFrame,
    X_new: pd.DataFrame,
    *,
    drift_mode: str,
) -> dict[str, Any]:
    features = []
    for col in FEATURE_COLUMNS:
        if col not in X_train.columns or col not in X_new.columns:
            continue
        exp = X_train[col].to_numpy(dtype=float)
        act = X_new[col].to_numpy(dtype=float)
        psi = population_stability_index(exp, act)
        ks, p = ks_statistic(exp, act)
        status = _status(psi, ks)
        features.append(
            {
                "feature": col,
                "psi": round(psi, 4),
                "ks_statistic": round(ks, 4),
                "ks_pvalue": round(p, 6),
                "train_mean": round(float(np.nanmean(exp)), 4),
                "batch_mean": round(float(np.nanmean(act)), 4),
                "mean_shift": round(float(np.nanmean(act) - np.nanmean(exp)), 4),
                "status": status,
            }
        )

    features.sort(key=lambda r: (0 if r["status"] == "red" else 1 if r["status"] == "yellow" else 2, -r["psi"]))
    n_red = sum(1 for f in features if f["status"] == "red")
    n_yellow = sum(1 for f in features if f["status"] == "yellow")
    n_green = sum(1 for f in features if f["status"] == "green")

    if n_red >= 2:
        overall = "red"
    elif n_red >= 1 or n_yellow >= 3:
        overall = "yellow"
    else:
        overall = "green"

    return {
        "drift_mode": drift_mode,
        "n_train_ref": int(len(X_train)),
        "n_batch": int(len(X_new)),
        "overall_status": overall,
        "thresholds": {
            "psi_yellow": PSI_YELLOW,
            "psi_red": PSI_RED,
            "ks_yellow": KS_YELLOW,
            "ks_red": KS_RED,
        },
        "summary": {
            "red": n_red,
            "yellow": n_yellow,
            "green": n_green,
            "flagged_features": [f["feature"] for f in features if f["status"] != "green"],
        },
        "features": features,
        "notes": [
            "PSI < 0.10 typically stable; 0.10–0.25 moderate shift; ≥ 0.25 severe.",
            "KS statistic is the max CDF gap; higher values indicate larger distributional change.",
            "Simulated batches intentionally shift geography / rush-hour mix to demonstrate alerts.",
        ],
    }
