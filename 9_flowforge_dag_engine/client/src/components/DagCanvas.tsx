import { useCallback, useEffect, useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type OnConnect,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { PipelineNode, type PipelineNodeData } from "./PipelineNode";
import type { NodeStatus, NodeType, PipelineGraphPayload } from "../types";
import { NODE_TYPE_META } from "../types";

const nodeTypes: NodeTypes = {
  pipeline: PipelineNode,
};

let idCounter = 1;
function nextId(type: NodeType): string {
  return `${type}_${idCounter++}`;
}

const INITIAL_NODES: Node<PipelineNodeData>[] = [
  {
    id: "fetch_seed",
    type: "pipeline",
    position: { x: 80, y: 160 },
    data: { nodeType: "fetch", label: "fetch_seed", status: "idle" },
  },
  {
    id: "transform_seed",
    type: "pipeline",
    position: { x: 320, y: 160 },
    data: { nodeType: "transform", label: "transform_seed", status: "idle" },
  },
  {
    id: "train_seed",
    type: "pipeline",
    position: { x: 560, y: 160 },
    data: { nodeType: "train", label: "train_seed", status: "idle" },
  },
  {
    id: "notify_seed",
    type: "pipeline",
    position: { x: 800, y: 160 },
    data: { nodeType: "notify", label: "notify_seed", status: "idle" },
  },
];

const INITIAL_EDGES: Edge[] = [
  { id: "e1", source: "fetch_seed", target: "transform_seed", animated: false },
  { id: "e2", source: "transform_seed", target: "train_seed", animated: false },
  { id: "e3", source: "train_seed", target: "notify_seed", animated: false },
];

// Keep counter above seed ids.
idCounter = 10;

interface Props {
  statuses: Record<string, NodeStatus>;
  running: boolean;
  onGraphChange: (graph: PipelineGraphPayload) => void;
  registerApi: (api: {
    addNode: (type: NodeType) => void;
    getGraph: () => PipelineGraphPayload;
    resetStatusesVisual: () => void;
  }) => void;
}

export function DagCanvas({ statuses, running, onGraphChange, registerApi }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);

  const decoratedNodes = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          status: (statuses[n.id] ?? "idle") as NodeStatus,
        },
      })),
    [nodes, statuses],
  );

  const decoratedEdges = useMemo(
    () =>
      edges.map((e) => {
        const srcStatus = statuses[e.source];
        const animated = srcStatus === "running" || srcStatus === "success";
        const failed =
          srcStatus === "failed" ||
          statuses[e.target] === "blocked" ||
          statuses[e.target] === "failed";
        return {
          ...e,
          animated: animated && !failed,
          style: failed
            ? { stroke: "#c1121f", strokeDasharray: "4 4" }
            : srcStatus === "success"
              ? { stroke: "#2a9d8f" }
              : undefined,
        };
      }),
    [edges, statuses],
  );

  const toPayload = useCallback(
    (ns: Node<PipelineNodeData>[], es: Edge[]): PipelineGraphPayload => {
      const deps = new Map<string, string[]>();
      for (const n of ns) deps.set(n.id, []);
      for (const e of es) {
        const list = deps.get(e.target) ?? [];
        list.push(e.source);
        deps.set(e.target, list);
      }
      return {
        nodes: ns.map((n) => ({
          id: n.id,
          type: n.data.nodeType,
          label: n.data.label,
          config: {},
          dependencies: deps.get(n.id) ?? [],
          position: n.position,
        })),
        edges: es.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
        })),
      };
    },
    [],
  );

  const emitGraph = useCallback(
    (ns: Node<PipelineNodeData>[], es: Edge[]) => {
      onGraphChange(toPayload(ns, es));
    },
    [onGraphChange, toPayload],
  );

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      if (running) return;
      setEdges((eds) => {
        const next = addEdge(
          { ...connection, id: `e_${connection.source}_${connection.target}_${Date.now()}` },
          eds,
        );
        setNodes((ns) => {
          emitGraph(ns, next);
          return ns;
        });
        return next;
      });
    },
    [emitGraph, running, setEdges, setNodes],
  );

  const addNode = useCallback(
    (type: NodeType) => {
      if (running) return;
      const id = nextId(type);
      const meta = NODE_TYPE_META[type];
      const node: Node<PipelineNodeData> = {
        id,
        type: "pipeline",
        position: {
          x: 120 + Math.random() * 420,
          y: 80 + Math.random() * 280,
        },
        data: {
          nodeType: type,
          label: id,
          status: "idle",
        },
      };
      setNodes((ns) => {
        const next = [...ns, node];
        setEdges((es) => {
          emitGraph(next, es);
          return es;
        });
        return next;
      });
      void meta;
    },
    [emitGraph, running, setEdges, setNodes],
  );

  const getGraph = useCallback(() => toPayload(nodes, edges), [nodes, edges, toPayload]);

  const resetStatusesVisual = useCallback(() => {
    // Statuses come from parent; no local mutation needed.
  }, []);

  // Expose imperative API to parent (palette / toolbar).
  useEffect(() => {
    registerApi({ addNode, getGraph, resetStatusesVisual });
  }, [addNode, getGraph, registerApi, resetStatusesVisual]);

  const onNodesChangeWrapped = useCallback(
    (changes: Parameters<typeof onNodesChange>[0]) => {
      if (running) {
        // Allow selection changes only while running.
        const safe = changes.filter((c) => c.type === "select");
        if (safe.length) onNodesChange(safe);
        return;
      }
      onNodesChange(changes);
    },
    [onNodesChange, running],
  );

  const onEdgesChangeWrapped = useCallback(
    (changes: Parameters<typeof onEdgesChange>[0]) => {
      if (running) {
        const safe = changes.filter((c) => c.type === "select");
        if (safe.length) onEdgesChange(safe);
        return;
      }
      onEdgesChange(changes);
    },
    [onEdgesChange, running],
  );

  // Notify parent when nodes/edges settle after drag/remove.
  const onNodeDragStop = useCallback(() => {
    emitGraph(nodes, edges);
  }, [emitGraph, nodes, edges]);

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      const next = edges.filter((e) => !deleted.some((d) => d.id === e.id));
      emitGraph(nodes, next);
    },
    [emitGraph, edges, nodes],
  );

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      const ids = new Set(deleted.map((d) => d.id));
      const nextNodes = nodes.filter((n) => !ids.has(n.id));
      const nextEdges = edges.filter((e) => !ids.has(e.source) && !ids.has(e.target));
      emitGraph(nextNodes, nextEdges);
    },
    [emitGraph, edges, nodes],
  );

  return (
    <div className="canvas-wrap">
      <ReactFlow
        nodes={decoratedNodes}
        edges={decoratedEdges}
        onNodesChange={onNodesChangeWrapped}
        onEdgesChange={onEdgesChangeWrapped}
        onConnect={onConnect}
        onNodeDragStop={onNodeDragStop}
        onEdgesDelete={onEdgesDelete}
        onNodesDelete={onNodesDelete}
        nodeTypes={nodeTypes}
        fitView
        deleteKeyCode={running ? null : ["Backspace", "Delete"]}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={18} size={1} color="#2a3340" />
        <Controls />
        <MiniMap
          nodeColor={(n) => NODE_TYPE_META[(n.data as PipelineNodeData).nodeType].accent}
          maskColor="rgba(10, 14, 20, 0.7)"
        />
      </ReactFlow>
    </div>
  );
}
