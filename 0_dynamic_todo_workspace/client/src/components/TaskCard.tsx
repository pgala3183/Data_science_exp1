import type { KeyboardEvent } from "react";
import type { Task, TaskStatus } from "../types";
import { STATUS_COLUMNS } from "../types";

type Props = {
  task: Task;
  onDelete: (id: string) => void;
  onMove: (id: string, status: TaskStatus) => void;
  onDragStart: (id: string) => void;
};

export function TaskCard({ task, onDelete, onMove, onDragStart }: Props) {
  function handleKeyDown(e: KeyboardEvent<HTMLArticleElement>) {
    if (e.key === "Delete" || e.key === "Backspace") {
      if ((e.target as HTMLElement).tagName === "BUTTON" || (e.target as HTMLElement).tagName === "SELECT") {
        return;
      }
    }
  }

  return (
    <article
      className={`task-card priority-${task.priority}`}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("text/plain", task.id);
        e.dataTransfer.effectAllowed = "move";
        onDragStart(task.id);
      }}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-label={`${task.title}, ${task.priority} priority, ${task.status.replace("_", " ")}`}
    >
      <div className="task-card-top">
        <h3>{task.title}</h3>
        <span className={`badge priority-${task.priority}`}>{task.priority}</span>
      </div>
      {task.description && <p className="task-desc">{task.description}</p>}
      {task.tags.length > 0 && (
        <ul className="tag-list" aria-label="Tags">
          {task.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      )}
      {task.dueDate && (
        <p className="due">
          Due{" "}
          <time dateTime={task.dueDate}>
            {new Date(task.dueDate).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </time>
        </p>
      )}
      <div className="task-actions">
        <label className="sr-only" htmlFor={`move-${task.id}`}>
          Move {task.title} to status
        </label>
        <select
          id={`move-${task.id}`}
          value={task.status}
          onChange={(e) => onMove(task.id, e.target.value as TaskStatus)}
          aria-label={`Change status for ${task.title}`}
        >
          {STATUS_COLUMNS.map((col) => (
            <option key={col.id} value={col.id}>
              {col.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="btn danger"
          onClick={() => onDelete(task.id)}
          aria-label={`Delete ${task.title}`}
        >
          Delete
        </button>
      </div>
    </article>
  );
}
