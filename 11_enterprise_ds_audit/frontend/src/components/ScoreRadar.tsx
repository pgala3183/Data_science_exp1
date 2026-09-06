import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { DimensionScore } from "../types";

interface Props {
  dimensions: DimensionScore[];
}

export function ScoreRadar({ dimensions }: Props) {
  const data = dimensions.map((d) => ({
    axis: d.label.replace(" / ", "\n"),
    score: d.score,
    fullMark: 100,
  }));

  return (
    <div className="radar-wrap" aria-label="Dimension radar chart">
      <ResponsiveContainer width="100%" height={340}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="72%">
          <PolarGrid stroke="var(--line)" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "var(--muted)", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: "var(--muted)", fontSize: 10 }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="var(--accent)"
            fill="var(--accent)"
            fillOpacity={0.28}
            strokeWidth={2}
            isAnimationActive
            animationDuration={700}
          />
          <Tooltip
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--line)",
              borderRadius: 8,
              color: "var(--ink)",
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
