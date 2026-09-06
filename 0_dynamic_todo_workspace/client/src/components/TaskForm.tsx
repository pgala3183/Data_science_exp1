import type { FormEvent } from "react";
import { useState } from "react";
import type { CreateTaskPayload, TaskPriority, TaskStatus } from "../types";

type Props = {
  onCreate: (payload: CreateTaskPayload) => Promise<void>;
};

export function TaskForm({ onCreate }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const [status, setStatus] = useState<TaskStatus>("todo");
  const [tags, setTags] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setFormError("Title is required");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await onCreate({
        title: title.trim(),
        description: description.trim(),
        priority,
        status,
        dueDate: dueDate ? new Date(dueDate).toISOString() : null,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      setTitle("");
      setDescription("");
      setTags("");
      setDueDate("");
      setPriority("medium");
      setStatus("todo");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not create task");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="task-form" onSubmit={handleSubmit} aria-labelledby="new-task-heading">
      <h2 id="new-task-heading">New task</h2>
      {formError && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}
      <div className="field">
        <label htmlFor="task-title">Title</label>
        <input
          id="task-title"
          name="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          autoComplete="off"
        />
      </div>
      <div className="field">
        <label htmlFor="task-description">Description</label>
        <textarea
          id="task-description"
          name="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          maxLength={5000}
        />
      </div>
      <div className="field-row">
        <div className="field">
          <label htmlFor="task-priority">Priority</label>
          <select
            id="task-priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="task-status">Status</label>
          <select
            id="task-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as TaskStatus)}
          >
            <option value="todo">To do</option>
            <option value="in_progress">In progress</option>
            <option value="done">Done</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="task-due">Due date</label>
          <input
            id="task-due"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor="task-tags">Tags (comma-separated)</label>
        <input
          id="task-tags"
          name="tags"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="design, backend"
          autoComplete="off"
        />
      </div>
      <button type="submit" className="btn primary" disabled={submitting}>
        {submitting ? "Adding…" : "Add task"}
      </button>
    </form>
  );
}
