from pydantic import BaseModel, Field


class ScoreRecord(BaseModel):
    cpu_pct: float = Field(..., ge=0, le=120)
    mem_pct: float = Field(..., ge=0, le=120)
    disk_io: float = Field(..., ge=0)
    net_in: float = Field(..., ge=0)
    net_out: float = Field(..., ge=0)
    temp_c: float = Field(..., ge=0, le=120)
    latency_ms: float = Field(..., ge=0)
    error_rate: float = Field(..., ge=0, le=1)


class ScoreRequest(BaseModel):
    records: list[ScoreRecord] = Field(..., min_length=1, max_length=200)


class ScoreItem(BaseModel):
    isolation_forest: float
    lof: float
    autoencoder: float
    ensemble: float
    flagged_by: list[str]


class ScoreResponse(BaseModel):
    scores: list[ScoreItem]
    thresholds: dict[str, float]
