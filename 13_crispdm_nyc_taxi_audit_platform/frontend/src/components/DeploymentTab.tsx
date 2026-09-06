import { useMemo, useState, type FormEvent } from "react";
import { predictTrip } from "../api";
import type { PredictResult, SchemaPayload } from "../types";

export function DeploymentTab({ schema }: { schema: SchemaPayload }) {
  const example = schema.example;
  const [form, setForm] = useState({
    pickup_latitude: Number(example.pickup_latitude ?? 40.758),
    pickup_longitude: Number(example.pickup_longitude ?? -73.9855),
    dropoff_latitude: Number(example.dropoff_latitude ?? 40.7484),
    dropoff_longitude: Number(example.dropoff_longitude ?? -73.9857),
    pickup_datetime: String(example.pickup_datetime ?? "2016-03-15T08:30:00"),
    passenger_count: Number(example.passenger_count ?? 1),
  });
  const [pred, setPred] = useState<PredictResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fields = useMemo(
    () =>
      [
        ["pickup_latitude", "Pickup lat"],
        ["pickup_longitude", "Pickup lon"],
        ["dropoff_latitude", "Dropoff lat"],
        ["dropoff_longitude", "Dropoff lon"],
        ["pickup_datetime", "Pickup datetime"],
        ["passenger_count", "Passengers"],
      ] as const,
    [],
  );

  async function onPredict(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await predictTrip(form);
      setPred(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Predict failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <section className="panel">
        <h2>Deployment</h2>
        <p className="lede">
          Score a pre-trip request. Features are engineered server-side with train-only zone
          clusters; the response includes a residual-based 95% interval.
        </p>
        <p className="meta">Primary model: {schema.primary_model}</p>
      </section>

      <form className="panel form-grid" onSubmit={onPredict}>
        {fields.map(([key, label]) => (
          <label key={key} className="field">
            {label}
            <input
              value={String(form[key])}
              onChange={(e) => {
                const raw = e.target.value;
                setForm((f) => ({
                  ...f,
                  [key]:
                    key === "pickup_datetime"
                      ? raw
                      : key === "passenger_count"
                        ? Number(raw)
                        : Number(raw),
                }));
              }}
            />
          </label>
        ))}
        <div className="form-actions">
          <button type="submit" disabled={busy}>
            Predict duration
          </button>
        </div>
      </form>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {pred && (
        <section className="panel">
          <h3>Prediction</h3>
          <div className="metric-row">
            <div className="metric metric-hi">
              <span>Duration</span>
              <strong className="mono">{pred.predicted_duration_minutes} min</strong>
            </div>
            <div className="metric">
              <span>Seconds</span>
              <strong className="mono">{pred.predicted_duration_seconds}</strong>
            </div>
            <div className="metric">
              <span>95% CI (s)</span>
              <strong className="mono">
                {pred.confidence_interval_95_seconds[0]}–{pred.confidence_interval_95_seconds[1]}
              </strong>
            </div>
            <div className="metric">
              <span>Distance</span>
              <strong className="mono">{pred.haversine_km} km</strong>
            </div>
          </div>
          <p className="meta">model={pred.model_name}</p>
          <h4>Top features</h4>
          <ul className="chip-list">
            {pred.top_features.map((f) => (
              <li key={f.feature}>
                {f.feature}: {f.importance.toFixed(3)}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
