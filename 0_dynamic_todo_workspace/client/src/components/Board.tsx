import { useState } from "react";
import type { Task, TaskStatus } from "../types";
import { STATUS_COLUMNS } from "../types";
import { TaskCard } from "./TaskCard";

type Props = {
  tasks: Task[];
  onDelete: (id: string) => Promise<void>;
  onMove: (id: string, status: TaskStatus) => Promise<void>;
};

export function Board({ tasks, onDelete, onMove }: Props) {
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<TaskStatus | null>(null);

  async function handleDrop(status: TaskStatus) {
    if (!draggingId) return;
    const task = tasks.find((t) => t.id === draggingId);
    setDropTarget(null);
    setDraggingId(null);
    if (task && task.status !== status) {
      await onMove(draggingId, status);
    }
  }

  return (
    <div className="board" role="region" aria-label="Task board">
      {STATUS_COLUMNS.map((col) => {
        const columnTasks = tasks
          .filter((t) => t.status === col.id)
          .sort((a, b) => a.sortOrder - b.sortOrder);
        return (
          <section
            key={col.id}
            className={`column ${dropTarget === col.id ? "drop-active" : ""}`}
            aria-labelledby={`col-${col.id}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDropTarget(col.id);
            }}
            onDragLeave={() => setDropTarget((cur) => (cur === col.id ? null : cur))}
            onDrop={(e) => {
              e.preventDefault();
              handleDrop(col.id);
            }}
          >
            <header className="column-header">
              <h2 id={`col-${col.id}`}>{col.label}</h2>
              <span className="count" aria-label={`${columnTasks.length} tasks`}>
                {columnTasks.length}
              </span>
            </header>
            <div className="column-body">
              {columnTasks.length === 0 ? (
                <p className="empty">Drop tasks here</p>
              ) : (
                columnTasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onDelete={(id) => void onDelete(id)}
                    onMove={(id, status) => void onMove(id, status)}
                    onDragStart={setDraggingId}
                  />
                ))
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
