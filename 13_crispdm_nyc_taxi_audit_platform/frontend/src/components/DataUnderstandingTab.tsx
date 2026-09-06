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
  const buckets = Object.entries(data.label_counts).map(([name, count]) => ({
    name,
    count,
  }));
  const missingTop = data.missingness.filter((m) => m.missing > 0).slice(0, 8);

  const corrTarget = data.correlation.columns.includes("trip_duration")
    ? data.correlation.columns
        .map((col, i) => {
          const ti = data.correlation.columns.indexOf("trip_duration");
          return {
            feature: col,
            corr: data.correlation.matrix[i]?.[ti] ?? 0,
          };
        })
        .filter((r) => r.feature !== "trip_duration")
        .sort((a, b) => Math.abs(b.corr ?? 0) - Math.abs(a.corr ?? 0))
    : [];

  const byHour = data.duration_by_hour.map((r) => ({
    hour: r.group,
    mean_min: r.mean_duration / 60,
  }));

  return (
    <div className="stack">
      <section className="panel">
        <h2>Data Understanding</h2>
        <p className="meta">
          {data.n_rows.toLocaleString()} rows · {data.n_cols} columns · mean duration{" "}
          {(data.mean_duration / 60).toFixed(1)} min · median{" "}
          {(data.median_duration / 60).toFixed(1)} min
        </p>
      </section>

      <div className="grid-2">
        <section className="panel">
          <h3>Duration buckets</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={buckets}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis dataKey="name" tick={{ fill: INK, fontSize: 11 }} />
                <YAxis tick={{ fill: INK, fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill={ACCENT} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel">
          <h3>Mean duration by hour</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={byHour}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 12 }} unit="m" />
                <Tooltip formatter={(v: number) => `${v.toFixed(1)} min`} />
                <Bar dataKey="mean_min" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <section className="panel">
        <h3>|Correlation| with trip_duration</h3>
        <div className="chart">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={corrTarget}>
              <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
              <XAxis
                dataKey="feature"
                tick={{ fontSize: 11 }}
                interval={0}
                angle={-20}
                textAnchor="end"
                height={70}
              />
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
        <RatePanel title="Mean duration by weekend" rows={data.duration_by_weekend} />
        <RatePanel title="Mean duration by rush hour" rows={data.duration_by_rush} />
      </div>

      {missingTop.length > 0 && (
        <section className="panel">
          <h3>Missingness</h3>
          <p className="muted">{missingTop.length} columns with missing values.</p>
        </section>
      )}

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
  rows: { group: string; n: number; mean_duration: number }[];
}) {
  const chart = rows.map((r) => ({
    group: r.group === "0" ? "no" : r.group === "1" ? "yes" : r.group,
    mean_min: r.mean_duration / 60,
  }));
  return (
    <section className="panel">
      <h3>{title}</h3>
      <div className="chart">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
            <XAxis dataKey="group" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v: number) => `${v.toFixed(1)} min`} />
            <Bar dataKey="mean_min" fill={ACCENT} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function fmt(v: number | null) {
  return v == null ? "—" : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
