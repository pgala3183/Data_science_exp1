export type TaskStatus = "todo" | "in_progress" | "done";
export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate: string | null;
  tags: string[];
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export type CreateTaskPayload = {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  dueDate?: string | null;
  tags?: string[];
};

export type UpdateTaskPayload = Partial<{
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate: string | null;
  tags: string[];
  sortOrder: number;
}>;

export type TaskEventType =
  | "task:created"
  | "task:updated"
  | "task:deleted"
  | "tasks:reordered"
  | "connected";

export interface TaskEvent {
  type: TaskEventType;
  payload: Task | Task[] | { id: string } | { clients: number };
  at?: string;
}

export const STATUS_COLUMNS: { id: TaskStatus; label: string }[] = [
  { id: "todo", label: "To do" },
  { id: "in_progress", label: "In progress" },
  { id: "done", label: "Done" },
];
