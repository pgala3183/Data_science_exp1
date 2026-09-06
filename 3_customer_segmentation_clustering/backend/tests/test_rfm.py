import pandas as pd

from app.clustering import label_segments, run_kmeans
from app.rfm import compute_rfm


def _toy_transactions(n_customers: int = 120) -> pd.DataFrame:
    rows = []
    inv = 1
    for cid in range(1, n_customers + 1):
        # Two rough groups by cid
        n_tx = 8 if cid % 2 == 0 else 2
        for j in range(n_tx):
            inv += 1
            rows.append(
                {
                    "InvoiceNo": f"I{inv}",
                    "Quantity": 2,
                    "InvoiceDate": pd.Timestamp("2024-01-01") + pd.Timedelta(days=cid + j * 3),
                    "UnitPrice": 10.0 if cid % 2 == 0 else 5.0,
                    "CustomerID": cid,
                    "line_total": 20.0 if cid % 2 == 0 else 10.0,
                }
            )
    return pd.DataFrame(rows)


def test_compute_rfm_shape():
    rfm = compute_rfm(_toy_transactions())
    assert set(["CustomerID", "Recency", "Frequency", "Monetary"]).issubset(rfm.columns)
    assert len(rfm) == 120
    assert (rfm["Frequency"] > 0).all()


def test_kmeans_chooses_k_and_projects():
    rfm = compute_rfm(_toy_transactions())
    result = run_kmeans(rfm)
    assert result.k >= 2
    assert len(result.labels) == len(rfm)
    assert result.projection.shape == (len(rfm), 2)
    assert len(result.silhouette_curve) >= 2
    profiles = label_segments(result.centers_original)
    assert len(profiles) == result.k
    assert all("marketing_actions" in p for p in profiles)


def test_persona_column_not_required():
    """Clustering uses only RFM — no leaked persona labels."""
    from app.clustering import RFM_FEATURES

    assert "persona_true" not in RFM_FEATURES
