# CRISP-DM NYC Taxi Audit Platform (Experiment 13 · Capstone)

Enterprise-style portfolio capstone that unifies three earlier experiments into one governed product:

| Layer | Source | Role here |
|-------|--------|-----------|
| Domain + model | Experiment 1 | Leakage-safe NYC taxi **trip duration** regression |
| Methodology | Experiment 10 | Full **six CRISP-DM phases** as docs, modules, APIs, and UI tabs |
| Governance | Experiment 11 | Embedded **DS audit scorecard** — this repo certifies itself |
| Operations | Capstone-new | **`/monitoring`** drift detection (PSI + KS) on simulated batches |

## Executive summary

**Business problem.** Estimate yellow-taxi `trip_duration` from pre-trip information only (coords, pickup time, passenger count) for ETA / ops analytics.

**Model.** Ridge baseline vs `HistGradientBoostingRegressor`, selected by time-holdout RMSE. Features are request-time only; KMeans pickup/dropoff zones are fit on the training window only.

**Governance.** `GET/POST /audit` runs the static auditor against *this* codebase and returns overall score, letter grade, six-dimension radar scores, and findings (leakage, seeds, validation, tests, docs, fairness).

**Monitoring.** `GET/POST /monitoring` builds a simulated “new batch,” compares feature distributions to the training reference, and flags each feature **green / yellow / red**.

Together, the platform reads as a complete story: problem → data → preparation → models → evaluation → deployment → **compliance** → **drift**.

## Architecture

```
docs/                  business_understanding.md, evaluation.md
data/                  synthetic (or Kaggle) trips → processed/trips.parquet
backend/
  app/                 CRISP-DM pipeline + train + EDA + service
  app/audit/           Embedded experiment-11 auditor
  app/monitoring.py    PSI + KS drift simulation
  main.py              FastAPI (:8013)
frontend/              Phase tabs + Audit radar + Monitoring dashboard (:5186)
```

### API surface

| Method | Path | Phase / concern |
|--------|------|-----------------|
| GET | `/business` | 1 Business understanding |
| GET | `/eda` | 2 Data understanding |
| GET | `/pipeline` | 3 Preparation diagram |
| GET | `/models` | 4 Modeling CV + holdout |
| GET | `/evaluate` | 5 Metrics, residuals, cluster fairness |
| POST | `/predict` | 6 Deployment scoring |
| GET | `/schema` | Deployment form schema |
| POST | `/retrain` | Rebuild artifacts |
| GET/POST | `/audit` | Live self-certification scorecard |
| GET/POST | `/monitoring` | Drift simulation (`none` / `moderate` / `severe`) |
| GET | `/health` | Liveness |

## How leakage was avoided

| Risk | Mitigation |
|------|------------|
| Random split | **Time-based split** by `pickup_datetime` |
| Target as feature | `trip_duration` excluded from `FEATURE_COLUMNS` |
| Post-trip fields | No fare, tip, tolls, speed, `dropoff_datetime` |
| Cluster leakage | KMeans **fit on train only**; test + `/predict` use `predict()` |
| Evaluation inflation | Holdout is the later time window only |

## Group fairness

Trip schemas lack classic protected attributes. Evaluation reports a **bias audit** by `pickup_cluster` (MAE / RMSE / residual disparities) as a geographic equity proxy — disparities are surfaced, not hidden.

## Dataset

| Mode | Source |
|------|--------|
| Default | `python data/fetch_data.py` — synthetic Kaggle-aligned sample |
| Optional | Place Kaggle `train.csv` at `data/raw/train.csv` or pass `--kaggle-csv` |

## How to run

Ports (portfolio convention for experiment **13**): API **8013**, UI **5186**.

```bash
# 1) Data
python data/fetch_data.py

# 2) Backend
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8013

# 3) Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5186 — Vite proxies `/api/*` → `http://localhost:8013/*`.

On first API startup, missing artifacts trigger automatic train.

### Tests

```bash
cd backend
pytest -q
```

## Frontend map

1–6 · CRISP-DM phase tabs with live taxi artifacts  
**G · Audit** · letter grade + radar + findings  
**M · Monitoring** · per-feature PSI/KS with red/yellow/green flags  

## What “production-minded” means here

- Explicit CRISP-DM phase boundaries (docs + code + API + UI)
- Leakage-safe training contract tested in CI-style unit tests
- Self-auditing governance endpoint (not a screenshot of a score)
- Drift monitoring hook that stakeholders can exercise with controlled shifts
- Residual-based prediction intervals on `/predict`

Next steps beyond this demo: model registry, auth, real batch ingestion, and online residual tracking.
