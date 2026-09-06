import type { Filters, GraphData, RecommendItem, RulesResponse } from "./types";

function qs(filters: Filters, extra: Record<string, string | number> = {}) {
  const p = new URLSearchParams({
    min_support: String(filters.min_support),
    min_confidence: String(filters.min_confidence),
    min_lift: String(filters.min_lift),
    ...Object.fromEntries(Object.entries(extra).map(([k, v]) => [k, String(v)])),
  });
  return p.toString();
}

export async function fetchRules(
  filters: Filters,
  page: number,
  pageSize: number,
): Promise<RulesResponse> {
  const res = await fetch(
    `/api/rules?${qs(filters, { sort_by: filters.sort_by, page, page_size: pageSize })}`,
  );
  if (!res.ok) throw new Error("Failed to load rules");
  return res.json();
}

export async function fetchGraph(filters: Filters): Promise<GraphData> {
  const res = await fetch(`/api/graph?${qs(filters, { max_edges: 80 })}`);
  if (!res.ok) throw new Error("Failed to load graph");
  return res.json();
}

export async function fetchItems(): Promise<string[]> {
  const res = await fetch("/api/items");
  if (!res.ok) throw new Error("Failed to load items");
  const body = await res.json();
  return body.items;
}

export async function recommend(basket: string[], topN = 8): Promise<RecommendItem[]> {
  const res = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ basket, top_n: topN }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Recommend failed");
  }
  const body = await res.json();
  return body.recommendations;
}
