import type { PipelineGraphPayload, ValidateResult } from "./types";

export async function validateGraph(
  graph: PipelineGraphPayload,
): Promise<ValidateResult> {
  const res = await fetch("/api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(graph),
  });
  return (await res.json()) as ValidateResult;
}

export async function executeGraph(
  graph: PipelineGraphPayload,
): Promise<{ accepted: boolean; order?: string[]; message?: string } & ValidateResult> {
  const res = await fetch("/api/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(graph),
  });
  return (await res.json()) as {
    accepted: boolean;
    order?: string[];
    message?: string;
  } & ValidateResult;
}
