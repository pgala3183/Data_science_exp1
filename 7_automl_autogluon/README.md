# AutoGluon AutoML — Adult Income

Experiment **7**: AutoGluon `TabularPredictor` with **bagging + multi-layer stacking** on the Adult Income dataset (predict `income` &gt; $50K).

## What AutoGluon’s stacking is doing

Hand-tuning one model (say XGBoost) means you pick a single inductive bias and hope your validation luck holds. AutoGluon’s **multi-layer stack ensemble** does something different:

1. **Layer 1 (base models + bagging):** Many diverse learners (trees, linear models, neighbors, neural nets depending on the preset) are trained. With `num_bag_folds`, each base family is trained on several CV folds and their out-of-fold predictions are kept — that is **bagging**, which reduces variance and produces honest meta-features.
2. **Higher stack levels:** Models at level *k+1* do **not** see the raw features only; they learn from the **predictions** of level *k* (plus, in AutoGluon’s design, often the original features as well). A `WeightedEnsemble_L2` / `L3` then learns how to blend those stacked predictions.
3. **Why this usually beats one hand-tuned model:** Errors of different families are imperfectly correlated. Stacking lets a second-stage model exploit complementary strengths (e.g., trees catch interactions; linear models stabilize margins). Bagged OOF predictions reduce the meta-learner’s overfitting to in-sample noise. You pay fit time and complexity; you typically gain robustness and leaderboard score without manually babysitting hyperparameters.

In this demo we set `presets="medium_quality"`, `num_bag_folds=4`, `num_stack_levels=2`, and a wall-clock `time_limit` so a laptop can finish a credible stack without an overnight run.

## Dataset

Adult Income via OpenML (`data/fetch_data.py`). Label: `income` (`<=50K` / `>50K`). Categorical + numeric census features. Stratified hold-out for reported test ROC-AUC.

## How to run

Ports: API **8007**, UI **5180**.

> Disk tip: AutoGluon is large. Prefer a venv on `D:`. On Windows, junction artifacts to D: so AutoGluon stays on one drive letter: `cmd /c mklink /J backend\artifacts D:\cursor-venvs\autogluon-artifacts`.

```bash
python data/fetch_data.py --n 8000

cd backend
python -m venv D:\cursor-venvs\autogluon
# Windows junction into project (optional):
#   cmd /c mklink /J .venv D:\cursor-venvs\autogluon
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8007
# First startup trains ~90s then caches the predictor

cd frontend
npm install
npm run dev
```

Open http://localhost:5180.

### Tests

```bash
cd backend
pytest
```

API tests run a shortened AutoGluon fit (~45s) into a temp directory.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/leaderboard` | Model leaderboard (val/test score, fit & pred times) + stack graph |
| `POST` | `/predict` | Ensemble prediction + per-base-model predictions |
| `GET` | `/explain` | Permutation feature importance |
| `GET` | `/schema` | Dynamic form schema |
| `POST` | `/retrain` | Force a fresh fit |

## Frontend

- Sortable leaderboard + bar chart of validation scores
- Schema-driven input form for live predictions
- Stacking architecture diagram (base → ensemble layers)
