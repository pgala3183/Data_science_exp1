"""AutoGluon Tabular AutoML API."""

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
from app.schemas import PredictRequest, PredictResponse  # noqa: E402
from app.service import (  # noqa: E402
    explain_payload,
    leaderboard_payload,
    load_meta,
    predict_record,
    train_predictor,
)

STATE = {"ready": False}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fit or load on startup (first run trains ~TIME_LIMIT_SEC)
    load_meta()
    STATE["ready"] = True
    yield


app = FastAPI(
    title="AutoGluon AutoML API",
    description="TabularPredictor with bagging + multi-layer stacking on Adult Income",
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


@app.get("/schema")
def schema():
    meta = load_meta()
    return {"label": meta["label"], "schema": meta["schema"], "class_labels": meta["class_labels"]}


@app.get("/leaderboard")
def leaderboard():
    if not STATE["ready"]:
        raise HTTPException(503, "Training in progress")
    return leaderboard_payload()


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        out = predict_record(req.record, include_base=req.include_base_models)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Prediction failed: {exc}") from exc
    return PredictResponse(**out)


@app.get("/explain")
def explain(top_k: int = Query(20, ge=1, le=50)):
    return explain_payload(top_k=top_k)


@app.post("/retrain")
def retrain():
    meta = train_predictor(force=True)
    STATE["ready"] = True
    return {
        "ok": True,
        "best_model": meta["best_model"],
        "n_train": meta["n_train"],
        "test_roc_auc": meta["test_roc_auc"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
