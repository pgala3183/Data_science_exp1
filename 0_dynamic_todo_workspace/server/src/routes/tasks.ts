import { Router } from "express";
import type { ITaskRepository } from "../repository/ITaskRepository.js";
import { sseHub } from "../sse/hub.js";
import { createTaskSchema, reorderSchema, updateTaskSchema } from "../validation.js";

export function createTasksRouter(repo: ITaskRepository): Router {
  const router = Router();

  router.get("/", async (_req, res, next) => {
    try {
      const tasks = await repo.list();
      res.json(tasks);
    } catch (err) {
      next(err);
    }
  });

  router.post("/reorder", async (req, res, next) => {
    try {
      const parsed = reorderSchema.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
        return;
      }
      const tasks = await repo.reorder(parsed.data.orderedIds);
      sseHub.broadcast({
        type: "tasks:reordered",
        payload: tasks,
        at: new Date().toISOString(),
      });
      res.json(tasks);
    } catch (err) {
      next(err);
    }
  });

  router.get("/:id", async (req, res, next) => {
    try {
      const task = await repo.getById(req.params.id);
      if (!task) {
        res.status(404).json({ error: "Task not found" });
        return;
      }
      res.json(task);
    } catch (err) {
      next(err);
    }
  });

  router.post("/", async (req, res, next) => {
    try {
      const parsed = createTaskSchema.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
        return;
      }
      const task = await repo.create(parsed.data);
      sseHub.broadcast({
        type: "task:created",
        payload: task,
        at: new Date().toISOString(),
      });
      res.status(201).json(task);
    } catch (err) {
      next(err);
    }
  });

  router.patch("/:id", async (req, res, next) => {
    try {
      const parsed = updateTaskSchema.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
        return;
      }
      const task = await repo.update(req.params.id, parsed.data);
      if (!task) {
        res.status(404).json({ error: "Task not found" });
        return;
      }
      sseHub.broadcast({
        type: "task:updated",
        payload: task,
        at: new Date().toISOString(),
      });
      res.json(task);
    } catch (err) {
      next(err);
    }
  });

  router.delete("/:id", async (req, res, next) => {
    try {
      const deleted = await repo.delete(req.params.id);
      if (!deleted) {
        res.status(404).json({ error: "Task not found" });
        return;
      }
      sseHub.broadcast({
        type: "task:deleted",
        payload: { id: req.params.id },
        at: new Date().toISOString(),
      });
      res.status(204).send();
    } catch (err) {
      next(err);
    }
  });

  return router;
}
