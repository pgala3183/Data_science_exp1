import type { ModelMetrics, PredictResponse } from "./types";

export async function fetchMetrics(): Promise<ModelMetrics> {
  const res = await fetch("/api/model/metrics");
  if (!res.ok) throw new Error("Failed to load model metrics");
  return res.json();
}

export async function predictTrip(payload: {
  pickup_latitude: number;
  pickup_longitude: number;
  dropoff_latitude: number;
  dropoff_longitude: number;
  pickup_datetime: string;
  passenger_count: number;
}): Promise<PredictResponse> {
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Prediction failed");
  }
  return res.json();
}
