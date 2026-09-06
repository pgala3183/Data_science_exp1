"""Cosine LSH via random hyperplanes (implemented in-repo, not a library)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def _l2_normalize(X: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(norms, eps)


@dataclass
class CosineLSH:
    """
    Locality-sensitive hashing for cosine similarity.

    Each table uses `n_bits` random hyperplanes. A vector hashes to the bit
    string of projection signs. Candidates are unioned across tables, then
    ranked by exact cosine similarity.
    """

    n_bits: int = 16
    n_tables: int = 8
    seed: int = 42
    planes: list[np.ndarray] = field(default_factory=list)
    tables: list[dict[int, list[int]]] = field(default_factory=list)
    X: np.ndarray | None = None
    X_norm: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> CosineLSH:
        X = np.asarray(X, dtype=np.float64)
        n_features = X.shape[1]
        rng = np.random.default_rng(self.seed)
        self.planes = [
            rng.normal(size=(self.n_bits, n_features)).astype(np.float64)
            for _ in range(self.n_tables)
        ]
        self.X = X
        self.X_norm = _l2_normalize(X)
        self.tables = [self._build_table(i) for i in range(self.n_tables)]
        return self

    def _hash_codes(self, X: np.ndarray, table_idx: int) -> np.ndarray:
        proj = X @ self.planes[table_idx].T
        bits = (proj >= 0).astype(np.uint64)
        # Pack bits into an integer code
        codes = np.zeros(X.shape[0], dtype=np.uint64)
        for b in range(self.n_bits):
            codes |= bits[:, b] << np.uint64(b)
        return codes

    def _build_table(self, table_idx: int) -> dict[int, list[int]]:
        assert self.X is not None
        codes = self._hash_codes(self.X, table_idx)
        buckets: dict[int, list[int]] = {}
        for i, code in enumerate(codes.tolist()):
            buckets.setdefault(int(code), []).append(i)
        return buckets

    def query(
        self,
        q: np.ndarray,
        k: int = 5,
        candidate_mult: int = 20,
    ) -> tuple[np.ndarray, np.ndarray, int]:
        """
        Return (indices, cosine_sims, n_candidates) for the top-k neighbors.
        """
        if self.X is None or self.X_norm is None:
            raise RuntimeError("LSH index is not fitted")
        q = np.asarray(q, dtype=np.float64).reshape(1, -1)
        q_norm = _l2_normalize(q)[0]

        candidates: set[int] = set()
        for t in range(self.n_tables):
            code = int(self._hash_codes(q, t)[0])
            candidates.update(self.tables[t].get(code, []))

        # Hamming-1 probes until we have enough candidates
        if len(candidates) < max(k * candidate_mult, k):
            for t in range(self.n_tables):
                code = int(self._hash_codes(q, t)[0])
                for bit in range(self.n_bits):
                    flipped = code ^ (1 << bit)
                    candidates.update(self.tables[t].get(flipped, []))
                if len(candidates) >= max(k * candidate_mult, k):
                    break

        if len(candidates) < k:
            # Absolute fallback: exact cosine against all rows
            sims_all = self.X_norm @ q_norm
            order = np.argsort(-sims_all)[:k]
            return order, sims_all[order], int(self.X.shape[0])

        idx = np.fromiter(candidates, dtype=np.int64)
        sims = self.X_norm[idx] @ q_norm
        order = np.argsort(-sims)[:k]
        return idx[order], sims[order], int(len(candidates))
