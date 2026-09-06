import { useEffect, useState } from "react";
import { fetchDemo, fetchMetrics } from "./api";
import { AccuracyChart } from "./components/AccuracyChart";
import { PredictForm } from "./components/PredictForm";
import { ResultsPanel } from "./components/ResultsPanel";
import type { DemoSample, MetricsResponse, PredictResponse } from "./types";

export default function App() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [samples, setSamples] = useState<DemoSample[]>([]);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchMetrics(), fetchDemo()])
      .then(([m, d]) => {
        setMetrics(m);
        setSamples(d.samples);
      })
      .catch((e) =>
        setError(
          e instanceof Error
            ? e.message
            : "Failed to load — is the API running on :8014? First start trains models.",
        ),
      );
  }, []);

  const liftPct = metrics ? (metrics.lift_vs_best_baseline * 100).toFixed(1) : null;
  const liftPositive = metrics ? metrics.lift_vs_best_baseline > 0.005 : false;

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 14</p>
        <h1>Multimodal AutoML Suite</h1>
        <p className="lede">
          AutoGluon <code>MultiModalPredictor</code> fuses product image + text + tabular fields,
          then we measure the lift against image-only, text-only, and tabular-only baselines.
        </p>
        {metrics && (
          <div className="lift-banner" data-positive={liftPositive ? "1" : "0"}>
            <span className="lift-label">Held-out multimodal lift</span>
            <strong>
              {liftPositive ? "+" : ""}
              {liftPct} pp vs {metrics.best_baseline.replace("_", " ")}
            </strong>
            <span className="lift-detail">
              multimodal {(metrics.multimodal_accuracy * 100).toFixed(1)}% · best baseline{" "}
              {(metrics.best_baseline_accuracy * 100).toFixed(1)}% · n=
              {metrics.n_train}/{metrics.n_test}
            </span>
          </div>
        )}
      </header>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!metrics && !error && (
        <p className="muted">Loading metrics (first API start trains multimodal + baselines)…</p>
      )}

      {metrics && (
        <>
          <section className="panel">
            <h2>Hold-out accuracy by modality</h2>
            <p className="hint">{metrics.notes}</p>
            <AccuracyChart accuracies={metrics.accuracies} />
          </section>

          <div className="split">
            <PredictForm samples={samples} onResult={setResult} />
            <ResultsPanel result={result} />
          </div>
        </>
      )}
    </div>
  );
}
