"""Load benchmark CSVs used by skill runners."""

from __future__ import annotations

import pandas as pd

from app.config import DATA_DIR


def ensure_data() -> None:
    if not (DATA_DIR / "iris.csv").exists():
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(root / "data"))
        from fetch_data import main as fetch_main

        fetch_main()


def load_dataset(name: str) -> pd.DataFrame:
    ensure_data()
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Unknown dataset '{name}' (expected {path})")
    return pd.read_csv(path)
