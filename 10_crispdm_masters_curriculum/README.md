# CRISP-DM Masters Curriculum (Experiment 10)

End-to-end **Adult / Census Income** project structured explicitly around the six CRISP-DM phases, with fairness reporting and LSH-backed similar-record search.

## CRISP-DM map

| Phase | Artifact |
|-------|----------|
| 1 Business Understanding | `docs/business_understanding.md`, `GET /business` |
| 2 Data Understanding | `GET /eda` (stats, missingness, correlations) |
| 3 Data Preparation | `app/preparation.py` + `GET /pipeline` |
| 4 Modeling | Logistic regression + HistGradientBoosting + CV |
| 5 Evaluation | `docs/evaluation.md`, `GET /evaluate` (metrics + fairness) |
| 6 Deployment | `POST /predict`, `POST /similar` (custom cosine LSH) |

## How to run

Ports: API **8010**, UI **5183**.

```bash
python data/fetch_data.py

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8010

cd frontend
npm install
npm run dev
```

Open http://localhost:5183.

First API start trains models and builds the LSH index (cached under `backend/artifacts/`).

### Tests

```bash
cd backend
pytest
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/business` | Business framing + markdown |
| `GET` | `/eda` | EDA summaries for charts |
| `GET` | `/pipeline` | Preprocessing diagram payload |
| `GET` | `/models` | CV + hold-out headline metrics |
| `GET` | `/evaluate` | Accuracy, F1, ROC-AUC, fairness, write-up |
| `POST` | `/predict` | Score one record |
| `POST` | `/similar` | Top-k cosine neighbors via custom LSH |
| `GET` | `/schema` | Feature schema + example row |
| `POST` | `/retrain` | Force retrain |

## Fairness note

Group metrics by **sex** and **race** are reported honestly (TPR, FPR, selection rate, base rate). Gaps are documented for governance discussion — this demo does **not** claim fairness or suitability for automated decisions.
