import { useCallback, useEffect, useRef, useState } from "react";
import type { ExecutionEvent, NodeStatus } from "../types";

/**
 * Subscribe to the server SSE stream and accumulate per-node status.
 */
export function useExecutionStream() {
  const [statuses, setStatuses] = useState<Record<string, NodeStatus>>({});
  const [running, setRunning] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [topoOrder, setTopoOrder] = useState<string[]>([]);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource("/api/events");
    sourceRef.current = es;

    const onEvent = (raw: MessageEvent) => {
      let payload: ExecutionEvent;
      try {
        payload = JSON.parse(raw.data as string) as ExecutionEvent;
      } catch {
        return;
      }

      // Prefer the SSE event name when present.
      const type = (raw.type !== "message" ? raw.type : payload.type) as ExecutionEvent["type"];

      if (type === "execution:started") {
        setRunning(true);
        setLastMessage(payload.message ?? "Execution started");
        setTopoOrder(payload.order ?? []);
        const next: Record<string, NodeStatus> = {};
        for (const id of payload.order ?? []) next[id] = "pending";
        setStatuses(next);
        return;
      }

      if (type === "node:status" && payload.nodeId && payload.status) {
        setStatuses((prev) => ({ ...prev, [payload.nodeId!]: payload.status! }));
        setLastMessage(payload.message ?? null);
        return;
      }

      if (type === "execution:completed" || type === "execution:aborted") {
        setRunning(false);
        setLastMessage(payload.message ?? type);
      }
    };

    es.addEventListener("execution:started", onEvent);
    es.addEventListener("node:status", onEvent);
    es.addEventListener("execution:completed", onEvent);
    es.addEventListener("execution:aborted", onEvent);
    es.onmessage = onEvent;

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, []);

  const resetStatuses = useCallback(() => {
    setStatuses({});
    setTopoOrder([]);
    setLastMessage(null);
    setRunning(false);
  }, []);

  return { statuses, running, lastMessage, topoOrder, resetStatuses };
}
