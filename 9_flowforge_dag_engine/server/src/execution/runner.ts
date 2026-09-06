import { randomUUID } from "node:crypto";
import type { ExecutionEvent, NodeStatus, PipelineGraph } from "../types.js";
import { kahnTopologicalSort } from "../graph/kahn.js";

export type EventSink = (event: ExecutionEvent) => void;

const FAIL_RATE = 0.18; // ~18% chance a node fails (demo chaos)
const MIN_MS = 400;
const MAX_MS = 1200;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function jitter(): number {
  return MIN_MS + Math.floor(Math.random() * (MAX_MS - MIN_MS));
}

/**
 * Mock pipeline runner: walk the Kahn order, emit SSE-friendly status
 * events, and mark every downstream descendant as `blocked` when a node fails.
 */
export async function runPipeline(
  graph: PipelineGraph,
  emit: EventSink,
  options?: { failRate?: number },
): Promise<string> {
  const runId = randomUUID();
  const failRate = options?.failRate ?? FAIL_RATE;
  const { order, isAcyclic } = kahnTopologicalSort(graph.nodes, graph.edges);

  if (!isAcyclic) {
    emit({
      type: "execution:aborted",
      runId,
      timestamp: new Date().toISOString(),
      message: "Refusing to execute a cyclic graph",
    });
    return runId;
  }

  // Build children map for cascading "blocked" marks.
  const children = new Map<string, string[]>();
  for (const n of graph.nodes) children.set(n.id, []);
  for (const e of graph.edges) {
    children.get(e.source)?.push(e.target);
  }
  for (const n of graph.nodes) {
    for (const dep of n.dependencies ?? []) {
      children.get(dep)?.push(n.id);
    }
  }

  const status = new Map<string, NodeStatus>();
  for (const id of order) status.set(id, "pending");

  emit({
    type: "execution:started",
    runId,
    timestamp: new Date().toISOString(),
    order,
    message: `Starting run with ${order.length} nodes`,
  });

  for (const id of order) {
    // Skip nodes already marked blocked by an upstream failure
    // (status was streamed immediately when the ancestor failed).
    if (status.get(id) === "blocked") {
      continue;
    }

    status.set(id, "running");
    emit({
      type: "node:status",
      runId,
      timestamp: new Date().toISOString(),
      nodeId: id,
      status: "running",
      message: `Executing ${id}`,
    });

    await sleep(jitter());

    const failed = Math.random() < failRate;
    if (failed) {
      status.set(id, "failed");
      emit({
        type: "node:status",
        runId,
        timestamp: new Date().toISOString(),
        nodeId: id,
        status: "failed",
        message: `Node ${id} failed (simulated)`,
      });

      // BFS: mark every reachable descendant blocked and notify the UI now.
      const stack = [...(children.get(id) ?? [])];
      const visited = new Set<string>();
      while (stack.length > 0) {
        const child = stack.pop()!;
        if (visited.has(child)) continue;
        visited.add(child);
        if (status.get(child) === "pending") {
          status.set(child, "blocked");
          emit({
            type: "node:status",
            runId,
            timestamp: new Date().toISOString(),
            nodeId: child,
            status: "blocked",
            message: `Blocked by failure of ${id}`,
          });
        }
        for (const next of children.get(child) ?? []) {
          stack.push(next);
        }
      }
      continue;
    }

    status.set(id, "success");
    emit({
      type: "node:status",
      runId,
      timestamp: new Date().toISOString(),
      nodeId: id,
      status: "success",
      message: `Node ${id} succeeded`,
    });
  }

  const anyFailed = [...status.values()].some((s) => s === "failed");
  emit({
    type: "execution:completed",
    runId,
    timestamp: new Date().toISOString(),
    message: anyFailed ? "Run finished with failures" : "Run finished successfully",
  });

  return runId;
}
