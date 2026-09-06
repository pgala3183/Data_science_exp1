import type { Method, SegmentCustomers, SegmentsResponse } from "./types";

export async function fetchSegments(method: Method): Promise<SegmentsResponse> {
  const res = await fetch(`/api/segments?method=${method}`);
  if (!res.ok) throw new Error("Failed to load segments");
  return res.json();
}

export async function fetchSegmentCustomers(
  clusterId: number,
  method: Method,
): Promise<SegmentCustomers> {
  const res = await fetch(`/api/segments/${clusterId}/customers?limit=15&method=${method}`);
  if (!res.ok) throw new Error("Failed to load customers");
  return res.json();
}
