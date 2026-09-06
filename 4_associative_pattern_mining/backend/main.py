"""Market basket association-rules API."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import (  # noqa: E402
    DATA_PATH,
    DEFAULT_MIN_CONFIDENCE,
    DEFAULT_MIN_LIFT,
    DEFAULT_MIN_SUPPORT,
    PORT,
)
from app.mining import filter_sort_rules, recommend_addons, rules_to_graph  # noqa: E402
from app.schemas import (  # noqa: E402
    GraphEdge,
    GraphNode,
    GraphResponse,
    ItemsResponse,
    RecommendRequest,
    RecommendResponse,
    RuleOut,
    RulesResponse,
)
from app.service import get_result  # noqa: E402


def ensure_data() -> None:
    if not DATA_PATH.exists():
        root = BACKEND_DIR.parent
        sys.path.insert(0, str(root / "data"))
        from fetch_data import baskets_to_frame, generate_baskets

        processed = root / "data" / "processed"
        processed.mkdir(parents=True, exist_ok=True)
        frame = baskets_to_frame(generate_baskets(2500, seed=42))
        frame.to_parquet(processed / "baskets.parquet", index=False)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_data()
    get_result()
    yield


app = FastAPI(
    title="Market Basket Mining API",
    description="Apriori + FP-Growth association rules",
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


@app.get("/items", response_model=ItemsResponse)
def list_items():
    result = get_result()
    return ItemsResponse(items=sorted(result.item_counts.keys()))


@app.get("/rules", response_model=RulesResponse)
def rules(
    min_support: float = Query(DEFAULT_MIN_SUPPORT, ge=0.0, le=1.0),
    min_confidence: float = Query(DEFAULT_MIN_CONFIDENCE, ge=0.0, le=1.0),
    min_lift: float = Query(DEFAULT_MIN_LIFT, ge=0.0),
    sort_by: str = Query("lift", pattern="^(lift|confidence|support)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        result = get_result()
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e

    filtered = filter_sort_rules(
        result.rules,
        min_support=min_support,
        min_confidence=min_confidence,
        min_lift=min_lift,
        sort_by=sort_by,
    )
    total = len(filtered)
    start = (page - 1) * page_size
    chunk = filtered.iloc[start : start + page_size]

    out = [
        RuleOut(
            antecedents=list(row.antecedents),
            consequents=list(row.consequents),
            support=round(float(row.support), 4),
            confidence=round(float(row.confidence), 4),
            lift=round(float(row.lift), 4),
        )
        for row in chunk.itertuples()
    ]

    return RulesResponse(
        total=total,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        rules=out,
        n_transactions=result.n_transactions,
        n_items=len(result.item_counts),
        benchmarks=[b.__dict__ for b in result.benchmarks],
    )


@app.get("/graph", response_model=GraphResponse)
def graph(
    min_support: float = Query(DEFAULT_MIN_SUPPORT, ge=0.0, le=1.0),
    min_confidence: float = Query(DEFAULT_MIN_CONFIDENCE, ge=0.0, le=1.0),
    min_lift: float = Query(DEFAULT_MIN_LIFT, ge=0.0),
    max_edges: int = Query(80, ge=10, le=300),
):
    result = get_result()
    filtered = filter_sort_rules(
        result.rules,
        min_support=min_support,
        min_confidence=min_confidence,
        min_lift=min_lift,
        sort_by="lift",
    )
    g = rules_to_graph(filtered, result.item_counts, max_edges=max_edges)
    return GraphResponse(
        nodes=[GraphNode(**n) for n in g["nodes"]],
        edges=[GraphEdge(**e) for e in g["edges"]],
    )


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    result = get_result()
    known = set(result.item_counts)
    unknown = [i for i in req.basket if i not in known]
    if unknown:
        raise HTTPException(400, f"Unknown items: {unknown}")
    recs = recommend_addons(result.rules, req.basket, top_n=req.top_n)
    return RecommendResponse(basket=req.basket, recommendations=recs)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
