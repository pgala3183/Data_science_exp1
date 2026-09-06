from __future__ import annotations

from pydantic import BaseModel, Field


class IntervalPoint(BaseModel):
    ds: str
    yhat: float
    yhat_lower: float
    yhat_upper: float


class HorizonForecast(BaseModel):
    horizon: int
    points: list[IntervalPoint]


class ModelForecast(BaseModel):
    model: str
    horizons: list[HorizonForecast]


class ForecastResponse(BaseModel):
    series: list[dict] = Field(description="Historical {ds, y} points (tail for chart)")
    forecasts: list[ModelForecast]
    last_train_ds: str
    alpha: float = 0.05


class MetricRow(BaseModel):
    model: str
    horizon: int
    mae: float | None
    rmse: float | None
    mape: float | None
    n: int


class BacktestResponse(BaseModel):
    method: str
    metrics: list[MetricRow]
    note: str


class AcfPacfResponse(BaseModel):
    lags: list[int]
    acf: list[float]
    pacf: list[float]
    acf_ci: float
    n: int
    interpretation: str
