"""Data load, time-based split, train backbones, evaluate PR-AUC."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    precision_score,
    recall_score,
)

from app.config import ARTIFACTS, DATA_PATH, FEATURE_COLS, RANDOM_STATE, TEST_FRACTION
from app.models import FittedBackbones, calibrate, fit_backbones, score_matrix


def ensure_data() -> None:
    if DATA_PATH.exists():
        return
    import sys

    root = DATA_PATH.parents[1]
    sys.path.insert(0, str(root))
    from fetch_data import generate

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    generate(4000, 0.05, RANDOM_STATE).to_parquet(DATA_PATH, index=False)


def load_frame() -> pd.DataFrame:
    ensure_data()
    df = pd.read_parquet(DATA_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


def time_split(df: pd.DataFrame, test_fraction: float = TEST_FRACTION):
    cut = int(len(df) * (1 - test_fraction))
    cut = max(1, min(cut, len(df) - 1))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def train_and_evaluate() -> dict:
    df = load_frame()
    train_df, test_df = time_split(df)

    # Fit ONLY on normal training rows (semi-supervised)
    normal_train = train_df[train_df["is_anomaly"] == 0]
    X_fit = normal_train[FEATURE_COLS].to_numpy(dtype=float)
    backbones = fit_backbones(X_fit, FEATURE_COLS, seed=RANDOM_STATE)

    X_test = test_df[FEATURE_COLS].to_numpy(dtype=float)
    y_test = test_df["is_anomaly"].to_numpy()
    # Calibrate normalization on normal training scores only (no label leakage into scale)
    backbones = calibrate(backbones, X_fit)
    # Expand max slightly so extreme anomalies are not all clipped identically
    for k in list(backbones.score_max):
        span = backbones.score_max[k] - backbones.score_min[k]
        backbones.score_max[k] = backbones.score_max[k] + 0.5 * max(span, 1e-6)
    scores = score_matrix(backbones, X_test)

    metrics = {}
    pr_curves = {}
    for name in ("isolation_forest", "lof", "autoencoder", "ensemble"):
        s = scores[name]
        ap = float(average_precision_score(y_test, s))
        precision, recall, thresholds = precision_recall_curve(y_test, s)
        # Choose threshold maximizing F1 on PR curve
        f1 = (2 * precision * recall) / np.maximum(precision + recall, 1e-12)
        # last PR point has no threshold
        best_i = int(np.nanargmax(f1[:-1])) if len(f1) > 1 else 0
        thr = float(thresholds[best_i]) if len(thresholds) else 0.5
        y_hat = (s >= thr).astype(int)
        cm = confusion_matrix(y_test, y_hat, labels=[0, 1]).tolist()
        metrics[name] = {
            "pr_auc": ap,
            "threshold": thr,
            "precision": float(precision_score(y_test, y_hat, zero_division=0)),
            "recall": float(recall_score(y_test, y_hat, zero_division=0)),
            "confusion_matrix": {"labels": [0, 1], "matrix": cm},
        }
        # Downsample curve for UI
        idx = np.linspace(0, len(precision) - 1, num=min(60, len(precision))).astype(int)
        pr_curves[name] = [
            {"recall": float(recall[i]), "precision": float(precision[i])} for i in idx
        ]

    # Top anomalous test records by ensemble score
    test_out = test_df.reset_index(drop=True).copy()
    test_out["score_isolation_forest"] = scores["isolation_forest"]
    test_out["score_lof"] = scores["lof"]
    test_out["score_autoencoder"] = scores["autoencoder"]
    test_out["score_ensemble"] = scores["ensemble"]
    top = test_out.sort_values("score_ensemble", ascending=False).head(50)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(backbones, ARTIFACTS / "backbones.joblib")
    # Save AE state separately for clarity
    torch.save(backbones.autoencoder.state_dict(), ARTIFACTS / "autoencoder.pt")

    payload = {
        "n_train": int(len(train_df)),
        "n_train_normal_fit": int(len(normal_train)),
        "n_test": int(len(test_df)),
        "test_anomaly_rate": float(y_test.mean()),
        "split": "time_ordered",
        "metrics": metrics,
        "pr_curves": pr_curves,
        "feature_cols": FEATURE_COLS,
        "top_anomalies": top[
            ["timestamp", "is_anomaly", "anomaly_kind", *FEATURE_COLS, "score_isolation_forest", "score_lof", "score_autoencoder", "score_ensemble"]
        ].assign(timestamp=lambda d: d["timestamp"].astype(str))
        .to_dict(orient="records"),
    }
    (ARTIFACTS / "eval.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_backbones() -> FittedBackbones:
    path = ARTIFACTS / "backbones.joblib"
    if not path.exists():
        train_and_evaluate()
    return joblib.load(path)


def load_eval() -> dict:
    path = ARTIFACTS / "eval.json"
    if not path.exists():
        return train_and_evaluate()
    return json.loads(path.read_text(encoding="utf-8"))
