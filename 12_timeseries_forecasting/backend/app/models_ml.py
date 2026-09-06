"""Gradient boosting on lag / rolling-window features (direct multi-horizon)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from app.config import ALPHA, LAGS, RANDOM_STATE, ROLL_WINDOWS


def _feature_frame(y: np.ndarray) -> pd.DataFrame:
    s = pd.Series(y, dtype=float)
    feats: dict[str, np.ndarray] = {}
    for lag in LAGS:
        feats[f"lag_{lag}"] = s.shift(lag).to_numpy()
    for w in ROLL_WINDOWS:
        feats[f"roll_mean_{w}"] = s.shift(1).rolling(w).mean().to_numpy()
        feats[f"roll_std_{w}"] = s.shift(1).rolling(w).std().to_numpy()
    # Calendar proxies from index position (weekday approx via mod 7)
    idx = np.arange(len(y))
    feats["dow_sin"] = np.sin(2 * np.pi * (idx % 7) / 7)
    feats["dow_cos"] = np.cos(2 * np.pi * (idx % 7) / 7)
    feats["doy_sin"] = np.sin(2 * np.pi * (idx % 365) / 365)
    feats["doy_cos"] = np.cos(2 * np.pi * (idx % 365) / 365)
    return pd.DataFrame(feats)


def build_supervised(y: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    X = _feature_frame(y)
    target = pd.Series(y).shift(-horizon)
    df = X.copy()
    df["target"] = target.to_numpy()
    df = df.dropna()
    return df.drop(columns=["target"]).to_numpy(dtype=float), df["target"].to_numpy(dtype=float)


def fit_gb(y: np.ndarray, horizon: int) -> tuple[HistGradientBoostingRegressor, float]:
    """Fit direct model for `horizon` steps ahead; return model + residual sigma."""
    X, yt = build_supervised(y, horizon)
    model = HistGradientBoostingRegressor(
        max_depth=4,
        max_iter=120,
        learning_rate=0.08,
        min_samples_leaf=20,
        random_state=RANDOM_STATE,
    )
    model.fit(X, yt)
    resid = yt - model.predict(X)
    sigma = float(np.std(resid, ddof=1)) if len(resid) > 1 else 1.0
    return model, max(sigma, 1e-6)


def _last_feature_row(y: np.ndarray) -> np.ndarray:
    X = _feature_frame(y)
    row = X.iloc[[-1]].to_numpy(dtype=float)
    if np.isnan(row).any():
        # Fill remaining NaNs with column means of finite rows
        col_means = np.nanmean(X.to_numpy(dtype=float), axis=0)
        row = np.where(np.isnan(row), col_means, row)
    return row


def fit_gb_models(y: np.ndarray, horizons: tuple[int, ...]) -> dict[int, tuple]:
    return {h: fit_gb(y, h) for h in horizons}


def predict_point_gb(y: np.ndarray, model: HistGradientBoostingRegressor) -> float:
    feat = _last_feature_row(y)
    return float(model.predict(feat)[0])


def forecast_gb_multi(
    y: np.ndarray,
    horizons: tuple[int, ...],
    dates: pd.DatetimeIndex,
    alpha: float = ALPHA,
) -> dict[int, pd.DataFrame]:
    """
    For each horizon h, return a DataFrame with a single point (at step h)
    plus intermediate recursive h=1 path used only for the fan when needed.

    Fan chart strategy: build a recursive 1-step path for length max(H),
    and also attach dedicated direct-h points with their own intervals.
    """
    from scipy.stats import norm

    z = float(norm.ppf(1 - alpha / 2))
    max_h = max(horizons)
    models = fit_gb_models(y, horizons)

    # Recursive 1-step path for the fan line
    model_1, sigma_1 = models[1] if 1 in models else fit_gb(y, 1)
    hist = list(map(float, y))
    path = []
    for k in range(1, max_h + 1):
        feat = _last_feature_row(np.asarray(hist, dtype=float))
        yhat = float(model_1.predict(feat)[0])
        half = z * sigma_1 * np.sqrt(k)
        path.append(
            {
                "ds": dates[k - 1],
                "yhat": yhat,
                "yhat_lower": yhat - half,
                "yhat_upper": yhat + half,
            }
        )
        hist.append(yhat)
    path_df = pd.DataFrame(path)

    out: dict[int, pd.DataFrame] = {}
    for h in horizons:
        model_h, sigma_h = models[h]
        # Direct forecast at horizon h from original y
        yhat_h = predict_point_gb(y, model_h)
        half = z * sigma_h
        # Fan for horizon h: use recursive path up to h, but replace last
        # point with direct forecast + direct interval
        sub = path_df.iloc[:h].copy()
        sub.loc[sub.index[-1], "yhat"] = yhat_h
        sub.loc[sub.index[-1], "yhat_lower"] = yhat_h - half
        sub.loc[sub.index[-1], "yhat_upper"] = yhat_h + half
        out[h] = sub.reset_index(drop=True)
    return out


def predict_horizons_gb(y: np.ndarray, horizons: tuple[int, ...]) -> dict[int, float]:
    models = fit_gb_models(y, horizons)
    return {h: predict_point_gb(y, models[h][0]) for h in horizons}
