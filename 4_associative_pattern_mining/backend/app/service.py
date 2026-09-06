"""Cached mining state for the API."""

from __future__ import annotations

from app.config import DEFAULT_MIN_CONFIDENCE, DEFAULT_MIN_SUPPORT
from app.mining import MiningResult, mine_rules

_STATE: MiningResult | None = None


def get_result(
    *,
    refresh: bool = False,
    min_support: float = DEFAULT_MIN_SUPPORT,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> MiningResult:
    global _STATE
    if _STATE is None or refresh:
        _STATE = mine_rules(
            min_support=min_support,
            min_confidence=min_confidence,
            primary="fpgrowth",
        )
    return _STATE


def clear_cache() -> None:
    global _STATE
    _STATE = None
