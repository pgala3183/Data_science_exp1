import { describe, expect, it } from "vitest";
import { kahnTopologicalSort } from "../src/graph/kahn.js";
import { validatePipelineGraph } from "../src/graph/validate.js";
import type { PipelineEdge, PipelineNode } from "../src/types.js";

function nodes(...ids: string[]): PipelineNode[] {
  return ids.map((id) => ({
    id,
    type: "transform" as const,
    config: {},
    dependencies: [],
  }));
}

function edges(...pairs: Array<[string, string]>): PipelineEdge[] {
  return pairs.map(([source, target], i) => ({
    id: `e${i}`,
    source,
    target,
  }));
}

describe("kahnTopologicalSort", () => {
  it("returns a valid order for a simple chain A→B→C", () => {
    const result = kahnTopologicalSort(nodes("A", "B", "C"), edges(["A", "B"], ["B", "C"]));
    expect(result.isAcyclic).toBe(true);
    expect(result.order).toEqual(["A", "B", "C"]);
    expect(result.remaining).toEqual([]);
  });

  it("handles a diamond DAG (A→B, A→C, B→D, C→D)", () => {
    const result = kahnTopologicalSort(
      nodes("A", "B", "C", "D"),
      edges(["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]),
    );
    expect(result.isAcyclic).toBe(true);
    expect(result.order[0]).toBe("A");
    expect(result.order[result.order.length - 1]).toBe("D");
    expect(result.order.indexOf("B")).toBeLessThan(result.order.indexOf("D"));
    expect(result.order.indexOf("C")).toBeLessThan(result.order.indexOf("D"));
  });

  it("detects a simple cycle A→B→A", () => {
    const result = kahnTopologicalSort(nodes("A", "B"), edges(["A", "B"], ["B", "A"]));
    expect(result.isAcyclic).toBe(false);
    expect(result.order).toHaveLength(0);
    expect(result.remaining.sort()).toEqual(["A", "B"]);
  });

  it("detects a self-loop as a cycle", () => {
    const result = kahnTopologicalSort(nodes("A", "B"), edges(["A", "A"]));
    expect(result.isAcyclic).toBe(false);
    expect(result.remaining).toContain("A");
  });

  it("honours node.dependencies when edges are empty", () => {
    const n: PipelineNode[] = [
      { id: "fetch", type: "fetch", config: {}, dependencies: [] },
      { id: "train", type: "train", config: {}, dependencies: ["fetch"] },
    ];
    const result = kahnTopologicalSort(n, []);
    expect(result.isAcyclic).toBe(true);
    expect(result.order).toEqual(["fetch", "train"]);
  });

  it("returns isolated nodes in declaration order", () => {
    const result = kahnTopologicalSort(nodes("x", "y", "z"), []);
    expect(result.isAcyclic).toBe(true);
    expect(result.order).toEqual(["x", "y", "z"]);
  });
});

describe("validatePipelineGraph", () => {
  it("accepts a valid DAG and returns order", () => {
    const result = validatePipelineGraph({
      nodes: [
        { id: "a", type: "fetch", config: {} },
        { id: "b", type: "notify", config: {}, dependencies: ["a"] },
      ],
      edges: [{ id: "e1", source: "a", target: "b" }],
    });
    expect(result.valid).toBe(true);
    expect(result.order).toEqual(["a", "b"]);
  });

  it("rejects cycles with a cycleHint", () => {
    const result = validatePipelineGraph({
      nodes: [
        { id: "a", type: "fetch", config: {} },
        { id: "b", type: "transform", config: {} },
      ],
      edges: [
        { id: "e1", source: "a", target: "b" },
        { id: "e2", source: "b", target: "a" },
      ],
    });
    expect(result.valid).toBe(false);
    expect(result.cycleHint).toEqual(expect.arrayContaining(["a", "b"]));
  });

  it("rejects duplicate node ids", () => {
    const result = validatePipelineGraph({
      nodes: [
        { id: "a", type: "fetch", config: {} },
        { id: "a", type: "notify", config: {} },
      ],
      edges: [],
    });
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/duplicate/i);
  });
});
