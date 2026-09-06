"""RFM feature engineering from transaction history."""

from __future__ import annotations

import pandas as pd

from app.config import DATA_PATH


def load_transactions(path=DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: python data/fetch_data.py from the project root."
        )
    df = pd.read_parquet(path)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    if "line_total" not in df.columns:
        df["line_total"] = df["Quantity"] * df["UnitPrice"]
    return df


def compute_rfm(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Per-customer Recency (days since last purchase), Frequency (n invoices),
    Monetary (sum of line totals). Snapshot = max invoice date in the data.
    """
    snapshot = transactions["InvoiceDate"].max() + pd.Timedelta(days=1)
    grouped = transactions.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda s: (snapshot - s.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("line_total", "sum"),
        last_purchase=("InvoiceDate", "max"),
        n_lines=("InvoiceNo", "count"),
    )
    grouped = grouped.reset_index()
    grouped["CustomerID"] = grouped["CustomerID"].astype(int)
    return grouped
