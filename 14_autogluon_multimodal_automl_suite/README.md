# AutoGluon Multimodal AutoML Suite

Experiment **14**: AutoGluon `MultiModalPredictor` on a synthetic product catalog with **image + text + tabular** features, compared against single-modality baselines.

## Why this experiment

Product listings are naturally multimodal. A price band alone is ambiguous; a short blurb can borrow words from another category; a thumbnail can be noisy. Fusion should help when modalities carry *complementary* errors — and on tiny data it often does not. This suite trains all four models on the same split so the **accuracy delta** is the headline, not a vibes-based claim.

## Dataset

Synthetic catalog (`data/generate_products.py`), 400 rows × 5 categories (`electronics`, `apparel`, `home`, `beauty`, `sports`):

| Modality | Columns |
|----------|---------|
| Image | `image` path (128×128 motif JPEG) |
| Text | `description` |
| Tabular | `price`, `rating`, `brand_tier`, `weight_oz`, `is_fragile` |
| Label | `category` |

Each modality is intentionally imperfect (color confusers, cross-category distractor phrases, overlapping price bands) so fusion has a job to do.

## Hold-out results

Stratified 75/25 split → **300 train / 100 test**. CPU training with small backbones (`mobilenetv3_small_100` + `electra-small`) and short time budgets.

| Model | Hold-out accuracy |
|-------|-------------------|
| **Multimodal** (image+text+tabular) | **100.0%** |
| Image-only (`MultiModalPredictor`) | 99.0% |
| Text-only (`TabularPredictor`) | 91.0% |
| Tabular-only (`TabularPredictor`) | 36.0% |

**Lift (multimodal − best baseline):** **+1.0 percentage points** over image-only.

### Interpretation

Fusion helped, but only slightly. The synthetic images use strong category motifs (shape + color), so the image-only model was already near ceiling (99%). Multimodal closed the last miss by combining text/tabular cues, but there was little room left to show a dramatic lift. Tabular-only collapsed to near chance because price bands overlap heavily by design — that modality alone is not enough. Text-only was strong (91%) thanks to category keywords in the blurb templates, yet still trailed vision.

On a real product corpus with messier photos, you would typically expect a larger multimodal gap; here the lesson is that **when one modality dominates, fusion’s incremental value shrinks** — and with only a few hundred labeled rows, deep fusion cannot invent signal that is not there.

## How to run

Ports: API **8014**, UI **5185**.

> Disk tip: AutoGluon multimodal + torch need space. This machine keeps the venv at `C:\agmm` (junctioned as `backend\.venv`) and artifacts/caches on `D:\ag-mm-artifacts` / `D:\ag-mm-cache` because `C:` was nearly full.

```bash
python data/generate_products.py --n 400

cd backend
# Prefer a short-path venv on Windows (torch nested paths hit MAX_PATH):
#   python -m venv C:\agmm
#   cmd /c mklink /J .venv C:\agmm
.\.venv\Scripts\activate
pip install -r requirements.txt
# Optional: point HF/torch caches at a roomy drive
#   set HF_HOME=D:\ag-mm-cache\hf
#   set TORCH_HOME=D:\ag-mm-cache\torch
uvicorn main:app --port 8014
# First startup trains multimodal + baselines (~2–5 min on CPU) then caches

cd frontend
npm install
npm run dev
```

Open http://localhost:5185.

### Tests

```bash
cd backend
pytest
```

API tests use shortened time limits into a temp artifacts directory (first run downloads small HF/timm weights).

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Readiness |
| `GET` | `/metrics` | Hold-out accuracies + lift vs best baseline |
| `GET` | `/demo` | Sample hold-out listings for the UI |
| `POST` | `/predict` | multipart: `image` + text/tabular fields → multimodal + baseline preds |
| `POST` | `/retrain` | Force a fresh fit of all models |

## Frontend

- Hold-out accuracy bar chart (multimodal vs image / text / tabular)
- Upload form (image + description + tabular fields) with demo-sample chips
- Side-by-side prediction panel showing each modality’s vote and its hold-out accuracy
