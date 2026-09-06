# Time Series Forecasting (Experiment 12)

Multi-horizon forecasting on a synthetic **daily retail sales** series with trend, weekly seasonality, and holiday peaks. Two model families — **SARIMA** (classical) and **HistGradientBoosting on lag/rolling features** (ML) — produce 1 / 7 / 30-step forecasts with prediction intervals, scored by **rolling-origin** backtest.

## Why random train/test splits are wrong for time series

Random k-fold (or a shuffled holdout) **leaks the future into the past**:

1. **Temporal dependence** — adjacent days are correlated. A random test row can sit between two training days, so the model effectively sees the neighborhood of the “held-out” point.
2. **Look-ahead** — features built from the full series (or models fit on shuffled folds) can use information that would not exist at forecast time.
3. **Optimistic metrics** — leakage makes MAE/RMSE look better than a real deployment, where you only ever know the past when predicting the future.

**What we do instead: rolling-origin (walk-forward) cross-validation**

- Choose origins \(t = t_0, t_0+\Delta, \ldots\)
- At each origin, **fit only on** \(y_1,\ldots,y_t\)
- Score forecasts at horizons \(h \in \{1,7,30\}\) against \(y_{t+h}\)
- Never shuffle calendar order; never train on any point after the origin

That matches how forecasts are produced in production and is the protocol behind `/backtest`.

## Dataset

`data/fetch_data.py` builds ~5 years of daily sales (`ds`, `y`) with:

- upward trend
- weekend uplift (weekly seasonality → ACF peaks at multiples of 7)
- annual sine + late-year holiday spike
- mild AR noise

```bash
python data/fetch_data.py
```

## Models

| Model | Role | Intervals |
|-------|------|-----------|
| **sarima** | `(1,1,1)×(1,0,1,7)` — order justified by ACF/PACF weekly structure + trend differencing | SARIMAX analytical `conf_int` |
| **gb_lags** | Direct multi-horizon `HistGradientBoostingRegressor` on lags `{1,2,3,7,14,21,28}`, rolling mean/std, Fourier calendar features | Residual \(\sigma\) × normal quantile (~95%) |

## How to run

Ports (experiment **12**): API **8012**, UI **5182**.

```bash
python data/fetch_data.py

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8012

cd frontend
npm install
npm run dev
```

Open http://localhost:5182.

First startup runs the rolling-origin backtest and caches `backend/artifacts/forecast_bundle.json`. Later starts load the cache; `POST /retrain` rebuilds it.

### Tests

```bash
cd backend
pytest
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/forecast` | Historical tail + point forecasts & intervals per model/horizon |
| `GET` | `/acf-pacf` | ACF & PACF up to 40 lags (+ CI) |
| `GET` | `/backtest` | MAE / RMSE / MAPE by model × horizon |
| `GET` | `/meta` | Model configs and backtest settings |
| `POST` | `/retrain` | Rebuild artifacts |

## Frontend

- **ACF/PACF** bar pair with significance bands
- **Forecast fan** — history + toggleable model lines with shaded confidence bands, horizon selector (1 / 7 / 30)
- **Backtest table** — MAE / RMSE / MAPE by model and horizon
