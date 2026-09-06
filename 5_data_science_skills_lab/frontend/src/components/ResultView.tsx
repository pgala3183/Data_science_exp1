import type { RunResult } from "../types";

function MetricsBlock({ metrics }: { metrics: Record<string, unknown> }) {
  return (
    <dl className="metrics">
      {Object.entries(metrics).map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd>
        </div>
      ))}
    </dl>
  );
}

function TableBlock({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 40).map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>{String(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartBlock({
  series,
  chartType,
  xKey,
  yKey,
  yKeys,
}: {
  series: Record<string, unknown>[];
  chartType: string;
  xKey: string;
  yKey?: string;
  yKeys?: string[];
}) {
  const keys = yKeys ?? (yKey ? [yKey] : ["y"]);
  const nums = series.flatMap((s) => keys.map((k) => Number(s[k] ?? 0)));
  const maxY = Math.max(...nums, 1e-6);

  return (
    <div className="mini-chart" role="img" aria-label={`${chartType} chart`}>
      {series.map((s, i) => {
        const label = String(s[xKey] ?? i);
        if (chartType === "line" || chartType === "line_multi") {
          return null;
        }
        const h = (Number(s[keys[0]] ?? 0) / maxY) * 100;
        return (
          <div key={i} className="bar-col" title={`${label}: ${s[keys[0]]}`}>
            <div className="bar" style={{ height: `${Math.max(h, 2)}%` }} />
            <span>{label.length > 8 ? `${label.slice(0, 8)}…` : label}</span>
          </div>
        );
      })}
      {(chartType === "line" || chartType === "line_multi") && (
        <svg viewBox="0 0 300 120" className="line-svg" aria-hidden="true">
          {keys.map((k, ki) => {
            const pts = series
              .map((s, i) => {
                const x = (i / Math.max(series.length - 1, 1)) * 280 + 10;
                const y = 110 - (Number(s[k] ?? 0) / maxY) * 100;
                return `${x},${y}`;
              })
              .join(" ");
            return (
              <polyline
                key={k}
                fill="none"
                stroke={ki === 0 ? "#0f766e" : "#b45309"}
                strokeWidth="2"
                points={pts}
              />
            );
          })}
        </svg>
      )}
    </div>
  );
}

export function ResultView({ result }: { result: RunResult }) {
  return (
    <div className="result">
      {result.title && <h3>{result.title}</h3>}
      {result.metrics && <MetricsBlock metrics={result.metrics} />}
      {result.sample_columns && (
        <p className="muted">Columns: {result.sample_columns.join(", ")}</p>
      )}
      {result.rows && <TableBlock rows={result.rows} />}
      {result.table && <TableBlock rows={result.table} />}
      {result.series && (
        <ChartBlock
          series={result.series}
          chartType={result.chart_type ?? "bar"}
          xKey={result.x_key ?? "x"}
          yKey={result.y_key}
          yKeys={result.y_keys}
        />
      )}
      {result.chart && (
        <ChartBlock
          series={result.chart.series}
          chartType={result.chart.chart_type}
          xKey={result.chart.x_key}
          yKey={result.chart.y_key}
          yKeys={result.chart.y_keys}
        />
      )}
    </div>
  );
}
