"""Fetch Adult / Census Income (OpenML 1590) for the CRISP-DM curriculum project."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "processed" / "adult.parquet"

FEATURE_NOTE = """
Adult Income (OpenML id=1590): predict whether annual income > $50K.
Label column renamed to `income` with values '<=50K' / '>50K'.
Sensitive attributes retained for fairness reporting: sex, race.
"""


def fetch_adult(n: int | None = None, seed: int = 42) -> pd.DataFrame:
    bunch = fetch_openml(data_id=1590, as_frame=True, parser="auto")
    df = bunch.frame.copy()
    if "class" in df.columns:
        df = df.rename(columns={"class": "income"})
    df["income"] = df["income"].astype(str).str.strip()
    # Normalize missing markers used in Adult (np.nan for sklearn)
    for col in df.select_dtypes(include=["object", "category"]).columns:
        s = df[col].astype(str).str.strip().replace({"?": np.nan, "nan": np.nan})
        df[col] = s
    df = df.dropna(subset=["income"]).reset_index(drop=True)
    if n is not None and n < len(df):
        df = df.sample(n=n, random_state=seed).reset_index(drop=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=None, help="Optional row subsample")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_adult(args.n, args.seed)
    df.to_parquet(OUT, index=False)
    print(f"Wrote {len(df):,} rows -> {OUT}")
    print(f"Columns: {list(df.columns)}")
    print(df["income"].value_counts().to_string())
    print(FEATURE_NOTE.strip())


if __name__ == "__main__":
    main()
