import Database from "better-sqlite3";
import { v4 as uuid } from "uuid";
import type { CreateTaskInput, Task, UpdateTaskInput } from "../types.js";
import type { ITaskRepository } from "./ITaskRepository.js";

type TaskRow = {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date: string | null;
  tags: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

function rowToTask(row: TaskRow): Task {
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    status: row.status as Task["status"],
    priority: row.priority as Task["priority"],
    dueDate: row.due_date,
    tags: JSON.parse(row.tags) as string[],
    sortOrder: row.sort_order,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

export class SqliteTaskRepository implements ITaskRepository {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.pragma("journal_mode = WAL");
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL,
        priority TEXT NOT NULL,
        due_date TEXT,
        tags TEXT NOT NULL DEFAULT '[]',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
    `);
  }

  async list(): Promise<Task[]> {
    const rows = this.db
      .prepare("SELECT * FROM tasks ORDER BY sort_order ASC")
      .all() as TaskRow[];
    return rows.map(rowToTask);
  }

  async getById(id: string): Promise<Task | null> {
    const row = this.db.prepare("SELECT * FROM tasks WHERE id = ?").get(id) as TaskRow | undefined;
    return row ? rowToTask(row) : null;
  }

  async create(input: CreateTaskInput): Promise<Task> {
    const now = new Date().toISOString();
    const maxRow = this.db.prepare("SELECT MAX(sort_order) AS m FROM tasks").get() as {
      m: number | null;
    };
    const sortOrder = (maxRow.m ?? -1) + 1;
    const task: Task = {
      id: uuid(),
      title: input.title,
      description: input.description ?? "",
      status: input.status ?? "todo",
      priority: input.priority ?? "medium",
      dueDate: input.dueDate ?? null,
      tags: input.tags ?? [],
      sortOrder,
      createdAt: now,
      updatedAt: now,
    };
    this.db
      .prepare(
        `INSERT INTO tasks (id, title, description, status, priority, due_date, tags, sort_order, created_at, updated_at)
         VALUES (@id, @title, @description, @status, @priority, @due_date, @tags, @sort_order, @created_at, @updated_at)`,
      )
      .run({
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        due_date: task.dueDate,
        tags: JSON.stringify(task.tags),
        sort_order: task.sortOrder,
        created_at: task.createdAt,
        updated_at: task.updatedAt,
      });
    return task;
  }

  async update(id: string, input: UpdateTaskInput): Promise<Task | null> {
    const existing = await this.getById(id);
    if (!existing) return null;
    const updated: Task = {
      ...existing,
      ...input,
      tags: input.tags ?? existing.tags,
      updatedAt: new Date().toISOString(),
    };
    this.db
      .prepare(
        `UPDATE tasks SET title=@title, description=@description, status=@status, priority=@priority,
         due_date=@due_date, tags=@tags, sort_order=@sort_order, updated_at=@updated_at WHERE id=@id`,
      )
      .run({
        id: updated.id,
        title: updated.title,
        description: updated.description,
        status: updated.status,
        priority: updated.priority,
        due_date: updated.dueDate,
        tags: JSON.stringify(updated.tags),
        sort_order: updated.sortOrder,
        updated_at: updated.updatedAt,
      });
    return updated;
  }

  async delete(id: string): Promise<boolean> {
    const result = this.db.prepare("DELETE FROM tasks WHERE id = ?").run(id);
    return result.changes > 0;
  }

  async reorder(orderedIds: string[]): Promise<Task[]> {
    const now = new Date().toISOString();
    const stmt = this.db.prepare(
      "UPDATE tasks SET sort_order = ?, updated_at = ? WHERE id = ?",
    );
    const tx = this.db.transaction((ids: string[]) => {
      ids.forEach((id, index) => stmt.run(index, now, id));
    });
    tx(orderedIds);
    return this.list();
  }

  close(): void {
    this.db.close();
  }
}
