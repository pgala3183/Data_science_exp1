"""
Fetch Online Retail (UCI) if reachable, else generate synthetic e-commerce
transactions with clear RFM structure (Champions, Loyal, At-Risk, New, Lost).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"

# Classic UCI Online Retail Excel mirror (may fail offline)
UCI_URLS = [
    "https://raw.githubusercontent.com/databricks/Spark-The-Definitive-Guide/master/data/retail-data/all/online-retail-dataset.csv",
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx",
]


def generate_synthetic(n_customers: int = 800, seed: int = 42) -> pd.DataFrame:
    """Transactions whose per-customer RFM naturally forms distinct groups."""
    rng = np.random.default_rng(seed)
    # Persona mix
    personas = rng.choice(
        ["champion", "loyal", "at_risk", "new", "hibernating"],
        size=n_customers,
        p=[0.15, 0.25, 0.2, 0.2, 0.2],
    )
    snapshot = pd.Timestamp("2024-12-31")
    rows = []
    invoice_id = 10000

    for cid, persona in enumerate(personas, start=1):
        if persona == "champion":
            n_tx = int(rng.integers(12, 30))
            recency_days = int(rng.integers(1, 20))
            avg_spend = float(rng.uniform(80, 250))
        elif persona == "loyal":
            n_tx = int(rng.integers(6, 15))
            recency_days = int(rng.integers(10, 45))
            avg_spend = float(rng.uniform(40, 120))
        elif persona == "at_risk":
            n_tx = int(rng.integers(4, 12))
            recency_days = int(rng.integers(60, 150))
            avg_spend = float(rng.uniform(50, 180))
        elif persona == "new":
            n_tx = int(rng.integers(1, 3))
            recency_days = int(rng.integers(1, 30))
            avg_spend = float(rng.uniform(20, 90))
        else:  # hibernating
            n_tx = int(rng.integers(1, 4))
            recency_days = int(rng.integers(120, 365))
            avg_spend = float(rng.uniform(15, 70))

        last_date = snapshot - pd.Timedelta(days=recency_days)
        # Spread earlier purchases backward from last_date
        for j in range(n_tx):
            days_back = int(rng.integers(0, max(1, 30 * n_tx))) if j > 0 else 0
            dt = last_date - pd.Timedelta(days=days_back)
            qty = int(rng.integers(1, 6))
            price = avg_spend / qty * float(rng.uniform(0.7, 1.3))
            invoice_id += 1
            rows.append(
                {
                    "InvoiceNo": f"INV{invoice_id}",
                    "StockCode": f"SKU{rng.integers(1, 500):04d}",
                    "Description": f"Item {persona}",
                    "Quantity": qty,
                    "InvoiceDate": dt,
                    "UnitPrice": round(price, 2),
                    "CustomerID": float(cid),
                    "Country": "United Kingdom",
                    "persona_true": persona,  # for validation only — not used in clustering features
                }
            )

    df = pd.DataFrame(rows)
    return df.sort_values("InvoiceDate").reset_index(drop=True)


def try_download_uci() -> pd.DataFrame | None:
    for url in UCI_URLS:
        try:
            print(f"Trying {url} ...")
            if url.endswith(".xlsx"):
                df = pd.read_excel(url)
            else:
                df = pd.read_csv(url, encoding="latin1")
            # Normalize columns
            rename = {
                "Invoice": "InvoiceNo",
                "Invoice Date": "InvoiceDate",
                "Customer ID": "CustomerID",
            }
            df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
            needed = {"InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"}
            if not needed.issubset(df.columns):
                print(f"Missing columns from {url}")
                continue
            df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
            print(f"Loaded {len(df):,} rows from remote source")
            return df
        except Exception as exc:  # noqa: BLE001
            print(f"Failed: {exc}")
    return None


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.dropna(subset=["CustomerID"])
    out["CustomerID"] = out["CustomerID"].astype(int)
    out = out[out["Quantity"] > 0]
    out = out[out["UnitPrice"] > 0]
    # Drop cancellations if invoice starts with C
    out = out[~out["InvoiceNo"].astype(str).str.startswith("C")]
    out["InvoiceDate"] = pd.to_datetime(out["InvoiceDate"])
    out["line_total"] = out["Quantity"] * out["UnitPrice"]
    return out.reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--n-customers", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    df = None
    source = "synthetic"
    if not args.synthetic_only:
        df = try_download_uci()
        if df is not None:
            source = "uci_or_mirror"

    if df is None:
        print(f"Generating synthetic retail transactions (n_customers={args.n_customers})")
        df = generate_synthetic(n_customers=args.n_customers, seed=args.seed)

    clean = clean_transactions(df)
    # Keep persona only if present (synthetic); strip before modeling in pipeline
    out_path = PROCESSED / "transactions.parquet"
    clean.to_parquet(out_path, index=False)
    clean.head(200).to_csv(PROCESSED / "transactions_preview.csv", index=False)
    print(f"Wrote {len(clean):,} rows ({source}) -> {out_path}")
    print(f"Unique customers: {clean['CustomerID'].nunique():,}")


if __name__ == "__main__":
    main()
