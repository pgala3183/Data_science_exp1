from pydantic import BaseModel, Field


class Centroid(BaseModel):
    Recency: float
    Frequency: float
    Monetary: float


class SegmentProfile(BaseModel):
    cluster_id: int
    name: str
    description: str
    marketing_actions: list[str]
    centroid: Centroid
    size: int = 0


class ProjectionPoint(BaseModel):
    customer_id: int
    cluster_id: int
    pc1: float
    pc2: float
    Recency: float
    Frequency: float
    Monetary: float


class CurvePoint(BaseModel):
    k: int
    inertia: float | None = None
    silhouette: float | None = None


class SegmentsResponse(BaseModel):
    method: str
    k: int
    silhouette: float
    chosen_reason: str
    profiles: list[SegmentProfile]
    projection: list[ProjectionPoint]
    inertia_curve: list[CurvePoint]
    silhouette_curve: list[CurvePoint]
    alternative_method: str
    alternative_silhouette: float
    n_customers: int


class CustomerRow(BaseModel):
    customer_id: int
    Recency: float
    Frequency: float
    Monetary: float
    cluster_id: int


class SegmentCustomersResponse(BaseModel):
    cluster_id: int
    name: str
    total: int
    customers: list[CustomerRow]
