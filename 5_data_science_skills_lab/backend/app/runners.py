"""
Mini-exercise runners — each returns a JSON-serializable result dict:
  { kind: table|metric|chart|mixed, ...payload }
Keep each function short and readable; this is a reference lab.
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.inspection import partial_dependence, permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_score,
    learning_curve,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils import resample

from app.datasets import load_dataset

Runner = Callable[[], dict[str, Any]]


def _table(rows: list[dict], title: str = "") -> dict:
    return {"kind": "table", "title": title, "rows": rows}


def _metric(metrics: dict[str, Any], title: str = "") -> dict:
    return {"kind": "metric", "title": title, "metrics": metrics}


def _chart(series: list[dict], chart_type: str, title: str = "", x_key="x", y_key="y") -> dict:
    return {
        "kind": "chart",
        "chart_type": chart_type,
        "title": title,
        "x_key": x_key,
        "y_key": y_key,
        "series": series,
    }


def eda_describe() -> dict:
    df = load_dataset("iris")
    desc = df.describe().T.reset_index().rename(columns={"index": "column"})
    return _table(desc.round(3).to_dict(orient="records"), "Iris describe()")


def eda_missingness() -> dict:
    df = load_dataset("titanic")
    # Introduce a little NA for demo clarity if none
    if df.isna().sum().sum() == 0:
        df.loc[df.sample(40, random_state=0).index, "age"] = np.nan
    miss = (
        (df.isna().mean() * 100)
        .sort_values(ascending=False)
        .rename("pct_missing")
        .reset_index()
        .rename(columns={"index": "column"})
    )
    return _table(miss.round(2).to_dict(orient="records"), "% missing by column")


def eda_correlation() -> dict:
    df = load_dataset("housing")
    corr = df.corr(numeric_only=True).round(3)
    rows = []
    for i in corr.index:
        rows.append({"feature": i, **{c: float(corr.loc[i, c]) for c in corr.columns}})
    return _table(rows, "Pearson correlation matrix")


def eda_class_balance() -> dict:
    df = load_dataset("wine")
    vc = df["target"].value_counts(normalize=True).sort_index()
    series = [{"x": str(i), "y": float(v)} for i, v in vc.items()]
    return _chart(series, "bar", "Wine class proportions", x_key="x", y_key="y")


def eda_distribution() -> dict:
    df = load_dataset("adult")
    cats = pd.cut(df["hours_per_week"], bins=8)
    vc = cats.value_counts().sort_index()
    series = [{"x": str(i), "y": int(v)} for i, v in vc.items()]
    return _chart(series, "bar", "Hours-per-week bins", x_key="x", y_key="y")


def fe_onehot() -> dict:
    df = load_dataset("titanic")
    X = df[["pclass", "sex", "embarked", "fare"]].copy()
    encoded = pd.get_dummies(X, columns=["sex", "embarked"], drop_first=True)
    return _metric(
        {"n_features_before": X.shape[1], "n_features_after": encoded.shape[1]},
        "One-hot expanded feature width",
    ) | {"sample_columns": list(encoded.columns)}


def fe_log_target() -> dict:
    df = load_dataset("housing")
    y = df["sale_price"]
    skew_raw = float(stats.skew(y))
    skew_log = float(stats.skew(np.log1p(y)))
    return _metric(
        {"skew_sale_price": round(skew_raw, 3), "skew_log1p_sale_price": round(skew_log, 3)},
        "Skew before/after log1p",
    )


def fe_interaction() -> dict:
    df = load_dataset("titanic")
    df = df.copy()
    df["family_size"] = df["sibsp"] + df["parch"] + 1
    corr = float(df[["family_size", "survived"]].corr().iloc[0, 1])
    means = df.groupby("family_size")["survived"].mean().reset_index()
    return {
        "kind": "mixed",
        "title": "family_size vs survival",
        "metrics": {"corr_with_survived": round(corr, 3)},
        "table": means.round(3).to_dict(orient="records"),
    }


def fe_standardize() -> dict:
    df = load_dataset("wine")
    X = df.drop(columns=["target"])
    y = df["target"]
    X_train, X_test, _, _ = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    scaler = StandardScaler().fit(X_train)
    Xt = scaler.transform(X_test)
    return _metric(
        {
            "train_mean_abs_max": round(float(np.abs(X_train.mean()).max()), 3),
            "scaled_test_mean_abs_max": round(float(np.abs(Xt.mean(axis=0)).max()), 4),
            "scaled_test_std_mean": round(float(Xt.std(axis=0).mean()), 3),
        },
        "Scaler fit on train only",
    )


def fe_binning() -> dict:
    df = load_dataset("adult")
    bands = pd.cut(df["age"], bins=[17, 30, 45, 60, 100], labels=["18-30", "31-45", "46-60", "61+"])
    out = (
        df.assign(age_band=bands)
        .groupby("age_band", observed=True)["income_gt_50k"]
        .mean()
        .reset_index()
    )
    return _table(out.round(3).to_dict(orient="records"), "P(income>50k) by age band")


def cv_kfold() -> dict:
    df = load_dataset("iris")
    X, y = df.drop(columns=["target"]), df["target"]
    clf = LogisticRegression(max_iter=500)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv)
    series = [{"x": f"fold{i+1}", "y": float(s)} for i, s in enumerate(scores)]
    return {
        "kind": "mixed",
        "title": "5-fold stratified accuracy",
        "metrics": {"mean": round(float(scores.mean()), 3), "std": round(float(scores.std()), 3)},
        "chart": {"chart_type": "bar", "series": series, "x_key": "x", "y_key": "y"},
    }


def cv_split_hygiene() -> dict:
    df = load_dataset("housing")
    X = df.drop(columns=["sale_price"])
    y = df["sale_price"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    scaler = StandardScaler().fit(X_train)
    model = Ridge(alpha=1.0).fit(scaler.transform(X_train), y_train)
    pred = model.predict(scaler.transform(X_test))
    return _metric(
        {"mae": round(float(mean_absolute_error(y_test, pred)), 1)},
        "Ridge MAE with train-only scaling",
    )


def cv_repeated() -> dict:
    df = load_dataset("wine")
    X, y = df.drop(columns=["target"]), df["target"]
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=42)
    scores = cross_val_score(LogisticRegression(max_iter=800), X, y, cv=cv)
    return _metric(
        {
            "n_scores": int(len(scores)),
            "mean_accuracy": round(float(scores.mean()), 3),
            "std": round(float(scores.std()), 3),
        },
        "Repeated stratified CV",
    )


def imb_baseline() -> dict:
    df = load_dataset("adult")
    X = pd.get_dummies(df.drop(columns=["income_gt_50k"]), drop_first=True)
    y = df["income_gt_50k"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    clf = LogisticRegression(max_iter=800).fit(X_train, y_train)
    pred = clf.predict(X_test)
    return _metric(
        {
            "positive_rate": round(float(y.mean()), 3),
            "accuracy": round(float(accuracy_score(y_test, pred)), 3),
            "balanced_accuracy": round(float(balanced_accuracy_score(y_test, pred)), 3),
            "f1": round(float(f1_score(y_test, pred)), 3),
        },
        "Accuracy can look OK while F1 lags on imbalance",
    )


def imb_class_weight() -> dict:
    df = load_dataset("adult")
    X = pd.get_dummies(df.drop(columns=["income_gt_50k"]), drop_first=True)
    y = df["income_gt_50k"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    base = LogisticRegression(max_iter=800).fit(X_train, y_train)
    bal = LogisticRegression(max_iter=800, class_weight="balanced").fit(X_train, y_train)
    return _metric(
        {
            "f1_default": round(float(f1_score(y_test, base.predict(X_test))), 3),
            "f1_balanced_weights": round(float(f1_score(y_test, bal.predict(X_test))), 3),
        },
        "class_weight='balanced' vs default",
    )


def imb_undersample() -> dict:
    df = load_dataset("titanic")
    X = pd.get_dummies(df.drop(columns=["survived"]), drop_first=True)
    y = df["survived"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    train = X_train.copy()
    train["y"] = y_train.values
    maj = train[train["y"] == train["y"].value_counts().idxmax()]
    mino = train[train["y"] == train["y"].value_counts().idxmin()]
    maj_down = resample(maj, replace=False, n_samples=len(mino), random_state=42)
    bal = pd.concat([maj_down, mino])
    clf = LogisticRegression(max_iter=800).fit(bal.drop(columns=["y"]), bal["y"])
    return _metric(
        {
            "train_before": int(len(train)),
            "train_after_undersample": int(len(bal)),
            "f1_holdout": round(float(f1_score(y_test, clf.predict(X_test))), 3),
        },
        "Undersample on train fold only",
    )


def tune_grid() -> dict:
    df = load_dataset("iris")
    X, y = df.drop(columns=["target"]), df["target"]
    grid = GridSearchCV(
        LogisticRegression(max_iter=800),
        {"C": [0.01, 0.1, 1, 10]},
        cv=5,
    )
    grid.fit(X, y)
    return _metric(
        {"best_C": grid.best_params_["C"], "best_cv_accuracy": round(float(grid.best_score_), 3)},
        "GridSearchCV best logistic C",
    )


def tune_random() -> dict:
    df = load_dataset("wine")
    X, y = df.drop(columns=["target"]), df["target"]
    search = RandomizedSearchCV(
        RandomForestClassifier(random_state=42),
        {"n_estimators": [50, 100, 150], "max_depth": [None, 3, 5, 8]},
        n_iter=6,
        cv=3,
        random_state=42,
    )
    search.fit(X, y)
    return _metric(
        {
            "best_params": search.best_params_,
            "best_cv_accuracy": round(float(search.best_score_), 3),
        },
        "RandomizedSearchCV forest",
    )


def tune_learning_curve() -> dict:
    df = load_dataset("housing")
    X, y = df.drop(columns=["sale_price"]), df["sale_price"]
    sizes, train_sc, val_sc = learning_curve(
        Ridge(alpha=1.0),
        X,
        y,
        train_sizes=np.linspace(0.2, 1.0, 5),
        cv=5,
        scoring="neg_mean_absolute_error",
    )
    series = [
        {"x": int(n), "train_mae": float(-tr.mean()), "val_mae": float(-va.mean())}
        for n, tr, va in zip(sizes, train_sc, val_sc)
    ]
    return {
        "kind": "chart",
        "chart_type": "line_multi",
        "title": "Learning curve (MAE)",
        "series": series,
        "x_key": "x",
        "y_keys": ["train_mae", "val_mae"],
    }


def interp_coef() -> dict:
    df = load_dataset("iris")
    X, y = df.drop(columns=["target"]), df["target"]
    clf = LogisticRegression(max_iter=800).fit(X, y)
    imp = np.abs(clf.coef_).mean(axis=0)
    rows = [
        {"feature": f, "abs_coef_mean": round(float(v), 3)}
        for f, v in sorted(zip(X.columns, imp), key=lambda t: -t[1])
    ]
    return _table(rows, "Mean |coefficient| across classes")


def interp_permutation() -> dict:
    df = load_dataset("wine")
    X, y = df.drop(columns=["target"]), df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_train)
    r = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42)
    rows = [
        {"feature": f, "importance": round(float(v), 4)}
        for f, v in sorted(zip(X.columns, r.importances_mean), key=lambda t: -t[1])[:8]
    ]
    return _table(rows, "Top permutation importances")


def interp_partial_dep() -> dict:
    df = load_dataset("housing")
    X, y = df.drop(columns=["sale_price"]), df["sale_price"]
    model = GradientBoostingRegressor(random_state=42).fit(X, y)
    pd_out = partial_dependence(model, X, ["sqft"], kind="average")
    xs = pd_out["grid_values"][0]
    ys = pd_out["average"][0]
    series = [{"x": float(a), "y": float(b)} for a, b in zip(xs, ys)]
    return _chart(series, "line", "Partial dependence: sqft → price", x_key="x", y_key="y")


def stats_ttest() -> dict:
    df = load_dataset("titanic")
    a = df.loc[df["survived"] == 1, "age"].dropna()
    b = df.loc[df["survived"] == 0, "age"].dropna()
    # ensure some NA filled for demo ages
    if a.empty or b.empty:
        a = df.loc[df["survived"] == 1, "age"]
        b = df.loc[df["survived"] == 0, "age"]
    t, p = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    return _metric(
        {
            "mean_age_survived": round(float(np.nanmean(a)), 2),
            "mean_age_not": round(float(np.nanmean(b)), 2),
            "t_stat": round(float(t), 3),
            "p_value": float(p),
        },
        "Welch t-test: age by survival",
    )


def stats_chi2() -> dict:
    df = load_dataset("titanic")
    ct = pd.crosstab(df["sex"], df["survived"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return {
        "kind": "mixed",
        "title": "Chi-square: sex vs survived",
        "metrics": {"chi2": round(float(chi2), 3), "dof": int(dof), "p_value": float(p)},
        "table": ct.reset_index().to_dict(orient="records"),
    }


def stats_corr() -> dict:
    df = load_dataset("housing")
    r, p = stats.pearsonr(df["sqft"], df["sale_price"])
    return _metric(
        {"pearson_r": round(float(r), 3), "p_value": float(p)},
        "sqft vs sale_price",
    )


def metrics_roc() -> dict:
    df = load_dataset("adult")
    X = pd.get_dummies(df.drop(columns=["income_gt_50k"]), drop_first=True)
    y = df["income_gt_50k"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    clf = LogisticRegression(max_iter=800).fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, proba)
    # downsample curve for UI
    idx = np.linspace(0, len(fpr) - 1, num=min(40, len(fpr))).astype(int)
    series = [{"x": float(fpr[i]), "y": float(tpr[i])} for i in idx]
    return {
        "kind": "mixed",
        "title": "ROC curve",
        "metrics": {"auc": round(float(roc_auc_score(y_test, proba)), 3)},
        "chart": {"chart_type": "line", "series": series, "x_key": "x", "y_key": "y"},
    }


def metrics_confusion() -> dict:
    df = load_dataset("wine")
    X, y = df.drop(columns=["target"]), df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    pred = LogisticRegression(max_iter=1000).fit(X_train, y_train).predict(X_test)
    cm = confusion_matrix(y_test, pred)
    rows = [
        {"actual": int(i), **{f"pred_{j}": int(cm[i, j]) for j in range(cm.shape[1])}}
        for i in range(cm.shape[0])
    ]
    return _table(rows, "Confusion matrix (rows=actual)")


def pipeline_basic() -> dict:
    df = load_dataset("titanic")
    y = df["survived"]
    X = df[["pclass", "sex", "age", "fare", "embarked"]].copy()
    X["age"] = X["age"].fillna(X["age"].median())
    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), ["pclass", "age", "fare"]),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["sex", "embarked"]),
        ]
    )
    pipe = Pipeline([("prep", pre), ("clf", LogisticRegression(max_iter=800))])
    scores = cross_val_score(pipe, X, y, cv=5)
    return _metric(
        {"cv_accuracy_mean": round(float(scores.mean()), 3), "cv_accuracy_std": round(float(scores.std()), 3)},
        "ColumnTransformer + Pipeline CV",
    )


RUNNERS: dict[str, Runner] = {
    "runners.eda_describe": eda_describe,
    "runners.eda_missingness": eda_missingness,
    "runners.eda_correlation": eda_correlation,
    "runners.eda_class_balance": eda_class_balance,
    "runners.eda_distribution": eda_distribution,
    "runners.fe_onehot": fe_onehot,
    "runners.fe_log_target": fe_log_target,
    "runners.fe_interaction": fe_interaction,
    "runners.fe_standardize": fe_standardize,
    "runners.fe_binning": fe_binning,
    "runners.cv_kfold": cv_kfold,
    "runners.cv_split_hygiene": cv_split_hygiene,
    "runners.cv_repeated": cv_repeated,
    "runners.imb_baseline": imb_baseline,
    "runners.imb_class_weight": imb_class_weight,
    "runners.imb_undersample": imb_undersample,
    "runners.tune_grid": tune_grid,
    "runners.tune_random": tune_random,
    "runners.tune_learning_curve": tune_learning_curve,
    "runners.interp_coef": interp_coef,
    "runners.interp_permutation": interp_permutation,
    "runners.interp_partial_dep": interp_partial_dep,
    "runners.stats_ttest": stats_ttest,
    "runners.stats_chi2": stats_chi2,
    "runners.stats_corr": stats_corr,
    "runners.metrics_roc": metrics_roc,
    "runners.metrics_confusion": metrics_confusion,
    "runners.pipeline_basic": pipeline_basic,
}


def run_skill(script_key: str) -> dict[str, Any]:
    if script_key not in RUNNERS:
        raise KeyError(f"No runner registered for {script_key}")
    return RUNNERS[script_key]()
