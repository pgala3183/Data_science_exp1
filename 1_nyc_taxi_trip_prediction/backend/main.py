"""NYC Taxi Trip Duration prediction API."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Allow `uvicorn main:app` from backend/
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import ARTIFACTS_DIR, DATA_PATH, PORT  # noqa: E402
from app.pipeline import build_feature_row  # noqa: E402
from app.schemas import (  # noqa: E402
    FeatureContribution,
    ModelMetricsResponse,
    PredictRequest,
    PredictResponse,
)
from app.train import load_bundle, load_metrics, train_models  # noqa: E402

STATE: dict = {"bundle": None, "metrics": None}


def ensure_artifacts() -> None:
    bundle_path = ARTIFACTS_DIR / "model_bundle.joblib"
    if not bundle_path.exists():
        if not DATA_PATH.exists():
            # Generate data from backend context
            root = BACKEND_DIR.parent
            sys.path.insert(0, str(root / "data"))
            from fetch_data import generate_synthetic  # type: ignore

            processed = root / "data" / "processed"
            processed.mkdir(parents=True, exist_ok=True)
            df = generate_synthetic(n=20_000, seed=42)
            df.to_parquet(processed / "trips.parquet", index=False)
        train_models()
    STATE["bundle"] = load_bundle()
    STATE["metrics"] = load_metrics()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_artifacts()
    yield


app = FastAPI(
    title="NYC Taxi Trip Duration API",
    description="CRISP-DM regression demo with time-based split and leakage-safe features.",
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
    return {"ok": True, "port": PORT}


@app.get("/model/metrics", response_model=ModelMetricsResponse)
def model_metrics():
    if STATE["metrics"] is None:
        raise HTTPException(503, "Model not ready")
    return STATE["metrics"]


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    bundle = STATE["bundle"]
    metrics = STATE["metrics"]
    if bundle is None or metrics is None:
        raise HTTPException(503, "Model not ready")

    features = build_feature_row(
        pickup_latitude=req.pickup_latitude,
        pickup_longitude=req.pickup_longitude,
        dropoff_latitude=req.dropoff_latitude,
        dropoff_longitude=req.dropoff_longitude,
        pickup_datetime=req.pickup_datetime.isoformat(),
        passenger_count=req.passenger_count,
        pickup_kmeans=bundle["pickup_kmeans"],
        dropoff_kmeans=bundle["dropoff_kmeans"],
    )

    pred = float(bundle["model"].predict(features)[0])
    pred = max(60.0, pred)
    std = float(bundle["residual_std"])
    lo = max(60.0, pred - 1.96 * std)
    hi = pred + 1.96 * std

    best = next(m for m in metrics["models"] if m["name"] == bundle["model_name"])
    top = sorted(
        best["feature_importances"].items(),
        key=lambda kv: kv[1],
        reverse=True,
    )[:5]

    return PredictResponse(
        predicted_duration_seconds=round(pred, 1),
        predicted_duration_minutes=round(pred / 60.0, 2),
        confidence_interval_95_seconds=(round(lo, 1), round(hi, 1)),
        model_name=bundle["model_name"],
        top_features=[FeatureContribution(feature=k, importance=round(v, 4)) for k, v in top],
        haversine_km=round(float(features["haversine_km"].iloc[0]), 3),
    )


@app.post("/model/retrain")
def retrain():
    """Re-run training pipeline (useful after swapping in Kaggle CSV)."""
    result = train_models()
    STATE["bundle"] = load_bundle()
    STATE["metrics"] = load_metrics()
    return {
        "best_model_name": result.best_model_name,
        "n_train": result.n_train,
        "n_test": result.n_test,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
