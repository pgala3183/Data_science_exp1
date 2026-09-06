import type { ModelMetrics, PredictResponse } from "../types";

type Props = {
  result: PredictResponse | null;
  metrics: ModelMetrics | null;
  error: string | null;
};

function formatMinutes(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

export function ResultCard({ result, metrics, error }: Props) {
  if (error) {
    return (
      <section className="panel result error" role="alert">
        <h2>Prediction</h2>
        <p>{error}</p>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="panel result muted">
        <h2>Prediction</h2>
        <p>Set pickup and dropoff on the map, then click Predict.</p>
        {metrics && (
          <p className="meta">
            Model ready: <strong>{metrics.best_model_name}</strong> · time-based holdout · n_test=
            {metrics.n_test.toLocaleString()}
          </p>
        )}
      </section>
    );
  }

  const [lo, hi] = result.confidence_interval_95_seconds;

  return (
    <section className="panel result" aria-live="polite">
      <h2>Prediction</h2>
      <p className="big">
        {result.predicted_duration_minutes.toFixed(1)}{" "}
        <span className="unit">minutes</span>
      </p>
      <p className="sub">
        {formatMinutes(result.predicted_duration_seconds)} · straight-line{" "}
        {result.haversine_km.toFixed(2)} km
      </p>
      <p className="ci">
        Approx. 95% interval: {formatMinutes(lo)} – {formatMinutes(hi)}
        <span className="hint"> (residual-based)</span>
      </p>
      <p className="meta">Model: {result.model_name}</p>

      <h3>Top contributing features</h3>
      <ul className="feat-list">
        {result.top_features.map((f) => (
          <li key={f.feature}>
            <span>{f.feature}</span>
            <div className="bar-track" aria-hidden="true">
              <div className="bar" style={{ width: `${Math.max(8, f.importance * 100)}%` }} />
            </div>
            <span className="pct">{(f.importance * 100).toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
