import { useMemo, useState } from "react";
import type { ForecastResponse } from "../types";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = { data: ForecastResponse };

const MODEL_COLORS: Record<string, { line: string; band: string }> = {
  sarima: { line: "#3d9b6e", band: "rgba(61, 155, 110, 0.28)" },
  gb_lags: { line: "#5b8def", band: "rgba(91, 141, 239, 0.28)" },
};

export function ForecastFan({ data }: Props) {
  const models = data.forecasts.map((f) => f.model);
  const horizons = Array.from(
    new Set(data.forecasts.flatMap((f) => f.horizons.map((h) => h.horizon))),
  ).sort((a, b) => a - b);

  const [activeModels, setActiveModels] = useState<Set<string>>(
    () => new Set(models),
  );
  const [horizon, setHorizon] = useState<number>(horizons[horizons.length - 1] ?? 30);

  const chartData = useMemo(() => {
    type Row = Record<string, string | number | number[] | null>;
    const byDs = new Map<string, Row>();
    for (const p of data.series) {
      byDs.set(p.ds, { ds: p.ds, y: p.y });
    }

    for (const mf of data.forecasts) {
      if (!activeModels.has(mf.model)) continue;
      const hf = mf.horizons.find((h) => h.horizon === horizon);
      if (!hf) continue;
      for (const pt of hf.points) {
        const row = byDs.get(pt.ds) ?? { ds: pt.ds, y: null };
        row[`${mf.model}_yhat`] = pt.yhat;
        row[`${mf.model}_ci`] = [pt.yhat_lower, pt.yhat_upper];
        byDs.set(pt.ds, row);
      }
    }

    return Array.from(byDs.values()).sort((a, b) =>
      String(a.ds).localeCompare(String(b.ds)),
    );
  }, [data, activeModels, horizon]);

  function toggleModel(m: string) {
    setActiveModels((prev) => {
      const next = new Set(prev);
      if (next.has(m)) next.delete(m);
      else next.add(m);
      return next;
    });
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Forecast fan</h2>
          <p className="muted small">
            History through {data.last_train_ds}; shaded bands are ~
            {Math.round((1 - data.alpha) * 100)}% intervals.
          </p>
        </div>
        <div className="toggles">
          <label className="toggle-group">
            Horizon
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            >
              {horizons.map((h) => (
                <option key={h} value={h}>
                  {h}-step
                </option>
              ))}
            </select>
          </label>
          {models.map((m) => (
            <button
              key={m}
              type="button"
              className={`btn chip ${activeModels.has(m) ? "on" : ""}`}
              style={
                activeModels.has(m)
                  ? {
                      borderColor: MODEL_COLORS[m]?.line,
                      color: MODEL_COLORS[m]?.line,
                    }
                  : undefined
              }
              onClick={() => toggleModel(m)}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-box tall">
        <ResponsiveContainer width="100%" height={360}>
          <ComposedChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3a2e" />
            <XAxis
              dataKey="ds"
              tick={{ fill: "#8a9a8e", fontSize: 10 }}
              minTickGap={40}
            />
            <YAxis tick={{ fill: "#8a9a8e", fontSize: 11 }} domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{ background: "#142018", border: "1px solid #2a3a2e" }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="y"
              name="history"
              stroke="#c4a35a"
              dot={false}
              strokeWidth={1.6}
              connectNulls={false}
            />
            {models
              .filter((m) => activeModels.has(m))
              .flatMap((m) => {
                const c = MODEL_COLORS[m] ?? MODEL_COLORS.sarima;
                return [
                  <Area
                    key={`${m}-ci`}
                    type="monotone"
                    dataKey={`${m}_ci`}
                    stroke="none"
                    fill={c.band}
                    name={`${m} 95% CI`}
                    connectNulls
                  />,
                  <Line
                    key={`${m}-line`}
                    type="monotone"
                    dataKey={`${m}_yhat`}
                    name={m}
                    stroke={c.line}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                  />,
                ];
              })}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
