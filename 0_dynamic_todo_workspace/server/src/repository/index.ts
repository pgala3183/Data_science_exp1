import fs from "node:fs";
import path from "node:path";
import type { ITaskRepository } from "./ITaskRepository.js";
import { InMemoryTaskRepository } from "./InMemoryTaskRepository.js";
import { SqliteTaskRepository } from "./SqliteTaskRepository.js";

export type StorageDriver = "memory" | "sqlite";

export function createRepository(driver: StorageDriver = "memory"): ITaskRepository {
  if (driver === "sqlite") {
    const dataDir = path.resolve(process.cwd(), "data");
    fs.mkdirSync(dataDir, { recursive: true });
    return new SqliteTaskRepository(path.join(dataDir, "tasks.db"));
  }
  return new InMemoryTaskRepository();
}

export type { ITaskRepository } from "./ITaskRepository.js";
export { InMemoryTaskRepository } from "./InMemoryTaskRepository.js";
export { SqliteTaskRepository } from "./SqliteTaskRepository.js";
