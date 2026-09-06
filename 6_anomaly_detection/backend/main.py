"""Anomaly detection API."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import FEATURE_COLS, PORT  # noqa: E402
from app.models import score_matrix  # noqa: E402
from app.pipeline import load_backbones, load_eval, train_and_evaluate  # noqa: E402
from app.schemas import ScoreRequest, ScoreResponse, ScoreItem  # noqa: E402

STATE: dict = {"backbones": None, "eval": None}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    STATE["eval"] = load_eval()
    STATE["backbones"] = load_backbones()
    yield


app = FastAPI(
    title="Anomaly Detection API",
    description="Isolation Forest + LOF + Autoencoder ensemble on telemetry",
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
    return {"ok": True, "port": PORT, "ready": STATE["backbones"] is not None}


@app.get("/features")
def features():
    return {"features": FEATURE_COLS}


@app.get("/evaluate")
def evaluate():
    if STATE["eval"] is None:
        raise HTTPException(503, "Not ready")
    return STATE["eval"]


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    if STATE["backbones"] is None or STATE["eval"] is None:
        raise HTTPException(503, "Not ready")
    X = np.array([[getattr(r, c) for c in FEATURE_COLS] for r in req.records], dtype=float)
    scores = score_matrix(STATE["backbones"], X)
    thresholds = {
        name: float(STATE["eval"]["metrics"][name]["threshold"])
        for name in ("isolation_forest", "lof", "autoencoder", "ensemble")
    }
    out: list[ScoreItem] = []
    for i in range(len(req.records)):
        item = {
            "isolation_forest": round(float(scores["isolation_forest"][i]), 4),
            "lof": round(float(scores["lof"][i]), 4),
            "autoencoder": round(float(scores["autoencoder"][i]), 4),
            "ensemble": round(float(scores["ensemble"][i]), 4),
        }
        flagged = [k for k in ("isolation_forest", "lof", "autoencoder", "ensemble") if item[k] >= thresholds[k]]
        out.append(ScoreItem(**item, flagged_by=flagged))
    return ScoreResponse(scores=out, thresholds=thresholds)


@app.post("/retrain")
def retrain():
    payload = train_and_evaluate()
    STATE["eval"] = payload
    STATE["backbones"] = load_backbones()
    return {"ok": True, "n_test": payload["n_test"], "metrics": payload["metrics"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
