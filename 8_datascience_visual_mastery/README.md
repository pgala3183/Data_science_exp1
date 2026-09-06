# Data Science Visual Mastery (Experiment 8)

Interactive visual explainers for core data-science math — Bayes, CLT, gradient descent, bias–variance, and confusion matrix / ROC — each with a live widget and a short quiz.

## Design

- **Client-side** for pure interactive math (Bayes prior/likelihood/posterior).
- **Backend** only when simulation grids or repeated sampling help (CLT, loss surface, polynomial bias–variance, ROC from synthetic scores).
- Progress per concept is stored in `localStorage`.

## How to run

Ports: API **8008**, UI **5181**.

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8008

cd frontend
npm install
npm run dev
```

Open http://localhost:5181.

### Tests

```bash
cd backend
pytest
```

## Concepts

| Path | Idea |
|------|------|
| `/bayes` | Prior × likelihood → posterior (sliders) |
| `/clt` | Sample means converge to a normal sampling distribution |
| `/gradient-descent` | Animated descent on a 2D loss bowl; learning-rate matters |
| `/bias-variance` | Polynomial degree vs train/test error |
| `/roc` | Threshold slider → confusion matrix, precision/recall, ROC point |
