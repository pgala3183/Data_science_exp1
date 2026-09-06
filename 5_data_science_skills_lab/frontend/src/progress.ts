const KEY = "skills-lab-progress-v1";

export function loadProgress(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw) as string[]);
  } catch {
    return new Set();
  }
}

export function saveProgress(ids: Set<string>) {
  localStorage.setItem(KEY, JSON.stringify([...ids]));
}

export function markComplete(id: string): Set<string> {
  const next = loadProgress();
  next.add(id);
  saveProgress(next);
  return next;
}

export function clearProgress() {
  localStorage.removeItem(KEY);
}
