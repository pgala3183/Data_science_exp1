import type { KahnResult, PipelineEdge, PipelineNode } from "../types.js";

/**
 * Kahn's algorithm — topological sort via iterative indegree peeling.
 *
 * Why this matters for a DAG engine:
 *   Execution must respect dependencies: a node may run only after every
 *   upstream parent has finished. A topological order is exactly such a
 *   linearization. If no total order exists, the graph contains a cycle
 *   and must be rejected before scheduling.
 *
 * Algorithm (O(V + E)):
 *   1. Build adjacency lists and count each node's indegree (incoming edges).
 *   2. Seed a queue with every node whose indegree is 0 (no unmet deps).
 *   3. While the queue is non-empty:
 *        - Dequeue a node, append it to the result order.
 *        - For each outgoing neighbor, decrement its indegree.
 *        - If a neighbor's indegree hits 0, enqueue it.
 *   4. If |order| === |nodes|, the graph is a DAG. Otherwise the leftover
 *      nodes with positive indegree form (or feed) a cycle.
 *
 * We implement this by hand (no library) so the experiment demonstrates
 * the CS concept clearly.
 */
export function kahnTopologicalSort(
  nodes: PipelineNode[],
  edges: PipelineEdge[],
): KahnResult {
  const nodeIds = nodes.map((n) => n.id);
  const idSet = new Set(nodeIds);

  // Adjacency: source → list of targets (downstream dependents).
  const adjacency = new Map<string, string[]>();
  // Indegree: how many unresolved upstream edges each node still has.
  const indegree = new Map<string, number>();

  for (const id of nodeIds) {
    adjacency.set(id, []);
    indegree.set(id, 0);
  }

  // Prefer explicit edges; also honour per-node `dependencies` so either
  // representation can drive the sort.
  const edgePairs: Array<{ source: string; target: string }> = [];

  for (const edge of edges) {
    if (!idSet.has(edge.source) || !idSet.has(edge.target)) {
      continue; // ignore dangling references
    }
    edgePairs.push({ source: edge.source, target: edge.target });
  }

  for (const node of nodes) {
    for (const dep of node.dependencies ?? []) {
      if (!idSet.has(dep)) continue;
      // dependency → node means: dep must finish before node.
      edgePairs.push({ source: dep, target: node.id });
    }
  }

  // Deduplicate parallel edges so indegree stays accurate.
  const seen = new Set<string>();
  for (const { source, target } of edgePairs) {
    if (source === target) {
      // Self-loop is an immediate cycle; keep indegree > 0 forever for it.
      const key = `${source}->${target}`;
      if (seen.has(key)) continue;
      seen.add(key);
      adjacency.get(source)!.push(target);
      indegree.set(target, (indegree.get(target) ?? 0) + 1);
      continue;
    }
    const key = `${source}->${target}`;
    if (seen.has(key)) continue;
    seen.add(key);
    adjacency.get(source)!.push(target);
    indegree.set(target, (indegree.get(target) ?? 0) + 1);
  }

  // --- Step 2: seed the queue with indegree-0 nodes -------------------
  const queue: string[] = [];
  for (const id of nodeIds) {
    if ((indegree.get(id) ?? 0) === 0) {
      queue.push(id);
    }
  }

  // Stable-ish order: process in the order nodes were declared when ties.
  // (Queue is FIFO; we seeded in declaration order.)
  const order: string[] = [];

  // --- Step 3: peel layers --------------------------------------------
  while (queue.length > 0) {
    const current = queue.shift()!;
    order.push(current);

    for (const neighbor of adjacency.get(current) ?? []) {
      const next = (indegree.get(neighbor) ?? 0) - 1;
      indegree.set(neighbor, next);
      // A neighbor becomes ready only when every parent has been peeled.
      if (next === 0) {
        queue.push(neighbor);
      }
    }
  }

  // --- Step 4: cycle detection ----------------------------------------
  const isAcyclic = order.length === nodeIds.length;
  const remaining = isAcyclic
    ? []
    : nodeIds.filter((id) => (indegree.get(id) ?? 0) > 0);

  return { order, isAcyclic, remaining };
}
