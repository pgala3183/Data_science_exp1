import type { BacktestResponse } from "../types";

type Props = { data: BacktestResponse };

export function BacktestTable({ data }: Props) {
  const sorted = [...data.metrics].sort((a, b) => {
    if (a.model !== b.model) return a.model.localeCompare(b.model);
    return a.horizon - b.horizon;
  });

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Backtest performance</h2>
          <p className="muted small">{data.note}</p>
        </div>
        <p className="meta">method={data.method}</p>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Horizon</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>MAPE %</th>
              <th>n origins</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={`${row.model}-${row.horizon}`}>
                <td>{row.model}</td>
                <td>{row.horizon}</td>
                <td>{row.mae ?? "—"}</td>
                <td>{row.rmse ?? "—"}</td>
                <td>{row.mape ?? "—"}</td>
                <td>{row.n}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
