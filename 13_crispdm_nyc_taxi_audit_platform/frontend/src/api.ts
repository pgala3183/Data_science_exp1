import type {
  AuditResponse,
  BusinessPayload,
  EdaPayload,
  EvalPayload,
  MonitoringPayload,
  PipelinePayload,
  PredictResult,
  SchemaPayload,
} from "./types";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json();
}

export const fetchBusiness = () => getJson<BusinessPayload>("/business");
export const fetchEda = () => getJson<EdaPayload>("/eda");
export const fetchPipeline = () => getJson<PipelinePayload>("/pipeline");
export const fetchEvaluate = () => getJson<EvalPayload>("/evaluate");
export const fetchSchema = () => getJson<SchemaPayload>("/schema");
export const fetchAudit = () => getJson<AuditResponse>("/audit");

export async function fetchMonitoring(
  driftMode: string = "moderate",
  n = 3000,
): Promise<MonitoringPayload> {
  return getJson<MonitoringPayload>(`/monitoring?drift_mode=${driftMode}&n=${n}`);
}

export async function predictTrip(body: {
  pickup_latitude: number;
  pickup_longitude: number;
  dropoff_latitude: number;
  dropoff_longitude: number;
  pickup_datetime: string;
  passenger_count: number;
}): Promise<PredictResult> {
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Predict failed");
  return res.json();
}
