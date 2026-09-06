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
import type { SegmentsResponse } from "../types";

type Props = { data: SegmentsResponse };

export function ModelSelectionCharts({ data }: Props) {
  const merged = data.silhouette_curve.map((s) => {
    const inertia = data.inertia_curve.find((i) => i.k === s.k)?.inertia ?? null;
    return {
      k: s.k,
      silhouette: s.silhouette,
      inertia,
      selected: s.k === data.k,
    };
  });

  return (
    <section className="panel chart-panel" aria-labelledby="k-title">
      <div className="panel-head">
        <h2 id="k-title">Choosing k</h2>
        <p className="muted">{data.chosen_reason}</p>
      </div>
      <div className="dual-charts">
        <div className="chart-box">
          <h3>Silhouette vs k</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={merged}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d6d3d1" />
              <XAxis dataKey="k" />
              <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="silhouette" stroke="#0f766e" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box">
          <h3>Elbow (inertia)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={merged}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d6d3d1" />
              <XAxis dataKey="k" />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="inertia" stroke="#b45309" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <p className="meta">
        Serving <strong>{data.method}</strong> (silhouette {data.silhouette.toFixed(3)}) · alternative{" "}
        {data.alternative_method} ({data.alternative_silhouette.toFixed(3)})
      </p>
    </section>
  );
}
