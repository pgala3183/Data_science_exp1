# Dynamic Task Workspace (Experiment 0)

A full-stack collaborative task board where every CRUD change is pushed live to open browser tabs over **Server-Sent Events (SSE)** — no polling and no WebSocket handshake required.

## Problem statement

Teams often keep a simple todo board open in multiple tabs or on multiple machines. Classic REST UIs force a refresh (or noisy polling) to see someone else’s edits. This experiment builds a small workspace where create / update / delete / status moves appear everywhere within a second, while keeping the stack deliberately simple and inspectable.

## Dataset & source

No external dataset. Tasks are user-generated application data. Persistence is swappable:

| Driver | Env | Notes |
|--------|-----|--------|
| `memory` (default) | `STORAGE=memory` | Fast, resets on restart — good for demos/tests |
| `sqlite` | `STORAGE=sqlite` | File at `server/data/tasks.db` |

Both implement the same `ITaskRepository` interface.

## Methodology / architecture

```
client (React + Vite :5173)
   │  REST  /api/tasks*
   │  SSE   /api/events
   ▼
server (Express :8000)
   ├─ routes → validation (Zod) → repository
   └─ SseHub.broadcast() on every mutation
```

- **Repository pattern:** `ITaskRepository` with `InMemoryTaskRepository` and `SqliteTaskRepository`.
- **REST:** CRUD on tasks (`id`, `title`, `description`, `status`, `priority`, `dueDate`, `tags`, timestamps) plus `POST /api/tasks/reorder`.
- **SSE:** After a successful mutation the API publishes a typed event (`task:created`, `task:updated`, `task:deleted`, `tasks:reordered`). Connected clients update local state; the UI never polls.

### Why SSE (design decision)

We chose **SSE over WebSockets** for this board because:

1. **One-way fan-out fits the product.** Clients already send mutations via REST. They only need a reliable *server → client* stream for live sync. SSE is purpose-built for that.
2. **Simpler ops.** Plain HTTP (`text/event-stream`), works through the Vite proxy, auto-reconnect via `EventSource`, no upgrade handshake or custom ping protocol (we still send comment keepalives for idle proxies).
3. **Enough for tab sync.** Multiple open tabs each open an `EventSource`; one write on the server fans out to all of them.

WebSockets would be preferable if we needed client-originated realtime frames (presence cursors, collaborative typing). For “board stays in sync,” SSE is the smaller correct tool.

## How to run

Ports follow the portfolio convention for experiment **0**: backend **8000**, frontend **5173**.

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

Open http://localhost:5173 — the Vite dev server proxies `/api` to the Express app.

Optional durable storage:

```bash
# Windows PowerShell
$env:STORAGE="sqlite"; npm run dev
```

### Scripts

| Location | Command | Purpose |
|----------|---------|---------|
| `server/` | `npm run dev` | API with hot reload (`tsx watch`) |
| `server/` | `npm test` | Vitest + Supertest |
| `server/` | `npm run lint` / `npm run format` | ESLint + Prettier |
| `client/` | `npm run dev` | Vite on :5173 |
| `client/` | `npm run lint` / `npm run format` | ESLint + Prettier |

## Key result / metric

**Live multi-tab sync without polling:** open two browser tabs, create or drag a task in one — the other updates via SSE within the same request/response cycle of the mutating tab (typically &lt;100 ms on localhost). Verify with DevTools → Network → `events` (type `eventsource`) while mutating.

## API sketch

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/api/health` | 200 |
| `GET` | `/api/tasks` | 200 |
| `POST` | `/api/tasks` | 201 / 400 |
| `GET` | `/api/tasks/:id` | 200 / 404 |
| `PATCH` | `/api/tasks/:id` | 200 / 400 / 404 |
| `DELETE` | `/api/tasks/:id` | 204 / 404 |
| `POST` | `/api/tasks/reorder` | 200 / 400 |
| `GET` | `/api/events` | SSE stream |

## Accessibility notes

- Skip link to the board, labeled form controls, status region for live connection, keyboard-focusable cards, and a status `<select>` on each card so status can change without drag-and-drop.
