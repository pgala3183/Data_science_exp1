import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { ConceptShell } from "../components/ConceptShell";
import { Quiz } from "../components/Quiz";
import { markVisited } from "../progress";
import { QUIZZES } from "../quizzes";

export function RocPage() {
  const [threshold, setThreshold] = useState(0.5);
  const [data, setData] = useState<Awaited<ReturnType<typeof api.roc>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => markVisited("roc"), []);

  useEffect(() => {
    setError(null);
    api
      .roc(threshold)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"));
  }, [threshold]);

  const cm = data?.confusion;

  return (
    <ConceptShell title="Confusion Matrix & ROC">
      <p className="lede">
        Every classifier score needs a <strong>threshold</strong>. Drag it and watch the confusion
        matrix, precision/recall, and the operating point on the ROC curve update together.
      </p>

      <section className="panel viz">
        <label>
          Decision threshold = {threshold.toFixed(2)}
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
        </label>
        {error && <p className="error">{error}</p>}
        {data && cm && (
          <>
            <div className="cm-grid" role="table" aria-label="Confusion matrix">
              <div className="cm-corner" />
              <div className="cm-head">Pred +</div>
              <div className="cm-head">Pred −</div>
              <div className="cm-head">Actual +</div>
              <div className="cm-cell tp">TP {cm.tp}</div>
              <div className="cm-cell fn">FN {cm.fn}</div>
              <div className="cm-head">Actual −</div>
              <div className="cm-cell fp">FP {cm.fp}</div>
              <div className="cm-cell tn">TN {cm.tn}</div>
            </div>
            <div className="metrics">
              <span>precision {(data.precision * 100).toFixed(1)}%</span>
              <span>recall {(data.recall * 100).toFixed(1)}%</span>
              <span>FPR {(data.fpr * 100).toFixed(1)}%</span>
              <span>AUC {data.auc.toFixed(3)}</span>
            </div>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.roc}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d4c4a8" />
                  <XAxis
                    dataKey="fpr"
                    type="number"
                    domain={[0, 1]}
                    label={{ value: "FPR", position: "insideBottom", offset: -2 }}
                  />
                  <YAxis
                    dataKey="tpr"
                    type="number"
                    domain={[0, 1]}
                    label={{ value: "TPR", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip />
                  <Line type="monotone" dataKey="tpr" stroke="#1f5c4a" dot={false} name="ROC" />
                  <ReferenceDot
                    x={data.operating_point.fpr}
                    y={data.operating_point.tpr}
                    r={7}
                    fill="#c45c26"
                    stroke="#fff"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="hint">Orange dot = current threshold on the ROC curve.</p>
          </>
        )}
      </section>

      <Quiz conceptId="roc" questions={QUIZZES.roc} />
    </ConceptShell>
  );
}
