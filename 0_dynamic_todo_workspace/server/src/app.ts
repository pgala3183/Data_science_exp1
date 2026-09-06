import cors from "cors";
import express, {
  type ErrorRequestHandler,
  type Express,
  type NextFunction,
  type Request,
  type Response,
} from "express";
import type { ITaskRepository } from "./repository/ITaskRepository.js";
import { createSseRouter } from "./routes/sse.js";
import { createTasksRouter } from "./routes/tasks.js";

export function createApp(repo: ITaskRepository): Express {
  const app = express();

  app.use(
    cors({
      origin: true,
      methods: ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    }),
  );
  app.use(express.json({ limit: "100kb" }));

  app.get("/api/health", (_req, res) => {
    res.json({ ok: true });
  });

  // Reorder must be registered before /:id on the same router — handled inside createTasksRouter
  // by defining /reorder after /:id would conflict; we mount reorder path carefully.
  const tasksRouter = createTasksRouter(repo);
  // Express matches in order; createTasksRouter defines /reorder after /:id which would treat
  // "reorder" as an id. Fix by remounting: we'll adjust routes file.
  app.use("/api/tasks", tasksRouter);
  app.use("/api", createSseRouter());

  app.use((_req, res) => {
    res.status(404).json({ error: "Not found" });
  });

  const errorHandler: ErrorRequestHandler = (
    err: unknown,
    _req: Request,
    res: Response,
    _next: NextFunction,
  ) => {
    if (
      typeof err === "object" &&
      err !== null &&
      "status" in err &&
      (err as { status?: number }).status === 400 &&
      "type" in err &&
      (err as { type?: string }).type === "entity.parse.failed"
    ) {
      res.status(400).json({ error: "Invalid JSON body" });
      return;
    }
    console.error(err);
    res.status(500).json({ error: "Internal server error" });
  };
  app.use(errorHandler);

  return app;
}
