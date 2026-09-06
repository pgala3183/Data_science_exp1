"""Orchestrate RFM + clustering; cache results for API."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.clustering import ClusterResult, label_segments, run_agglomerative, run_kmeans
from app.rfm import compute_rfm, load_transactions


@dataclass
class SegmentationBundle:
    rfm_base: pd.DataFrame
    primary: ClusterResult
    alternative: ClusterResult


_BUNDLE: SegmentationBundle | None = None


def _ensure_bundle() -> SegmentationBundle:
    global _BUNDLE
    if _BUNDLE is not None:
        return _BUNDLE
    tx = load_transactions()
    rfm = compute_rfm(tx)[["CustomerID", "Recency", "Frequency", "Monetary"]].copy()
    primary = run_kmeans(rfm)
    alternative = run_agglomerative(rfm, n_clusters=primary.k)
    _BUNDLE = SegmentationBundle(rfm_base=rfm, primary=primary, alternative=alternative)
    return _BUNDLE


def view_for_method(method: str = "kmeans") -> dict:
    bundle = _ensure_bundle()
    chosen = bundle.primary if method == "kmeans" else bundle.alternative
    labeled = bundle.rfm_base.copy()
    labeled["cluster_id"] = chosen.labels
    labeled["pc1"] = chosen.projection[:, 0]
    labeled["pc2"] = chosen.projection[:, 1]
    profiles = label_segments(chosen.centers_original)
    return {
        "rfm": labeled,
        "primary": bundle.primary,
        "alternative": bundle.alternative,
        "chosen": chosen,
        "profiles": profiles,
        "method": chosen.method,
    }


def build_segmentation(method: str = "kmeans") -> dict:
    global _BUNDLE
    _BUNDLE = None
    return view_for_method(method)


def get_state(method: str = "kmeans") -> dict:
    return view_for_method(method)
