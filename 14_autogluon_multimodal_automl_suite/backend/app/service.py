"""Train / load multimodal + single-modality baselines; serve predictions."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from app.config import (
    ARTIFACTS,
    DATA_PATH,
    IMAGE_COL,
    IMAGE_DIR,
    IMAGE_TIME_LIMIT_SEC,
    IMAGES_DIR,
    LABEL,
    META_PATH,
    MM_DIR,
    MM_TIME_LIMIT_SEC,
    N_SAMPLES,
    PROJECT_ROOT,
    RANDOM_STATE,
    TABULAR_COLS,
    TABULAR_DIR,
    TABULAR_PRESETS,
    TABULAR_TIME_LIMIT_SEC,
    TEXT_COL,
    TEXT_DIR,
    TEXT_TIME_LIMIT_SEC,
    TEST_FRACTION,
    UPLOADS,
)

_predictors: dict[str, Any] = {}
_meta: dict[str, Any] | None = None


def ensure_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        sys.path.insert(0, str(PROJECT_ROOT / "data"))
        from generate_products import generate

        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df = generate(n=N_SAMPLES, seed=RANDOM_STATE)
        df.to_csv(DATA_PATH, index=False)
    else:
        df = pd.read_csv(DATA_PATH)

    # MultiModalPredictor needs absolute image paths that still exist
    df = df.copy()
    df[IMAGE_COL] = df[IMAGE_COL].astype(str).map(_resolve_image_path)
    return df


def _resolve_image_path(p: str) -> str:
    path = Path(p)
    if path.exists():
        return str(path.resolve())
    # Relocate if parquet was copied across machines
    alt = IMAGES_DIR / path.name
    if alt.exists():
        return str(alt.resolve())
    return str(path)


def _mm_hyperparameters() -> dict[str, Any]:
    """Small CPU-friendly backbone so a laptop demo can finish."""
    return {
        "model.names": ["timm_image", "hf_text", "numerical_mlp", "categorical_mlp", "fusion_mlp"],
        "model.timm_image.checkpoint_name": "mobilenetv3_small_100",
        "model.hf_text.checkpoint_name": "google/electra-small-discriminator",
        "optim.max_epochs": 3,
        "optim.lr": 2e-4,
        "optim.val_check_interval": 1.0,
        "env.num_workers": 0,
        "env.batch_size": 8,
    }


def _image_hyperparameters() -> dict[str, Any]:
    return {
        "model.names": ["timm_image"],
        "model.timm_image.checkpoint_name": "mobilenetv3_small_100",
        "optim.max_epochs": 3,
        "optim.lr": 2e-4,
        "env.num_workers": 0,
        "env.batch_size": 8,
    }


def _accuracy(predictor: Any, df: pd.DataFrame) -> float:
    y_true = df[LABEL]
    y_pred = predictor.predict(df.drop(columns=[LABEL], errors="ignore"))
    return float(accuracy_score(y_true, y_pred))


def _predict_one(predictor: Any, row: pd.DataFrame) -> dict[str, Any]:
    pred = predictor.predict(row).iloc[0]
    try:
        proba = predictor.predict_proba(row).iloc[0]
        if hasattr(proba, "to_dict"):
            probs = {str(k): float(v) for k, v in proba.to_dict().items()}
        else:
            labels = list(getattr(predictor, "class_labels", []) or [])
            probs = {str(labels[i]): float(proba[i]) for i in range(len(proba))}
    except Exception:  # noqa: BLE001
        probs = {str(pred): 1.0}
    return {"prediction": str(pred), "probabilities": probs}


def train_all(force: bool = False) -> dict[str, Any]:
    global _predictors, _meta
    from autogluon.multimodal import MultiModalPredictor
    from autogluon.tabular import TabularPredictor

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)

    if META_PATH.exists() and all(p.exists() for p in (MM_DIR, TABULAR_DIR, TEXT_DIR, IMAGE_DIR)) and not force:
        return load_meta()

    for d in (MM_DIR, TABULAR_DIR, TEXT_DIR, IMAGE_DIR):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    df = ensure_data()
    train_df, test_df = train_test_split(
        df, test_size=TEST_FRACTION, random_state=RANDOM_STATE, stratify=df[LABEL]
    )
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # --- Multimodal fusion (image + text + tabular) ---
    mm = MultiModalPredictor(label=LABEL, path=str(MM_DIR), problem_type="multiclass")
    mm.fit(
        train_df,
        time_limit=MM_TIME_LIMIT_SEC,
        hyperparameters=_mm_hyperparameters(),
        seed=RANDOM_STATE,
    )

    # --- Image-only (MultiModalPredictor, image column only) ---
    img_train = train_df[[IMAGE_COL, LABEL]].copy()
    img_test = test_df[[IMAGE_COL, LABEL]].copy()
    image_pred = MultiModalPredictor(label=LABEL, path=str(IMAGE_DIR), problem_type="multiclass")
    image_pred.fit(
        img_train,
        time_limit=IMAGE_TIME_LIMIT_SEC,
        hyperparameters=_image_hyperparameters(),
        seed=RANDOM_STATE,
    )

    # --- Tabular-only (plain AutoGluon Tabular) ---
    tab_cols = TABULAR_COLS + [LABEL]
    tab_train = train_df[tab_cols].copy()
    tab_test = test_df[tab_cols].copy()
    tabular = TabularPredictor(label=LABEL, path=str(TABULAR_DIR), problem_type="multiclass", eval_metric="accuracy")
    tabular.fit(
        tab_train,
        time_limit=TABULAR_TIME_LIMIT_SEC,
        presets=TABULAR_PRESETS,
        excluded_model_types=["NN_TORCH", "FASTAI"],
        verbosity=1,
    )

    # --- Text-only (TabularPredictor on description — AG text n-grams / models) ---
    text_train = train_df[[TEXT_COL, LABEL]].copy()
    text_test = test_df[[TEXT_COL, LABEL]].copy()
    text_pred = TabularPredictor(label=LABEL, path=str(TEXT_DIR), problem_type="multiclass", eval_metric="accuracy")
    text_pred.fit(
        text_train,
        time_limit=TEXT_TIME_LIMIT_SEC,
        presets=TABULAR_PRESETS,
        excluded_model_types=["NN_TORCH", "FASTAI"],
        verbosity=1,
    )

    accuracies = {
        "multimodal": _accuracy(mm, test_df),
        "image_only": _accuracy(image_pred, img_test),
        "text_only": _accuracy(text_pred, text_test),
        "tabular_only": _accuracy(tabular, tab_test),
    }
    baseline_keys = ["image_only", "text_only", "tabular_only"]
    best_baseline = max(baseline_keys, key=lambda k: accuracies[k])
    lift = accuracies["multimodal"] - accuracies[best_baseline]

    # Keep a few demo samples for the UI (absolute image paths)
    demo = test_df.head(5)[[IMAGE_COL, TEXT_COL, *TABULAR_COLS, LABEL]].copy()
    demo_records = []
    for _, row in demo.iterrows():
        demo_records.append(
            {
                "image": str(row[IMAGE_COL]),
                "description": str(row[TEXT_COL]),
                "price": float(row["price"]),
                "rating": float(row["rating"]),
                "brand_tier": str(row["brand_tier"]),
                "weight_oz": float(row["weight_oz"]),
                "is_fragile": int(row["is_fragile"]),
                "category": str(row[LABEL]),
            }
        )

    meta = {
        "label": LABEL,
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "class_labels": [str(c) for c in sorted(df[LABEL].unique())],
        "accuracies": accuracies,
        "best_baseline": best_baseline,
        "best_baseline_accuracy": float(accuracies[best_baseline]),
        "multimodal_accuracy": float(accuracies["multimodal"]),
        "lift_vs_best_baseline": float(lift),
        "modalities": {
            "image": IMAGE_COL,
            "text": TEXT_COL,
            "tabular": TABULAR_COLS,
        },
        "time_limits": {
            "multimodal": MM_TIME_LIMIT_SEC,
            "image_only": IMAGE_TIME_LIMIT_SEC,
            "text_only": TEXT_TIME_LIMIT_SEC,
            "tabular_only": TABULAR_TIME_LIMIT_SEC,
        },
        "demo_samples": demo_records,
        "notes": _lift_note(lift, accuracies, best_baseline),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # Persist test split for optional re-eval
    test_df.to_csv(ARTIFACTS / "test_split.csv", index=False)

    _predictors = {
        "multimodal": mm,
        "image_only": image_pred,
        "text_only": text_pred,
        "tabular_only": tabular,
    }
    _meta = meta
    return meta


def _lift_note(lift: float, accuracies: dict[str, float], best_baseline: str) -> str:
    if lift > 0.01:
        return (
            f"Multimodal fusion beat the best single-modality baseline ({best_baseline}) "
            f"by {lift:.1%} absolute accuracy on the held-out set."
        )
    if lift >= -0.01:
        return (
            "Multimodal fusion tied the best single-modality baseline within 1pp — "
            "with only a few hundred samples, fusion often has little room to shine."
        )
    return (
        f"Multimodal fusion underperformed the best baseline ({best_baseline}) by "
        f"{abs(lift):.1%}. Small-n + short training budgets are the usual culprits: "
        f"image/text encoders underfit while tabular trees already capture most of the signal."
    )


def load_meta() -> dict[str, Any]:
    global _meta
    if _meta is not None:
        return _meta
    if not META_PATH.exists():
        return train_all()
    _meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    return _meta


def get_predictors() -> dict[str, Any]:
    global _predictors
    if _predictors:
        return _predictors
    from autogluon.multimodal import MultiModalPredictor
    from autogluon.tabular import TabularPredictor

    if not META_PATH.exists() or not MM_DIR.exists():
        train_all()
    _predictors = {
        "multimodal": MultiModalPredictor.load(str(MM_DIR)),
        "image_only": MultiModalPredictor.load(str(IMAGE_DIR)),
        "text_only": TabularPredictor.load(str(TEXT_DIR)),
        "tabular_only": TabularPredictor.load(str(TABULAR_DIR)),
    }
    return _predictors


def metrics_payload() -> dict[str, Any]:
    meta = load_meta()
    return {
        "label": meta["label"],
        "n_train": meta["n_train"],
        "n_test": meta["n_test"],
        "class_labels": meta["class_labels"],
        "accuracies": meta["accuracies"],
        "best_baseline": meta["best_baseline"],
        "best_baseline_accuracy": meta["best_baseline_accuracy"],
        "multimodal_accuracy": meta["multimodal_accuracy"],
        "lift_vs_best_baseline": meta["lift_vs_best_baseline"],
        "modalities": meta["modalities"],
        "notes": meta.get("notes", ""),
        "demo_samples": meta.get("demo_samples", []),
        "time_limits": meta.get("time_limits", {}),
    }


def predict_multimodal(
    image_path: Path,
    description: str,
    price: float,
    rating: float,
    brand_tier: str,
    weight_oz: float,
    is_fragile: int,
) -> dict[str, Any]:
    preds = get_predictors()
    meta = load_meta()

    abs_img = str(Path(image_path).resolve())
    full = pd.DataFrame(
        [
            {
                IMAGE_COL: abs_img,
                TEXT_COL: description,
                "price": float(price),
                "rating": float(rating),
                "brand_tier": str(brand_tier),
                "weight_oz": float(weight_oz),
                "is_fragile": int(is_fragile),
            }
        ]
    )
    img_row = full[[IMAGE_COL]].copy()
    text_row = full[[TEXT_COL]].copy()
    tab_row = full[TABULAR_COLS].copy()

    multimodal = _predict_one(preds["multimodal"], full)
    baselines = {
        "image_only": _predict_one(preds["image_only"], img_row),
        "text_only": _predict_one(preds["text_only"], text_row),
        "tabular_only": _predict_one(preds["tabular_only"], tab_row),
    }
    return {
        "multimodal": multimodal,
        "baselines": baselines,
        "holdout_accuracies": meta["accuracies"],
        "lift_vs_best_baseline": meta["lift_vs_best_baseline"],
        "best_baseline": meta["best_baseline"],
    }
