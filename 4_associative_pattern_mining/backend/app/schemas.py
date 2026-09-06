from pydantic import BaseModel, Field


class RuleOut(BaseModel):
    antecedents: list[str]
    consequents: list[str]
    support: float
    confidence: float
    lift: float


class RulesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    sort_by: str
    rules: list[RuleOut]
    n_transactions: int
    n_items: int
    benchmarks: list[dict]


class GraphNode(BaseModel):
    id: str
    label: str
    count: int


class GraphEdge(BaseModel):
    source: str
    target: str
    lift: float
    confidence: float
    support: float


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class RecommendRequest(BaseModel):
    basket: list[str] = Field(..., min_length=1)
    top_n: int = Field(8, ge=1, le=30)


class RecommendItem(BaseModel):
    item: str
    score: float
    lift: float
    confidence: float
    support: float
    rule: dict


class RecommendResponse(BaseModel):
    basket: list[str]
    recommendations: list[RecommendItem]


class ItemsResponse(BaseModel):
    items: list[str]
