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
import type { Accuracies } from "../types";

const LABELS: Record<keyof Accuracies, string> = {
  multimodal: "Multimodal",
  image_only: "Image",
  text_only: "Text",
  tabular_only: "Tabular",
};

const COLORS: Record<keyof Accuracies, string> = {
  multimodal: "#1f7a5c",
  image_only: "#c45c26",
  text_only: "#2f5d8c",
  tabular_only: "#8a6d3b",
};

export function AccuracyChart({ accuracies }: { accuracies: Accuracies }) {
  const data = (Object.keys(LABELS) as (keyof Accuracies)[]).map((k) => ({
    name: LABELS[k],
    key: k,
    accuracy: Math.round(accuracies[k] * 1000) / 10,
  }));

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d5cfc4" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: "#4a453c", fontSize: 13 }} />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fill: "#4a453c", fontSize: 12 }}
            width={48}
          />
          <Tooltip
            formatter={(v: number) => [`${v}%`, "Accuracy"]}
            contentStyle={{ borderRadius: 8, borderColor: "#cfc7b8" }}
          />
          <Bar dataKey="accuracy" radius={[6, 6, 0, 0]} maxBarSize={56}>
            {data.map((d) => (
              <Cell key={d.key} fill={COLORS[d.key]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
