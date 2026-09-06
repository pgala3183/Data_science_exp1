# Enterprise DS Audit (Experiment 11)

Static-analysis auditor for data science projects. It scores a codebase across **six quality dimensions**, returns file/line findings, and visualizes the result as a radar chart with a letter grade.

This is a **heuristic linter**, not a proof of correctness — see [Limitations](#limitations) below.

## Dimensions

| ID | Label | What the checker looks for |
|----|--------|----------------------------|
| `leakage` | Train/Test Leakage | `.fit` / `.fit_transform` **before** a `train_test_split` (or similar) call; scaler fit with no split in-file; suspicious post-outcome identifiers |
| `reproducibility` | Reproducibility / Seeds | Missing `random_state` on stochastic sklearn APIs; absence of `SEED` / `np.random.seed` / `torch.manual_seed` |
| `validation` | Data Validation | pandera / pydantic / GE-style libs; schema hints; null handling (`isna`/`dropna`/`fillna`); asserts |
| `tests` | Test Coverage | Presence of `tests/` / `test_*.py`; rough test-to-source file ratio; pytest/unittest imports |
| `documentation` | Documentation | README length + section signals (problem, dataset, how to run, methodology); `requirements.txt` / env specs |
| `fairness` | Fairness / Bias | fairlearn / AIF360 / metric language; protected-attribute mentions without fairness checks |

**Scoring:** each dimension starts at 100. Findings deduct by severity (`critical` −35, `high` −22, `medium` −12, `low` −5, `info` 0). Overall score is the mean of the six dimensions; letter grade: A≥90, B≥80, C≥70, D≥60, else F.

## How to run

Ports (experiment **11**): API **8011**, UI **5184**.

```bash
# Backend
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8011

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5184 — paste a workspace-relative path (e.g. `1_nyc_taxi_trip_prediction`) or upload a project `.zip`.

### API

```bash
# Health
curl http://localhost:8011/health

# Audit a sibling experiment folder
curl -X POST http://localhost:8011/audit ^
  -H "Content-Type: application/json" ^
  -d "{\"path\": \"1_nyc_taxi_trip_prediction\"}"
```

`POST /audit/upload` accepts a multipart `.zip`. Paths must resolve under the `data_science_exp1` workspace (sandbox).

### Tests

```bash
cd backend
pytest
```

## Demo audits (real sibling projects)

The auditor was run against two other experiments in this portfolio. Full JSON lives in `artifacts/`.

### Experiment 1 — NYC Taxi Trip Prediction → **A (94)**

| Dimension | Score |
|-----------|------:|
| Train/Test Leakage | 100 |
| Reproducibility / Seeds | 100 |
| Data Validation | 88 |
| Test Coverage | 100 |
| Documentation | 100 |
| Fairness / Bias | 78 |

Notable findings:

- **VAL_NO_NULL_HANDLING** (medium) — no `isna`/`dropna`/`fillna` patterns in scanned Python.
- **FAIR_NO_CHECKS** (high) — no fairness library / metric language (expected for this regression task; the score still deducts honestly).

Leakage scored clean: KMeans/scaler fits are after train materialization in the pipeline files the checker sees.

### Experiment 3 — Customer Segmentation → **A (94)**

| Dimension | Score |
|-----------|------:|
| Train/Test Leakage | 83 |
| Reproducibility / Seeds | 100 |
| Data Validation | 100 |
| Test Coverage | 100 |
| Documentation | 100 |
| Fairness / Bias | 78 |

Notable findings:

- **LEAK_FIT_NO_SPLIT_IN_FILE** (medium) at `backend/app/clustering.py:61` — `StandardScaler().fit_transform(...)` with no train/test split in that file. For unsupervised RFM clustering this is often intentional (fit on the full customer table), but the static rule still flags it for human review.
- **LEAK_NO_SPLIT_PROJECT** (low) — no `train_test_split`-style call across the project (again expected for clustering).
- **FAIR_NO_CHECKS** (high) — no fairness audit tooling detected (segments can encode sensitive proxies; worth a manual review).

### Contrast: intentional leaky fixture → **F (57)**

`backend/tests/fixtures/sample_leaky` deliberately fits a scaler **before** `train_test_split`, omits `random_state`, has almost no README, no env spec, and no tests. The auditor flags `LEAK_FIT_BEFORE_SPLIT`, `TEST_NONE`, documentation gaps, etc. — showing the rules fire when problems are real.

## Frontend

- Letter-grade summary + overall score
- Radar / spider chart of the six dimension scores (Recharts)
- Findings list grouped by dimension, filterable by severity, with `file:line` and evidence snippets

## Limitations

Be honest about what this tool **cannot** do:

1. **Cross-file leakage** — a split in `pipeline.py` and a fit in `train.py` may not be ordered correctly by a per-file scan. We catch same-file order and missing-split smells, not full dataflow.
2. **Semantic leakage** — using `distance/duration` as a feature, target encoding fit on all rows, or group leakage across customers needs domain review; keyword hints are incomplete.
3. **Seeds** — custom RNGs, bash-level nondeterminism, and data-download drift are invisible.
4. **Validation** — detecting `pandera` imports ≠ proving schemas run in CI.
5. **“Test coverage”** — file presence / ratio only; not line or branch coverage from `pytest-cov`.
6. **Fairness** — keyword/library detection only; we do **not** compute disparate impact or equalized odds.
7. **Docs** — README section matching is regex-based and can false-positive on odd wording.

Treat scores as a **triage checklist**, then verify findings manually before blocking a release.

## Project layout

```
11_enterprise_ds_audit/
  backend/
    main.py                 # FastAPI: /health, /dimensions, /audit, /audit/upload
    app/
      auditor.py            # Orchestration + zip extract
      scoring.py
      checks/               # leakage, reproducibility, validation, tests, docs, fairness
    tests/                  # unit + API smoke tests + fixtures
  frontend/                 # React + Vite + Recharts
  artifacts/                # Saved audit JSON from demo runs
```
