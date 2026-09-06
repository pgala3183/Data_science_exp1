# Anomaly Detection (Experiment 6)

Tabular telemetry anomaly detection with **three backbones** — Isolation Forest, Local Outlier Factor (novelty), and a small PyTorch **autoencoder** (reconstruction error) — plus a simple mean ensemble. Evaluation emphasizes **Precision–Recall AUC** (not accuracy) on a heavily imbalanced held-out window.

## Problem statement

Operations telemetry is mostly normal. Accuracy is misleading when 95%+ of rows are healthy. We need detectors that rank rare faults highly and a UI to score live records.

## Dataset & ground-truth strategy

`data/fetch_data.py` generates synthetic multi-sensor telemetry (`cpu_pct`, `mem_pct`, `disk_io`, `net_in`, `net_out`, `temp_c`, `latency_ms`, `error_rate`).

**How “true anomalies” are defined:**

| Label | Definition |
|-------|------------|
| `is_anomaly = 0` | Sampled from a healthy multivariate operating regime (Gaussian-ish sensors). |
| `is_anomaly = 1` | **Injected** faults of three kinds: **spike** (CPU/latency/error blast), **drift** (memory + temperature creep), **off_manifold** (inverted network / odd disk). |

These injection labels are the evaluation ground truth. They are **not** used as model features.

**Training protocol (semi-supervised):** time-ordered split; Isolation Forest / LOF / autoencoder are fit on **normal training rows only** (`is_anomaly == 0`). Contaminated train anomalies are excluded from fitting so detectors learn “normal,” not attack signatures.

```bash
python data/fetch_data.py --n 5000 --anomaly-rate 0.05
```

## Models

1. **Isolation Forest** — path-length anomaly score (negated decision_function).
2. **Local Outlier Factor** — `novelty=True` for scoring new points.
3. **Autoencoder** — MLP encode/decode; MSE reconstruction error.
4. **Ensemble** — mean of min–max calibrated backbone scores.

Threshold per backbone: maximize F1 on the PR curve of the held-out set (reporting threshold; production would use a validation window).

## How to run

Ports (experiment **6**): API **8006**, UI **5179**.

```bash
python data/fetch_data.py

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# If disk is tight: pip install torch --index-url https://download.pytorch.org/whl/cpu
uvicorn main:app --reload --port 8006

cd frontend
npm install
npm run dev
```

Open http://localhost:5179.

### Tests

```bash
cd backend
pytest
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/evaluate` | PR curves, PR-AUC, confusion matrices, top anomalies |
| `POST` | `/score` | Score one/batch records; per-backbone + ensemble + flags |
| `GET` | `/features` | Feature schema |
| `POST` | `/retrain` | Rebuild artifacts |

## Key result

On the synthetic set, PR-AUC for the ensemble typically matches or exceeds the weaker single backbone; the dashboard overlays all PR curves and shows which models flag a live “anomaly preset” record.
