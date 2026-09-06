"""
Generate a synthetic market-basket dataset with planted co-purchase patterns
(or load a simple CSV of baskets if placed at data/raw/baskets.csv).

Each row is one transaction with a list of item names.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"

# Catalog with affinity groups (items that often co-occur)
AFFINITY_GROUPS = {
    "breakfast": ["bread", "butter", "jam", "milk", "eggs", "cereal"],
    "italian": ["pasta", "tomato_sauce", "parmesan", "olive_oil", "garlic"],
    "bbq": ["burger_buns", "ground_beef", "ketchup", "charcoal", "coleslaw"],
    "movie_night": ["popcorn", "soda", "chips", "chocolate", "ice_cream"],
    "baby": ["diapers", "baby_wipes", "formula", "baby_shampoo"],
    "cleaning": ["detergent", "fabric_softener", "bleach", "sponges"],
}

# Cross-group bridges (weaker associations)
BRIDGES = [
    ("milk", "cereal"),
    ("pasta", "garlic"),
    ("soda", "chips"),
    ("bread", "eggs"),
    ("detergent", "fabric_softener"),
]


def generate_baskets(n_baskets: int = 4000, seed: int = 42) -> list[list[str]]:
    rng = np.random.default_rng(seed)
    groups = list(AFFINITY_GROUPS.values())
    all_items = sorted({i for g in groups for i in g})
    baskets: list[list[str]] = []

    for _ in range(n_baskets):
        basket: set[str] = set()
        # Pick 1–2 affinity themes
        n_themes = int(rng.integers(1, 3))
        themes = rng.choice(len(groups), size=n_themes, replace=False)
        for ti in themes:
            items = groups[int(ti)]
            # Take a subset of the theme
            k = int(rng.integers(2, min(5, len(items) + 1)))
            basket.update(rng.choice(items, size=k, replace=False).tolist())

        # Occasionally add bridge pairs
        if rng.random() < 0.35:
            a, b = BRIDGES[int(rng.integers(0, len(BRIDGES)))]
            basket.add(a)
            basket.add(b)

        # Noise items
        if rng.random() < 0.4:
            noise_n = int(rng.integers(1, 3))
            basket.update(rng.choice(all_items, size=noise_n, replace=False).tolist())

        if len(basket) >= 2:
            baskets.append(sorted(basket))

    return baskets


def baskets_to_frame(baskets: list[list[str]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": [f"T{i:05d}" for i in range(len(baskets))],
            "items": baskets,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-baskets", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    raw_csv = RAW / "baskets.csv"
    if raw_csv.exists():
        print(f"Loading {raw_csv}")
        df = pd.read_csv(raw_csv)
        if "items" in df.columns:
            # items as semicolon-separated
            baskets = [str(x).split(";") for x in df["items"]]
        else:
            raise SystemExit("Expected column 'items' with semicolon-separated SKUs")
        frame = baskets_to_frame(baskets)
        source = "csv"
    else:
        print(f"Generating synthetic baskets (n={args.n_baskets})")
        baskets = generate_baskets(args.n_baskets, args.seed)
        frame = baskets_to_frame(baskets)
        source = "synthetic"

    out = PROCESSED / "baskets.parquet"
    frame.to_parquet(out, index=False)
    # Also JSONL for easy inspection
    with (PROCESSED / "baskets.jsonl").open("w", encoding="utf-8") as f:
        for _, row in frame.iterrows():
            f.write(json.dumps({"transaction_id": row["transaction_id"], "items": row["items"]}) + "\n")

    n_items = len({i for b in frame["items"] for i in b})
    print(f"Wrote {len(frame):,} baskets, {n_items} unique items ({source}) -> {out}")


if __name__ == "__main__":
    main()
