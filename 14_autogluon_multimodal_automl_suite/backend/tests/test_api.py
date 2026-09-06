"""API smoke tests with shortened training budgets."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import app.config as cfg
    import app.service as svc

    art = tmp_path_factory.mktemp("mm_artifacts")
    cfg.ARTIFACTS = art
    cfg.UPLOADS = art / "uploads"
    cfg.META_PATH = art / "meta.json"
    cfg.MM_DIR = art / "multimodal"
    cfg.TABULAR_DIR = art / "tabular"
    cfg.TEXT_DIR = art / "text"
    cfg.IMAGE_DIR = art / "image"
    cfg.MM_TIME_LIMIT_SEC = 90
    cfg.IMAGE_TIME_LIMIT_SEC = 60
    cfg.TABULAR_TIME_LIMIT_SEC = 30
    cfg.TEXT_TIME_LIMIT_SEC = 30
    cfg.N_SAMPLES = 120

    for name in (
        "ARTIFACTS",
        "UPLOADS",
        "META_PATH",
        "MM_DIR",
        "TABULAR_DIR",
        "TEXT_DIR",
        "IMAGE_DIR",
        "MM_TIME_LIMIT_SEC",
        "IMAGE_TIME_LIMIT_SEC",
        "TABULAR_TIME_LIMIT_SEC",
        "TEXT_TIME_LIMIT_SEC",
        "N_SAMPLES",
        "DATA_PATH",
        "IMAGES_DIR",
    ):
        setattr(svc, name, getattr(cfg, name))

    svc._predictors = {}
    svc._meta = None

    import sys

    sys.path.insert(0, str(ROOT / "data"))
    from generate_products import generate

    cfg.DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    generate(n=cfg.N_SAMPLES, seed=0).to_csv(cfg.DATA_PATH, index=False)
    svc.DATA_PATH = cfg.DATA_PATH

    from fastapi.testclient import TestClient
    from main import STATE, app

    with TestClient(app) as c:
        assert STATE["ready"] is True, STATE.get("error")
        yield c


def _fake_jpeg() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (64, 64), (40, 90, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def test_health(client):
    body = client.get("/health").json()
    assert body["ok"] is True


def test_metrics(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    body = res.json()
    assert "multimodal" in body["accuracies"]
    assert "tabular_only" in body["accuracies"]
    assert "text_only" in body["accuracies"]
    assert "lift_vs_best_baseline" in body


def test_predict(client):
    files = {"image": ("sample.jpg", _fake_jpeg(), "image/jpeg")}
    data = {
        "description": "Wireless earbuds. compact gadget with rechargeable battery.",
        "price": "79.99",
        "rating": "4.2",
        "brand_tier": "mid",
        "weight_oz": "3.5",
        "is_fragile": "1",
    }
    res = client.post("/predict", files=files, data=data)
    assert res.status_code == 200, res.text
    body = res.json()
    assert "prediction" in body["multimodal"]
    assert "text_only" in body["baselines"]
    assert "tabular_only" in body["baselines"]
    assert "image_only" in body["baselines"]
