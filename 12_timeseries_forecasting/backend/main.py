"""Multi-horizon time series forecasting API."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import PORT  # noqa: E402
from app.pipeline import get_or_build_bundle, train_and_evaluate  # noqa: E402
from app.schemas import (  # noqa: E402
    AcfPacfResponse,
    BacktestResponse,
    ForecastResponse,
    MetricRow,
)

STATE: dict = {"bundle": None}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    STATE["bundle"] = get_or_build_bundle()
    yield


app = FastAPI(
    title="Time Series Forecasting API",
    description="SARIMA + lag-feature GB multi-horizon forecasts with rolling-origin backtest",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _bundle() -> dict:
    if STATE["bundle"] is None:
        raise HTTPException(503, "Not ready")
    return STATE["bundle"]


@app.get("/health")
def health():
    return {"ok": True, "port": PORT, "ready": STATE["bundle"] is not None}


@app.get("/acf-pacf", response_model=AcfPacfResponse)
def acf_pacf():
    b = _bundle()
    return b["acf_pacf"]


@app.get("/forecast", response_model=ForecastResponse)
def forecast():
    b = _bundle()
    return {
        "series": b["series"],
        "forecasts": b["forecasts"],
        "last_train_ds": b["last_train_ds"],
        "alpha": b["alpha"],
    }


@app.get("/backtest", response_model=BacktestResponse)
def backtest():
    b = _bundle()
    bt = b["backtest"]
    return {
        "method": bt["method"],
        "metrics": [MetricRow(**m) for m in bt["metrics"]],
        "note": bt["note"],
    }


@app.get("/meta")
def meta():
    b = _bundle()
    return {
        "series_full_n": b["series_full_n"],
        "last_train_ds": b["last_train_ds"],
        "models": b["models"],
        "backtest": {
            "method": b["backtest"]["method"],
            "min_train": b["backtest"]["min_train"],
            "step": b["backtest"]["step"],
            "horizons": b["backtest"]["horizons"],
        },
    }


@app.post("/retrain")
def retrain():
    bundle = train_and_evaluate()
    STATE["bundle"] = bundle
    return {
        "ok": True,
        "series_full_n": bundle["series_full_n"],
        "metrics": bundle["backtest"]["metrics"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
