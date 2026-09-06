"""AutoGluon Multimodal AutoML API — fusion vs single-modality baselines."""

from __future__ import annotations

import shutil
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import PORT, UPLOADS  # noqa: E402
from app.schemas import MetricsResponse, PredictResponse  # noqa: E402
from app.service import load_meta, metrics_payload, predict_multimodal, train_all  # noqa: E402

STATE = {"ready": False, "error": None}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        UPLOADS.mkdir(parents=True, exist_ok=True)
        load_meta()
        STATE["ready"] = True
        STATE["error"] = None
    except Exception as exc:  # noqa: BLE001
        STATE["ready"] = False
        STATE["error"] = str(exc)
        raise
    yield


app = FastAPI(
    title="AutoGluon Multimodal AutoML Suite",
    description="MultiModalPredictor (image+text+tabular) vs single-modality baselines",
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
    return {"ok": True, "port": PORT, "ready": STATE["ready"], "error": STATE["error"]}


@app.get("/metrics", response_model=MetricsResponse)
def metrics():
    if not STATE["ready"]:
        raise HTTPException(503, STATE["error"] or "Models not ready")
    return MetricsResponse(**{k: v for k, v in metrics_payload().items() if k in MetricsResponse.model_fields})


@app.get("/demo")
def demo():
    """Held-out demo rows + relative image URLs for the UI."""
    if not STATE["ready"]:
        raise HTTPException(503, "Models not ready")
    meta = metrics_payload()
    samples = []
    for i, s in enumerate(meta.get("demo_samples", [])):
        samples.append(
            {
                **{k: v for k, v in s.items() if k != "image"},
                "image_url": f"/demo/image/{i}",
                "true_category": s.get("category"),
            }
        )
    return {"samples": samples, "accuracies": meta["accuracies"], "lift_vs_best_baseline": meta["lift_vs_best_baseline"]}


@app.get("/demo/image/{idx}")
def demo_image(idx: int):
    meta = load_meta()
    samples = meta.get("demo_samples") or []
    if idx < 0 or idx >= len(samples):
        raise HTTPException(404, "Sample not found")
    path = Path(samples[idx]["image"])
    if not path.exists():
        raise HTTPException(404, "Image file missing")
    return FileResponse(path, media_type="image/jpeg")


@app.post("/predict", response_model=PredictResponse)
async def predict(
    image: UploadFile = File(...),
    description: str = Form(...),
    price: float = Form(...),
    rating: float = Form(4.0),
    brand_tier: str = Form("mid"),
    weight_oz: float = Form(8.0),
    is_fragile: int = Form(0),
):
    if not STATE["ready"]:
        raise HTTPException(503, STATE["error"] or "Models not ready")
    if brand_tier not in ("budget", "mid", "premium"):
        raise HTTPException(400, "brand_tier must be budget|mid|premium")

    UPLOADS.mkdir(parents=True, exist_ok=True)
    suffix = Path(image.filename or "upload.jpg").suffix or ".jpg"
    dest = UPLOADS / f"{uuid.uuid4().hex}{suffix}"
    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(image.file, f)
        out = predict_multimodal(
            image_path=dest,
            description=description,
            price=price,
            rating=rating,
            brand_tier=brand_tier,
            weight_oz=weight_oz,
            is_fragile=is_fragile,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Prediction failed: {exc}") from exc
    finally:
        if dest.exists():
            dest.unlink(missing_ok=True)

    return PredictResponse(**out)


@app.post("/retrain")
def retrain():
    meta = train_all(force=True)
    STATE["ready"] = True
    STATE["error"] = None
    return {
        "ok": True,
        "accuracies": meta["accuracies"],
        "lift_vs_best_baseline": meta["lift_vs_best_baseline"],
        "best_baseline": meta["best_baseline"],
        "notes": meta.get("notes"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
