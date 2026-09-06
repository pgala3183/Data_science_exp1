import { v4 as uuid } from "uuid";
import type { CreateTaskInput, Task, UpdateTaskInput } from "../types.js";
import type { ITaskRepository } from "./ITaskRepository.js";

export class InMemoryTaskRepository implements ITaskRepository {
  private tasks = new Map<string, Task>();

  async list(): Promise<Task[]> {
    return [...this.tasks.values()].sort((a, b) => a.sortOrder - b.sortOrder);
  }

  async getById(id: string): Promise<Task | null> {
    return this.tasks.get(id) ?? null;
  }

  async create(input: CreateTaskInput): Promise<Task> {
    const now = new Date().toISOString();
    const maxOrder = Math.max(-1, ...[...this.tasks.values()].map((t) => t.sortOrder));
    const task: Task = {
      id: uuid(),
      title: input.title,
      description: input.description ?? "",
      status: input.status ?? "todo",
      priority: input.priority ?? "medium",
      dueDate: input.dueDate ?? null,
      tags: input.tags ?? [],
      sortOrder: maxOrder + 1,
      createdAt: now,
      updatedAt: now,
    };
    this.tasks.set(task.id, task);
    return task;
  }

  async update(id: string, input: UpdateTaskInput): Promise<Task | null> {
    const existing = this.tasks.get(id);
    if (!existing) return null;
    const updated: Task = {
      ...existing,
      ...input,
      tags: input.tags ?? existing.tags,
      updatedAt: new Date().toISOString(),
    };
    this.tasks.set(id, updated);
    return updated;
  }

  async delete(id: string): Promise<boolean> {
    return this.tasks.delete(id);
  }

  async reorder(orderedIds: string[]): Promise<Task[]> {
    const now = new Date().toISOString();
    orderedIds.forEach((id, index) => {
      const task = this.tasks.get(id);
      if (task) {
        this.tasks.set(id, { ...task, sortOrder: index, updatedAt: now });
      }
    });
    return this.list();
  }
}
