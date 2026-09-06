import { PipelineGraphSchema, type PipelineGraph, type ValidateResult } from "../types.js";
import { kahnTopologicalSort } from "./kahn.js";

/**
 * Validate request body shape, then prove acyclicity via Kahn's algorithm.
 */
export function validatePipelineGraph(input: unknown): ValidateResult {
  const parsed = PipelineGraphSchema.safeParse(input);
  if (!parsed.success) {
    return {
      valid: false,
      error: parsed.error.issues.map((i) => i.message).join("; ") || "Invalid graph payload",
    };
  }

  const graph: PipelineGraph = parsed.data;
  const ids = new Set(graph.nodes.map((n) => n.id));

  if (ids.size !== graph.nodes.length) {
    return { valid: false, error: "Duplicate node ids are not allowed" };
  }

  for (const edge of graph.edges) {
    if (!ids.has(edge.source) || !ids.has(edge.target)) {
      return {
        valid: false,
        error: `Edge "${edge.id}" references a missing node (${edge.source} → ${edge.target})`,
      };
    }
  }

  const { order, isAcyclic, remaining } = kahnTopologicalSort(graph.nodes, graph.edges);

  if (!isAcyclic) {
    return {
      valid: false,
      error:
        "Graph contains a cycle — a topological order does not exist. " +
        "Remove an edge in the strongly connected component before executing.",
      cycleHint: remaining,
    };
  }

  return { valid: true, order };
}
