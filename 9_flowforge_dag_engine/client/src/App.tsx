import { useCallback, useEffect, useRef, useState } from "react";
import { DagCanvas } from "./components/DagCanvas";
import { NodePalette } from "./components/NodePalette";
import { ValidationBanner } from "./components/ValidationBanner";
import { executeGraph, validateGraph } from "./api";
import { useExecutionStream } from "./hooks/useExecutionStream";
import type { NodeType, PipelineGraphPayload, ValidateResult } from "./types";
import "./App.css";

const SEED_GRAPH: PipelineGraphPayload = {
  nodes: [
    {
      id: "fetch_seed",
      type: "fetch",
      label: "fetch_seed",
      config: {},
      dependencies: [],
      position: { x: 80, y: 160 },
    },
    {
      id: "transform_seed",
      type: "transform",
      label: "transform_seed",
      config: {},
      dependencies: ["fetch_seed"],
      position: { x: 320, y: 160 },
    },
    {
      id: "train_seed",
      type: "train",
      label: "train_seed",
      config: {},
      dependencies: ["transform_seed"],
      position: { x: 560, y: 160 },
    },
    {
      id: "notify_seed",
      type: "notify",
      label: "notify_seed",
      config: {},
      dependencies: ["train_seed"],
      position: { x: 800, y: 160 },
    },
  ],
  edges: [
    { id: "e1", source: "fetch_seed", target: "transform_seed" },
    { id: "e2", source: "transform_seed", target: "train_seed" },
    { id: "e3", source: "train_seed", target: "notify_seed" },
  ],
};

export default function App() {
  const [graph, setGraph] = useState<PipelineGraphPayload>(SEED_GRAPH);
  const [validation, setValidation] = useState<ValidateResult | null>(null);
  const { statuses, running, lastMessage, resetStatuses } = useExecutionStream();

  const apiRef = useRef<{
    addNode: (type: NodeType) => void;
    getGraph: () => PipelineGraphPayload;
    resetStatusesVisual: () => void;
  } | null>(null);

  const registerApi = useCallback(
    (api: NonNullable<typeof apiRef.current>) => {
      apiRef.current = api;
    },
    [],
  );

  // Re-validate whenever the graph structure changes (debounced lightly).
  useEffect(() => {
    let cancelled = false;
    const t = window.setTimeout(() => {
      void validateGraph(graph).then((r) => {
        if (!cancelled) setValidation(r);
      });
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, [graph]);

  const onAdd = (type: NodeType) => {
    apiRef.current?.addNode(type);
  };

  const onValidate = async () => {
    const g = apiRef.current?.getGraph() ?? graph;
    setGraph(g);
    const r = await validateGraph(g);
    setValidation(r);
  };

  const onExecute = async () => {
    const g = apiRef.current?.getGraph() ?? graph;
    setGraph(g);
    const r = await validateGraph(g);
    setValidation(r);
    if (!r.valid) return;

    resetStatuses();
    await executeGraph(g);
  };

  const canExecute = Boolean(validation?.valid) && !running;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark">FF</span>
          <div>
            <h1>FlowForge</h1>
            <p>Lightweight DAG workflow builder — Kahn topological execution</p>
          </div>
        </div>
        <div className="topbar__actions">
          <button type="button" className="btn btn--ghost" onClick={() => void onValidate()} disabled={running}>
            Validate
          </button>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => void onExecute()}
            disabled={!canExecute}
            title={validation?.valid ? "Run in topological order" : "Fix cycles before running"}
          >
            {running ? "Running…" : "Execute"}
          </button>
        </div>
      </header>

      <ValidationBanner result={validation} />

      <div className="workspace">
        <NodePalette onAdd={onAdd} disabled={running} />
        <main className="workspace__main">
          <DagCanvas
            statuses={statuses}
            running={running}
            onGraphChange={setGraph}
            registerApi={registerApi}
          />
          <footer className="statusline">
            <span>{lastMessage ?? "Idle — edit the graph, then Execute."}</span>
            {running ? <span className="statusline__live">LIVE</span> : null}
          </footer>
        </main>
      </div>
    </div>
  );
}
