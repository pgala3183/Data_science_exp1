import request from "supertest";
import { describe, expect, it } from "vitest";
import { createApp } from "../src/app.js";
import { InMemoryTaskRepository } from "../src/repository/InMemoryTaskRepository.js";

describe("tasks API", () => {
  it("validates create payload", async () => {
    const app = createApp(new InMemoryTaskRepository());
    const res = await request(app).post("/api/tasks").send({ title: "" });
    expect(res.status).toBe(400);
    expect(res.body.error).toBe("Validation failed");
  });

  it("performs CRUD with correct status codes", async () => {
    const app = createApp(new InMemoryTaskRepository());

    const created = await request(app)
      .post("/api/tasks")
      .send({
        title: "Write tests",
        priority: "medium",
        tags: ["dev"],
      });
    expect(created.status).toBe(201);
    expect(created.body.title).toBe("Write tests");

    const list = await request(app).get("/api/tasks");
    expect(list.status).toBe(200);
    expect(list.body).toHaveLength(1);

    const patched = await request(app)
      .patch(`/api/tasks/${created.body.id}`)
      .send({ status: "done" });
    expect(patched.status).toBe(200);
    expect(patched.body.status).toBe("done");

    const missing = await request(app).get("/api/tasks/00000000-0000-4000-8000-000000000000");
    expect(missing.status).toBe(404);

    const deleted = await request(app).delete(`/api/tasks/${created.body.id}`);
    expect(deleted.status).toBe(204);
  });

  it("rejects empty patch bodies", async () => {
    const app = createApp(new InMemoryTaskRepository());
    const created = await request(app).post("/api/tasks").send({ title: "X" });
    const res = await request(app).patch(`/api/tasks/${created.body.id}`).send({});
    expect(res.status).toBe(400);
  });
});
