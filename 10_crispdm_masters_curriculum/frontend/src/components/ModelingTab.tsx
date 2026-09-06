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
    roc_auc: m.roc_auc_mean,
    f1: m.f1_mean,
  }));

  return (
    <div className="stack">
      <section className="panel">
        <h2>Modeling</h2>
        <p className="lede">
          Logistic regression baseline vs HistGradientBoosting, with stratified{" "}
          {Object.values(data.cv)[0]?.cv_folds ?? 5}-fold CV on the training set (n=
          {data.n_train.toLocaleString()}).
        </p>
        <p className="meta">Primary deployment model: {data.primary_model}</p>
      </section>

      <section className="panel">
        <h3>Cross-validation (train)</h3>
        <div className="chart">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={cvRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis domain={[0.5, 1]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="roc_auc" name="ROC-AUC" fill="#0f766e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="f1" name="F1" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Model</th>
              <th>CV ROC-AUC</th>
              <th>CV F1</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.cv).map(([name, m]) => (
              <tr key={name}>
                <td>{name}</td>
                <td className="mono">
                  {m.roc_auc_mean.toFixed(3)} ± {m.roc_auc_std.toFixed(3)}
                </td>
                <td className="mono">
                  {m.f1_mean.toFixed(3)} ± {m.f1_std.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
