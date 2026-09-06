import type { AuditResponse } from "./types";

const BASE = "/api";

export async function auditPath(path: string): Promise<AuditResponse> {
  const res = await fetch(`${BASE}/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Audit failed (${res.status})`);
  }
  return res.json() as Promise<AuditResponse>;
}

export async function auditUpload(file: File): Promise<AuditResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/audit/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Upload audit failed (${res.status})`);
  }
  return res.json() as Promise<AuditResponse>;
}
