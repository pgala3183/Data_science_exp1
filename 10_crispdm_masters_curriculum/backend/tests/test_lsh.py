"""Tests for custom cosine LSH."""

from __future__ import annotations

import numpy as np

from app.lsh import CosineLSH, _l2_normalize


def test_lsh_returns_self_as_top_neighbor():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(200, 16))
    lsh = CosineLSH(n_bits=12, n_tables=6, seed=0).fit(X)
    q = X[7]
    idx, sims, n_cand = lsh.query(q, k=5)
    assert n_cand >= 1
    assert idx[0] == 7
    assert sims[0] > 0.99


def test_lsh_orders_by_cosine():
    rng = np.random.default_rng(1)
    base = rng.normal(size=32)
    X = np.vstack(
        [
            base,
            base + 0.01 * rng.normal(size=32),
            rng.normal(size=32),
            -base,
        ]
    )
    # Pad with noise rows
    X = np.vstack([X, rng.normal(size=(50, 32))])
    lsh = CosineLSH(n_bits=10, n_tables=8, seed=2).fit(X)
    idx, sims, _ = lsh.query(base, k=3)
    # Nearest should be exact / near duplicate (rows 0 or 1)
    assert idx[0] in (0, 1)
    assert len(sims) >= 2
    assert sims[0] >= sims[1]
    if len(sims) >= 3:
        assert sims[1] >= sims[2]


def test_l2_normalize_unit_norm():
    X = np.array([[3.0, 4.0], [0.0, 2.0]])
    N = _l2_normalize(X)
    norms = np.linalg.norm(N, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-6)
