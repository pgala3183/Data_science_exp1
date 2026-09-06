export type NodeType = "fetch" | "transform" | "train" | "notify";

export type NodeStatus =
  | "idle"
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "blocked";

export interface PipelineNodePayload {
  id: string;
  type: NodeType;
  label?: string;
  config: Record<string, unknown>;
  dependencies: string[];
  position?: { x: number; y: number };
}

export interface PipelineEdgePayload {
  id: string;
  source: string;
  target: string;
}

export interface PipelineGraphPayload {
  nodes: PipelineNodePayload[];
  edges: PipelineEdgePayload[];
}

export interface ValidateResult {
  valid: boolean;
  order?: string[];
  error?: string;
  cycleHint?: string[];
}

export type ExecutionEventType =
  | "connected"
  | "execution:started"
  | "node:status"
  | "execution:completed"
  | "execution:aborted";

export interface ExecutionEvent {
  type: ExecutionEventType;
  runId?: string;
  timestamp?: string;
  nodeId?: string;
  status?: Exclude<NodeStatus, "idle">;
  message?: string;
  order?: string[];
}

export const NODE_TYPE_META: Record<
  NodeType,
  { label: string; accent: string; description: string }
> = {
  fetch: {
    label: "Fetch",
    accent: "#2a9d8f",
    description: "Pull data from a source",
  },
  transform: {
    label: "Transform",
    accent: "#e9c46a",
    description: "Clean / feature engineer",
  },
  train: {
    label: "Train",
    accent: "#e76f51",
    description: "Fit a model",
  },
  notify: {
    label: "Notify",
    accent: "#457b9d",
    description: "Send an alert / report",
  },
};
