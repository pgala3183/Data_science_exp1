import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LeaderboardRow } from "../types";

type SortKey = "score_val" | "fit_time" | "pred_time_val" | "model";

type Props = { rows: LeaderboardRow[]; metric: string };

export function LeaderboardPanel({ rows, metric }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("score_val");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string") {
        return asc ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const an = av == null ? -Infinity : Number(av);
      const bn = bv == null ? -Infinity : Number(bv);
      return asc ? an - bn : bn - an;
    });
    return copy;
  }, [rows, sortKey, asc]);

  const chartData = useMemo(
    () =>
      [...rows]
        .filter((r) => r.score_val != null)
        .sort((a, b) => Number(b.score_val) - Number(a.score_val))
        .slice(0, 12)
        .map((r) => ({
          name: r.model.replace(/_BAG_/g, " ").slice(0, 22),
          score: Number(r.score_val),
        })),
    [rows],
  );

  function toggle(key: SortKey) {
    if (key === sortKey) setAsc((v) => !v);
    else {
      setSortKey(key);
      setAsc(key === "model");
    }
  }

  return (
    <section className="panel" aria-labelledby="lb-title">
      <h2 id="lb-title">Model leaderboard</h2>
      <p className="hint">Sorted by {sortKey} ({metric}). Click headers to re-sort.</p>
      <div className="lb-layout">
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3a3a" />
              <XAxis type="number" domain={["auto", "auto"]} tick={{ fill: "#9bb0b0", fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fill: "#c5d4d4", fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{ background: "#122020", border: "1px solid #2a4040" }}
                labelStyle={{ color: "#e8f2f2" }}
              />
              <Bar dataKey="score" fill="#3dba9c" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>
                  <button type="button" onClick={() => toggle("model")}>
                    Model
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => toggle("score_val")}>
                    Val score
                  </button>
                </th>
                <th>Test</th>
                <th>
                  <button type="button" onClick={() => toggle("fit_time")}>
                    Fit (s)
                  </button>
                </th>
                <th>
                  <button type="button" onClick={() => toggle("pred_time_val")}>
                    Infer (s)
                  </button>
                </th>
                <th>L</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((r) => (
                <tr key={r.model}>
                  <td className="mono">{r.model}</td>
                  <td>{r.score_val?.toFixed(4) ?? "—"}</td>
                  <td>{r.score_test?.toFixed(4) ?? "—"}</td>
                  <td>{r.fit_time?.toFixed(1) ?? "—"}</td>
                  <td>{r.pred_time_val?.toFixed(3) ?? "—"}</td>
                  <td>{r.stack_level}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
