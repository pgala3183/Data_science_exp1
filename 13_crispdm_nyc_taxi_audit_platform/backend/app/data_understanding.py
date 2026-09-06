"""Phase 2 — Data Understanding for NYC taxi duration regression."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.config import FEATURE_COLUMNS, TARGET
from app.features import add_time_and_distance_features, filter_valid_trips


def compute_eda(raw: pd.DataFrame) -> dict[str, Any]:
    featured = add_time_and_distance_features(raw)
    df = filter_valid_trips(featured)

    duration = df[TARGET]
    # Duration buckets for class-balance-style chart
    bins = [60, 300, 600, 900, 1200, 1800, 3600, 7200]
    labels = ["1-5m", "5-10m", "10-15m", "15-20m", "20-30m", "30-60m", "60-120m"]
    bucketed = pd.cut(duration, bins=bins, labels=labels, include_lowest=True)
    label_counts = {str(k): int(v) for k, v in bucketed.value_counts().sort_index().items()}

    missingness = []
    for col in df.columns:
        miss = int(df[col].isna().sum())
        missingness.append(
            {
                "column": col,
                "missing": miss,
                "missing_pct": round(100.0 * miss / max(len(df), 1), 3),
            }
        )

    numeric_cols = [
        c
        for c in [
            TARGET,
            "haversine_km",
            "hour",
            "day_of_week",
            "passenger_count",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
        ]
        if c in df.columns
    ]
    numeric_summary = []
    for col in numeric_cols:
        s = pd.to_numeric(df[col], errors="coerce")
        numeric_summary.append(
            {
                "column": col,
                "mean": _f(s.mean()),
                "std": _f(s.std()),
                "min": _f(s.min()),
                "p25": _f(s.quantile(0.25)),
                "median": _f(s.median()),
                "p75": _f(s.quantile(0.75)),
                "max": _f(s.max()),
            }
        )

    corr_cols = [c for c in numeric_cols if c != TARGET][:10]
    corr_frame = df[[TARGET] + corr_cols].apply(pd.to_numeric, errors="coerce")
    corr = corr_frame.corr()
    corr_columns = list(corr.columns)
    matrix = [
        [None if (isinstance(v, float) and np.isnan(v)) else round(float(v), 4) for v in row]
        for row in corr.to_numpy()
    ]

    def _group_duration(col: str) -> list[dict]:
        rows = []
        for g, part in df.groupby(col):
            rows.append(
                {
                    "group": str(g),
                    "n": int(len(part)),
                    "mean_duration": float(part[TARGET].mean()),
                    "median_duration": float(part[TARGET].median()),
                }
            )
        return rows

    # Duration histogram for UI
    hist, edges = np.histogram(duration.to_numpy(), bins=40)
    duration_hist = {
        "counts": hist.astype(int).tolist(),
        "bin_edges": edges.astype(float).tolist(),
    }

    return {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "label": TARGET,
        "label_counts": label_counts,
        "mean_duration": float(duration.mean()),
        "median_duration": float(duration.median()),
        "missingness": missingness,
        "numeric_summary": numeric_summary,
        "categorical_summary": [
            {
                "column": "passenger_count",
                "n_unique": int(df["passenger_count"].nunique()),
                "top": [
                    {"value": str(k), "count": int(v)}
                    for k, v in df["passenger_count"].value_counts().head(6).items()
                ],
            }
        ],
        "correlation": {"columns": corr_columns, "matrix": matrix},
        "duration_by_hour": _group_duration("hour"),
        "duration_by_weekend": _group_duration("is_weekend"),
        "duration_by_rush": _group_duration("is_rush_hour"),
        "duration_histogram": duration_hist,
        "feature_columns": list(FEATURE_COLUMNS),
    }


def _f(v) -> float | None:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v)
