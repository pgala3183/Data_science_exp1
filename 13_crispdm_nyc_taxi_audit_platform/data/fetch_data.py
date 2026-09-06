"""
Fetch or generate NYC taxi trip data for duration prediction.

Primary approach: generate a realistic sample modeled on the Kaggle
"NYC Taxi Trip Duration" schema (pickup/dropoff coords, timestamps,
passenger_count, trip_duration). Optional: set USE_KAGGLE=1 and place
`train.csv` from the competition into data/raw/.

No post-trip fields beyond the target are kept as features.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"

# Rough NYC bounding box (focus on Manhattan / nearby boroughs)
LAT_MIN, LAT_MAX = 40.60, 40.90
LON_MIN, LON_MAX = -74.05, -73.75


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def generate_synthetic(n: int = 25_000, seed: int = 42) -> pd.DataFrame:
    """Synthetic trips with duration driven by distance, rush hour, and noise."""
    rng = np.random.default_rng(seed)

    # Sample pickup near denser Manhattan center, dropoff with wider spread
    pickup_latitude = rng.normal(40.758, 0.035, n).clip(LAT_MIN, LAT_MAX)
    pickup_longitude = rng.normal(-73.985, 0.04, n).clip(LON_MIN, LON_MAX)
    dropoff_latitude = (pickup_latitude + rng.normal(0, 0.04, n)).clip(LAT_MIN, LAT_MAX)
    dropoff_longitude = (pickup_longitude + rng.normal(0, 0.05, n)).clip(LON_MIN, LON_MAX)

    start = pd.Timestamp("2016-01-01")
    pickup_datetime = pd.to_datetime(
        start + pd.to_timedelta(rng.integers(0, 180 * 24 * 3600, n), unit="s")
    )

    passenger_count = rng.choice([1, 2, 3, 4, 5, 6], size=n, p=[0.7, 0.15, 0.07, 0.04, 0.02, 0.02])
    vendor_id = rng.choice([1, 2], size=n)

    dist = haversine_km(
        pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude
    )
    hour = pickup_datetime.hour.to_numpy()
    dow = pickup_datetime.dayofweek.to_numpy()
    rush = ((hour >= 7) & (hour <= 9) | (hour >= 16) & (hour <= 19)) & (dow < 5)

    # Duration (seconds): base speed ~22 km/h, slower in rush, floor/ceiling like real data
    speed_kmh = np.where(rush, 14.0, 22.0) + rng.normal(0, 3.0, n)
    speed_kmh = np.clip(speed_kmh, 6.0, 45.0)
    duration = (dist / speed_kmh) * 3600
    duration = duration * rng.lognormal(0, 0.25, n)
    duration = np.clip(duration, 60, 7200).astype(int)

    # Drop near-zero distance outliers similar to competition cleaning
    df = pd.DataFrame(
        {
            "id": [f"id{i:07d}" for i in range(n)],
            "vendor_id": vendor_id,
            "pickup_datetime": pickup_datetime,
            "passenger_count": passenger_count,
            "pickup_longitude": pickup_longitude,
            "pickup_latitude": pickup_latitude,
            "dropoff_longitude": dropoff_longitude,
            "dropoff_latitude": dropoff_latitude,
            "store_and_fwd_flag": rng.choice(["N", "Y"], size=n, p=[0.99, 0.01]),
            "trip_duration": duration,
        }
    )
    df = df[dist > 0.05].reset_index(drop=True)
    return df


def load_kaggle_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["pickup_datetime"])
    required = {
        "pickup_datetime",
        "pickup_longitude",
        "pickup_latitude",
        "dropoff_longitude",
        "dropoff_latitude",
        "passenger_count",
        "trip_duration",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Kaggle CSV missing columns: {missing}")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch/generate NYC taxi trip data")
    parser.add_argument("--n", type=int, default=25_000, help="Synthetic row count")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--kaggle-csv",
        type=Path,
        default=None,
        help="Optional path to Kaggle NYC Taxi Trip Duration train.csv",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    kaggle_default = RAW_DIR / "train.csv"
    source = args.kaggle_csv or (kaggle_default if kaggle_default.exists() else None)

    if source is not None:
        print(f"Loading Kaggle-style CSV from {source}")
        df = load_kaggle_csv(source)
        # Cap size for local training speed while keeping time order
        if len(df) > 80_000:
            df = df.sort_values("pickup_datetime").iloc[:80_000].reset_index(drop=True)
        label = "kaggle_sample"
    else:
        print(f"Generating synthetic NYC taxi trips (n={args.n})...")
        df = generate_synthetic(n=args.n, seed=args.seed)
        label = "synthetic"

    out = PROCESSED_DIR / "trips.parquet"
    df.to_parquet(out, index=False)
    # Also write a small CSV preview for inspection
    df.head(500).to_csv(PROCESSED_DIR / "trips_preview.csv", index=False)
    print(f"Wrote {len(df):,} rows ({label}) -> {out}")


if __name__ == "__main__":
    main()
