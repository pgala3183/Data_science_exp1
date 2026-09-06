import type { AcfPacfResponse, BacktestResponse, ForecastResponse } from "./types";

export async function fetchForecast(): Promise<ForecastResponse> {
  const res = await fetch("/api/forecast");
  if (!res.ok) throw new Error("Failed to load forecasts");
  return res.json();
}

export async function fetchAcfPacf(): Promise<AcfPacfResponse> {
  const res = await fetch("/api/acf-pacf");
  if (!res.ok) throw new Error("Failed to load ACF/PACF");
  return res.json();
}

export async function fetchBacktest(): Promise<BacktestResponse> {
  const res = await fetch("/api/backtest");
  if (!res.ok) throw new Error("Failed to load backtest");
  return res.json();
}
