"""Phase 2 — Data Understanding / EDA summaries."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.config import CATEGORICAL_FEATURES, LABEL, NUMERIC_FEATURES


def compute_eda(df: pd.DataFrame) -> dict[str, Any]:
    """Summary stats, missingness, correlations, and class balance."""
    n_rows, n_cols = df.shape
    label_counts = df[LABEL].value_counts(dropna=False).to_dict()
    label_counts = {str(k): int(v) for k, v in label_counts.items()}

    missing = []
    for col in df.columns:
        miss = int(df[col].isna().sum())
        missing.append(
            {
                "column": col,
                "missing": miss,
                "missing_pct": round(100.0 * miss / max(n_rows, 1), 3),
            }
        )
    missing.sort(key=lambda x: -x["missing"])

    numeric_summary = []
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        numeric_summary.append(
            {
                "column": col,
                "mean": _f(s.mean()),
                "std": _f(s.std()),
                "min": _f(s.min()),
                "p25": _f(s.quantile(0.25)),
                "median": _f(s.median()),
                "p75": _f(s.quantile(0.75)),
                "max": _f(s.max()),
            }
        )

    cat_summary = []
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            continue
        vc = df[col].astype(str).value_counts(dropna=False).head(8)
        cat_summary.append(
            {
                "column": col,
                "n_unique": int(df[col].nunique(dropna=True)),
                "top": [{"value": str(i), "count": int(c)} for i, c in vc.items()],
            }
        )

    # Correlations among numeric features + binary target
    corr_df = df[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce").copy()
    corr_df["income_gt_50k"] = (df[LABEL].astype(str) == ">50K").astype(float)
    corr = corr_df.corr(numeric_only=True)
    corr_matrix = {
        "columns": list(corr.columns),
        "matrix": [[_f(v) for v in row] for row in corr.to_numpy().tolist()],
    }

    # Target vs key categoricals (for charts)
    target_by_sex = _crosstab_rates(df, "sex")
    target_by_race = _crosstab_rates(df, "race")
    target_by_education = _crosstab_rates(df, "education", top_n=10)

    return {
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "label": LABEL,
        "label_counts": label_counts,
        "positive_rate": round(
            float((df[LABEL].astype(str) == ">50K").mean()), 4
        ),
        "missingness": missing,
        "numeric_summary": numeric_summary,
        "categorical_summary": cat_summary,
        "correlation": corr_matrix,
        "target_by_sex": target_by_sex,
        "target_by_race": target_by_race,
        "target_by_education": target_by_education,
    }


def _crosstab_rates(df: pd.DataFrame, col: str, top_n: int | None = None) -> list[dict]:
    if col not in df.columns:
        return []
    tmp = df[[col, LABEL]].copy()
    tmp[col] = tmp[col].astype(str)
    if top_n is not None:
        keep = tmp[col].value_counts().head(top_n).index
        tmp = tmp[tmp[col].isin(keep)]
    rows = []
    for val, g in tmp.groupby(col, dropna=False):
        n = len(g)
        pos = int((g[LABEL].astype(str) == ">50K").sum())
        rows.append(
            {
                "group": str(val),
                "n": n,
                "gt_50k": pos,
                "gt_50k_rate": round(pos / max(n, 1), 4),
            }
        )
    rows.sort(key=lambda r: -r["n"])
    return rows


def _f(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None
