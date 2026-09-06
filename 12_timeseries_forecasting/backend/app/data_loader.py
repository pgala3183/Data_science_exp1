from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.config import DATA_PATH


def load_series(path: Path | None = None) -> pd.DataFrame:
    p = path or DATA_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Missing {p}. Run: python data/fetch_data.py"
        )
    df = pd.read_parquet(p)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds").reset_index(drop=True)
    df["y"] = df["y"].astype(float)
    return df
