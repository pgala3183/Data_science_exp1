import type { Response } from "express";
import type { TaskEvent } from "../types.js";

/**
 * Fan-out hub for Server-Sent Events. Each connected browser tab holds an
 * open HTTP response; mutations publish once and every client receives the event.
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

  broadcast(event: TaskEvent): void {
    const data = `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`;
    for (const client of this.clients) {
      client.write(data);
    }
  }

  /** Keepalive comment so proxies do not idle-close the stream. */
  heartbeat(): void {
    for (const client of this.clients) {
      client.write(": keepalive\n\n");
    }
  }
}

export const sseHub = new SseHub();
