# Business Understanding — NYC Taxi Duration Audit Platform

## Problem statement

Operations teams need reliable **pre-trip ETA** for NYC yellow taxis: given pickup and dropoff locations, pickup time, and passenger count, estimate `trip_duration` in seconds. Duration underpins dispatch, SLA monitoring, and pricing analytics.

This capstone is not only a model — it is a **governed platform**: the same repo that trains the regressor also **self-audits** for leakage / reproducibility and **monitors** feature drift on simulated new batches.

## Business objectives

1. Deliver a leakage-safe duration model (time-based split, train-only clusters, no post-trip features).
2. Expose the full CRISP-DM story as API phases and UI tabs so stakeholders can inspect every stage.
3. Certify governance via a live `/audit` scorecard (embedded experiment-11 auditor).
4. Detect distribution shift via `/monitoring` (PSI + KS) before silent performance decay.

## Success criteria

| Criterion | Target |
|-----------|--------|
| Predictive quality | HistGradientBoosting beats Ridge RMSE on time holdout |
| Leakage control | No duration/fare/speed features; KMeans fit on train only |
| Audit | Self-scan returns usable letter grade; leakage dimension strong |
| Monitoring | Drifted batches flag features red/yellow/green |
| Group fairness | Residual MAE reported by pickup cluster (geographic equity proxy) |

## Stakeholders & constraints

- **Product / ops**: actionable ETA with confidence band.
- **Data science**: reproducible pipeline with seeds and tests.
- **Governance / risk**: static audit + drift alerts without blocking experimentation.
- **Constraint**: classic protected attributes (sex/race) are not in the trip schema — fairness is framed as **spatial group fairness**.

## Out of scope

- Real-time traffic APIs or map-matched routes.
- Automated fare quotation (would require different leakage rules).
- Production auth, multi-tenant tenancy, or model registry (documented as next steps).
