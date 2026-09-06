from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    parquet = processed / "telemetry.parquet"
    if not parquet.exists():
        import sys

        sys.path.insert(0, str(ROOT / "data"))
        from fetch_data import generate

        generate(1500, 0.06, 0).to_parquet(parquet, index=False)

    artifacts = ROOT / "backend" / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    for p in artifacts.glob("*"):
        if p.is_file():
            p.unlink()

    from main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_evaluate(client):
    res = client.get("/evaluate")
    assert res.status_code == 200
    body = res.json()
    assert "metrics" in body and "pr_curves" in body
    for name in ("isolation_forest", "lof", "autoencoder", "ensemble"):
        assert "pr_auc" in body["metrics"][name]
        assert body["metrics"][name]["confusion_matrix"]["matrix"]


def test_score(client):
    record = {
        "cpu_pct": 95,
        "mem_pct": 90,
        "disk_io": 500,
        "net_in": 50,
        "net_out": 900,
        "temp_c": 80,
        "latency_ms": 300,
        "error_rate": 0.4,
    }
    res = client.post("/score", json={"records": [record]})
    assert res.status_code == 200
    body = res.json()
    assert len(body["scores"]) == 1
    assert "ensemble" in body["scores"][0]
