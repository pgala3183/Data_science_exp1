import { useMemo, useState } from "react";
import { scoreRecord } from "../api";
import type { ScoreItem } from "../types";

const DEFAULTS: Record<string, number> = {
  cpu_pct: 35,
  mem_pct: 55,
  disk_io: 120,
  net_in: 200,
  net_out: 180,
  temp_c: 42,
  latency_ms: 25,
  error_rate: 0.01,
};

const SPIKE: Record<string, number> = {
  cpu_pct: 96,
  mem_pct: 92,
  disk_io: 480,
  net_in: 40,
  net_out: 950,
  temp_c: 84,
  latency_ms: 280,
  error_rate: 0.35,
};

type Props = { features: string[] };

export function ScoreForm({ features }: Props) {
  const [values, setValues] = useState<Record<string, number>>({ ...DEFAULTS });
  const [result, setResult] = useState<ScoreItem | null>(null);
  const [thresholds, setThresholds] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fields = useMemo(
    () => (features.length ? features : Object.keys(DEFAULTS)),
    [features],
  );

  async function onScore() {
    setLoading(true);
    setError(null);
    try {
      const payload: Record<string, number> = {};
      for (const f of fields) payload[f] = Number(values[f] ?? 0);
      const res = await scoreRecord(payload);
      setResult(res.scores[0]);
      setThresholds(res.thresholds);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Score failed");
    } finally {
      setLoading(false);
    }
  }

  const ensemble = result?.ensemble ?? 0;
  const angle = -90 + ensemble * 180;

  return (
    <section className="panel" aria-labelledby="score-title">
      <h2 id="score-title">Score a record</h2>
      <div className="score-grid">
        <form
          className="score-form"
          onSubmit={(e) => {
            e.preventDefault();
            void onScore();
          }}
        >
          {fields.map((f) => (
            <label key={f}>
              {f}
              <input
                type="number"
                step="any"
                value={values[f] ?? 0}
                onChange={(e) => setValues((v) => ({ ...v, [f]: Number(e.target.value) }))}
              />
            </label>
          ))}
          <div className="actions">
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? "Scoring…" : "Score"}
            </button>
            <button type="button" className="btn" onClick={() => setValues({ ...DEFAULTS })}>
              Healthy preset
            </button>
            <button type="button" className="btn" onClick={() => setValues({ ...SPIKE })}>
              Anomaly preset
            </button>
          </div>
        </form>

        <div className="gauge-wrap">
          <div className="gauge" role="img" aria-label={`Ensemble score ${ensemble.toFixed(2)}`}>
            <div className="gauge-arc" />
            <div className="needle" style={{ transform: `rotate(${angle}deg)` }} />
            <div className="gauge-value">{(ensemble * 100).toFixed(0)}</div>
            <p>Ensemble score</p>
          </div>
          {result && (
            <ul className="flags">
              {(["isolation_forest", "lof", "autoencoder", "ensemble"] as const).map((k) => (
                <li key={k} className={result.flagged_by.includes(k) ? "hot" : ""}>
                  <strong>{k}</strong>: {result[k].toFixed(3)}
                  {thresholds[k] != null && ` (thr ${thresholds[k].toFixed(3)})`}
                  {result.flagged_by.includes(k) ? " — flagged" : ""}
                </li>
              ))}
            </ul>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
