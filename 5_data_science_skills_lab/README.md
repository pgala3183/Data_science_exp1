# Data Science Skills Lab (Experiment 5)

A personal **skills reference library**: 28 discrete data-science skills (EDA, feature engineering, CV, imbalance, tuning, interpretability, stats tests, metrics, pipelines), each with a short description and a **runnable mini-exercise** on a classic benchmark dataset.

## Problem statement

Interview prep and day-to-day work need crisp reminders — not another 400-page course. This lab catalogs skills and proves each one with a tiny, inspectable run that returns a metric, table, or chart payload.

## Datasets (~5)

Prepared by `data/fetch_data.py` into `data/processed/`:

| Dataset | Origin |
|---------|--------|
| `iris` | sklearn `load_iris` |
| `wine` | sklearn `load_wine` |
| `titanic` | compact synthetic Titanic-like table |
| `housing` | compact synthetic House-Prices-like table |
| `adult` | compact synthetic Adult/Census-like income table |

```bash
python data/fetch_data.py
```

## Skills registry

`backend/app/skills.json` entries include: `id`, `name`, `category`, `difficulty`, `dataset`, `description`, `snippet`, and `script` (runner key). Runners live in `backend/app/runners.py` — clarity over cleverness.

## How to run

Ports (experiment **5**): API **8005**, UI **5178**.

```bash
python data/fetch_data.py

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8005

cd frontend
npm install
npm run dev
```

Open http://localhost:5178 — filter the catalog, open a skill, click **Run**. Progress is stored in `localStorage`.

### Tests

```bash
cd backend
pytest
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/skills` | List/filter (`category`, `dataset`, `q`) |
| `GET` | `/skills/{id}` | Skill detail |
| `POST` | `/skills/{id}/run` | Execute mini-exercise; return result payload |
| `GET` | `/categories` | Category list |

## Design notes

- No data leakage demos that cheat: scalers/undersampling fit on **train** only where relevant.
- Results are JSON (`table` / `metric` / `chart` / `mixed`) so the UI stays simple.
- Aim is a **reference library**, not a full LMS.
