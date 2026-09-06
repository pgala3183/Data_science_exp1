"""Model training and evaluation (CRISP-DM Modeling + Evaluation)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import (
    ARTIFACTS_DIR,
    BUNDLE_PATH,
    EVAL_PATH,
    META_PATH,
    METRICS_PATH,
    RANDOM_STATE,
    TARGET,
    TEST_FRACTION,
    TRAIN_REF_PATH,
)
from app.pipeline import PreparedData, pipeline_diagram, prepare_dataset


@dataclass
class ModelMetrics:
    name: str
    rmse: float
    mae: float
    r2: float
    feature_importances: dict[str, float]


@dataclass
class TrainResult:
    best_model_name: str
    metrics: list[ModelMetrics]
    residual_std: float
    n_train: int
    n_test: int
    cv: dict
    residuals: dict
    cluster_fairness: dict


def _score(name: str, y_true, y_pred, importances: dict[str, float]) -> ModelMetrics:
    return ModelMetrics(
        name=name,
        rmse=float(np.sqrt(mean_squared_error(y_true, y_pred))),
        mae=float(mean_absolute_error(y_true, y_pred)),
        r2=float(r2_score(y_true, y_pred)),
        feature_importances=importances,
    )


def _ridge_importances(model: Pipeline, feature_names: list[str]) -> dict[str, float]:
    coefs = np.abs(model.named_steps["model"].coef_)
    total = float(coefs.sum()) or 1.0
    return {f: float(c / total) for f, c in zip(feature_names, coefs)}


def _permutation_importances(model, X, y, feature_names: list[str]) -> dict[str, float]:
    n = min(2000, len(X))
    sample_idx = X.sample(n, random_state=RANDOM_STATE).index
    perm = permutation_importance(
        model,
        X.loc[sample_idx],
        y.loc[sample_idx],
        n_repeats=5,
        random_state=RANDOM_STATE,
        scoring="neg_root_mean_squared_error",
    )
    raw = np.clip(perm.importances_mean, 0, None)
    total = float(raw.sum()) or 1.0
    return {f: float(v / total) for f, v in zip(feature_names, raw)}


def _cv_scores(models: dict, X_train, y_train) -> dict:
    out = {}
    for name, model in models.items():
        scores = cross_val_score(
            model,
            X_train,
            y_train,
            cv=3,
            scoring="neg_root_mean_squared_error",
            n_jobs=1,
        )
        rmse = -scores
        out[name] = {
            "cv_folds": 3,
            "rmse_mean": float(rmse.mean()),
            "rmse_std": float(rmse.std()),
            "neg_rmse_mean": float(scores.mean()),
        }
    return out


def _residual_summary(y_true, y_pred) -> dict:
    resid = np.asarray(y_true) - np.asarray(y_pred)
    # Histogram for UI
    hist, edges = np.histogram(resid, bins=30)
    return {
        "mean": float(resid.mean()),
        "std": float(resid.std()),
        "p05": float(np.percentile(resid, 5)),
        "p50": float(np.percentile(resid, 50)),
        "p95": float(np.percentile(resid, 95)),
        "histogram": {
            "counts": hist.astype(int).tolist(),
            "bin_edges": edges.astype(float).tolist(),
        },
    }


def _cluster_fairness(test_df, y_true, y_pred) -> dict:
    """
    Group fairness / bias audit by pickup zone cluster (geographic equity proxy).

    Classic protected attributes (sex/race) are absent from taxi trip schemas;
    we instead report residual error disparate impact across spatial clusters.
    """
    df = test_df.copy()
    df = df.assign(
        y_true=np.asarray(y_true),
        y_pred=np.asarray(y_pred),
        abs_err=np.abs(np.asarray(y_true) - np.asarray(y_pred)),
    )
    rows = []
    for cluster, g in df.groupby("pickup_cluster"):
        rows.append(
            {
                "group": f"pickup_cluster_{int(cluster)}",
                "support": int(len(g)),
                "mean_duration": float(g["y_true"].mean()),
                "mae": float(g["abs_err"].mean()),
                "rmse": float(np.sqrt(((g["y_true"] - g["y_pred"]) ** 2).mean())),
                "mean_residual": float((g["y_true"] - g["y_pred"]).mean()),
            }
        )
    maes = [r["mae"] for r in rows] or [0.0]
    return {
        "by_attribute": {"pickup_cluster": rows},
        "disparities": {
            "pickup_cluster": {
                "majority_group": max(rows, key=lambda r: r["support"])["group"] if rows else "n/a",
                "mae_range": float(max(maes) - min(maes)),
                "note": (
                    "Bias audit: MAE spread across pickup clusters is a group-fairness "
                    "signal for geographic equity — high MAE_range may indicate "
                    "disparate impact on under-served zones."
                ),
            }
        },
    }


def train_models(data: PreparedData | None = None) -> TrainResult:
    data = data or prepare_dataset()
    feature_names = data.feature_columns

    ridge = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]
    )
    hgb = HistGradientBoostingRegressor(
        max_depth=8,
        learning_rate=0.08,
        max_iter=200,
        random_state=RANDOM_STATE,
    )

    # CV on unfitted clones (sklearn clones internally)
    cv = _cv_scores(
        {
            "ridge": Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=1.0))]),
            "hist_gradient_boosting": HistGradientBoostingRegressor(
                max_depth=8, learning_rate=0.08, max_iter=200, random_state=RANDOM_STATE
            ),
        },
        data.X_train,
        data.y_train,
    )

    ridge.fit(data.X_train, data.y_train)
    ridge_pred = ridge.predict(data.X_test)
    ridge_metrics = _score(
        "ridge",
        data.y_test,
        ridge_pred,
        _ridge_importances(ridge, feature_names),
    )

    hgb.fit(data.X_train, data.y_train)
    hgb_pred = hgb.predict(data.X_test)
    hgb_metrics = _score(
        "hist_gradient_boosting",
        data.y_test,
        hgb_pred,
        _permutation_importances(hgb, data.X_test, data.y_test, feature_names),
    )

    use_hgb = hgb_metrics.rmse <= ridge_metrics.rmse
    best_name = hgb_metrics.name if use_hgb else ridge_metrics.name
    best_model = hgb if use_hgb else ridge
    best_pred = hgb_pred if use_hgb else ridge_pred
    residual_std = float(np.std(data.y_test.to_numpy() - best_pred))

    residuals = {
        "ridge": _residual_summary(data.y_test, ridge_pred),
        "hist_gradient_boosting": _residual_summary(data.y_test, hgb_pred),
    }
    fairness = {
        "ridge": _cluster_fairness(data.test_df, data.y_test, ridge_pred),
        "hist_gradient_boosting": _cluster_fairness(data.test_df, data.y_test, hgb_pred),
    }

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": best_model,
            "model_name": best_name,
            "pickup_kmeans": data.pickup_kmeans,
            "dropoff_kmeans": data.dropoff_kmeans,
            "feature_columns": feature_names,
            "residual_std": residual_std,
        },
        BUNDLE_PATH,
    )

    # Training feature reference for drift monitoring
    joblib.dump(
        {
            "X_train": data.X_train.reset_index(drop=True),
            "feature_columns": feature_names,
            "pickup_kmeans": data.pickup_kmeans,
            "dropoff_kmeans": data.dropoff_kmeans,
        },
        TRAIN_REF_PATH,
    )

    result = TrainResult(
        best_model_name=best_name,
        metrics=[ridge_metrics, hgb_metrics],
        residual_std=residual_std,
        n_train=len(data.X_train),
        n_test=len(data.X_test),
        cv=cv,
        residuals=residuals,
        cluster_fairness=fairness,
    )

    metrics_payload = {
        "best_model_name": result.best_model_name,
        "residual_std": result.residual_std,
        "n_train": result.n_train,
        "n_test": result.n_test,
        "split": "time_based",
        "target": "trip_duration_seconds",
        "models": [asdict(m) for m in result.metrics],
    }
    METRICS_PATH.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    eval_payload = {
        "n_train": result.n_train,
        "n_test": result.n_test,
        "test_fraction": TEST_FRACTION,
        "target": TARGET,
        "split": "time_based",
        "cv": cv,
        "metrics": {m.name: asdict(m) for m in result.metrics},
        "residuals": residuals,
        "fairness": fairness,
        "primary_model": best_name,
        "pipeline": pipeline_diagram(),
        "evaluation_doc": "",  # filled by service from docs/
    }
    EVAL_PATH.write_text(json.dumps(eval_payload, indent=2), encoding="utf-8")

    meta = {
        "n_train": result.n_train,
        "n_test": result.n_test,
        "label": TARGET,
        "feature_cols": feature_names,
        "models": [m.name for m in result.metrics],
        "primary_model": best_name,
        "holdout_rmse": {m.name: m.rmse for m in result.metrics},
        "schema": {
            "pickup_latitude": 40.758,
            "pickup_longitude": -73.9855,
            "dropoff_latitude": 40.7484,
            "dropoff_longitude": -73.9857,
            "pickup_datetime": "2016-03-15T08:30:00",
            "passenger_count": 1,
        },
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return result


def load_bundle(path: Path | None = None) -> dict:
    path = path or BUNDLE_PATH
    if not path.exists():
        raise FileNotFoundError(f"No trained model at {path}. Call train_models() first.")
    return joblib.load(path)


def load_metrics(path: Path | None = None) -> dict:
    path = path or METRICS_PATH
    if not path.exists():
        raise FileNotFoundError(f"No metrics at {path}.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    result = train_models()
    print(f"Best: {result.best_model_name}")
    for m in result.metrics:
        print(f"  {m.name}: RMSE={m.rmse:.1f}s MAE={m.mae:.1f}s R²={m.r2:.3f}")
