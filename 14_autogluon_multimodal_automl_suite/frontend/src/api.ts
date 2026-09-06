import type { DemoSample, MetricsResponse, PredictResponse } from "./types";

const BASE = "/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json() as Promise<T>;
}

export function fetchMetrics() {
  return getJson<MetricsResponse>("/metrics");
}

export function fetchDemo() {
  return getJson<{ samples: DemoSample[]; accuracies: MetricsResponse["accuracies"] }>("/demo");
}

export async function predictForm(form: FormData) {
  const res = await fetch(`${BASE}/predict`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`predict failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<PredictResponse>;
}

/** Proxy-friendly absolute URL for demo images. */
export function demoImageSrc(path: string) {
  if (path.startsWith("http")) return path;
  return `${BASE}${path}`;
}
