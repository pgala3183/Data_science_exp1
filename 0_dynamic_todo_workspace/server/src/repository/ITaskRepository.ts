import type { CreateTaskInput, Task, UpdateTaskInput } from "../types.js";

/**
 * Swappable persistence contract. Implementations: in-memory, SQLite.
 */
export interface ITaskRepository {
  list(): Promise<Task[]>;
  getById(id: string): Promise<Task | null>;
  create(input: CreateTaskInput): Promise<Task>;
  update(id: string, input: UpdateTaskInput): Promise<Task | null>;
  delete(id: string): Promise<boolean>;
  reorder(orderedIds: string[]): Promise<Task[]>;
}
