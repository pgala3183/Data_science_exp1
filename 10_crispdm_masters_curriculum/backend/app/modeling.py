"""Phase 4 — Modeling: logistic regression + histogram gradient boosting."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from app.config import CV_FOLDS, POSITIVE_LABEL, RANDOM_STATE
from app.preparation import build_preprocessor


def build_models() -> dict[str, Pipeline]:
    """Named model pipelines sharing the same preprocessor pattern."""
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("prep", build_preprocessor()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            steps=[
                ("prep", build_preprocessor()),
                (
                    "clf",
                    HistGradientBoostingClassifier(
                        max_depth=6,
                        learning_rate=0.08,
                        max_iter=200,
                        early_stopping=True,
                        validation_fraction=0.1,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def cross_validate_models(
    models: dict[str, Pipeline],
    X,
    y,
) -> dict[str, Any]:
    """Stratified CV ROC-AUC and F1 for each model."""
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    f1_scorer = make_scorer(f1_score, pos_label=POSITIVE_LABEL)
    # roc_auc needs predict_proba / decision_function — default scorer handles it
    out: dict[str, Any] = {}
    for name, pipe in models.items():
        auc = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
        f1 = cross_val_score(pipe, X, y, cv=cv, scoring=f1_scorer, n_jobs=-1)
        out[name] = {
            "cv_folds": CV_FOLDS,
            "roc_auc_mean": round(float(np.mean(auc)), 4),
            "roc_auc_std": round(float(np.std(auc)), 4),
            "f1_mean": round(float(np.mean(f1)), 4),
            "f1_std": round(float(np.std(f1)), 4),
        }
    return out
