"""Customer segmentation API."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import DATA_PATH, PORT  # noqa: E402
from app.schemas import (  # noqa: E402
    Centroid,
    CurvePoint,
    CustomerRow,
    ProjectionPoint,
    SegmentCustomersResponse,
    SegmentProfile,
    SegmentsResponse,
)
from app.service import build_segmentation, get_state  # noqa: E402


def ensure_data() -> None:
    if not DATA_PATH.exists():
        root = BACKEND_DIR.parent
        sys.path.insert(0, str(root / "data"))
        from fetch_data import clean_transactions, generate_synthetic

        processed = root / "data" / "processed"
        processed.mkdir(parents=True, exist_ok=True)
        df = clean_transactions(generate_synthetic(n_customers=600, seed=42))
        df.to_parquet(processed / "transactions.parquet", index=False)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_data()
    build_segmentation(method="kmeans")
    yield


app = FastAPI(
    title="Customer Segmentation API",
    description="RFM + K-Means / Agglomerative clustering",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "port": PORT}


@app.get("/segments", response_model=SegmentsResponse)
def segments(method: str = Query("kmeans", pattern="^(kmeans|agglomerative)$")):
    try:
        state = get_state(method=method)
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e

    primary = state["primary"]
    alt = state["alternative"]
    chosen = state["chosen"]
    rfm = state["rfm"]

    size_map = rfm["cluster_id"].value_counts().to_dict()
    profiles = [
        SegmentProfile(
            cluster_id=p["cluster_id"],
            name=p["name"],
            description=p["description"],
            marketing_actions=p["marketing_actions"],
            centroid=Centroid(**p["centroid"]),
            size=int(size_map.get(p["cluster_id"], 0)),
        )
        for p in state["profiles"]
    ]

    projection = [
        ProjectionPoint(
            customer_id=int(row.CustomerID),
            cluster_id=int(row.cluster_id),
            pc1=float(row.pc1),
            pc2=float(row.pc2),
            Recency=float(row.Recency),
            Frequency=float(row.Frequency),
            Monetary=float(row.Monetary),
        )
        for row in rfm.itertuples()
    ]

    return SegmentsResponse(
        method=chosen.method,
        k=chosen.k,
        silhouette=chosen.silhouette,
        chosen_reason=primary.chosen_reason,
        profiles=profiles,
        projection=projection,
        inertia_curve=[CurvePoint(k=p["k"], inertia=p["inertia"]) for p in primary.inertia_curve],
        silhouette_curve=[
            CurvePoint(k=p["k"], silhouette=p["silhouette"]) for p in primary.silhouette_curve
        ],
        alternative_method=alt.method,
        alternative_silhouette=alt.silhouette,
        n_customers=len(rfm),
    )


@app.get("/segments/{cluster_id}/customers", response_model=SegmentCustomersResponse)
def segment_customers(
    cluster_id: int,
    limit: int = Query(25, ge=1, le=200),
    method: str = Query("kmeans", pattern="^(kmeans|agglomerative)$"),
):
    state = get_state(method=method)
    rfm = state["rfm"]
    subset = rfm[rfm["cluster_id"] == cluster_id]
    if subset.empty:
        raise HTTPException(404, f"No customers in cluster {cluster_id}")

    name = next(
        (p["name"] for p in state["profiles"] if p["cluster_id"] == cluster_id),
        f"Segment {cluster_id}",
    )
    sample = subset.nsmallest(limit, "Recency")
    customers = [
        CustomerRow(
            customer_id=int(r.CustomerID),
            Recency=float(r.Recency),
            Frequency=float(r.Frequency),
            Monetary=float(r.Monetary),
            cluster_id=int(r.cluster_id),
        )
        for r in sample.itertuples()
    ]
    return SegmentCustomersResponse(
        cluster_id=cluster_id,
        name=name,
        total=len(subset),
        customers=customers,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
