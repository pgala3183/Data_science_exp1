import type { Filters } from "../hooks/useTasks";
import type { TaskPriority } from "../types";

type Props = {
  filters: Filters;
  allTags: string[];
  onChange: (next: Filters) => void;
};

export function FilterBar({ filters, allTags, onChange }: Props) {
  return (
    <section className="filter-bar" aria-label="Filter tasks">
      <div className="field grow">
        <label htmlFor="search">Search</label>
        <input
          id="search"
          type="search"
          placeholder="Search title, description, or tags"
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="filter-priority">Priority</label>
        <select
          id="filter-priority"
          value={filters.priority}
          onChange={(e) =>
            onChange({ ...filters, priority: e.target.value as TaskPriority | "all" })
          }
        >
          <option value="all">All</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor="filter-tag">Tag</label>
        <select
          id="filter-tag"
          value={filters.tag}
          onChange={(e) => onChange({ ...filters, tag: e.target.value })}
        >
          <option value="">All tags</option>
          {allTags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
