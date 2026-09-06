import type { Response } from "express";
import type { ExecutionEvent } from "../types.js";

/**
 * Per-run SSE hub: clients subscribe to `/api/execute/:runId/events`
 * (or a shared stream keyed by runId in the event payload).
 */
export class SseHub {
  private clients = new Set<Response>();

  addClient(res: Response): void {
    this.clients.add(res);
    res.on("close", () => {
      this.clients.delete(res);
    });
  }

  clientCount(): number {
    return this.clients.size;
  }

  broadcast(event: ExecutionEvent): void {
    const data = `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`;
    for (const client of this.clients) {
      client.write(data);
    }
  }
}

/** Global fan-out for execution events (all connected editors). */
export const executionHub = new SseHub();
