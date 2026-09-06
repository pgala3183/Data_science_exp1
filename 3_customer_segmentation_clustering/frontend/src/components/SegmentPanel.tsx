import { CLUSTER_COLORS } from "../colors";
import type { SegmentCustomers, SegmentProfile } from "../types";

type Props = {
  profiles: SegmentProfile[];
  selectedId: number | null;
  customers: SegmentCustomers | null;
  onSelect: (id: number) => void;
};

export function SegmentPanel({ profiles, selectedId, customers, onSelect }: Props) {
  return (
    <section className="panel segments" aria-labelledby="seg-title">
      <h2 id="seg-title">Segments &amp; actions</h2>
      <div className="seg-grid">
        {profiles.map((p, i) => (
          <article
            key={p.cluster_id}
            className={`seg-card ${selectedId === p.cluster_id ? "active" : ""}`}
            style={{ borderTopColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}
          >
            <button type="button" className="seg-hit" onClick={() => onSelect(p.cluster_id)}>
              <header>
                <h3>{p.name}</h3>
                <span className="size">{p.size} customers</span>
              </header>
              <p>{p.description}</p>
              <dl>
                <div>
                  <dt>Recency</dt>
                  <dd>{p.centroid.Recency.toFixed(0)}d</dd>
                </div>
                <div>
                  <dt>Frequency</dt>
                  <dd>{p.centroid.Frequency.toFixed(1)}</dd>
                </div>
                <div>
                  <dt>Monetary</dt>
                  <dd>${p.centroid.Monetary.toFixed(0)}</dd>
                </div>
              </dl>
              <h4>Suggested actions</h4>
              <ul>
                {p.marketing_actions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </button>
          </article>
        ))}
      </div>

      {customers && (
        <div className="customer-table" aria-live="polite">
          <h3>
            Sample: {customers.name} ({customers.total} total)
          </h3>
          <table>
            <thead>
              <tr>
                <th scope="col">Customer</th>
                <th scope="col">R</th>
                <th scope="col">F</th>
                <th scope="col">M</th>
              </tr>
            </thead>
            <tbody>
              {customers.customers.map((c) => (
                <tr key={c.customer_id}>
                  <td>{c.customer_id}</td>
                  <td>{c.Recency.toFixed(0)}</td>
                  <td>{c.Frequency}</td>
                  <td>${c.Monetary.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
