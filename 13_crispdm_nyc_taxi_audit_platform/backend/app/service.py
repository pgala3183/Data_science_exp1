"""Train, persist, and serve CRISP-DM + audit + monitoring artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib

from app.audit import run_audit
from app.audit.config import PROJECT_ROOT
from app.config import (
    ARTIFACTS_DIR,
    BUNDLE_PATH,
    DATA_PATH,
    DOCS_DIR,
    EDA_PATH,
    EVAL_PATH,
    META_PATH,
    METRICS_PATH,
    TRAIN_REF_PATH,
)
from app.data_understanding import compute_eda
from app.monitoring import compute_drift_report, simulate_drifted_batch
from app.pipeline import build_feature_row, load_raw, pipeline_diagram
from app.train import load_bundle, load_metrics, train_models

STATE: dict[str, Any] = {
    "bundle": None,
    "metrics": None,
    "eda": None,
    "eval": None,
    "meta": None,
    "train_ref": None,
}


def _ensure_data() -> Path:
    if DATA_PATH.exists():
        return DATA_PATH
    from app.config import ROOT

    data_dir = ROOT / "data"
    sys.path.insert(0, str(data_dir))
    from fetch_data import generate_synthetic  # type: ignore

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic(n=20_000, seed=42)
    df.to_parquet(DATA_PATH, index=False)
    return DATA_PATH


def business_payload() -> dict[str, Any]:
    path = DOCS_DIR / "business_understanding.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "phase": "business_understanding",
        "title": "Predict NYC yellow-taxi trip duration for ETA & ops",
        "objective": (
            "Estimate trip_duration (seconds) from pre-trip information only, "
            "with leakage-safe CRISP-DM process, self-certifying DS audit, "
            "and live drift monitoring for production readiness."
        ),
        "success_criteria": [
            {"metric": "Holdout RMSE", "target": "Beat Ridge baseline with HGB"},
            {"metric": "Leakage", "target": "Time-based split; no post-trip features"},
            {"metric": "Audit grade", "target": "Self-audit ≥ B on leakage dimension"},
            {"metric": "Monitoring", "target": "PSI/KS flags drifted features red/yellow/green"},
            {
                "metric": "Group fairness",
                "target": "Report residual MAE disparities by pickup cluster (bias audit)",
            },
        ],
        "markdown": text,
    }


def evaluation_doc_payload() -> dict[str, Any]:
    path = DOCS_DIR / "evaluation.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {"phase": "evaluation", "markdown": text}


def train_and_persist(force: bool = False) -> dict[str, Any]:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_data()

    if (
        not force
        and BUNDLE_PATH.exists()
        and METRICS_PATH.exists()
        and EVAL_PATH.exists()
        and EDA_PATH.exists()
        and META_PATH.exists()
        and TRAIN_REF_PATH.exists()
    ):
        return json.loads(META_PATH.read_text(encoding="utf-8"))

    raw = load_raw()
    eda = compute_eda(raw)
    EDA_PATH.write_text(json.dumps(eda, indent=2), encoding="utf-8")

    result = train_models()
    # Attach evaluation markdown
    eval_payload = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    eval_payload["evaluation_doc"] = evaluation_doc_payload()["markdown"]
    EVAL_PATH.write_text(json.dumps(eval_payload, indent=2), encoding="utf-8")
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def load_state(force_train: bool = False) -> None:
    train_and_persist(force=force_train)
    STATE["bundle"] = load_bundle()
    STATE["metrics"] = load_metrics()
    STATE["eda"] = json.loads(EDA_PATH.read_text(encoding="utf-8"))
    STATE["eval"] = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    if not STATE["eval"].get("evaluation_doc"):
        STATE["eval"]["evaluation_doc"] = evaluation_doc_payload()["markdown"]
    STATE["meta"] = json.loads(META_PATH.read_text(encoding="utf-8"))
    STATE["train_ref"] = joblib.load(TRAIN_REF_PATH)


def predict_trip(req) -> dict[str, Any]:
    bundle = STATE["bundle"]
    metrics = STATE["metrics"]
    if bundle is None or metrics is None:
        raise RuntimeError("Model not ready")

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
    top = sorted(best["feature_importances"].items(), key=lambda kv: kv[1], reverse=True)[:5]

    return {
        "predicted_duration_seconds": round(pred, 1),
        "predicted_duration_minutes": round(pred / 60.0, 2),
        "confidence_interval_95_seconds": (round(lo, 1), round(hi, 1)),
        "model_name": bundle["model_name"],
        "top_features": [{"feature": k, "importance": round(v, 4)} for k, v in top],
        "haversine_km": round(float(features["haversine_km"].iloc[0]), 3),
    }


def self_audit() -> dict[str, Any]:
    """Run the experiment-11 auditor against this project's own codebase.

    Excludes embedded audit *rule* modules — they intentionally contain leakage
    keyword patterns and would otherwise false-positive the self-scan.
    """
    result = run_audit(
        PROJECT_ROOT,
        exclude_globs=("backend/app/audit/checks/",),
    )
    return result.model_dump()


def monitoring_report(drift_mode: str = "moderate", n: int = 3000) -> dict[str, Any]:
    ref = STATE["train_ref"]
    if ref is None:
        raise RuntimeError("Training reference not loaded")
    X_new = simulate_drifted_batch(
        ref["X_train"],
        ref["pickup_kmeans"],
        ref["dropoff_kmeans"],
        n=n,
        drift_mode=drift_mode,
    )
    return compute_drift_report(ref["X_train"], X_new, drift_mode=drift_mode)


def schema_payload() -> dict[str, Any]:
    meta = STATE["meta"]
    return {
        "label": meta["label"],
        "feature_cols": meta["feature_cols"],
        "example": meta["schema"],
        "models": meta["models"],
        "primary_model": meta["primary_model"],
    }
