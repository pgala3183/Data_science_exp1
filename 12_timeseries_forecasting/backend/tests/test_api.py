from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    parquet = processed / "retail_sales.parquet"
    if not parquet.exists():
        import sys

        sys.path.insert(0, str(ROOT / "data"))
        from fetch_data import generate

        # Shorter series for faster tests
        generate("2021-01-01", "2022-12-31", 0).to_parquet(parquet, index=False)

    artifacts = ROOT / "backend" / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    for p in artifacts.glob("*"):
        if p.is_file():
            p.unlink()

    # Speed up backtest in tests
    import app.config as cfg

    cfg.MIN_TRAIN = 200
    cfg.STEP = 60
    cfg.HORIZONS = (1, 7)

    from main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_acf_pacf(client):
    res = client.get("/acf-pacf")
    assert res.status_code == 200
    body = res.json()
    assert len(body["lags"]) == len(body["acf"]) == len(body["pacf"])
    assert body["lags"][-1] >= 40 or len(body["lags"]) > 1


def test_forecast(client):
    res = client.get("/forecast")
    assert res.status_code == 200
    body = res.json()
    assert body["series"]
    assert len(body["forecasts"]) >= 2
    models = {f["model"] for f in body["forecasts"]}
    assert "sarima" in models and "gb_lags" in models
    for f in body["forecasts"]:
        for h in f["horizons"]:
            assert h["points"]
            p = h["points"][-1]
            assert "yhat" in p and "yhat_lower" in p and "yhat_upper" in p
            assert p["yhat_lower"] <= p["yhat"] <= p["yhat_upper"]


def test_backtest(client):
    res = client.get("/backtest")
    assert res.status_code == 200
    body = res.json()
    assert body["method"] == "rolling_origin"
    assert body["metrics"]
    for row in body["metrics"]:
        assert row["n"] >= 0
        if row["n"] > 0:
            assert row["mae"] is not None
