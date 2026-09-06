import type { EvalResponse, ScoreItem } from "./types";

export async function fetchEvaluate(): Promise<EvalResponse> {
  const res = await fetch("/api/evaluate");
  if (!res.ok) throw new Error("Failed to load evaluation");
  return res.json();
}

export async function fetchFeatures(): Promise<string[]> {
  const res = await fetch("/api/features");
  if (!res.ok) throw new Error("Failed to load features");
  return (await res.json()).features;
}

export async function scoreRecord(
  record: Record<string, number>,
): Promise<{ scores: ScoreItem[]; thresholds: Record<string, number> }> {
  const res = await fetch("/api/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ records: [record] }),
  });
  if (!res.ok) throw new Error("Score failed");
  return res.json();
}
