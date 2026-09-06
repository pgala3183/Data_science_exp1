import { useState, type FormEvent } from "react";
import { auditPath, auditUpload } from "./api";
import { FindingsList } from "./components/FindingsList";
import { GradeSummary } from "./components/GradeSummary";
import { ScoreRadar } from "./components/ScoreRadar";
import type { AuditResponse } from "./types";

const PRESETS = [
  { label: "Exp 1 — NYC Taxi", path: "1_nyc_taxi_trip_prediction" },
  { label: "Exp 3 — Customer Segmentation", path: "3_customer_segmentation_clustering" },
  { label: "Exp 6 — Anomaly Detection", path: "6_anomaly_detection" },
];

export default function App() {
  const [path, setPath] = useState(PRESETS[0].path);
  const [result, setResult] = useState<AuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runPath(p: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await auditPath(p);
      setResult(data);
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "Audit failed");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void runPath(path.trim());
  }

  async function onUpload(file: File | null) {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await auditUpload(file);
      setResult(data);
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 11</p>
        <h1>Enterprise DS Audit</h1>
        <p className="lede">
          Static-analysis scores for leakage, seeds, validation, tests, docs, and fairness —
          with file/line findings you can act on.
        </p>
      </header>

      <section className="controls">
        <form className="path-form" onSubmit={onSubmit}>
          <label htmlFor="path">Project path</label>
          <div className="row">
            <input
              id="path"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="1_nyc_taxi_trip_prediction"
              spellCheck={false}
            />
            <button type="submit" disabled={loading || !path.trim()}>
              {loading ? "Auditing…" : "Run audit"}
            </button>
          </div>
        </form>

        <div className="presets">
          {PRESETS.map((p) => (
            <button
              key={p.path}
              type="button"
              className="chip"
              disabled={loading}
              onClick={() => {
                setPath(p.path);
                void runPath(p.path);
              }}
            >
              {p.label}
            </button>
          ))}
        </div>

        <label className="upload">
          <span>Or upload a .zip</span>
          <input
            type="file"
            accept=".zip,application/zip"
            disabled={loading}
            onChange={(e) => void onUpload(e.target.files?.[0] ?? null)}
          />
        </label>
      </section>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {result && (
        <>
          <div className="results-grid">
            <GradeSummary result={result} />
            <div className="panel radar-panel">
              <h2>Dimension scores</h2>
              <ScoreRadar dimensions={result.dimensions} />
              <ul className="dim-scores">
                {result.dimensions.map((d) => (
                  <li key={d.dimension}>
                    <span>{d.label}</span>
                    <strong className="mono">{d.score}</strong>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <FindingsList findings={result.findings} />

          <section className="panel limits">
            <h2>Auditor limitations</h2>
            <ul>
              {result.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
