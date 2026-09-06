import { useMemo, useState, type FormEvent } from "react";
import { findSimilar, predictRecord } from "../api";
import type { PredictResult, SchemaPayload, SimilarResult } from "../types";

const NUMERIC = new Set([
  "age",
  "fnlwgt",
  "education-num",
  "capital-gain",
  "capital-loss",
  "hours-per-week",
]);

export function DeploymentTab({ schema }: { schema: SchemaPayload }) {
  const initial = useMemo(() => {
    const out: Record<string, string> = {};
    for (const c of schema.feature_cols) {
      const v = schema.example[c];
      out[c] = v == null ? "" : String(v);
    }
    return out;
  }, [schema]);

  const [form, setForm] = useState(initial);
  const [k, setK] = useState(5);
  const [pred, setPred] = useState<PredictResult | null>(null);
  const [sim, setSim] = useState<SimilarResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toRecord() {
    const record: Record<string, string | number | null> = {};
    for (const c of schema.feature_cols) {
      const raw = form[c]?.trim() ?? "";
      if (raw === "") {
        record[c] = null;
      } else if (NUMERIC.has(c)) {
        record[c] = Number(raw);
      } else {
        record[c] = raw;
      }
    }
    return record;
  }

  async function onPredict(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await predictRecord(toRecord());
      setPred(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Predict failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSimilar(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await findSimilar(toRecord(), k);
      setSim(result);
      if (result.query_prediction != null) {
        setPred({
          prediction: result.query_prediction,
          probability_gt_50k: result.query_probability_gt_50k ?? 0,
          model: schema.models[schema.models.length - 1] ?? "hist_gradient_boosting",
          probabilities: {},
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Similar search failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <section className="panel">
        <h2>Deployment</h2>
        <p className="lede">
          Score a census-style record and retrieve the k most similar training rows via cosine
          similarity, accelerated with a custom random-hyperplane LSH index.
        </p>
      </section>

      <form className="panel form-grid" onSubmit={onPredict}>
        {schema.feature_cols.map((c) => (
          <label key={c} className="field">
            {c}
            <input
              value={form[c] ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, [c]: e.target.value }))}
            />
          </label>
        ))}
        <div className="form-actions">
          <button type="submit" disabled={busy}>
            Predict
          </button>
          <label className="field inline">
            k
            <input
              type="number"
              min={1}
              max={25}
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              style={{ width: "4rem" }}
            />
          </label>
          <button type="button" disabled={busy} onClick={onSimilar}>
            Find similar records
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
          <p className="meta">
            {pred.prediction} · P(&gt;50K)={pred.probability_gt_50k.toFixed(3)} · model={pred.model}
          </p>
        </section>
      )}

      {sim && (
        <section className="panel">
          <h3>Similar training records</h3>
          <p className="meta">
            LSH candidates scanned: {sim.lsh_candidates_scanned} · method={sim.method}
          </p>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Cosine</th>
                  <th>Income</th>
                  <th>Age</th>
                  <th>Education</th>
                  <th>Occupation</th>
                  <th>Hours</th>
                  <th>Sex</th>
                  <th>Race</th>
                </tr>
              </thead>
              <tbody>
                {sim.neighbors.map((n) => (
                  <tr key={n.rank}>
                    <td>{n.rank}</td>
                    <td className="mono">{n.cosine_similarity.toFixed(3)}</td>
                    <td>{n.income}</td>
                    <td className="mono">{String(n.record.age ?? "")}</td>
                    <td>{String(n.record.education ?? "")}</td>
                    <td>{String(n.record.occupation ?? "")}</td>
                    <td className="mono">{String(n.record["hours-per-week"] ?? "")}</td>
                    <td>{String(n.record.sex ?? "")}</td>
                    <td>{String(n.record.race ?? "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
