from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client():
    # Ensure data exists
    import sys

    sys.path.insert(0, str(ROOT / "data"))
    from fetch_data import main as fetch_main

    fetch_main()

    from main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    body = client.get("/health").json()
    assert body["ok"] is True
    assert body["n_skills"] >= 20


def test_list_and_filter(client):
    all_skills = client.get("/skills").json()["skills"]
    assert len(all_skills) >= 20
    eda = client.get("/skills?category=EDA").json()["skills"]
    assert eda and all(s["category"] == "EDA" for s in eda)


def test_run_endpoint(client):
    res = client.post("/skills/cv-kfold-iris/run")
    assert res.status_code == 200
    body = res.json()
    assert body["skill_id"] == "cv-kfold-iris"
    assert "result" in body
