export type SeriesPoint = { ds: string; y: number };

export type IntervalPoint = {
  ds: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
};

export type HorizonForecast = {
  horizon: number;
  points: IntervalPoint[];
};

export type ModelForecast = {
  model: string;
  horizons: HorizonForecast[];
};

export type ForecastResponse = {
  series: SeriesPoint[];
  forecasts: ModelForecast[];
  last_train_ds: string;
  alpha: number;
};

export type AcfPacfResponse = {
  lags: number[];
  acf: number[];
  pacf: number[];
  acf_ci: number;
  n: number;
  interpretation: string;
};

export type MetricRow = {
  model: string;
  horizon: number;
  mae: number | null;
  rmse: number | null;
  mape: number | null;
  n: number;
};

export type BacktestResponse = {
  method: string;
  metrics: MetricRow[];
  note: string;
};
