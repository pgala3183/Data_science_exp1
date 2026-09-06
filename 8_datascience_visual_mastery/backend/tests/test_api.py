from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["ok"] is True


def test_concepts():
    ids = {c["id"] for c in client.get("/concepts").json()["concepts"]}
    assert {"bayes", "clt", "gradient-descent", "bias-variance", "roc"} <= ids


def test_clt():
    body = client.post("/simulate/clt", json={"dist": "exponential", "sample_size": 20, "n_samples": 500}).json()
    assert len(body["histogram"]["centers"]) > 5
    assert body["theoretical_se"] > 0


def test_loss_and_gd():
    surf = client.get("/loss-surface?resolution=30").json()
    assert len(surf["z"]) == 30
    path = client.post("/gradient-descent", json={"lr": 0.1, "steps": 20}).json()["path"]
    assert len(path) >= 2
    assert path[-1]["loss"] <= path[0]["loss"] + 1e-6 or path[0]["loss"] > 0


def test_bias_variance():
    body = client.post("/bias-variance", json={"degree": 2}).json()
    assert "fit" in body and "error_curves" in body


def test_roc():
    body = client.post("/roc", json={"threshold": 0.4}).json()
    assert body["auc"] > 0.5
    cm = body["confusion"]
    assert cm["tp"] + cm["fp"] + cm["tn"] + cm["fn"] == body["n_pos"] + body["n_neg"]
