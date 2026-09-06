import { Router } from "express";
import { validatePipelineGraph } from "../graph/validate.js";
import { runPipeline } from "../execution/runner.js";
import { executionHub } from "../sse/hub.js";
import { PipelineGraphSchema } from "../types.js";

export function createExecuteRouter(): Router {
  const router = Router();

  /**
   * GET /api/events — long-lived SSE stream for execution status updates.
   * Client opens this before POSTing /api/execute.
   */
  router.get("/events", (req, res) => {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no");
    res.flushHeaders?.();

    res.write(
      `event: connected\ndata: ${JSON.stringify({ clients: executionHub.clientCount() + 1 })}\n\n`,
    );
    executionHub.addClient(res);

    const heartbeat = setInterval(() => {
      res.write(": keepalive\n\n");
    }, 25000);

    req.on("close", () => {
      clearInterval(heartbeat);
    });
  });

  /**
   * POST /api/execute — validate DAG, then run mock nodes in topo order,
   * streaming status via the SSE hub.
   */
  router.post("/execute", (req, res) => {
    const validation = validatePipelineGraph(req.body);
    if (!validation.valid) {
      res.status(400).json(validation);
      return;
    }

    const graph = PipelineGraphSchema.parse(req.body);

    // Respond immediately; work continues asynchronously while SSE pushes updates.
    res.status(202).json({
      accepted: true,
      order: validation.order,
      message: "Execution started — listen on /api/events for status",
    });

    void runPipeline(graph, (event) => executionHub.broadcast(event)).catch((err) => {
      executionHub.broadcast({
        type: "execution:aborted",
        runId: "unknown",
        timestamp: new Date().toISOString(),
        message: err instanceof Error ? err.message : "Unknown execution error",
      });
    });
  });

  return router;
}
