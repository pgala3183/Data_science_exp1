import { describe, expect, it } from "vitest";
import { InMemoryTaskRepository } from "../src/repository/InMemoryTaskRepository.js";

describe("InMemoryTaskRepository", () => {
  it("creates, lists, updates, and deletes tasks", async () => {
    const repo = new InMemoryTaskRepository();
    const created = await repo.create({
      title: "Ship feature",
      description: "Build SSE board",
      priority: "high",
      tags: ["work"],
    });

    expect(created.id).toBeTruthy();
    expect(created.status).toBe("todo");
    expect(created.priority).toBe("high");
    expect(created.tags).toEqual(["work"]);

    const listed = await repo.list();
    expect(listed).toHaveLength(1);

    const updated = await repo.update(created.id, { status: "in_progress" });
    expect(updated?.status).toBe("in_progress");
    expect(updated?.updatedAt).not.toBe(created.updatedAt);

    const deleted = await repo.delete(created.id);
    expect(deleted).toBe(true);
    expect(await repo.list()).toHaveLength(0);
  });

  it("reorders by ordered ids", async () => {
    const repo = new InMemoryTaskRepository();
    const a = await repo.create({ title: "A" });
    const b = await repo.create({ title: "B" });
    const c = await repo.create({ title: "C" });

    const reordered = await repo.reorder([c.id, a.id, b.id]);
    expect(reordered.map((t) => t.title)).toEqual(["C", "A", "B"]);
    expect(reordered.map((t) => t.sortOrder)).toEqual([0, 1, 2]);
  });
});
