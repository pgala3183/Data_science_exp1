"""Unit tests for clean sample."""

from train import run


def test_run_returns_score():
    score = run()
    assert 0.0 <= score <= 1.0
