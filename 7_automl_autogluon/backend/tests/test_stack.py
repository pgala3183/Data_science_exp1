"""Unit tests that do not require a full AutoGluon fit."""

from app.service import build_stack_architecture, _stack_level


def test_stack_level_parsing():
    assert _stack_level("LightGBM_BAG_L1") == 1
    assert _stack_level("WeightedEnsemble_L2") == 2
    assert _stack_level("CatBoost_BAG_L3") == 3


def test_stack_architecture_edges():
    names = ["LightGBM_BAG_L1", "XGBoost_BAG_L1", "WeightedEnsemble_L2", "WeightedEnsemble_L3"]
    graph = build_stack_architecture(names)
    assert "1" in graph["levels"] and "2" in graph["levels"]
    assert any(e["to"] == "WeightedEnsemble_L2" for e in graph["edges"])
    assert any(e["from"] == "WeightedEnsemble_L2" and e["to"] == "WeightedEnsemble_L3" for e in graph["edges"])
