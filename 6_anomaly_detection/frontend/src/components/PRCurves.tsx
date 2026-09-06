import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EvalResponse } from "../types";

const COLORS: Record<string, string> = {
  isolation_forest: "#0f766e",
  lof: "#b45309",
  autoencoder: "#1d4ed8",
  ensemble: "#be123c",
};

type Props = { data: EvalResponse };

export function PRCurves({ data }: Props) {
  const names = Object.keys(data.pr_curves);
  const recalls = Array.from({ length: 41 }, (_, i) => i / 40);
  const chartData = recalls.map((r) => {
    const row: Record<string, number> = { recall: r };
    for (const n of names) {
      const curve = data.pr_curves[n];
      let best = curve[0];
      let bestD = Infinity;
      for (const p of curve) {
        const d = Math.abs(p.recall - r);
        if (d < bestD) {
          bestD = d;
          best = p;
        }
      }
      row[n] = best.precision;
    }
    return row;
  });

  return (
    <section className="panel" aria-labelledby="pr-title">
      <h2 id="pr-title">Precision–Recall curves</h2>
      <p className="muted">
        Held-out time split · anomaly rate {(data.test_anomaly_rate * 100).toFixed(1)}% · PR-AUC
        preferred over accuracy.
      </p>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="recall"
              type="number"
              domain={[0, 1]}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: "Recall", position: "insideBottom", offset: -2, fill: "#94a3b8" }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{ value: "Precision", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
            />
            <Tooltip />
            <Legend />
            {names.map((n) => (
              <Line
                key={n}
                type="monotone"
                dataKey={n}
                name={`${n} (AP=${data.metrics[n].pr_auc.toFixed(3)})`}
                stroke={COLORS[n] ?? "#e2e8f0"}
                dot={false}
                strokeWidth={n === "ensemble" ? 3 : 2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="metric-cards">
        {names.map((n) => (
          <article key={n}>
            <h3>{n}</h3>
            <p>PR-AUC {data.metrics[n].pr_auc.toFixed(3)}</p>
            <p>
              P {data.metrics[n].precision.toFixed(2)} · R {data.metrics[n].recall.toFixed(2)}
            </p>
            <p className="cm">
              CM [[TN,FP],[FN,TP]] = {JSON.stringify(data.metrics[n].confusion_matrix.matrix)}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
