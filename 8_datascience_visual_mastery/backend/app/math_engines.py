"""Numerical helpers for visual explainers."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats


def simulate_clt(
    dist: str = "exponential",
    sample_size: int = 30,
    n_samples: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    sample_size = int(np.clip(sample_size, 1, 500))
    n_samples = int(np.clip(n_samples, 100, 10000))

    if dist == "uniform":
        draws = rng.uniform(0, 1, size=(n_samples, sample_size))
        true_mean, true_var = 0.5, 1 / 12
    elif dist == "bernoulli":
        p = 0.3
        draws = rng.binomial(1, p, size=(n_samples, sample_size)).astype(float)
        true_mean, true_var = p, p * (1 - p)
    else:  # exponential (skewed)
        draws = rng.exponential(1.0, size=(n_samples, sample_size))
        true_mean, true_var = 1.0, 1.0

    means = draws.mean(axis=1)
    hist_counts, bin_edges = np.histogram(means, bins=40, density=True)
    centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    se = np.sqrt(true_var / sample_size)
    xs = np.linspace(means.min(), means.max(), 120)
    normal_pdf = stats.norm.pdf(xs, loc=true_mean, scale=se)

    return {
        "dist": dist,
        "sample_size": sample_size,
        "n_samples": n_samples,
        "population_mean": float(true_mean),
        "sampling_mean": float(means.mean()),
        "sampling_std": float(means.std(ddof=1)),
        "theoretical_se": float(se),
        "histogram": {
            "centers": centers.tolist(),
            "density": hist_counts.tolist(),
        },
        "normal_curve": {"x": xs.tolist(), "y": normal_pdf.tolist()},
        "example_sample": draws[0].tolist(),
    }


def loss_surface(resolution: int = 60) -> dict[str, Any]:
    """Classic bowl: L(w1, w2) = (w1-1)^2 + 0.6*(w2+0.5)^2 + 0.15*sin terms for mild nonconvexity."""
    resolution = int(np.clip(resolution, 20, 120))
    w1 = np.linspace(-2.5, 3.5, resolution)
    w2 = np.linspace(-3.0, 2.5, resolution)
    W1, W2 = np.meshgrid(w1, w2)
    Z = (W1 - 1.0) ** 2 + 0.6 * (W2 + 0.5) ** 2 + 0.15 * np.sin(2.2 * W1) * np.cos(1.5 * W2)
    # Analytic gradient of smooth part + numeric-friendly closed form
    # d/dw1 = 2(w1-1) + 0.15*2.2*cos(2.2 w1)*cos(1.5 w2)
    # d/dw2 = 1.2(w2+0.5) - 0.15*1.5*sin(2.2 w1)*sin(1.5 w2)
    return {
        "w1": w1.tolist(),
        "w2": w2.tolist(),
        "z": Z.tolist(),
        "minimum": {"w1": 1.0, "w2": -0.5},
        "formula": "L=(w1-1)^2 + 0.6(w2+0.5)^2 + 0.15 sin(2.2 w1) cos(1.5 w2)",
    }


def gradient_at(w1: float, w2: float) -> dict[str, float]:
    g1 = 2 * (w1 - 1.0) + 0.15 * 2.2 * np.cos(2.2 * w1) * np.cos(1.5 * w2)
    g2 = 1.2 * (w2 + 0.5) - 0.15 * 1.5 * np.sin(2.2 * w1) * np.sin(1.5 * w2)
    loss = (w1 - 1.0) ** 2 + 0.6 * (w2 + 0.5) ** 2 + 0.15 * np.sin(2.2 * w1) * np.cos(1.5 * w2)
    return {"w1": float(w1), "w2": float(w2), "g1": float(g1), "g2": float(g2), "loss": float(loss)}


def gd_trajectory(
    w1: float = -1.5,
    w2: float = 1.5,
    lr: float = 0.08,
    steps: int = 80,
) -> dict[str, Any]:
    steps = int(np.clip(steps, 5, 300))
    lr = float(np.clip(lr, 0.001, 1.5))
    path = []
    for _ in range(steps):
        state = gradient_at(w1, w2)
        path.append(state)
        w1 = w1 - lr * state["g1"]
        w2 = w2 - lr * state["g2"]
        if abs(state["g1"]) + abs(state["g2"]) < 1e-5:
            path.append(gradient_at(w1, w2))
            break
    path.append(gradient_at(w1, w2))
    return {"lr": lr, "path": path}


def bias_variance(
    degree: int = 3,
    n_train: int = 40,
    noise: float = 0.35,
    seed: int = 42,
) -> dict[str, Any]:
    """True function sin(1.5 x); polynomial fits of varying degree."""
    degree = int(np.clip(degree, 0, 15))
    n_train = int(np.clip(n_train, 10, 200))
    rng = np.random.default_rng(seed)

    def f(x: np.ndarray) -> np.ndarray:
        return np.sin(1.5 * x)

    x_train = np.sort(rng.uniform(-3, 3, n_train))
    y_train = f(x_train) + rng.normal(0, noise, n_train)
    x_test = np.linspace(-3, 3, 80)
    y_test_true = f(x_test)
    y_test = y_test_true + rng.normal(0, noise, len(x_test))

    # Sweep degrees for curves
    degrees = list(range(0, 13))
    train_err, test_err = [], []
    for d in degrees:
        coef = np.polyfit(x_train, y_train, d)
        pred_tr = np.polyval(coef, x_train)
        pred_te = np.polyval(coef, x_test)
        train_err.append(float(np.mean((pred_tr - y_train) ** 2)))
        test_err.append(float(np.mean((pred_te - y_test) ** 2)))

    coef = np.polyfit(x_train, y_train, degree)
    x_grid = np.linspace(-3, 3, 200)
    fit = np.polyval(coef, x_grid)

    return {
        "degree": degree,
        "train_points": {"x": x_train.tolist(), "y": y_train.tolist()},
        "truth": {"x": x_grid.tolist(), "y": f(x_grid).tolist()},
        "fit": {"x": x_grid.tolist(), "y": fit.tolist()},
        "error_curves": {
            "degrees": degrees,
            "train_mse": train_err,
            "test_mse": test_err,
        },
        "train_mse": train_err[degree] if degree < len(train_err) else float(np.mean((np.polyval(coef, x_train) - y_train) ** 2)),
        "test_mse": test_err[degree] if degree < len(test_err) else float(np.mean((np.polyval(coef, x_test) - y_test) ** 2)),
    }


def roc_bundle(threshold: float = 0.5, seed: int = 42, n: int = 400) -> dict[str, Any]:
    """Synthetic score/label set; metrics at threshold + full ROC curve."""
    rng = np.random.default_rng(seed)
    n = int(np.clip(n, 50, 2000))
    # Two overlapping score distributions
    n_pos = n // 3
    n_neg = n - n_pos
    scores_pos = rng.normal(0.65, 0.18, n_pos)
    scores_neg = rng.normal(0.35, 0.18, n_neg)
    scores = np.clip(np.concatenate([scores_pos, scores_neg]), 0, 1)
    labels = np.concatenate([np.ones(n_pos), np.zeros(n_neg)]).astype(int)

    threshold = float(np.clip(threshold, 0.0, 1.0))
    preds = (scores >= threshold).astype(int)
    tp = int(((preds == 1) & (labels == 1)).sum())
    fp = int(((preds == 1) & (labels == 0)).sum())
    tn = int(((preds == 0) & (labels == 0)).sum())
    fn = int(((preds == 0) & (labels == 1)).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0

    # ROC over many thresholds
    thr_grid = np.linspace(0, 1, 101)
    roc = []
    for t in thr_grid:
        p = (scores >= t).astype(int)
        tp_i = ((p == 1) & (labels == 1)).sum()
        fp_i = ((p == 1) & (labels == 0)).sum()
        fn_i = ((p == 0) & (labels == 1)).sum()
        tn_i = ((p == 0) & (labels == 0)).sum()
        tpr_i = tp_i / (tp_i + fn_i) if (tp_i + fn_i) else 0.0
        fpr_i = fp_i / (fp_i + tn_i) if (fp_i + tn_i) else 0.0
        roc.append({"threshold": float(t), "fpr": float(fpr_i), "tpr": float(tpr_i)})

    # AUC trapezoid
    ordered = sorted(roc, key=lambda r: r["fpr"])
    auc = 0.0
    for i in range(1, len(ordered)):
        dx = ordered[i]["fpr"] - ordered[i - 1]["fpr"]
        avg_y = 0.5 * (ordered[i]["tpr"] + ordered[i - 1]["tpr"])
        auc += dx * avg_y

    return {
        "threshold": threshold,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": float(prec),
        "recall": float(rec),
        "fpr": float(fpr),
        "specificity": float(spec),
        "roc": roc,
        "auc": float(auc),
        "operating_point": {"fpr": float(fpr), "tpr": float(rec)},
        "n_pos": int(n_pos),
        "n_neg": int(n_neg),
    }


CONCEPTS = [
    {
        "id": "bayes",
        "title": "Bayes' Theorem",
        "blurb": "Prior belief updated by evidence into a posterior.",
        "compute": "client",
    },
    {
        "id": "clt",
        "title": "Central Limit Theorem",
        "blurb": "Sample means form a near-normal sampling distribution.",
        "compute": "server",
    },
    {
        "id": "gradient-descent",
        "title": "Gradient Descent",
        "blurb": "Follow the negative gradient down a loss surface.",
        "compute": "server",
    },
    {
        "id": "bias-variance",
        "title": "Bias–Variance Tradeoff",
        "blurb": "Model complexity vs train and test error.",
        "compute": "server",
    },
    {
        "id": "roc",
        "title": "Confusion Matrix & ROC",
        "blurb": "Thresholds trade precision, recall, and false alarms.",
        "compute": "server",
    },
]
