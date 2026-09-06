"""Train / load AutoGluon TabularPredictor and expose leaderboard, predict, explain."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from app.config import (
    ARTIFACTS,
    DATA_PATH,
    LABEL,
    META_PATH,
    NUM_BAG_FOLDS,
    NUM_STACK_LEVELS,
    PREDICTOR_DIR,
    PRESETS,
    RANDOM_STATE,
    TEST_FRACTION,
    TIME_LIMIT_SEC,
)

_predictor = None
_meta: dict[str, Any] | None = None


def ensure_data() -> None:
    if DATA_PATH.exists():
        return
    root = DATA_PATH.parents[1]
    sys.path.insert(0, str(root))
    from fetch_data import fetch_adult

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Cap rows for faster first-time fit on student machines
    fetch_adult(n=8000, seed=RANDOM_STATE).to_parquet(DATA_PATH, index=False)


def _infer_schema(df: pd.DataFrame) -> list[dict[str, Any]]:
    schema: list[dict[str, Any]] = []
    for col in df.columns:
        if col == LABEL:
            continue
        s = df[col]
        entry: dict[str, Any] = {"name": col}
        if pd.api.types.is_numeric_dtype(s):
            entry["type"] = "number"
            entry["example"] = float(s.dropna().median()) if s.notna().any() else 0.0
        else:
            entry["type"] = "categorical"
            cats = sorted(s.dropna().astype(str).unique().tolist())
            entry["categories"] = cats[:40]
            entry["example"] = cats[0] if cats else ""
        schema.append(entry)
    return schema


def _stack_level(name: str) -> int:
    m = re.search(r"_L(\d+)$", name)
    if m:
        return int(m.group(1))
    if "Ensemble" in name:
        return 2
    return 1


def build_stack_architecture(model_names: list[str]) -> dict[str, Any]:
    """Derive a simple stack graph from AutoGluon model naming conventions."""
    levels: dict[int, list[str]] = {}
    for name in model_names:
        levels.setdefault(_stack_level(name), []).append(name)

    nodes = [{"id": n, "level": _stack_level(n), "ensemble": "Ensemble" in n} for n in model_names]
    edges: list[dict[str, str]] = []
    sorted_levels = sorted(levels.keys())
    for i, lvl in enumerate(sorted_levels):
        if i == 0:
            continue
        prev = sorted_levels[i - 1]
        # Ensembles / higher stack models consume predictions from previous level
        consumers = [n for n in levels[lvl] if "Ensemble" in n] or levels[lvl]
        for src in levels[prev]:
            for dst in consumers:
                if src != dst:
                    edges.append({"from": src, "to": dst})
    return {"levels": {str(k): v for k, v in sorted(levels.items())}, "nodes": nodes, "edges": edges}


def train_predictor(force: bool = False) -> dict[str, Any]:
    global _predictor, _meta
    from autogluon.tabular import TabularPredictor

    ensure_data()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    if PREDICTOR_DIR.exists() and META_PATH.exists() and not force:
        return load_meta()

    if PREDICTOR_DIR.exists():
        import shutil

        shutil.rmtree(PREDICTOR_DIR, ignore_errors=True)

    df = pd.read_parquet(DATA_PATH)
    train_df, test_df = train_test_split(
        df, test_size=TEST_FRACTION, random_state=RANDOM_STATE, stratify=df[LABEL]
    )

    predictor = TabularPredictor(
        label=LABEL,
        path=str(PREDICTOR_DIR),
        eval_metric="roc_auc",
        problem_type="binary",
    )
    predictor.fit(
        train_data=train_df,
        time_limit=TIME_LIMIT_SEC,
        presets=PRESETS,
        num_bag_folds=NUM_BAG_FOLDS,
        num_stack_levels=NUM_STACK_LEVELS,
        excluded_model_types=["NN_TORCH", "FASTAI"],
        verbosity=2,
    )

    lb = predictor.leaderboard(test_df, silent=True)
    # Persist a JSON-friendly leaderboard + schema + stack graph
    records = []
    for _, row in lb.iterrows():
        records.append(
            {
                "model": str(row["model"]),
                "score_val": _f(row.get("score_val")),
                "score_test": _f(row.get("score_test")),
                "fit_time": _f(row.get("fit_time")),
                "pred_time_val": _f(row.get("pred_time_val")),
                "pred_time_test": _f(row.get("pred_time_test")),
                "stack_level": _stack_level(str(row["model"])),
            }
        )

    schema = _infer_schema(train_df)
    model_names = [r["model"] for r in records]
    # Feature importance on a sample of test (permutation can be slow)
    fi_sample = test_df.sample(n=min(400, len(test_df)), random_state=RANDOM_STATE)
    try:
        fi = predictor.feature_importance(fi_sample, silent=True)
        importance = [
            {
                "feature": str(idx),
                "importance": float(fi.loc[idx, "importance"]),
                "stddev": float(fi.loc[idx, "stddev"]) if "stddev" in fi.columns else None,
            }
            for idx in fi.index
        ]
    except Exception as exc:  # noqa: BLE001
        importance = []
        fi_error = str(exc)
    else:
        fi_error = None

    # Hold-out accuracy / AUC for README-style summary
    y_pred = predictor.predict(test_df.drop(columns=[LABEL]))
    y_proba = predictor.predict_proba(test_df.drop(columns=[LABEL]))
    from sklearn.metrics import accuracy_score, roc_auc_score

    # proba columns ordered by class
    pos = ">50K" if ">50K" in y_proba.columns else y_proba.columns[-1]
    meta = {
        "label": LABEL,
        "positive_class": str(pos),
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "time_limit_sec": TIME_LIMIT_SEC,
        "presets": PRESETS,
        "num_bag_folds": NUM_BAG_FOLDS,
        "num_stack_levels": NUM_STACK_LEVELS,
        "eval_metric": "roc_auc",
        "test_accuracy": float(accuracy_score(test_df[LABEL], y_pred)),
        "test_roc_auc": float(roc_auc_score((test_df[LABEL] == pos).astype(int), y_proba[pos])),
        "schema": schema,
        "leaderboard": records,
        "stack_architecture": build_stack_architecture(model_names),
        "feature_importance": importance,
        "feature_importance_error": fi_error,
        "best_model": predictor.model_best,
        "class_labels": [str(c) for c in predictor.class_labels],
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # Keep a stratified sample for /explain refresh
    fi_sample.to_parquet(ARTIFACTS / "explain_sample.parquet", index=False)

    _predictor = predictor
    _meta = meta
    return meta


def _f(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_meta() -> dict[str, Any]:
    global _meta
    if _meta is not None:
        return _meta
    if not META_PATH.exists():
        return train_predictor()
    _meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    return _meta


def get_predictor():
    global _predictor
    if _predictor is not None:
        return _predictor
    from autogluon.tabular import TabularPredictor

    if not PREDICTOR_DIR.exists():
        train_predictor()
    _predictor = TabularPredictor.load(str(PREDICTOR_DIR))
    return _predictor


def leaderboard_payload() -> dict[str, Any]:
    meta = load_meta()
    return {
        "leaderboard": meta["leaderboard"],
        "best_model": meta["best_model"],
        "eval_metric": meta["eval_metric"],
        "n_train": meta["n_train"],
        "n_test": meta["n_test"],
        "test_roc_auc": meta["test_roc_auc"],
        "test_accuracy": meta["test_accuracy"],
        "presets": meta["presets"],
        "num_bag_folds": meta["num_bag_folds"],
        "num_stack_levels": meta["num_stack_levels"],
        "stack_architecture": meta["stack_architecture"],
        "schema": meta["schema"],
        "class_labels": meta["class_labels"],
        "positive_class": meta["positive_class"],
    }


def predict_record(record: dict[str, Any], include_base: bool = True) -> dict[str, Any]:
    predictor = get_predictor()
    meta = load_meta()
    df = pd.DataFrame([record])
    # Coerce types lightly from schema
    for field in meta["schema"]:
        name = field["name"]
        if name not in df.columns:
            continue
        if field["type"] == "number":
            df[name] = pd.to_numeric(df[name], errors="coerce")
        else:
            df[name] = df[name].astype(str)

    ensemble_pred = predictor.predict(df).iloc[0]
    proba = predictor.predict_proba(df).iloc[0].to_dict()
    proba = {str(k): float(v) for k, v in proba.items()}

    per_model: dict[str, Any] = {}
    if include_base:
        for m in predictor.model_names():
            try:
                p = predictor.predict(df, model=m).iloc[0]
                per_model[m] = str(p)
            except Exception:  # noqa: BLE001
                continue

    return {
        "prediction": str(ensemble_pred),
        "probabilities": proba,
        "best_model": meta["best_model"],
        "per_model_predictions": per_model,
    }


def explain_payload(top_k: int = 20) -> dict[str, Any]:
    meta = load_meta()
    importance = meta.get("feature_importance") or []
    importance = sorted(importance, key=lambda x: abs(x.get("importance") or 0), reverse=True)[:top_k]
    return {
        "method": "permutation_importance",
        "features": importance,
        "error": meta.get("feature_importance_error"),
    }
