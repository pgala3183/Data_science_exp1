import { Board } from "./components/Board";
import { FilterBar } from "./components/FilterBar";
import { TaskForm } from "./components/TaskForm";
import { useTasks } from "./hooks/useTasks";
import "./styles.css";

export default function App() {
  const {
    tasks,
    loading,
    error,
    connected,
    filters,
    setFilters,
    allTags,
    createTask,
    deleteTask,
    moveTask,
  } = useTasks();

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to board
      </a>
      <header className="topbar">
        <div>
          <p className="eyebrow">Experiment 0</p>
          <h1>Dynamic Task Workspace</h1>
          <p className="subtitle">Live-synced board over Server-Sent Events</p>
        </div>
        <p className={`live-pill ${connected ? "on" : "off"}`} role="status" aria-live="polite">
          <span className="dot" aria-hidden="true" />
          {connected ? "Live" : "Reconnecting…"}
        </p>
      </header>

      <aside className="sidebar" aria-label="Create and filter">
        <TaskForm onCreate={createTask} />
        <FilterBar filters={filters} allTags={allTags} onChange={setFilters} />
      </aside>

      <main id="main" className="main">
        {error && (
          <p className="banner error" role="alert">
            {error}
          </p>
        )}
        {loading ? <p className="loading">Loading tasks…</p> : <Board tasks={tasks} onDelete={deleteTask} onMove={moveTask} />}
      </main>
    </div>
  );
}
