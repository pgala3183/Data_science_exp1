import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EvalPayload, FairnessGroup } from "../types";

export function EvaluationTab({ data }: { data: EvalPayload }) {
  const models = Object.keys(data.metrics);
  const [model, setModel] = useState(data.primary_model || models[0]);
  const m = data.metrics[model];
  const fair = data.fairness[model];
  const resid = data.residuals[model];

  const hist =
    resid?.histogram.bin_edges.slice(0, -1).map((edge, i) => ({
      bin: Math.round(edge),
      count: resid.histogram.counts[i],
    })) ?? [];

  const importances = Object.entries(m.feature_importances)
    .map(([feature, importance]) => ({ feature, importance }))
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 8);

  return (
    <div className="stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Evaluation</h2>
            <p className="lede">
              Time-based holdout (n={data.n_test.toLocaleString()}) plus residual diagnostics and
              geographic group-fairness by pickup cluster.
            </p>
          </div>
          <label className="field inline">
            Model
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {models.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="metric-row">
          <Metric label="RMSE (s)" value={m.rmse} highlight />
          <Metric label="MAE (s)" value={m.mae} />
          <Metric label="R²" value={m.r2} digits={3} />
        </div>
      </section>

      <div className="grid-2">
        <section className="panel">
          <h3>Residual histogram</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={hist}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis dataKey="bin" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#0f766e" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {resid && (
            <p className="meta">
              mean={resid.mean.toFixed(1)} · σ={resid.std.toFixed(1)} · p05={resid.p05.toFixed(1)} ·
              p95={resid.p95.toFixed(1)}
            </p>
          )}
        </section>

        <section className="panel">
          <h3>Feature importance</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={importances} layout="vertical" margin={{ left: 90 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="feature" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="importance" fill="#1d4ed8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      {fair && (
        <>
          {Object.entries(fair.by_attribute).map(([attr, groups]) => (
            <FairnessTable key={attr} attr={attr} groups={groups} />
          ))}
          <section className="panel warn">
            <h3>Disparity summary (bias audit)</h3>
            {Object.entries(fair.disparities).map(([attr, d]) => (
              <p key={attr}>
                <strong>{attr}</strong>: MAE range {d.mae_range.toFixed(1)}s (majority=
                {d.majority_group}). {d.note}
              </p>
            ))}
          </section>
        </>
      )}

      <section className="panel">
        <h3>Evaluation write-up</h3>
        <article className="markdown">
          <pre>{data.evaluation_doc}</pre>
        </article>
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  highlight,
  digits = 1,
}: {
  label: string;
  value: number;
  highlight?: boolean;
  digits?: number;
}) {
  return (
    <div className={`metric ${highlight ? "metric-hi" : ""}`}>
      <span>{label}</span>
      <strong className="mono">{value.toFixed(digits)}</strong>
    </div>
  );
}

function FairnessTable({ attr, groups }: { attr: string; groups: FairnessGroup[] }) {
  return (
    <section className="panel">
      <h3>Group fairness by {attr}</h3>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Group</th>
              <th>n</th>
              <th>Mean duration</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>Mean residual</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.group}>
                <td>{g.group}</td>
                <td className="mono">{g.support}</td>
                <td className="mono">{g.mean_duration.toFixed(0)}</td>
                <td className="mono">{g.mae.toFixed(1)}</td>
                <td className="mono">{g.rmse.toFixed(1)}</td>
                <td className="mono">{g.mean_residual.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
