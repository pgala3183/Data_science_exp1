import { useState } from "react";
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
import { fetchMonitoring } from "../api";
import type { MonitoringPayload } from "../types";

const STATUS_COLOR = {
  green: "#15803d",
  yellow: "#ca8a04",
  red: "#b91c1c",
};

export function MonitoringTab({
  initial,
  onRefresh,
}: {
  initial: MonitoringPayload;
  onRefresh: (p: MonitoringPayload) => void;
}) {
  const [data, setData] = useState(initial);
  const [mode, setMode] = useState<"none" | "moderate" | "severe">(
    (initial.drift_mode as "none" | "moderate" | "severe") || "moderate",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(nextMode = mode) {
    setBusy(true);
    setError(null);
    try {
      const payload = await fetchMonitoring(nextMode, 2500);
      setData(payload);
      onRefresh(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Monitoring failed");
    } finally {
      setBusy(false);
    }
  }

  const chart = data.features.map((f) => ({
    feature: f.feature,
    psi: f.psi,
    status: f.status,
  }));

  return (
    <div className="stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Drift Monitoring</h2>
            <p className="lede">
              Compare a simulated new taxi batch against the training feature reference using
              Population Stability Index (PSI) and Kolmogorov–Smirnov tests.
            </p>
          </div>
          <div className={`status-pill status-${data.overall_status}`}>
            overall · {data.overall_status}
          </div>
        </div>

        <div className="form-actions" style={{ marginTop: "0.75rem" }}>
          {(["none", "moderate", "severe"] as const).map((m) => (
            <button
              key={m}
              type="button"
              className={mode === m ? "chip active" : "chip"}
              disabled={busy}
              onClick={() => {
                setMode(m);
                void run(m);
              }}
            >
              Simulate: {m}
            </button>
          ))}
          <button type="button" disabled={busy} onClick={() => void run()}>
            Refresh
          </button>
        </div>

        <p className="meta" style={{ marginTop: "0.75rem" }}>
          train ref={data.n_train_ref.toLocaleString()} · batch={data.n_batch.toLocaleString()} ·
          red={data.summary.red} · yellow={data.summary.yellow} · green={data.summary.green}
        </p>
      </section>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <section className="panel">
        <h3>Per-feature PSI</h3>
        <div className="chart">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chart} layout="vertical" margin={{ left: 110 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="feature" width={120} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="psi" name="PSI" radius={[0, 4, 4, 0]}>
                {chart.map((r) => (
                  <Cell key={r.feature} fill={STATUS_COLOR[r.status as keyof typeof STATUS_COLOR]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <h3>Feature drift table</h3>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Status</th>
                <th>PSI</th>
                <th>KS</th>
                <th>Train mean</th>
                <th>Batch mean</th>
                <th>Shift</th>
              </tr>
            </thead>
            <tbody>
              {data.features.map((f) => (
                <tr key={f.feature} className={`row-${f.status}`}>
                  <td>{f.feature}</td>
                  <td>
                    <span className={`badge status-${f.status}`}>{f.status}</span>
                  </td>
                  <td className="mono">{f.psi.toFixed(3)}</td>
                  <td className="mono">{f.ks_statistic.toFixed(3)}</td>
                  <td className="mono">{f.train_mean.toFixed(3)}</td>
                  <td className="mono">{f.batch_mean.toFixed(3)}</td>
                  <td className="mono">{f.mean_shift.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel warn">
        <h3>Notes</h3>
        <ul>
          {data.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
        <p className="meta">
          Thresholds: PSI yellow≥{data.thresholds.psi_yellow} red≥{data.thresholds.psi_red} · KS
          yellow≥{data.thresholds.ks_yellow} red≥{data.thresholds.ks_red}
        </p>
      </section>
    </div>
  );
}
