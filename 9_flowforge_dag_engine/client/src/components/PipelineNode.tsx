import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { NodeStatus, NodeType } from "../types";
import { NODE_TYPE_META } from "../types";

export type PipelineNodeData = {
  nodeType: NodeType;
  label: string;
  status: NodeStatus;
};

const STATUS_LABEL: Record<NodeStatus, string> = {
  idle: "idle",
  pending: "pending",
  running: "running",
  success: "success",
  failed: "failed",
  blocked: "blocked",
};

export function PipelineNode({ data, selected }: NodeProps) {
  const d = data as PipelineNodeData;
  const meta = NODE_TYPE_META[d.nodeType];
  const status = d.status ?? "idle";

  return (
    <div
      className={`pipeline-node status-${status}${selected ? " selected" : ""}`}
      style={{ ["--accent" as string]: meta.accent }}
    >
      <Handle type="target" position={Position.Left} className="node-handle" />
      <div className="pipeline-node__type">{meta.label}</div>
      <div className="pipeline-node__label">{d.label}</div>
      <div className={`pipeline-node__status badge-${status}`}>
        {STATUS_LABEL[status]}
        {status === "running" ? <span className="pulse" /> : null}
      </div>
      <Handle type="source" position={Position.Right} className="node-handle" />
    </div>
  );
}
