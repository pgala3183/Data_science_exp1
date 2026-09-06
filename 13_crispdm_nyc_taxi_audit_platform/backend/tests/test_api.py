import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["ready"] is True


def test_crispdm_endpoints(client):
    for path in ("/business", "/eda", "/pipeline", "/models", "/evaluate", "/schema"):
        r = client.get(path)
        assert r.status_code == 200, path


def test_predict(client):
    r = client.post(
        "/predict",
        json={
            "pickup_latitude": 40.758,
            "pickup_longitude": -73.9855,
            "dropoff_latitude": 40.7484,
            "dropoff_longitude": -73.9857,
            "pickup_datetime": "2016-03-15T08:30:00",
            "passenger_count": 1,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["predicted_duration_seconds"] >= 60
    assert "model_name" in body


def test_audit_and_monitoring(client):
    audit = client.get("/audit")
    assert audit.status_code == 200
    body = audit.json()
    assert "overall_score" in body
    assert "letter_grade" in body
    assert len(body["dimensions"]) == 6

    mon = client.get("/monitoring?drift_mode=moderate&n=800")
    assert mon.status_code == 200
    body = mon.json()
    assert body["overall_status"] in {"green", "yellow", "red"}
    assert len(body["features"]) > 0
