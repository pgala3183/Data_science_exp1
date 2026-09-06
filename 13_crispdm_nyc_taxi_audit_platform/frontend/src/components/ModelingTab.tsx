import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EvalPayload } from "../types";

export function ModelingTab({ data }: { data: EvalPayload }) {
  const cvRows = Object.entries(data.cv).map(([name, m]) => ({
    name: name.replace(/_/g, " "),
    rmse: m.rmse_mean,
  }));

  const holdout = Object.values(data.metrics).map((m) => ({
    name: m.name.replace(/_/g, " "),
    rmse: m.rmse,
    mae: m.mae,
    r2: m.r2,
  }));

  return (
    <div className="stack">
      <section className="panel">
        <h2>Modeling</h2>
        <p className="lede">
          Ridge baseline vs HistGradientBoosting with {Object.values(data.cv)[0]?.cv_folds ?? 3}
          -fold CV on the training window (n={data.n_train.toLocaleString()}). Primary model
          selected by holdout RMSE.
        </p>
        <p className="meta">Primary deployment model: {data.primary_model}</p>
      </section>

      <div className="grid-2">
        <section className="panel">
          <h3>Cross-validation RMSE (train)</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={cvRows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="rmse" name="CV RMSE (s)" fill="#0f766e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel">
          <h3>Holdout metrics</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={holdout}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="rmse" name="RMSE" fill="#0f766e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="mae" name="MAE" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Model</th>
              <th>CV RMSE</th>
              <th>Holdout RMSE</th>
              <th>MAE</th>
              <th>R²</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.metrics).map(([name, m]) => (
              <tr key={name}>
                <td>
                  {name}
                  {name === data.primary_model ? " ★" : ""}
                </td>
                <td className="mono">
                  {data.cv[name]
                    ? `${data.cv[name].rmse_mean.toFixed(1)} ± ${data.cv[name].rmse_std.toFixed(1)}`
                    : "—"}
                </td>
                <td className="mono">{m.rmse.toFixed(1)}</td>
                <td className="mono">{m.mae.toFixed(1)}</td>
                <td className="mono">{m.r2.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
