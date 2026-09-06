"""K-Means (+ elbow/silhouette) and Agglomerative clustering on scaled RFM."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.config import K_RANGE, RANDOM_STATE


RFM_FEATURES = ["Recency", "Frequency", "Monetary"]


@dataclass
class ClusterResult:
    method: str
    k: int
    labels: np.ndarray
    centers_scaled: np.ndarray | None
    centers_original: pd.DataFrame
    silhouette: float
    inertia_curve: list[dict]
    silhouette_curve: list[dict]
    projection: np.ndarray
    scaler: StandardScaler
    chosen_reason: str


def _elbow_silhouette(X: np.ndarray) -> tuple[list[dict], list[dict], int, str]:
    inertias: list[dict] = []
    silhouettes: list[dict] = []
    best_k = 3
    best_sil = -1.0

    for k in K_RANGE:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X)
        inertias.append({"k": k, "inertia": float(km.inertia_)})
        sil = float(silhouette_score(X, labels))
        silhouettes.append({"k": k, "silhouette": sil})
        if sil > best_sil:
            best_sil = sil
            best_k = k

    # Prefer silhouette max; note elbow as secondary narrative
    reason = (
        f"Selected k={best_k} by maximum average silhouette "
        f"({best_sil:.3f}) over k in {list(K_RANGE)}; inertia curve shown for elbow context."
    )
    return inertias, silhouettes, best_k, reason


def run_kmeans(rfm: pd.DataFrame) -> ClusterResult:
    scaler = StandardScaler()
    X = scaler.fit_transform(rfm[RFM_FEATURES])
    inertias, silhouettes, best_k, reason = _elbow_silhouette(X)

    model = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
    labels = model.fit_predict(X)
    sil = float(silhouette_score(X, labels))

    centers_scaled = model.cluster_centers_
    centers_original = pd.DataFrame(
        scaler.inverse_transform(centers_scaled),
        columns=RFM_FEATURES,
    )
    centers_original.insert(0, "cluster_id", range(best_k))

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    projection = pca.fit_transform(X)

    return ClusterResult(
        method="kmeans",
        k=best_k,
        labels=labels,
        centers_scaled=centers_scaled,
        centers_original=centers_original,
        silhouette=sil,
        inertia_curve=inertias,
        silhouette_curve=silhouettes,
        projection=projection,
        scaler=scaler,
        chosen_reason=reason,
    )


def run_agglomerative(rfm: pd.DataFrame, n_clusters: int) -> ClusterResult:
    scaler = StandardScaler()
    X = scaler.fit_transform(rfm[RFM_FEATURES])
    model = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
    labels = model.fit_predict(X)
    sil = float(silhouette_score(X, labels))

    # Centroids = mean of members in original space
    tmp = rfm[RFM_FEATURES].copy()
    tmp["cluster_id"] = labels
    centers_original = tmp.groupby("cluster_id")[RFM_FEATURES].mean().reset_index()

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    projection = pca.fit_transform(X)

    return ClusterResult(
        method="agglomerative",
        k=n_clusters,
        labels=labels,
        centers_scaled=None,
        centers_original=centers_original,
        silhouette=sil,
        inertia_curve=[],
        silhouette_curve=[],
        projection=projection,
        scaler=scaler,
        chosen_reason=f"Ward agglomerative with k={n_clusters} (aligned to K-Means choice for comparison).",
    )


def label_segments(centers: pd.DataFrame) -> list[dict]:
    """
    Map cluster centroids to plain-language RFM personas + marketing actions.
    Uses relative ranking across clusters (low recency = more recent).
    """
    c = centers.copy()
    # Ranks: lower Recency is better; higher F/M better
    c["r_rank"] = c["Recency"].rank(ascending=True)  # 1 = most recent
    c["f_rank"] = c["Frequency"].rank(ascending=False)
    c["m_rank"] = c["Monetary"].rank(ascending=False)
    c["value_score"] = c["f_rank"] + c["m_rank"] + c["r_rank"]

    profiles = []
    for _, row in c.sort_values("cluster_id").iterrows():
        cid = int(row["cluster_id"])
        r, f, m = float(row["Recency"]), float(row["Frequency"]), float(row["Monetary"])
        # Heuristic naming
        if row["r_rank"] <= 2 and row["f_rank"] <= 2 and row["m_rank"] <= 2:
            name = "Champions"
            blurb = "Recent, frequent, high spenders — your best customers."
            actions = [
                "Invite to loyalty / VIP program",
                "Ask for referrals and reviews",
                "Early access to new products",
            ]
        elif row["r_rank"] <= 2 and row["f_rank"] >= c["f_rank"].median():
            name = "New / Promising"
            blurb = "Bought recently but still building habit frequency."
            actions = [
                "Onboarding email series",
                "Starter discounts on second purchase",
                "Educate on category bestsellers",
            ]
        elif row["r_rank"] >= c["r_rank"].median() and row["m_rank"] <= 2:
            name = "At Risk High Value"
            blurb = "Historically valuable but going quiet — win-back priority."
            actions = [
                "Personalized win-back offer",
                "Survey why they left",
                "Remind of loyalty points / credit",
            ]
        elif row["f_rank"] <= 2 and row["r_rank"] <= 3:
            name = "Loyal Regulars"
            blurb = "Steady repeat buyers with solid spend."
            actions = [
                "Upsell bundles",
                "Subscription or replenishment reminders",
                "Cross-sell adjacent categories",
            ]
        else:
            name = "Hibernating / Low Engagement"
            blurb = "Infrequent and/or distant last purchase with lower monetary value."
            actions = [
                "Low-cost reactivation campaign",
                "Clearance / entry-price offers",
                "Suppress from premium channels if unresponsive",
            ]

        profiles.append(
            {
                "cluster_id": cid,
                "name": name,
                "description": blurb,
                "marketing_actions": actions,
                "centroid": {
                    "Recency": round(r, 1),
                    "Frequency": round(f, 2),
                    "Monetary": round(m, 2),
                },
            }
        )
    return profiles
