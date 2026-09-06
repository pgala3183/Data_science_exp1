import { useEffect, useRef, useState } from "react";
import type { TaskEvent } from "../types";

const SSE_URL = "/api/events";

/**
 * Subscribes to the backend SSE stream and forwards typed task events.
 * Auto-reconnects with backoff if the connection drops.
 */
export function useTaskEvents(onEvent: (event: TaskEvent) => void): {
  connected: boolean;
} {
  const [connected, setConnected] = useState(false);
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    let source: EventSource | null = null;
    let closed = false;
    let retryMs = 1000;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    const attach = () => {
      source = new EventSource(SSE_URL);

      source.addEventListener("connected", () => {
        setConnected(true);
        retryMs = 1000;
      });

      const forward = (type: TaskEvent["type"]) => (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data) as TaskEvent;
          handlerRef.current({ ...payload, type });
        } catch {
          // ignore malformed frames
        }
      };

      source.addEventListener("task:created", forward("task:created"));
      source.addEventListener("task:updated", forward("task:updated"));
      source.addEventListener("task:deleted", forward("task:deleted"));
      source.addEventListener("tasks:reordered", forward("tasks:reordered"));

      source.onerror = () => {
        setConnected(false);
        source?.close();
        if (closed) return;
        retryTimer = setTimeout(attach, retryMs);
        retryMs = Math.min(retryMs * 2, 15000);
      };
    };

    attach();

    return () => {
      closed = true;
      clearTimeout(retryTimer);
      source?.close();
    };
  }, []);

  return { connected };
}
