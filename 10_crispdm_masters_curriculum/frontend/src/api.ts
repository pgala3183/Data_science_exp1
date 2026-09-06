import type {
  BusinessPayload,
  EdaPayload,
  EvalPayload,
  PipelinePayload,
  PredictResult,
  SchemaPayload,
  SimilarResult,
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

export async function predictRecord(
  record: Record<string, string | number | null>,
): Promise<PredictResult> {
  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ record }),
  });
  if (!res.ok) throw new Error("Predict failed");
  return res.json();
}

export async function findSimilar(
  record: Record<string, string | number | null>,
  k = 5,
): Promise<SimilarResult> {
  const res = await fetch("/api/similar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ record, k }),
  });
  if (!res.ok) throw new Error("Similarity search failed");
  return res.json();
}
