import type { ModelMetrics } from "../types";

type Props = { metrics: ModelMetrics | null };

export function MetricsPanel({ metrics }: Props) {
  if (!metrics) return null;
  return (
    <section className="panel metrics" aria-labelledby="metrics-title">
      <h2 id="metrics-title">Holdout metrics</h2>
      <p className="meta">
        Split: <strong>{metrics.split}</strong> (earlier → train, later → test). Target:{" "}
        {metrics.target}.
      </p>
      <div className="metric-grid">
        {metrics.models.map((m) => (
          <article key={m.name} className={m.name === metrics.best_model_name ? "best" : ""}>
            <h3>{m.name}</h3>
            <dl>
              <div>
                <dt>RMSE</dt>
                <dd>{m.rmse.toFixed(1)} s</dd>
              </div>
              <div>
                <dt>MAE</dt>
                <dd>{m.mae.toFixed(1)} s</dd>
              </div>
              <div>
                <dt>R²</dt>
                <dd>{m.r2.toFixed(3)}</dd>
              </div>
            </dl>
            {m.name === metrics.best_model_name && <p className="badge">Serving</p>}
          </article>
        ))}
      </div>
    </section>
  );
}
