import { useEffect, useState } from "react";
import { fetchEvaluate, fetchFeatures } from "./api";
import { AnomaliesTable } from "./components/AnomaliesTable";
import { PRCurves } from "./components/PRCurves";
import { ScoreForm } from "./components/ScoreForm";
import type { EvalResponse } from "./types";
import "./styles.css";

export default function App() {
  const [data, setData] = useState<EvalResponse | null>(null);
  const [features, setFeatures] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchEvaluate(), fetchFeatures()])
      .then(([ev, feats]) => {
        setData(ev);
        setFeatures(feats);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, []);

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 6</p>
        <h1>Anomaly Detection</h1>
        <p className="lede">
          Isolation Forest, Local Outlier Factor, and a reconstruction autoencoder on telemetry —
          scored with PR-AUC on a time-held-out set.
        </p>
        {data && (
          <p className="meta">
            fit on {data.n_train_normal_fit.toLocaleString()} normal train rows · test n=
            {data.n_test.toLocaleString()} · split={data.split}
          </p>
        )}
      </header>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!data && !error && <p className="muted">Loading models &amp; evaluation…</p>}

      {data && (
        <>
          <PRCurves data={data} />
          <ScoreForm features={features.length ? features : data.feature_cols} />
          <AnomaliesTable rows={data.top_anomalies} />
        </>
      )}
    </div>
  );
}
