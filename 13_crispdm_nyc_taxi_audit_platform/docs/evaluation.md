# Evaluation — Trip Duration Capstone

## Hold-out protocol

Evaluation uses a **time-based split**: trips sorted by `pickup_datetime`, earlier window for training, later window for test. Random splits would leak future traffic patterns and inflate RMSE/MAE.

## Metrics

| Metric | Role |
|--------|------|
| RMSE | Primary ranking metric (seconds) |
| MAE | Interpretable average absolute error |
| R² | Relative explained variance vs mean baseline |

Ridge (scaled) is the linear baseline; `HistGradientBoostingRegressor` is the primary challenger. The lower-RMSE model is deployed.

## Residual diagnostics

Residuals on the holdout are summarized (mean, std, percentiles, histogram). Large residual std widens the 95% prediction interval served by `/predict` (`± 1.96 σ`).

## Group fairness / bias audit

Taxi trip files lack sex/race fields. We run a **bias audit** using **pickup_cluster** as a geographic group:

- Per-cluster MAE / RMSE / mean residual
- `mae_range` across clusters as a disparate-impact style signal

High MAE on sparse outer clusters may indicate uneven service quality for those zones — reported transparently, not “fixed” away.

## Leakage checklist (re-verified at evaluation)

- `trip_duration` never in `FEATURE_COLUMNS`
- No `dropoff_datetime`, fare, tip, tolls, or speed features
- KMeans fit only on the training window
- Target hygiene filters remove impossible labels before split but do not create features from duration

## Monitoring link

Holdout metrics certify a snapshot. Production readiness also requires `/monitoring`: Population Stability Index and Kolmogorov–Smirnov tests compare a new batch to the training feature reference and flag drifted features.
