import type { AcfPacfResponse } from "../types";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = { data: AcfPacfResponse };

export function AcfPacfCharts({ data }: Props) {
  const acfRows = data.lags.map((lag, i) => ({
    lag,
    value: data.acf[i],
  }));
  const pacfRows = data.lags.map((lag, i) => ({
    lag,
    value: data.pacf[i],
  }));

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>ACF / PACF</h2>
          <p className="muted small">{data.interpretation}</p>
        </div>
        <p className="meta">
          n={data.n} · 95% CI ≈ ±{data.acf_ci.toFixed(3)}
        </p>
      </div>
      <div className="acf-grid">
        <div className="chart-box">
          <h3>ACF</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={acfRows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3a2e" />
              <XAxis dataKey="lag" tick={{ fill: "#8a9a8e", fontSize: 11 }} />
              <YAxis tick={{ fill: "#8a9a8e", fontSize: 11 }} domain={[-1, 1]} />
              <Tooltip
                contentStyle={{ background: "#142018", border: "1px solid #2a3a2e" }}
              />
              <ReferenceLine y={data.acf_ci} stroke="#c4a35a" strokeDasharray="4 4" />
              <ReferenceLine y={-data.acf_ci} stroke="#c4a35a" strokeDasharray="4 4" />
              <Bar dataKey="value" fill="#3d9b6e" name="ACF" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box">
          <h3>PACF</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={pacfRows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3a2e" />
              <XAxis dataKey="lag" tick={{ fill: "#8a9a8e", fontSize: 11 }} />
              <YAxis tick={{ fill: "#8a9a8e", fontSize: 11 }} domain={[-1, 1]} />
              <Tooltip
                contentStyle={{ background: "#142018", border: "1px solid #2a3a2e" }}
              />
              <ReferenceLine y={data.acf_ci} stroke="#c4a35a" strokeDasharray="4 4" />
              <ReferenceLine y={-data.acf_ci} stroke="#c4a35a" strokeDasharray="4 4" />
              <Bar dataKey="value" fill="#5b8def" name="PACF" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
