import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { AuditResponse, DimensionScore } from "../types";
import { FindingsList } from "./FindingsList";
import { GradeSummary } from "./GradeSummary";

export function AuditTab({ data }: { data: AuditResponse }) {
  return (
    <div className="stack">
      <section className="panel">
        <h2>Governance · Self-Audit</h2>
        <p className="lede">
          Live score from the experiment-11 static auditor run against this repository — the
          platform certifies its own leakage, reproducibility, tests, docs, and fairness signals.
        </p>
      </section>

      <div className="grid-2">
        <GradeSummary result={data} />
        <section className="panel">
          <h3>Dimension radar</h3>
          <ScoreRadar dimensions={data.dimensions} />
        </section>
      </div>

      <section className="panel">
        <h3>Dimension scores</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Dimension</th>
              <th>Score</th>
              <th>Findings</th>
            </tr>
          </thead>
          <tbody>
            {data.dimensions.map((d) => (
              <tr key={d.dimension}>
                <td>{d.label}</td>
                <td className="mono">{d.score}</td>
                <td className="mono">{d.finding_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <FindingsList findings={data.findings} />

      <section className="panel warn">
        <h3>Limitations</h3>
        <ul>
          {data.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function ScoreRadar({ dimensions }: { dimensions: DimensionScore[] }) {
  const chart = dimensions.map((d) => ({
    axis: d.label.replace(" / ", "\n"),
    score: d.score,
    fullMark: 100,
  }));

  return (
    <div className="radar-wrap" aria-label="Dimension radar chart">
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={chart} cx="50%" cy="50%" outerRadius="72%">
          <PolarGrid stroke="var(--line)" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: "var(--muted)", fontSize: 11 }} />
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
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
