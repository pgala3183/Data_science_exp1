"""Train, backtest, forecast, and cache artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.acf_pacf import compute_acf_pacf
from app.backtest import rolling_origin_backtest
from app import config
from app.data_loader import load_series
from app.models_classical import forecast_sarima
from app.models_ml import forecast_gb_multi


def _ensure_artifacts() -> Path:
    config.ARTIFACTS.mkdir(parents=True, exist_ok=True)
    return config.ARTIFACTS


def _json_path() -> Path:
    return _ensure_artifacts() / "forecast_bundle.json"


def _series_tail(df: pd.DataFrame, n: int = 365) -> list[dict]:
    tail = df.tail(n)
    return [
        {"ds": r.ds.strftime("%Y-%m-%d"), "y": round(float(r.y), 2)}
        for r in tail.itertuples()
    ]


def _horizon_points(frame: pd.DataFrame) -> list[dict]:
    return [
        {
            "ds": pd.Timestamp(r.ds).strftime("%Y-%m-%d"),
            "yhat": round(float(r.yhat), 2),
            "yhat_lower": round(float(r.yhat_lower), 2),
            "yhat_upper": round(float(r.yhat_upper), 2),
        }
        for r in frame.itertuples()
    ]


def build_forecasts(df: pd.DataFrame) -> list[dict]:
    y = df["y"].to_numpy(dtype=float)
    last = pd.Timestamp(df["ds"].iloc[-1])
    horizons = config.HORIZONS
    max_h = max(horizons)
    future_dates = pd.date_range(last + pd.Timedelta(days=1), periods=max_h, freq="D")

    sarima_full = forecast_sarima(y, steps=max_h, alpha=config.ALPHA, dates=future_dates)
    gb_by_h = forecast_gb_multi(y, horizons, dates=future_dates, alpha=config.ALPHA)

    forecasts = []
    # SARIMA: one path; expose per-horizon prefixes so UI can toggle
    sarima_horizons = []
    for h in horizons:
        sarima_horizons.append(
            {"horizon": h, "points": _horizon_points(sarima_full.iloc[:h])}
        )
    forecasts.append({"model": "sarima", "horizons": sarima_horizons})

    gb_horizons = []
    for h in horizons:
        gb_horizons.append({"horizon": h, "points": _horizon_points(gb_by_h[h])})
    forecasts.append({"model": "gb_lags", "horizons": gb_horizons})
    return forecasts


def train_and_evaluate() -> dict:
    df = load_series()
    acf_pacf = compute_acf_pacf(df["y"].to_numpy(dtype=float), nlags=config.MAX_LAGS)
    metrics = rolling_origin_backtest(df)
    forecasts = build_forecasts(df)
    bundle = {
        "series": _series_tail(df, 400),
        "series_full_n": len(df),
        "last_train_ds": df["ds"].iloc[-1].strftime("%Y-%m-%d"),
        "alpha": config.ALPHA,
        "forecasts": forecasts,
        "acf_pacf": acf_pacf,
        "backtest": {
            "method": "rolling_origin",
            "min_train": config.MIN_TRAIN,
            "step": config.STEP,
            "horizons": list(config.HORIZONS),
            "metrics": metrics,
            "note": (
                "Each origin uses only past observations for fitting; "
                "labels at t+h are held out. No random shuffle."
            ),
        },
        "models": {
            "sarima": {
                "order": [1, 1, 1],
                "seasonal_order": [1, 0, 1, 7],
                "intervals": "analytical SARIMAX conf_int",
            },
            "gb_lags": {
                "features": "lags + rolling mean/std + Fourier calendar",
                "strategy": "direct multi-horizon HistGradientBoosting",
                "intervals": "residual-sigma normal approx (±z·σ)",
            },
        },
    }
    path = _json_path()
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return bundle


def load_bundle() -> dict | None:
    path = _json_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_or_build_bundle() -> dict:
    bundle = load_bundle()
    if bundle is None:
        bundle = train_and_evaluate()
    return bundle
