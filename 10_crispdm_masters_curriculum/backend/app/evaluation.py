"""Phase 5 — Evaluation metrics and fairness breakdowns."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)

from app.config import POSITIVE_LABEL, SENSITIVE_ATTRS


def evaluate_classifier(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, Any]:
    """Hold-out metrics for a binary classifier (positive = >50K)."""
    y_bin = (np.asarray(y_true).astype(str) == POSITIVE_LABEL).astype(int)
    pred_bin = (np.asarray(y_pred).astype(str) == POSITIVE_LABEL).astype(int)
    cm = confusion_matrix(y_bin, pred_bin, labels=[0, 1])
    fpr, tpr, _ = roc_curve(y_bin, y_prob)
    idxs = np.linspace(0, len(fpr) - 1, num=min(80, len(fpr))).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y_bin, pred_bin)), 4),
        "f1": round(float(f1_score(y_bin, pred_bin, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_bin, y_prob)), 4),
        "confusion_matrix": {
            "labels": ["<=50K", ">50K"],
            "matrix": cm.astype(int).tolist(),
        },
        "roc_curve": {
            "fpr": [round(float(fpr[i]), 4) for i in idxs],
            "tpr": [round(float(tpr[i]), 4) for i in idxs],
        },
    }


def fairness_report(
    df_test: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    attributes: tuple[str, ...] = SENSITIVE_ATTRS,
) -> dict[str, Any]:
    """
    Honest group metrics by sensitive attribute.

    Reports base rate, selection rate, TPR, FPR, accuracy, F1 per group.
    Disparities are documented, not hidden.
    """
    df = df_test.reset_index(drop=True)
    y_bin = (np.asarray(y_true).astype(str) == POSITIVE_LABEL).astype(int)
    pred_bin = (np.asarray(y_pred).astype(str) == POSITIVE_LABEL).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)

    by_attribute: dict[str, list[dict[str, Any]]] = {}
    for attr in attributes:
        if attr not in df.columns:
            continue
        groups: list[dict[str, Any]] = []
        grouped = df.groupby(df[attr].astype(str).fillna("Unknown"), dropna=False)
        for group_name, g in grouped:
            i = g.index.to_numpy()
            yt = y_bin[i]
            yp = pred_bin[i]
            n = int(len(i))
            tp = int(((yt == 1) & (yp == 1)).sum())
            fn = int(((yt == 1) & (yp == 0)).sum())
            fp = int(((yt == 0) & (yp == 1)).sum())
            tn = int(((yt == 0) & (yp == 0)).sum())
            groups.append(
                {
                    "group": str(group_name),
                    "support": n,
                    "base_rate": round(float(yt.mean()), 4),
                    "selection_rate": round(float(yp.mean()), 4),
                    "tpr": round(float(tp / max(tp + fn, 1)), 4),
                    "fpr": round(float(fp / max(fp + tn, 1)), 4),
                    "accuracy": round(float((yt == yp).mean()), 4),
                    "f1": round(float(f1_score(yt, yp, zero_division=0)), 4),
                    "mean_prob_gt_50k": round(float(np.mean(y_prob[i])), 4),
                }
            )
        groups.sort(key=lambda g: -g["support"])
        by_attribute[attr] = groups

    disparities: dict[str, Any] = {}
    for attr, groups in by_attribute.items():
        if len(groups) < 2:
            continue
        disparities[attr] = {
            "majority_group": groups[0]["group"],
            "tpr_range": round(
                max(g["tpr"] for g in groups) - min(g["tpr"] for g in groups), 4
            ),
            "selection_rate_range": round(
                max(g["selection_rate"] for g in groups)
                - min(g["selection_rate"] for g in groups),
                4,
            ),
            "note": (
                "Non-zero gaps indicate unequal error/selection rates across groups. "
                "These are reported for transparency, not mitigated away."
            ),
        }

    return {"by_attribute": by_attribute, "disparities": disparities}
