"""NYC Taxi CRISP-DM Audit Platform API (Experiment 13 Capstone)."""

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
from app.pipeline import pipeline_diagram  # noqa: E402
from app.schemas import MonitoringRequest, PredictRequest, PredictResponse  # noqa: E402
from app.service import (  # noqa: E402
    STATE,
    business_payload,
    load_state,
    monitoring_report,
    predict_trip,
    schema_payload,
    self_audit,
    train_and_persist,
)

READY = {"ok": False}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_state(force_train=False)
    READY["ok"] = True
    yield


app = FastAPI(
    title="CRISP-DM NYC Taxi Audit Platform",
    description=(
        "Capstone: taxi duration prediction wrapped in six CRISP-DM phases, "
        "with live self-audit scorecard and feature drift monitoring."
    ),
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
    return {"ok": True, "port": PORT, "ready": READY["ok"], "service": "nyc-taxi-audit-platform"}


@app.get("/business")
def business():
    """Phase 1 — Business Understanding."""
    return business_payload()


@app.get("/eda")
def eda():
    """Phase 2 — Data Understanding."""
    if STATE["eda"] is None:
        raise HTTPException(503, "EDA not ready")
    return STATE["eda"]


@app.get("/pipeline")
def pipeline():
    """Phase 3 — Data Preparation diagram."""
    if STATE["eval"] is not None and STATE["eval"].get("pipeline"):
        return STATE["eval"]["pipeline"]
    return pipeline_diagram()


@app.get("/models")
def models():
    """Phase 4 — Modeling artifacts."""
    if STATE["meta"] is None or STATE["eval"] is None:
        raise HTTPException(503, "Models not ready")
    return {
        "models": STATE["meta"]["models"],
        "primary_model": STATE["meta"]["primary_model"],
        "cv": STATE["eval"]["cv"],
        "holdout": STATE["eval"]["metrics"],
        "n_train": STATE["eval"]["n_train"],
        "n_test": STATE["eval"]["n_test"],
    }


@app.get("/evaluate")
def evaluate():
    """Phase 5 — Holdout metrics, residuals, cluster fairness."""
    if STATE["eval"] is None:
        raise HTTPException(503, "Evaluation not ready")
    return STATE["eval"]


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """Phase 6 — Score a single pre-trip request."""
    try:
        return PredictResponse(**predict_trip(req))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Prediction failed: {exc}") from exc


@app.get("/schema")
def schema():
    if STATE["meta"] is None:
        raise HTTPException(503, "Not ready")
    return schema_payload()


@app.post("/retrain")
def retrain():
    meta = train_and_persist(force=True)
    load_state(force_train=False)
    READY["ok"] = True
    return {
        "ok": True,
        "n_train": meta["n_train"],
        "primary_model": meta["primary_model"],
        "holdout_rmse": meta["holdout_rmse"],
    }


@app.get("/audit")
@app.post("/audit")
def audit():
    """
    Live self-certification: run the enterprise DS auditor against this repo.

    Returns overall score, letter grade, six-dimension radar scores, and findings.
    """
    try:
        return self_audit()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Audit failed: {exc}") from exc


@app.get("/monitoring")
def monitoring_get(
    drift_mode: str = Query("moderate", pattern="^(none|moderate|severe)$"),
    n: int = Query(3000, ge=200, le=20_000),
):
    """Simulate a new taxi batch and compare feature distributions to training."""
    try:
        return monitoring_report(drift_mode=drift_mode, n=n)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Monitoring failed: {exc}") from exc


@app.post("/monitoring")
def monitoring_post(req: MonitoringRequest):
    try:
        return monitoring_report(drift_mode=req.drift_mode, n=req.n)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Monitoring failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
