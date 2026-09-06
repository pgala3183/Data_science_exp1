import { useEffect, useState } from "react";
import { fetchExplain, fetchLeaderboard } from "./api";
import { LeaderboardPanel } from "./components/LeaderboardPanel";
import { PredictForm } from "./components/PredictForm";
import { StackDiagram } from "./components/StackDiagram";
import type { ExplainResponse, LeaderboardResponse } from "./types";

export default function App() {
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [explain, setExplain] = useState<ExplainResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchLeaderboard(), fetchExplain()])
      .then(([lb, ex]) => {
        setData(lb);
        setExplain(ex);
      })
      .catch((e) =>
        setError(
          e instanceof Error
            ? e.message
            : "Failed to load — is the API running on :8007?",
        ),
      );
  }, []);

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 7</p>
        <h1>AutoGluon AutoML</h1>
        <p className="lede">
          Multi-layer stacked TabularPredictor on Adult Income — bagged base models, weighted
          ensembles, live predictions.
        </p>
        {data && (
          <p className="meta">
            test ROC-AUC {data.test_roc_auc.toFixed(3)} · accuracy {data.test_accuracy.toFixed(3)} ·
            bags={data.num_bag_folds} · stack levels={data.num_stack_levels} · best=
            {data.best_model}
          </p>
        )}
      </header>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!data && !error && (
        <p className="muted">Loading leaderboard (first API start may still be training)…</p>
      )}

      {data && (
        <>
          <LeaderboardPanel rows={data.leaderboard} metric={data.eval_metric} />
          <StackDiagram architecture={data.stack_architecture} />
          <PredictForm schema={data.schema} />
          {explain && explain.features.length > 0 && (
            <section className="panel">
              <h2>Feature importance</h2>
              <p className="hint">Permutation importance on a held-out sample.</p>
              <ul className="fi-list">
                {explain.features.slice(0, 12).map((f) => (
                  <li key={f.feature}>
                    <span>{f.feature}</span>
                    <strong>{f.importance.toFixed(4)}</strong>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}
