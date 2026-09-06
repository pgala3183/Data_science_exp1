import type { ExplainResponse, LeaderboardResponse, PredictResponse, SchemaField } from "./types";

const BASE = "/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json() as Promise<T>;
}

export function fetchLeaderboard() {
  return getJson<LeaderboardResponse>("/leaderboard");
}

export function fetchSchema() {
  return getJson<{ schema: SchemaField[]; class_labels: string[] }>("/schema");
}

export function fetchExplain() {
  return getJson<ExplainResponse>("/explain");
}

export async function predictRecord(record: Record<string, string | number>) {
  const res = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ record, include_base_models: true }),
  });
  if (!res.ok) throw new Error(`predict failed (${res.status})`);
  return res.json() as Promise<PredictResponse>;
}
