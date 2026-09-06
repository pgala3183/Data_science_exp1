import { Router } from "express";
import { sseHub } from "../sse/hub.js";

export function createSseRouter(): Router {
  const router = Router();

  router.get("/events", (req, res) => {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no");
    res.flushHeaders?.();

    res.write(`event: connected\ndata: ${JSON.stringify({ clients: sseHub.clientCount() + 1 })}\n\n`);
    sseHub.addClient(res);

    const heartbeat = setInterval(() => {
      res.write(": keepalive\n\n");
    }, 25000);

    req.on("close", () => {
      clearInterval(heartbeat);
    });
  });

  return router;
}
