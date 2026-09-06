import type { RunResult, Skill } from "./types";

export async function fetchSkills(params: {
  category?: string;
  dataset?: string;
  q?: string;
}): Promise<Skill[]> {
  const sp = new URLSearchParams();
  if (params.category) sp.set("category", params.category);
  if (params.dataset) sp.set("dataset", params.dataset);
  if (params.q) sp.set("q", params.q);
  const res = await fetch(`/api/skills?${sp}`);
  if (!res.ok) throw new Error("Failed to load skills");
  const body = await res.json();
  return body.skills;
}

export async function fetchCategories(): Promise<string[]> {
  const res = await fetch("/api/categories");
  if (!res.ok) throw new Error("Failed to load categories");
  return (await res.json()).categories;
}

export async function fetchSkill(id: string): Promise<Skill> {
  const res = await fetch(`/api/skills/${id}`);
  if (!res.ok) throw new Error("Skill not found");
  return res.json();
}

export async function runSkill(id: string): Promise<RunResult> {
  const res = await fetch(`/api/skills/${id}/run`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.error ?? err.detail ?? "Run failed");
  }
  const body = await res.json();
  return body.result;
}
