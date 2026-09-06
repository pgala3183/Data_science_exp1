"""Visual mastery API — computation endpoints for interactive explainers."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import PORT  # noqa: E402
from app.math_engines import (  # noqa: E402
    CONCEPTS,
    bias_variance,
    gd_trajectory,
    loss_surface,
    roc_bundle,
    simulate_clt,
)

app = FastAPI(
    title="Data Science Visual Mastery",
    description="Computation helpers for interactive math explainers",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CLTRequest(BaseModel):
    dist: str = Field("exponential", pattern="^(exponential|uniform|bernoulli)$")
    sample_size: int = Field(30, ge=1, le=500)
    n_samples: int = Field(2000, ge=100, le=10000)
    seed: int = 42


class GDRequest(BaseModel):
    w1: float = -1.5
    w2: float = 1.5
    lr: float = Field(0.08, ge=0.001, le=1.5)
    steps: int = Field(80, ge=5, le=300)


class BiasVarRequest(BaseModel):
    degree: int = Field(3, ge=0, le=15)
    n_train: int = Field(40, ge=10, le=200)
    noise: float = Field(0.35, ge=0.01, le=2.0)
    seed: int = 42


class ROCRequest(BaseModel):
    threshold: float = Field(0.5, ge=0.0, le=1.0)
    seed: int = 42
    n: int = Field(400, ge=50, le=2000)


@app.get("/health")
def health():
    return {"ok": True, "port": PORT}


@app.get("/concepts")
def concepts():
    return {"concepts": CONCEPTS}


@app.post("/simulate/clt")
def clt(req: CLTRequest):
    return simulate_clt(req.dist, req.sample_size, req.n_samples, req.seed)


@app.get("/loss-surface")
def surface(resolution: int = Query(60, ge=20, le=120)):
    return loss_surface(resolution)


@app.post("/gradient-descent")
def gd(req: GDRequest):
    return {
        "surface_hint": "GET /loss-surface",
        **gd_trajectory(req.w1, req.w2, req.lr, req.steps),
    }


@app.post("/bias-variance")
def bv(req: BiasVarRequest):
    return bias_variance(req.degree, req.n_train, req.noise, req.seed)


@app.post("/roc")
def roc(req: ROCRequest):
    return roc_bundle(req.threshold, req.seed, req.n)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
