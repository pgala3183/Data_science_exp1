import type { CreateTaskPayload, Task, UpdateTaskPayload } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listTasks: () => request<Task[]>("/api/tasks"),
  createTask: (payload: CreateTaskPayload) =>
    request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(payload) }),
  updateTask: (id: string, payload: UpdateTaskPayload) =>
    request<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteTask: (id: string) => request<void>(`/api/tasks/${id}`, { method: "DELETE" }),
  reorderTasks: (orderedIds: string[]) =>
    request<Task[]>("/api/tasks/reorder", {
      method: "POST",
      body: JSON.stringify({ orderedIds }),
    }),
};
