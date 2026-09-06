from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    parquet = processed / "transactions.parquet"
    if not parquet.exists():
        import sys

        sys.path.insert(0, str(ROOT / "data"))
        from fetch_data import clean_transactions, generate_synthetic

        clean_transactions(generate_synthetic(400, seed=0)).to_parquet(parquet, index=False)

    from main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_segments(client):
    res = client.get("/segments?method=kmeans")
    assert res.status_code == 200
    body = res.json()
    assert body["k"] >= 2
    assert len(body["projection"]) == body["n_customers"]
    assert len(body["profiles"]) == body["k"]
    assert len(body["silhouette_curve"]) >= 2
    assert body["alternative_method"] == "agglomerative"


def test_segment_customers(client):
    segs = client.get("/segments").json()
    cid = segs["profiles"][0]["cluster_id"]
    res = client.get(f"/segments/{cid}/customers?limit=5")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert len(body["customers"]) <= 5
