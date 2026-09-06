import express from "express";
import cors from "cors";
import { createGraphRouter } from "./routes/graph.js";
import { createExecuteRouter } from "./routes/execute.js";

export function createApp() {
  const app = express();
  app.use(cors());
  app.use(express.json({ limit: "1mb" }));

  app.get("/api/health", (_req, res) => {
    res.json({ ok: true, service: "flowforge-dag-engine" });
  });

  app.use("/api", createGraphRouter());
  app.use("/api", createExecuteRouter());

  return app;
}
