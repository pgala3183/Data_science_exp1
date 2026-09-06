import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EdaPayload } from "../types";

const ACCENT = "#0f766e";
const INK = "#1e293b";

export function DataUnderstandingTab({ data }: { data: EdaPayload }) {
  const labels = Object.entries(data.label_counts).map(([name, count]) => ({
    name,
    count,
  }));
  const missingTop = data.missingness.filter((m) => m.missing > 0).slice(0, 8);
  const corrTarget = data.correlation.columns.includes("income_gt_50k")
    ? data.correlation.columns
        .map((col, i) => {
          const ti = data.correlation.columns.indexOf("income_gt_50k");
          return {
            feature: col,
            corr: data.correlation.matrix[i]?.[ti] ?? 0,
          };
        })
        .filter((r) => r.feature !== "income_gt_50k")
        .sort((a, b) => Math.abs(b.corr ?? 0) - Math.abs(a.corr ?? 0))
    : [];

  return (
    <div className="stack">
      <section className="panel">
        <h2>Data Understanding</h2>
        <p className="meta">
          {data.n_rows.toLocaleString()} rows · {data.n_cols} columns · positive rate{" "}
          {(data.positive_rate * 100).toFixed(1)}%
        </p>
      </section>

      <div className="grid-2">
        <section className="panel">
          <h3>Class balance</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={labels}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis dataKey="name" tick={{ fill: INK, fontSize: 12 }} />
                <YAxis tick={{ fill: INK, fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill={ACCENT} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel">
          <h3>Missingness (top)</h3>
          {missingTop.length === 0 ? (
            <p className="muted">No missing values after fetch normalization.</p>
          ) : (
            <div className="chart">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={missingTop} layout="vertical" margin={{ left: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="column" width={90} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="missing_pct" name="% missing" fill="#b45309" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>

      <section className="panel">
        <h3>|Correlation| with income &gt; $50K</h3>
        <div className="chart">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={corrTarget}>
              <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
              <XAxis dataKey="feature" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={70} />
              <YAxis tick={{ fontSize: 12 }} domain={[-1, 1]} />
              <Tooltip />
              <Bar dataKey="corr" name="corr">
                {corrTarget.map((r) => (
                  <Cell key={r.feature} fill={(r.corr ?? 0) >= 0 ? ACCENT : "#b91c1c"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid-2">
        <RatePanel title=">50K rate by sex" rows={data.target_by_sex} />
        <RatePanel title=">50K rate by race" rows={data.target_by_race} />
      </div>

      <section className="panel">
        <h3>Numeric summary</h3>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Mean</th>
                <th>Std</th>
                <th>Min</th>
                <th>Median</th>
                <th>Max</th>
              </tr>
            </thead>
            <tbody>
              {data.numeric_summary.map((r) => (
                <tr key={r.column}>
                  <td>{r.column}</td>
                  <td className="mono">{fmt(r.mean)}</td>
                  <td className="mono">{fmt(r.std)}</td>
                  <td className="mono">{fmt(r.min)}</td>
                  <td className="mono">{fmt(r.median)}</td>
                  <td className="mono">{fmt(r.max)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function RatePanel({
  title,
  rows,
}: {
  title: string;
  rows: { group: string; n: number; gt_50k_rate: number }[];
}) {
  return (
    <section className="panel">
      <h3>{title}</h3>
      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
            <XAxis dataKey="group" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
            <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} />
            <Bar dataKey="gt_50k_rate" fill={ACCENT} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function fmt(v: number | null) {
  return v == null ? "—" : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
