from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure data exists before importing app lifespan
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def client():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    parquet = PROCESSED / "trips.parquet"
    if not parquet.exists():
        import sys

        sys.path.insert(0, str(ROOT / "data"))
        from fetch_data import generate_synthetic

        generate_synthetic(n=3000, seed=1).to_parquet(parquet, index=False)

    # Clear stale artifacts so tests retrain on small data
    artifacts = ROOT / "backend" / "artifacts"
    for p in artifacts.glob("*"):
        p.unlink()

    from main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_metrics(client):
    res = client.get("/model/metrics")
    assert res.status_code == 200
    body = res.json()
    assert body["split"] == "time_based"
    assert len(body["models"]) >= 2
    names = {m["name"] for m in body["models"]}
    assert "ridge" in names
    assert "hist_gradient_boosting" in names


def test_predict(client):
    res = client.post(
        "/predict",
        json={
            "pickup_latitude": 40.758,
            "pickup_longitude": -73.9855,
            "dropoff_latitude": 40.6413,
            "dropoff_longitude": -73.7781,
            "pickup_datetime": "2016-03-15T08:30:00",
            "passenger_count": 1,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["predicted_duration_seconds"] >= 60
    lo, hi = body["confidence_interval_95_seconds"]
    assert lo <= body["predicted_duration_seconds"] <= hi
    assert len(body["top_features"]) > 0
