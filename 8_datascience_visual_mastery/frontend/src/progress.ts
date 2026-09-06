import type { ConceptId } from "./types";

const KEY = "dsvm-progress-v1";

export type ProgressMap = Partial<Record<ConceptId, { quizScore: number; quizTotal: number; visited: boolean }>>;

export function loadProgress(): ProgressMap {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "{}") as ProgressMap;
  } catch {
    return {};
  }
}

export function markVisited(id: ConceptId) {
  const p = loadProgress();
  p[id] = { ...(p[id] ?? { quizScore: 0, quizTotal: 0 }), visited: true };
  localStorage.setItem(KEY, JSON.stringify(p));
}

export function saveQuiz(id: ConceptId, score: number, total: number) {
  const p = loadProgress();
  p[id] = { visited: true, quizScore: score, quizTotal: total };
  localStorage.setItem(KEY, JSON.stringify(p));
}

export function progressFraction(p: ProgressMap, id: ConceptId): number {
  const row = p[id];
  if (!row) return 0;
  if (row.quizTotal > 0) return 0.35 + 0.65 * (row.quizScore / row.quizTotal);
  return row.visited ? 0.35 : 0;
}
