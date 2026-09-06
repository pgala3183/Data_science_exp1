"""CRISP-DM Adult Income curriculum API."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import PORT  # noqa: E402
from app.preparation import pipeline_diagram  # noqa: E402
from app.schemas import (  # noqa: E402
    PredictRequest,
    PredictResponse,
    SimilarRequest,
    SimilarResponse,
)
from app.service import (  # noqa: E402
    business_payload,
    evaluation_doc_payload,
    load_state,
    predict_record,
    similar_records,
    train_and_persist,
)

STATE = {"ready": False}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_state(force_train=False)
    STATE["ready"] = True
    yield


app = FastAPI(
    title="CRISP-DM Masters Curriculum API",
    description="Adult/Census Income end-to-end CRISP-DM with LSH similarity search",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "port": PORT, "ready": STATE["ready"]}


@app.get("/business")
def business():
    """Phase 1 — Business Understanding summary + markdown."""
    return business_payload()


@app.get("/eda")
def eda():
    """Phase 2 — Data Understanding summaries for visualization."""
    from app.service import STATE as S

    if S["eda"] is None:
        raise HTTPException(503, "EDA not ready")
    return S["eda"]


@app.get("/pipeline")
def pipeline():
    """Phase 3 — Documented preprocessing pipeline structure."""
    from app.service import STATE as S

    base = pipeline_diagram()
    if S["eval"] is not None:
        base = S["eval"].get("pipeline", base)
    return base


@app.get("/models")
def models():
    """Phase 4 — Modeling artifacts (CV + hold-out headline metrics)."""
    from app.service import STATE as S

    if S["meta"] is None or S["eval"] is None:
        raise HTTPException(503, "Models not ready")
    return {
        "models": S["meta"]["models"],
        "primary_model": S["meta"]["primary_model"],
        "cv": S["eval"]["cv"],
        "holdout": S["eval"]["metrics"],
        "n_train": S["eval"]["n_train"],
        "n_test": S["eval"]["n_test"],
    }


@app.get("/evaluate")
def evaluate():
    """Phase 5 — Accuracy, F1, ROC-AUC, fairness, evaluation write-up."""
    from app.service import STATE as S

    if S["eval"] is None:
        raise HTTPException(503, "Evaluation not ready")
    payload = dict(S["eval"])
    if not payload.get("evaluation_doc"):
        payload["evaluation_doc"] = evaluation_doc_payload()["markdown"]
    return payload


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, model: str | None = Query(default=None)):
    """Phase 6 — Score a single census-style record."""
    try:
        out = predict_record(req.record, model_name=model)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Prediction failed: {exc}") from exc
    return PredictResponse(**out)


@app.post("/similar", response_model=SimilarResponse)
def similar(req: SimilarRequest):
    """Phase 6 — LSH-backed cosine similarity search over training rows."""
    try:
        out = similar_records(req.record, k=req.k)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Similarity search failed: {exc}") from exc
    return SimilarResponse(**out)


@app.get("/schema")
def schema():
    from app.service import STATE as S

    if S["meta"] is None:
        raise HTTPException(503, "Not ready")
    return {
        "label": S["meta"]["label"],
        "feature_cols": S["meta"]["feature_cols"],
        "example": S["meta"]["schema"],
        "models": S["meta"]["models"],
    }


@app.post("/retrain")
def retrain():
    meta = train_and_persist(force=True)
    load_state(force_train=False)
    STATE["ready"] = True
    return {
        "ok": True,
        "n_train": meta["n_train"],
        "holdout_roc_auc": meta["holdout_roc_auc"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
