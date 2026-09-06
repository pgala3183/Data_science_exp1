from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    parquet = processed / "baskets.parquet"
    if not parquet.exists():
        import sys

        sys.path.insert(0, str(ROOT / "data"))
        from fetch_data import baskets_to_frame, generate_baskets

        baskets_to_frame(generate_baskets(800, seed=1)).to_parquet(parquet, index=False)

    from main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_rules_pagination(client):
    res = client.get("/rules?page=1&page_size=5&sort_by=lift&min_lift=1")
    assert res.status_code == 200
    body = res.json()
    assert body["page"] == 1
    assert len(body["rules"]) <= 5
    assert len(body["benchmarks"]) == 2


def test_graph(client):
    res = client.get("/graph?min_lift=1&max_edges=30")
    assert res.status_code == 200
    body = res.json()
    assert "nodes" in body and "edges" in body


def test_recommend(client):
    items = client.get("/items").json()["items"]
    basket = items[:2]
    res = client.post("/recommend", json={"basket": basket, "top_n": 5})
    assert res.status_code == 200
    assert res.json()["basket"] == basket
