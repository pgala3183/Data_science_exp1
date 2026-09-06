"""Classical SARIMA multi-horizon forecasts with analytical intervals."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.config import ALPHA, SARIMA_ORDER, SARIMA_SEASONAL_ORDER


def fit_sarima(y: np.ndarray):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = SARIMAX(
            y,
            order=SARIMA_ORDER,
            seasonal_order=SARIMA_SEASONAL_ORDER,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        return model.fit(disp=False, maxiter=50)


def forecast_sarima(
    y: np.ndarray,
    steps: int,
    alpha: float = ALPHA,
    dates: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    """Return frame with columns yhat, yhat_lower, yhat_upper for `steps` ahead."""
    res = fit_sarima(y)
    pred = res.get_forecast(steps=steps)
    mean = np.asarray(pred.predicted_mean, dtype=float)
    ci = pred.conf_int(alpha=alpha)
    if hasattr(ci, "iloc"):
        lower = np.asarray(ci.iloc[:, 0], dtype=float)
        upper = np.asarray(ci.iloc[:, 1], dtype=float)
    else:
        ci_arr = np.asarray(ci, dtype=float)
        lower = ci_arr[:, 0]
        upper = ci_arr[:, 1]

    if dates is None:
        last = pd.Timestamp("2000-01-01")
        dates = pd.date_range(last + pd.Timedelta(days=1), periods=steps, freq="D")

    return pd.DataFrame(
        {
            "ds": dates,
            "yhat": mean,
            "yhat_lower": lower,
            "yhat_upper": upper,
        }
    )


def predict_horizons_sarima(
    y: np.ndarray,
    horizons: tuple[int, ...],
    alpha: float = ALPHA,
) -> dict[int, float]:
    """Point forecast only at selected horizons (1-indexed steps ahead)."""
    steps = max(horizons)
    res = fit_sarima(y)
    mean = np.asarray(res.get_forecast(steps=steps).predicted_mean, dtype=float)
    return {h: float(mean[h - 1]) for h in horizons}
