import type { Filters, Rule } from "../types";

type Props = {
  rules: Rule[];
  total: number;
  page: number;
  pageSize: number;
  filters: Filters;
  benchmarks: { algorithm: string; seconds: number; n_itemsets: number; peak_note: string }[];
  onFilters: (f: Filters) => void;
  onPage: (p: number) => void;
};

export function RulesTable({
  rules,
  total,
  page,
  pageSize,
  filters,
  benchmarks,
  onFilters,
  onPage,
}: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <section className="panel" aria-labelledby="rules-title">
      <h2 id="rules-title">Association rules</h2>
      <div className="filters" role="group" aria-label="Rule filters">
        <label>
          Min support ({filters.min_support.toFixed(2)})
          <input
            type="range"
            min={0.01}
            max={0.2}
            step={0.01}
            value={filters.min_support}
            onChange={(e) => onFilters({ ...filters, min_support: Number(e.target.value) })}
          />
        </label>
        <label>
          Min confidence ({filters.min_confidence.toFixed(2)})
          <input
            type="range"
            min={0.05}
            max={0.9}
            step={0.05}
            value={filters.min_confidence}
            onChange={(e) => onFilters({ ...filters, min_confidence: Number(e.target.value) })}
          />
        </label>
        <label>
          Min lift ({filters.min_lift.toFixed(1)})
          <input
            type="range"
            min={0.5}
            max={5}
            step={0.1}
            value={filters.min_lift}
            onChange={(e) => onFilters({ ...filters, min_lift: Number(e.target.value) })}
          />
        </label>
        <label>
          Sort by
          <select
            value={filters.sort_by}
            onChange={(e) =>
              onFilters({ ...filters, sort_by: e.target.value as Filters["sort_by"] })
            }
          >
            <option value="lift">Lift</option>
            <option value="confidence">Confidence</option>
            <option value="support">Support</option>
          </select>
        </label>
      </div>

      <div className="bench">
        {benchmarks.map((b) => (
          <p key={b.algorithm}>
            <strong>{b.algorithm}</strong>: {b.seconds}s · {b.n_itemsets} itemsets — {b.peak_note}
          </p>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Antecedent</th>
              <th scope="col">Consequent</th>
              <th scope="col">Support</th>
              <th scope="col">Confidence</th>
              <th scope="col">Lift</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r, i) => (
              <tr key={`${r.antecedents.join()}-${r.consequents.join()}-${i}`}>
                <td>{r.antecedents.join(", ")}</td>
                <td>{r.consequents.join(", ")}</td>
                <td>{r.support.toFixed(3)}</td>
                <td>{r.confidence.toFixed(3)}</td>
                <td>{r.lift.toFixed(3)}</td>
              </tr>
            ))}
            {rules.length === 0 && (
              <tr>
                <td colSpan={5}>No rules match these thresholds.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="pager">
        <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Prev
        </button>
        <span>
          Page {page} / {pages} · {total} rules
        </span>
        <button type="button" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Next
        </button>
      </div>
    </section>
  );
}
