"""Rolling-origin (walk-forward) cross-validation — no random shuffling."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app import config
from app.models_classical import predict_horizons_sarima
from app.models_ml import predict_horizons_gb


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    err = y_pred - y_true
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    denom = np.clip(np.abs(y_true), 1e-6, None)
    mape = float(np.mean(np.abs(err) / denom) * 100)
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "mape": round(mape, 3)}


def rolling_origin_backtest(
    df: pd.DataFrame,
    horizons: tuple[int, ...] | None = None,
    min_train: int | None = None,
    step: int | None = None,
) -> list[dict]:
    horizons = horizons or config.HORIZONS
    min_train = min_train if min_train is not None else config.MIN_TRAIN
    step = step if step is not None else config.STEP
    """
    For each origin t = min_train, min_train+step, ...:
      - train on y[:t]  (strict past only)
      - score forecasts at t+h-1 for each horizon h
    Never peeks at future labels when fitting.
    """
    y = df["y"].to_numpy(dtype=float)
    n = len(y)
    max_h = max(horizons)
    records: dict[tuple[str, int], list[tuple[float, float]]] = {
        (model, h): [] for model in ("sarima", "gb_lags") for h in horizons
    }

    origins = list(range(min_train, n - max_h, step))
    for t in origins:
        y_train = y[:t]
        # SARIMA
        try:
            sarima_preds = predict_horizons_sarima(y_train, horizons)
        except Exception:
            sarima_preds = {h: float("nan") for h in horizons}
        # GB
        try:
            gb_preds = predict_horizons_gb(y_train, horizons)
        except Exception:
            gb_preds = {h: float("nan") for h in horizons}

        for h in horizons:
            actual = float(y[t + h - 1])
            if np.isfinite(sarima_preds[h]):
                records[("sarima", h)].append((actual, sarima_preds[h]))
            if np.isfinite(gb_preds[h]):
                records[("gb_lags", h)].append((actual, gb_preds[h]))

    rows = []
    for (model, h), pairs in records.items():
        if not pairs:
            rows.append(
                {
                    "model": model,
                    "horizon": h,
                    "mae": None,
                    "rmse": None,
                    "mape": None,
                    "n": 0,
                }
            )
            continue
        yt = np.array([p[0] for p in pairs])
        yp = np.array([p[1] for p in pairs])
        m = _metrics(yt, yp)
        rows.append({"model": model, "horizon": h, "n": len(pairs), **m})
    return rows
