import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type {
  CreateTaskPayload,
  Task,
  TaskEvent,
  TaskPriority,
  TaskStatus,
  UpdateTaskPayload,
} from "../types";
import { useTaskEvents } from "./useTaskEvents";

export type Filters = {
  search: string;
  priority: TaskPriority | "all";
  tag: string;
};

function applyEvent(tasks: Task[], event: TaskEvent): Task[] {
  switch (event.type) {
    case "task:created": {
      const task = event.payload as Task;
      if (tasks.some((t) => t.id === task.id)) return tasks;
      return [...tasks, task].sort((a, b) => a.sortOrder - b.sortOrder);
    }
    case "task:updated": {
      const task = event.payload as Task;
      return tasks
        .map((t) => (t.id === task.id ? task : t))
        .sort((a, b) => a.sortOrder - b.sortOrder);
    }
    case "task:deleted": {
      const { id } = event.payload as { id: string };
      return tasks.filter((t) => t.id !== id);
    }
    case "tasks:reordered":
      return [...(event.payload as Task[])].sort((a, b) => a.sortOrder - b.sortOrder);
    default:
      return tasks;
  }
}

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>({
    search: "",
    priority: "all",
    tag: "",
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.listTasks();
        if (!cancelled) setTasks(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load tasks");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onEvent = useCallback((event: TaskEvent) => {
    setTasks((prev) => applyEvent(prev, event));
  }, []);

  const { connected } = useTaskEvents(onEvent);

  const createTask = useCallback(async (payload: CreateTaskPayload) => {
    setError(null);
    const task = await api.createTask(payload);
    setTasks((prev) => applyEvent(prev, { type: "task:created", payload: task }));
  }, []);

  const updateTask = useCallback(async (id: string, payload: UpdateTaskPayload) => {
    setError(null);
    const task = await api.updateTask(id, payload);
    setTasks((prev) => applyEvent(prev, { type: "task:updated", payload: task }));
  }, []);

  const deleteTask = useCallback(async (id: string) => {
    setError(null);
    await api.deleteTask(id);
    setTasks((prev) => applyEvent(prev, { type: "task:deleted", payload: { id } }));
  }, []);

  const moveTask = useCallback(
    async (id: string, status: TaskStatus) => {
      await updateTask(id, { status });
    },
    [updateTask],
  );

  const allTags = useMemo(() => {
    const set = new Set<string>();
    tasks.forEach((t) => t.tags.forEach((tag) => set.add(tag)));
    return [...set].sort();
  }, [tasks]);

  const filtered = useMemo(() => {
    const q = filters.search.trim().toLowerCase();
    return tasks.filter((task) => {
      if (filters.priority !== "all" && task.priority !== filters.priority) return false;
      if (filters.tag && !task.tags.includes(filters.tag)) return false;
      if (!q) return true;
      return (
        task.title.toLowerCase().includes(q) ||
        task.description.toLowerCase().includes(q) ||
        task.tags.some((tag) => tag.toLowerCase().includes(q))
      );
    });
  }, [tasks, filters]);

  return {
    tasks: filtered,
    allTasks: tasks,
    loading,
    error,
    connected,
    filters,
    setFilters,
    allTags,
    createTask,
    updateTask,
    deleteTask,
    moveTask,
  };
}
