import type { PredictResponse } from "../types";

const ORDER = [
  { key: "multimodal", label: "Multimodal fusion", kind: "main" as const },
  { key: "image_only", label: "Image-only", kind: "base" as const },
  { key: "text_only", label: "Text-only", kind: "base" as const },
  { key: "tabular_only", label: "Tabular-only", kind: "base" as const },
];

function topProb(probs: Record<string, number>): string {
  const entries = Object.entries(probs);
  if (!entries.length) return "—";
  entries.sort((a, b) => b[1] - a[1]);
  return `${(entries[0][1] * 100).toFixed(0)}%`;
}

export function ResultsPanel({ result }: { result: PredictResponse | null }) {
  if (!result) {
    return (
      <section className="panel results empty">
        <h2>Predictions</h2>
        <p className="hint">Submit a listing to compare multimodal vs each baseline side by side.</p>
      </section>
    );
  }

  const sides = {
    multimodal: result.multimodal,
    ...result.baselines,
  };

  return (
    <section className="panel results">
      <h2>Predictions</h2>
      <p className="hint">
        Hold-out lift vs {result.best_baseline.replace("_", " ")}:{" "}
        <strong>
          {result.lift_vs_best_baseline >= 0 ? "+" : ""}
          {(result.lift_vs_best_baseline * 100).toFixed(1)} pp
        </strong>
      </p>
      <ul className="pred-list">
        {ORDER.map(({ key, label, kind }) => {
          const side = sides[key as keyof typeof sides];
          const acc = result.holdout_accuracies[key as keyof typeof result.holdout_accuracies];
          return (
            <li key={key} className={kind === "main" ? "pred-main" : undefined}>
              <div>
                <span className="pred-name">{label}</span>
                <span className="pred-acc">hold-out {(acc * 100).toFixed(1)}%</span>
              </div>
              <div className="pred-out">
                <strong>{side.prediction}</strong>
                <span>{topProb(side.probabilities)} conf.</span>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
