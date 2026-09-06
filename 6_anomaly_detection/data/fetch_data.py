"""
Generate synthetic multi-sensor telemetry with explicit injected anomalies.

Ground-truth strategy (documented also in README):
- Normal points: multivariate Gaussian around a healthy operating regime.
- Injected anomalies (label=1): point spikes, sensor drift bursts, and
  rare off-manifold clusters. These labels are the evaluation ground truth.
- Train/fit for unsupervised models uses ONLY label=0 rows from the
  training window (time-ordered split) so detectors never train on known
  attacks — matching a typical semi-supervised anomaly setup.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "processed"

FEATURE_COLS = [
    "cpu_pct",
    "mem_pct",
    "disk_io",
    "net_in",
    "net_out",
    "temp_c",
    "latency_ms",
    "error_rate",
]


def generate(n: int = 5000, anomaly_rate: float = 0.05, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_anom = int(n * anomaly_rate)
    n_norm = n - n_anom

    # Healthy regime
    normal = np.column_stack(
        [
            rng.normal(35, 8, n_norm).clip(5, 90),  # cpu
            rng.normal(55, 10, n_norm).clip(10, 95),  # mem
            rng.normal(120, 30, n_norm).clip(10, 400),  # disk_io
            rng.normal(200, 50, n_norm).clip(20, 800),  # net_in
            rng.normal(180, 45, n_norm).clip(20, 800),  # net_out
            rng.normal(42, 3, n_norm).clip(30, 70),  # temp
            rng.normal(25, 8, n_norm).clip(1, 120),  # latency
            rng.beta(1.5, 30, n_norm) * 0.05,  # error_rate small
        ]
    )

    anomalies = []
    kinds = []
    for _ in range(n_anom):
        kind = rng.choice(["spike", "drift", "off_manifold"], p=[0.4, 0.3, 0.3])
        base = normal[rng.integers(0, n_norm)].copy()
        if kind == "spike":
            # Sudden CPU/latency/error spike
            base[0] = rng.uniform(85, 100)
            base[6] = rng.uniform(150, 400)
            base[7] = rng.uniform(0.15, 0.6)
        elif kind == "drift":
            # Temperature + memory creep
            base[1] = rng.uniform(88, 99)
            base[5] = rng.uniform(72, 95)
            base[2] = rng.uniform(350, 600)
        else:
            # Off-manifold: inverted network pattern + odd disk
            base[3] = rng.uniform(5, 30)
            base[4] = rng.uniform(700, 1200)
            base[2] = rng.uniform(5, 25)
            base[0] = rng.uniform(5, 15)
        anomalies.append(base)
        kinds.append(kind)

    anomalies_arr = np.vstack(anomalies) if anomalies else np.empty((0, 8))
    X = np.vstack([normal, anomalies_arr])
    y = np.array([0] * n_norm + [1] * n_anom)
    kind_col = ["normal"] * n_norm + kinds

    # Time index then shuffle within? Keep chronological: normals and anomalies interleaved
    order = rng.permutation(len(X))
    X, y = X[order], y[order]
    kind_col = [kind_col[i] for i in order]

    t0 = pd.Timestamp("2024-01-01")
    times = [t0 + pd.Timedelta(minutes=int(i)) for i in range(len(X))]

    df = pd.DataFrame(X, columns=FEATURE_COLS)
    df.insert(0, "timestamp", times)
    df["is_anomaly"] = y
    df["anomaly_kind"] = kind_col
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5000)
    parser.add_argument("--anomaly-rate", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df = generate(args.n, args.anomaly_rate, args.seed)
    out = PROCESSED / "telemetry.parquet"
    df.to_parquet(out, index=False)
    df.head(200).to_csv(PROCESSED / "telemetry_preview.csv", index=False)
    print(f"Wrote {len(df):,} rows -> {out}")
    print(f"Anomaly rate: {df['is_anomaly'].mean():.3%} ({df['is_anomaly'].sum()} positives)")
    print(df["anomaly_kind"].value_counts().to_string())


if __name__ == "__main__":
    main()
