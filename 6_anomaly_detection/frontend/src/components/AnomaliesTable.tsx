import { useMemo, useState } from "react";

type Row = Record<string, string | number>;

type Props = { rows: Row[] };

type SortKey = "score_ensemble" | "score_isolation_forest" | "score_lof" | "score_autoencoder";

export function AnomaliesTable({ rows }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("score_ensemble");
  const sorted = useMemo(
    () => [...rows].sort((a, b) => Number(b[sortKey] ?? 0) - Number(a[sortKey] ?? 0)),
    [rows, sortKey],
  );

  return (
    <section className="panel" aria-labelledby="top-title">
      <div className="panel-head">
        <h2 id="top-title">Most anomalous test records</h2>
        <label>
          Sort by{" "}
          <select value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)}>
            <option value="score_ensemble">ensemble</option>
            <option value="score_isolation_forest">isolation_forest</option>
            <option value="score_lof">lof</option>
            <option value="score_autoencoder">autoencoder</option>
          </select>
        </label>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>time</th>
              <th>true</th>
              <th>kind</th>
              <th>IF</th>
              <th>LOF</th>
              <th>AE</th>
              <th>ensemble</th>
            </tr>
          </thead>
          <tbody>
            {sorted.slice(0, 30).map((r, i) => (
              <tr key={i} className={Number(r.is_anomaly) === 1 ? "anom" : ""}>
                <td>{String(r.timestamp).slice(0, 16)}</td>
                <td>{r.is_anomaly}</td>
                <td>{r.anomaly_kind}</td>
                <td>{Number(r.score_isolation_forest).toFixed(3)}</td>
                <td>{Number(r.score_lof).toFixed(3)}</td>
                <td>{Number(r.score_autoencoder).toFixed(3)}</td>
                <td>{Number(r.score_ensemble).toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
