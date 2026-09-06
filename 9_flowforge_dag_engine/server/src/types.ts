import { z } from "zod";

/** Pipeline step kinds — mirrors common Airflow/Prefect-style operators. */
export const NodeTypeSchema = z.enum(["fetch", "transform", "train", "notify"]);
export type NodeType = z.infer<typeof NodeTypeSchema>;

/** Per-node runtime / UI configuration (kept intentionally loose). */
export const NodeConfigSchema = z.record(z.unknown()).default({});
export type NodeConfig = z.infer<typeof NodeConfigSchema>;

export const PipelineNodeSchema = z.object({
  id: z.string().min(1),
  type: NodeTypeSchema,
  label: z.string().min(1).optional(),
  config: NodeConfigSchema,
  /** Explicit upstream ids; edges are the canonical dependency source when present. */
  dependencies: z.array(z.string()).default([]),
  /** Canvas position for round-tripping the editor layout. */
  position: z
    .object({
      x: z.number(),
      y: z.number(),
    })
    .optional(),
});
export type PipelineNode = z.infer<typeof PipelineNodeSchema>;

export const PipelineEdgeSchema = z.object({
  id: z.string().min(1),
  source: z.string().min(1),
  target: z.string().min(1),
});
export type PipelineEdge = z.infer<typeof PipelineEdgeSchema>;

export const PipelineGraphSchema = z.object({
  nodes: z.array(PipelineNodeSchema).min(1),
  edges: z.array(PipelineEdgeSchema).default([]),
});
export type PipelineGraph = z.infer<typeof PipelineGraphSchema>;

export type NodeStatus =
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "blocked";

export type ExecutionEventType =
  | "execution:started"
  | "node:status"
  | "execution:completed"
  | "execution:aborted";

export interface ExecutionEvent {
  type: ExecutionEventType;
  runId: string;
  timestamp: string;
  nodeId?: string;
  status?: NodeStatus;
  message?: string;
  order?: string[];
}

export interface ValidateResult {
  valid: boolean;
  order?: string[];
  error?: string;
  cycleHint?: string[];
}

export interface KahnResult {
  /** Topological order when the graph is a DAG; empty when a cycle exists. */
  order: string[];
  /** True iff every node appears in `order` (graph is acyclic). */
  isAcyclic: boolean;
  /**
   * Nodes that still have unresolved incoming edges after the algorithm
   * finishes — these belong to (or feed into) a cycle.
   */
  remaining: string[];
}
