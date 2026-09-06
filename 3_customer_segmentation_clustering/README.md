# Customer Segmentation & Clustering (Experiment 3)

RFM-based customer segmentation for e-commerce transactions: **K-Means** (k chosen via silhouette + elbow curves) compared with **Ward agglomerative** clustering, served through FastAPI and a React dashboard.

## Problem statement

Marketing teams need actionable groups — Champions, At Risk, New, Hibernating — not raw transaction dumps. We compress purchase history into Recency / Frequency / Monetary features and cluster customers into plain-language segments with suggested actions.

## Dataset & source

| Mode | Source |
|------|--------|
| Preferred | [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) (or GitHub CSV mirror) via `data/fetch_data.py` |
| Fallback | Synthetic transactions with planted RFM personas (`--synthetic-only`) |

```bash
python data/fetch_data.py
# or force synthetic:
python data/fetch_data.py --synthetic-only --n-customers 800
```

Raw/processed files are gitignored. If a synthetic `persona_true` column exists, it is **never** used as a clustering feature (only RFM).

## Methodology

1. Clean invoices (positive qty/price, drop cancellations, require CustomerID).
2. Compute RFM as of max(InvoiceDate)+1 day.
3. Standardize RFM → K-Means for k=2…8; pick **max silhouette**; keep inertia curve for elbow context.
4. Fit Ward **agglomerative** with the same k for comparison.
5. PCA (2D) for visualization; label centroids with marketing personas.

## AutoResearch note

Alternatives tried before settling on the final stack:

| Approach | Why considered | Why not final (alone) |
|----------|----------------|------------------------|
| **RFM quartile scoring (1–5 bins)** | Classic CRM playbook, very interpretable | Hard boundaries; no multivariate density; weak for overlapping behaviors |
| **DBSCAN on scaled RFM** | Finds odd-shaped groups / noise | Sensitive to `eps` on 3-D RFM; often one giant cluster + noise on retail data |
| **t-SNE for projection** | Pretty clusters | Non-parametric / non-reproducible for API centroids; slower; PCA keeps a linear, inspectable map |
| **K-Means + silhouette (chosen primary)** | Fast, stable centroids, clear “why k” story | Assumes spherical clusters — mitigated by also reporting agglomerative silhouette |
| **Ward agglomerative (chosen alternative)** | No random init; hierarchical structure | Less scalable; we still align k to the K-Means choice for a fair comparison |

**Final pick:** serve **K-Means** by default (best ops story: elbow + silhouette UI), expose **agglomerative** as a one-click alternative, project with **PCA**.

## How to run

Ports (experiment **3**): API **8003**, UI **5176**.

```bash
python data/fetch_data.py --synthetic-only

cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

cd frontend
npm install
npm run dev
```

Open http://localhost:5176.

### Tests

```bash
cd backend
pytest
ruff check app tests
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness |
| `GET` | `/segments?method=kmeans\|agglomerative` | Profiles, PCA points, elbow/silhouette curves |
| `GET` | `/segments/{id}/customers` | Sample customers in a segment |

## Key result

On the synthetic RFM-structured sample, silhouette-selected **k** typically lands in the 4–6 range, separating high-value recent buyers from dormant low-frequency cohorts. Toggle methods in the UI to compare silhouettes; use segment cards for marketing actions.
