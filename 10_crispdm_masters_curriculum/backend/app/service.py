"""Train, persist, and serve CRISP-DM artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from app.config import (
    ARTIFACTS,
    DATA_PATH,
    DOCS_DIR,
    EDA_PATH,
    EVAL_PATH,
    FEATURE_COLS,
    LABEL,
    LSH_CANDIDATE_MULT,
    LSH_N_BITS,
    LSH_N_TABLES,
    LSH_PATH,
    META_PATH,
    MODELS_PATH,
    POSITIVE_LABEL,
    RANDOM_STATE,
    TEST_FRACTION,
    TRAIN_META_PATH,
)
from app.data_understanding import compute_eda
from app.evaluation import evaluate_classifier, fairness_report
from app.lsh import CosineLSH
from app.modeling import build_models, cross_validate_models
from app.preparation import pipeline_diagram, transform_record

STATE: dict[str, Any] = {
    "models": None,
    "eval": None,
    "eda": None,
    "meta": None,
    "lsh": None,
    "train_df": None,
    "train_X": None,
}


def _ensure_data() -> Path:
    if DATA_PATH.exists():
        return DATA_PATH
    # Lazy fetch if missing
    import subprocess
    import sys

    fetch = DATA_PATH.parents[1] / "fetch_data.py"
    subprocess.check_call([sys.executable, str(fetch)], cwd=str(fetch.parent.parent))
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Expected dataset at {DATA_PATH}")
    return DATA_PATH


def load_raw() -> pd.DataFrame:
    _ensure_data()
    df = pd.read_parquet(DATA_PATH)
    if "class" in df.columns and LABEL not in df.columns:
        df = df.rename(columns={"class": LABEL})
    df[LABEL] = df[LABEL].astype(str).str.strip()
    # Normalize Adult '?' missings to np.nan (sklearn-friendly; avoid pd.NA)
    for col in df.columns:
        if col == LABEL:
            continue
        if df[col].dtype == object or str(df[col].dtype) in ("category", "string"):
            s = df[col].astype(str).str.strip()
            s = s.replace({"?": np.nan, "nan": np.nan, "None": np.nan, "<NA>": np.nan})
            df[col] = s
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=[LABEL]).reset_index(drop=True)


def business_payload() -> dict[str, Any]:
    path = DOCS_DIR / "business_understanding.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {
        "phase": "business_understanding",
        "title": "Predict income bracket from census attributes",
        "objective": (
            "Estimate whether an adult earns >$50K/year to support screening "
            "and fairness analysis — not automated decisions."
        ),
        "success_criteria": [
            {"metric": "ROC-AUC", "target": ">= 0.85"},
            {"metric": "F1 (>50K)", "target": ">= 0.60"},
            {"metric": "Baseline", "target": "Boosting beats logistic regression AUC"},
            {
                "metric": "Fairness",
                "target": "Report TPR/FPR/selection gaps by sex and race honestly",
            },
        ],
        "markdown": text,
    }


def evaluation_doc_payload() -> dict[str, Any]:
    path = DOCS_DIR / "evaluation.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return {"phase": "evaluation", "markdown": text}


def train_and_persist(force: bool = False) -> dict[str, Any]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    if (
        not force
        and META_PATH.exists()
        and EVAL_PATH.exists()
        and MODELS_PATH.exists()
        and LSH_PATH.exists()
    ):
        return json.loads(META_PATH.read_text(encoding="utf-8"))

    df = load_raw()
    eda = compute_eda(df)
    EDA_PATH.write_text(json.dumps(eda, indent=2), encoding="utf-8")

    X = df[FEATURE_COLS].copy()
    y = df[LABEL].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_FRACTION,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    train_df = X_train.copy()
    train_df[LABEL] = y_train.values
    test_df = X_test.copy()

    models = build_models()
    cv_scores = cross_validate_models(models, X_train, y_train)

    fitted: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    fairness: dict[str, Any] = {}
    for name, pipe in models.items():
        pipe.fit(X_train, y_train)
        fitted[name] = pipe
        proba = pipe.predict_proba(X_test)
        # positive class column
        classes = list(pipe.named_steps["clf"].classes_)
        pos_idx = classes.index(POSITIVE_LABEL)
        y_prob = proba[:, pos_idx]
        y_pred = pipe.predict(X_test)
        metrics[name] = evaluate_classifier(y_test.to_numpy(), y_prob, y_pred)
        fairness[name] = fairness_report(test_df, y_test.to_numpy(), y_pred, y_prob)

    # Prefer stronger model for LSH feature space (its preprocessor)
    primary = "hist_gradient_boosting"
    prep = fitted[primary].named_steps["prep"]
    X_train_t = np.asarray(prep.transform(X_train), dtype=np.float64)
    lsh = CosineLSH(n_bits=LSH_N_BITS, n_tables=LSH_N_TABLES, seed=RANDOM_STATE)
    lsh.fit(X_train_t)

    joblib.dump(fitted, MODELS_PATH)
    joblib.dump(lsh, LSH_PATH)
    joblib.dump(
        {"train_df": train_df.reset_index(drop=True), "feature_cols": FEATURE_COLS},
        TRAIN_META_PATH,
    )

    eval_payload = {
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "test_fraction": TEST_FRACTION,
        "positive_label": POSITIVE_LABEL,
        "cv": cv_scores,
        "metrics": metrics,
        "fairness": fairness,
        "primary_model": primary,
        "pipeline": pipeline_diagram(),
        "evaluation_doc": evaluation_doc_payload()["markdown"],
    }
    EVAL_PATH.write_text(json.dumps(eval_payload, indent=2), encoding="utf-8")

    meta = {
        "n_rows": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "label": LABEL,
        "feature_cols": FEATURE_COLS,
        "models": list(fitted.keys()),
        "primary_model": primary,
        "cv": cv_scores,
        "holdout_roc_auc": {k: v["roc_auc"] for k, v in metrics.items()},
        "holdout_f1": {k: v["f1"] for k, v in metrics.items()},
        "schema": _schema_example(df),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def _schema_example(df: pd.DataFrame) -> dict[str, Any]:
    sample = df.iloc[0]
    out = {}
    for c in FEATURE_COLS:
        v = sample[c]
        if pd.isna(v):
            out[c] = None
        elif hasattr(v, "item"):
            out[c] = v.item()
        else:
            out[c] = v if not isinstance(v, (np.floating, float)) else float(v)
            if isinstance(out[c], (np.integer,)):
                out[c] = int(out[c])
            elif isinstance(out[c], float):
                out[c] = float(out[c])
            else:
                out[c] = str(out[c])
    return out


def load_state(force_train: bool = False) -> None:
    meta = train_and_persist(force=force_train)
    STATE["meta"] = meta
    STATE["eda"] = json.loads(EDA_PATH.read_text(encoding="utf-8"))
    STATE["eval"] = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    STATE["models"] = joblib.load(MODELS_PATH)
    STATE["lsh"] = joblib.load(LSH_PATH)
    train_bundle = joblib.load(TRAIN_META_PATH)
    STATE["train_df"] = train_bundle["train_df"]


def predict_record(record: dict[str, Any], model_name: str | None = None) -> dict[str, Any]:
    if STATE["models"] is None:
        raise RuntimeError("Models not loaded")
    name = model_name or STATE["meta"]["primary_model"]
    if name not in STATE["models"]:
        raise ValueError(f"Unknown model: {name}")
    pipe = STATE["models"][name]
    X = pd.DataFrame([{c: record.get(c) for c in FEATURE_COLS}])
    proba = pipe.predict_proba(X)[0]
    classes = [str(c) for c in pipe.named_steps["clf"].classes_]
    pred = str(pipe.predict(X)[0])
    probs = {classes[i]: round(float(proba[i]), 4) for i in range(len(classes))}
    return {
        "prediction": pred,
        "probability_gt_50k": probs.get(POSITIVE_LABEL, 0.0),
        "model": name,
        "probabilities": probs,
    }


def similar_records(record: dict[str, Any], k: int = 5) -> dict[str, Any]:
    if STATE["lsh"] is None or STATE["models"] is None or STATE["train_df"] is None:
        raise RuntimeError("Similarity index not loaded")
    primary = STATE["meta"]["primary_model"]
    pipe = STATE["models"][primary]
    prep = pipe.named_steps["prep"]
    q = transform_record(prep, record)
    idx, sims, n_cand = STATE["lsh"].query(q, k=k, candidate_mult=LSH_CANDIDATE_MULT)
    train_df: pd.DataFrame = STATE["train_df"]
    neighbors = []
    for rank, (i, sim) in enumerate(zip(idx.tolist(), sims.tolist()), start=1):
        row = train_df.iloc[int(i)]
        rec = {c: _jsonable(row[c]) for c in FEATURE_COLS}
        neighbors.append(
            {
                "rank": rank,
                "cosine_similarity": round(float(sim), 4),
                "income": str(row[LABEL]),
                "record": rec,
            }
        )
    pred = predict_record(record, primary)
    return {
        "query_prediction": pred["prediction"],
        "query_probability_gt_50k": pred["probability_gt_50k"],
        "neighbors": neighbors,
        "lsh_candidates_scanned": int(n_cand),
        "method": "cosine_lsh",
    }


def _jsonable(v: Any) -> Any:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if pd.isna(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return float(v)
    return str(v)
