"""
Generate a synthetic daily retail sales series with clear trend + seasonality.

The series is designed so ACF shows strong weekly (lag-7) and milder annual
structure, making SARIMA seasonal order and lag features for GB easy to justify.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "processed"


def generate(
    start: str = "2019-01-01",
    end: str = "2023-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    t = np.arange(len(dates), dtype=float)

    # Slow growth + mild quadratic bend
    trend = 420 + 0.085 * t + 1.2e-5 * t**2

    # Weekly: weekend uplift (Sat/Sun)
    dow = dates.dayofweek.to_numpy()
    weekly = np.array([0, 5, 8, 12, 35, 55, -8], dtype=float)[dow]

    # Annual: holiday peak (late Nov–Dec) and summer soft patch
    doy = dates.dayofyear.to_numpy()
    annual = 40 * np.sin(2 * np.pi * (doy - 80) / 365.25)
    holiday = np.where((doy >= 330) | (doy <= 5), 90.0, 0.0)
    holiday = np.where((doy >= 320) & (doy < 330), 45.0, holiday)

    # Mild AR noise for serial correlation
    eps = rng.normal(0, 18, len(dates))
    noise = np.zeros(len(dates))
    for i in range(1, len(dates)):
        noise[i] = 0.35 * noise[i - 1] + eps[i]

    sales = np.clip(trend + weekly + annual + holiday + noise, 50, None)

    return pd.DataFrame({"ds": dates, "y": sales.round(2)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate retail sales time series")
    parser.add_argument("--start", default="2019-01-01")
    parser.add_argument("--end", default="2023-12-31")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df = generate(args.start, args.end, args.seed)
    out = PROCESSED / "retail_sales.parquet"
    df.to_parquet(out, index=False)
    df.to_csv(PROCESSED / "retail_sales_preview.csv", index=False)
    print(f"Wrote {len(df)} rows -> {out}")
    print(f"y mean={df['y'].mean():.1f}  std={df['y'].std():.1f}")


if __name__ == "__main__":
    main()
