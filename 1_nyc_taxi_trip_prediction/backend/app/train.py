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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import ARTIFACTS_DIR
from app.pipeline import PreparedData, prepare_dataset


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
    sample_idx = X.sample(n, random_state=42).index
    perm = permutation_importance(
        model,
        X.loc[sample_idx],
        y.loc[sample_idx],
        n_repeats=5,
        random_state=42,
        scoring="neg_root_mean_squared_error",
    )
    raw = np.clip(perm.importances_mean, 0, None)
    total = float(raw.sum()) or 1.0
    return {f: float(v / total) for f, v in zip(feature_names, raw)}


def train_models(data: PreparedData | None = None) -> TrainResult:
    data = data or prepare_dataset()
    feature_names = data.feature_columns

    ridge = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]
    )
    ridge.fit(data.X_train, data.y_train)
    ridge_pred = ridge.predict(data.X_test)
    ridge_metrics = _score(
        "ridge",
        data.y_test,
        ridge_pred,
        _ridge_importances(ridge, feature_names),
    )

    hgb = HistGradientBoostingRegressor(
        max_depth=8,
        learning_rate=0.08,
        max_iter=200,
        random_state=42,
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
        ARTIFACTS_DIR / "model_bundle.joblib",
    )

    result = TrainResult(
        best_model_name=best_name,
        metrics=[ridge_metrics, hgb_metrics],
        residual_std=residual_std,
        n_train=len(data.X_train),
        n_test=len(data.X_test),
    )
    with open(ARTIFACTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_model_name": result.best_model_name,
                "residual_std": result.residual_std,
                "n_train": result.n_train,
                "n_test": result.n_test,
                "split": "time_based",
                "target": "trip_duration_seconds",
                "models": [asdict(m) for m in result.metrics],
            },
            f,
            indent=2,
        )
    return result


def load_bundle(path: Path | None = None) -> dict:
    path = path or (ARTIFACTS_DIR / "model_bundle.joblib")
    if not path.exists():
        raise FileNotFoundError(f"No trained model at {path}. Call train_models() first.")
    return joblib.load(path)


def load_metrics(path: Path | None = None) -> dict:
    path = path or (ARTIFACTS_DIR / "metrics.json")
    if not path.exists():
        raise FileNotFoundError(f"No metrics at {path}.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    result = train_models()
    print(f"Best: {result.best_model_name}")
    for m in result.metrics:
        print(f"  {m.name}: RMSE={m.rmse:.1f}s MAE={m.mae:.1f}s R²={m.r2:.3f}")
