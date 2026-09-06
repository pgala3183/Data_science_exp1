import { useMemo, useState, type FormEvent } from "react";
import { predictRecord } from "../api";
import type { PredictResponse, SchemaField } from "../types";

type Props = { schema: SchemaField[] };

export function PredictForm({ schema }: Props) {
  const defaults = useMemo(() => {
    const o: Record<string, string | number> = {};
    for (const f of schema) o[f.name] = f.example ?? (f.type === "number" ? 0 : "");
    return o;
  }, [schema]);

  const [values, setValues] = useState<Record<string, string | number>>(defaults);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await predictRecord(values);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Predict failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel" aria-labelledby="pred-title">
      <h2 id="pred-title">Live prediction</h2>
      <p className="hint">Form fields are generated from the training schema.</p>
      <div className="pred-grid">
        <form className="pred-form" onSubmit={onSubmit}>
          {schema.map((f) => (
            <label key={f.name}>
              {f.name}
              {f.type === "categorical" && f.categories?.length ? (
                <select
                  value={String(values[f.name] ?? "")}
                  onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
                >
                  {f.categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={f.type === "number" ? "number" : "text"}
                  step="any"
                  value={values[f.name] ?? ""}
                  onChange={(e) =>
                    setValues((v) => ({
                      ...v,
                      [f.name]: f.type === "number" ? Number(e.target.value) : e.target.value,
                    }))
                  }
                />
              )}
            </label>
          ))}
          <button type="submit" disabled={loading}>
            {loading ? "Scoring…" : "Predict"}
          </button>
        </form>

        <div className="pred-result">
          {error && <p className="error">{error}</p>}
          {result && (
            <>
              <p className="pred-label">
                Ensemble: <strong>{result.prediction}</strong>
              </p>
              <ul className="proba">
                {Object.entries(result.probabilities).map(([k, v]) => (
                  <li key={k}>
                    <span>{k}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${v * 100}%` }} />
                    </div>
                    <span>{(v * 100).toFixed(1)}%</span>
                  </li>
                ))}
              </ul>
              <h3>Per-model votes</h3>
              <ul className="votes mono">
                {Object.entries(result.per_model_predictions)
                  .slice(0, 16)
                  .map(([m, p]) => (
                    <li key={m}>
                      <span>{m}</span>
                      <span>{p}</span>
                    </li>
                  ))}
              </ul>
            </>
          )}
          {!result && !error && <p className="muted">Submit a census record to score income class.</p>}
        </div>
      </div>
    </section>
  );
}
