# FlowForge DAG Engine (Experiment 9)

A lightweight visual **DAG** (directed acyclic graph) workflow builder in TypeScript — a minimal Airflow/Prefect-style editor that validates acyclicity with **Kahn’s algorithm** and streams mock execution status over **SSE**.

## Design

```
client (React + Vite + @xyflow/react :5179)
   │  REST  POST /api/validate
   │  REST  POST /api/execute
   │  SSE   GET  /api/events
   ▼
server (Express :8009)
   ├─ Zod schema (nodes / edges)
   ├─ Kahn topological sort (hand-rolled)
   └─ Mock runner → SseHub status fan-out
```

- **Schema:** each step has `id`, `type` (`fetch` | `transform` | `train` | `notify`), `config`, and `dependencies` (plus canvas `position`).
- **Kahn’s algorithm:** implemented in `server/src/graph/kahn.ts` with step-by-step comments — no library for the topo sort.
- **Execution:** nodes run in topological order with simulated latency and occasional failures; downstream dependents are marked `blocked`.
- **UI:** drag edges on the React Flow canvas, palette to add steps, live status badges, and a validation banner that blocks Execute on cycles.

## How to run

Ports: API **8009**, UI **5179**.

```bash
# Terminal 1 — API
cd server
npm install
npm run dev

# Terminal 2 — UI
cd client
npm install
npm run dev
```

Open http://localhost:5179.

### Tests

```bash
cd server
npm test
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/health` | Liveness |
| `POST` | `/api/validate` | Schema + Kahn acyclicity check → `{ valid, order?, error?, cycleHint? }` |
| `POST` | `/api/execute` | Validate then accept run (`202`); status streams on SSE |
| `GET` | `/api/events` | SSE: `execution:started`, `node:status`, `execution:completed` |

### Example graph body

```json
{
  "nodes": [
    { "id": "fetch_1", "type": "fetch", "config": {}, "dependencies": [] },
    { "id": "train_1", "type": "train", "config": {}, "dependencies": ["fetch_1"] }
  ],
  "edges": [
    { "id": "e1", "source": "fetch_1", "target": "train_1" }
  ]
}
```

## Kahn’s algorithm (core concept)

1. Count indegrees; queue every node with indegree `0`.
2. Peel a ready node, append to the order, decrement neighbors.
3. When a neighbor hits indegree `0`, enqueue it.
4. If the order length equals `|V|`, the graph is a DAG; otherwise leftover nodes with positive indegree participate in a cycle.

That linearization is the execution order FlowForge uses for the mock runner.
