"""API smoke tests — train a tiny AutoGluon run once per session."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import app.config as cfg
    import app.service as svc

    art = tmp_path_factory.mktemp("ag_artifacts")
    cfg.ARTIFACTS = art
    cfg.PREDICTOR_DIR = art / "predictor"
    cfg.META_PATH = art / "meta.json"
    cfg.TIME_LIMIT_SEC = 45
    cfg.NUM_BAG_FOLDS = 2
    cfg.NUM_STACK_LEVELS = 1
    cfg.PRESETS = "medium_quality"

    svc.ARTIFACTS = cfg.ARTIFACTS
    svc.PREDICTOR_DIR = cfg.PREDICTOR_DIR
    svc.META_PATH = cfg.META_PATH
    svc.TIME_LIMIT_SEC = cfg.TIME_LIMIT_SEC
    svc.NUM_BAG_FOLDS = cfg.NUM_BAG_FOLDS
    svc.NUM_STACK_LEVELS = cfg.NUM_STACK_LEVELS
    svc.PRESETS = cfg.PRESETS
    svc._predictor = None
    svc._meta = None

    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    parquet = processed / "adult.parquet"
    if not parquet.exists():
        import sys

        sys.path.insert(0, str(ROOT / "data"))
        from fetch_data import fetch_adult

        fetch_adult(n=1200, seed=0).to_parquet(parquet, index=False)

    from fastapi.testclient import TestClient
    from main import STATE, app

    with TestClient(app) as c:
        STATE["ready"] = True
        yield c


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_leaderboard(client):
    res = client.get("/leaderboard")
    assert res.status_code == 200
    body = res.json()
    assert body["leaderboard"]
    assert "stack_architecture" in body
    row = body["leaderboard"][0]
    assert "model" in row and "score_val" in row


def test_predict(client):
    schema = client.get("/schema").json()["schema"]
    record = {f["name"]: f["example"] for f in schema}
    res = client.post("/predict", json={"record": record, "include_base_models": True})
    assert res.status_code == 200
    body = res.json()
    assert "prediction" in body
    assert body["probabilities"]
    assert body["per_model_predictions"]


def test_explain(client):
    res = client.get("/explain")
    assert res.status_code == 200
    body = res.json()
    assert body["method"] == "permutation_importance"
