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

export type CreateTaskInput = {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  dueDate?: string | null;
  tags?: string[];
};

export type UpdateTaskInput = Partial<{
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate: string | null;
  tags: string[];
  sortOrder: number;
}>;

export type TaskEventType = "task:created" | "task:updated" | "task:deleted" | "tasks:reordered";

export interface TaskEvent {
  type: TaskEventType;
  payload: Task | Task[] | { id: string };
  at: string;
}
