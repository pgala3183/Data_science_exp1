"""
Prepare small classic-benchmark CSVs for the skills lab.

Uses sklearn built-ins (Iris, Wine) and generates compact Titanic-like,
House-Prices-like, and Adult/Census-like tables so the lab runs offline.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris, load_wine

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "processed"


def write_iris() -> None:
    data = load_iris(as_frame=True)
    df = data.frame
    df.to_csv(PROCESSED / "iris.csv", index=False)


def write_wine() -> None:
    data = load_wine(as_frame=True)
    df = data.frame
    df.to_csv(PROCESSED / "wine.csv", index=False)


def write_titanic(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    n = 600
    pclass = rng.choice([1, 2, 3], size=n, p=[0.2, 0.3, 0.5])
    sex = rng.choice(["male", "female"], size=n, p=[0.65, 0.35])
    age = rng.normal(30, 14, n).clip(1, 80)
    fare = rng.lognormal(2.5, 0.8, n)
    sibsp = rng.integers(0, 4, n)
    parch = rng.integers(0, 3, n)
    embarked = rng.choice(["C", "Q", "S"], size=n, p=[0.2, 0.1, 0.7])
    # Survival odds: female, higher class, higher fare
    logit = (
        -1.2
        + 1.8 * (sex == "female")
        + 0.7 * (pclass == 1)
        - 0.4 * (pclass == 3)
        + 0.01 * fare
        - 0.01 * age
    )
    prob = 1 / (1 + np.exp(-logit))
    survived = (rng.random(n) < prob).astype(int)
    pd.DataFrame(
        {
            "survived": survived,
            "pclass": pclass,
            "sex": sex,
            "age": age.round(1),
            "sibsp": sibsp,
            "parch": parch,
            "fare": fare.round(2),
            "embarked": embarked,
        }
    ).to_csv(PROCESSED / "titanic.csv", index=False)


def write_housing(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    n = 800
    sqft = rng.normal(1800, 500, n).clip(600, 4500)
    beds = rng.integers(1, 6, n)
    baths = rng.integers(1, 5, n)
    age = rng.integers(0, 80, n)
    dist = rng.uniform(0.5, 25, n)
    price = (
        80_000
        + 160 * sqft
        + 15_000 * beds
        + 20_000 * baths
        - 800 * age
        - 2500 * dist
        + rng.normal(0, 25_000, n)
    ).clip(50_000, None)
    pd.DataFrame(
        {
            "sqft": sqft.round(0),
            "bedrooms": beds,
            "bathrooms": baths,
            "house_age": age,
            "dist_to_center": dist.round(2),
            "sale_price": price.round(0),
        }
    ).to_csv(PROCESSED / "housing.csv", index=False)


def write_adult(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    n = 1000
    age = rng.integers(18, 70, n)
    education_num = rng.integers(1, 17, n)
    hours = rng.integers(10, 80, n)
    capital_gain = rng.choice([0, 0, 0, 5000, 15000], size=n)
    sex = rng.choice(["Male", "Female"], size=n)
    # Income >50K more likely with education, hours, capital
    logit = -6 + 0.25 * education_num + 0.03 * hours + 0.00008 * capital_gain + 0.01 * age
    high = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    pd.DataFrame(
        {
            "age": age,
            "education_num": education_num,
            "hours_per_week": hours,
            "capital_gain": capital_gain,
            "sex": sex,
            "income_gt_50k": high,
        }
    ).to_csv(PROCESSED / "adult.csv", index=False)


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    write_iris()
    write_wine()
    write_titanic()
    write_housing()
    write_adult()
    print(f"Wrote benchmark CSVs to {PROCESSED}")
    for p in sorted(PROCESSED.glob("*.csv")):
        print(f"  {p.name}: {sum(1 for _ in open(p, encoding='utf-8')) - 1} rows")


if __name__ == "__main__":
    main()
