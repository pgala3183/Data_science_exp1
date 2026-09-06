import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EvalPayload, FairnessGroup } from "../types";

export function EvaluationTab({ data }: { data: EvalPayload }) {
  const models = Object.keys(data.metrics);
  const [model, setModel] = useState(data.primary_model || models[0]);
  const m = data.metrics[model];
  const fair = data.fairness[model];
  const roc = m.roc_curve.fpr.map((fpr, i) => ({
    fpr,
    tpr: m.roc_curve.tpr[i],
  }));

  return (
    <div className="stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Evaluation</h2>
            <p className="lede">
              Hold-out metrics (n={data.n_test.toLocaleString()}) and fairness by sex / race —
              disparities are reported, not hidden.
            </p>
          </div>
          <label className="field inline">
            Model
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {models.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="metric-row">
          <Metric label="Accuracy" value={m.accuracy} />
          <Metric label="F1 (>50K)" value={m.f1} />
          <Metric label="ROC-AUC" value={m.roc_auc} highlight />
        </div>
      </section>

      <div className="grid-2">
        <section className="panel">
          <h3>ROC curve</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={roc}>
                <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                <XAxis
                  dataKey="fpr"
                  type="number"
                  domain={[0, 1]}
                  tick={{ fontSize: 12 }}
                  label={{ value: "FPR", position: "insideBottom", offset: -2 }}
                />
                <YAxis dataKey="tpr" domain={[0, 1]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="tpr"
                  stroke="#0f766e"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel">
          <h3>Confusion matrix</h3>
          <table className="table cm">
            <thead>
              <tr>
                <th />
                <th>Pred ≤50K</th>
                <th>Pred &gt;50K</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>True ≤50K</th>
                <td className="mono">{m.confusion_matrix.matrix[0][0]}</td>
                <td className="mono">{m.confusion_matrix.matrix[0][1]}</td>
              </tr>
              <tr>
                <th>True &gt;50K</th>
                <td className="mono">{m.confusion_matrix.matrix[1][0]}</td>
                <td className="mono">{m.confusion_matrix.matrix[1][1]}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>

      {fair && (
        <>
          {Object.entries(fair.by_attribute).map(([attr, groups]) => (
            <FairnessTable key={attr} attr={attr} groups={groups} />
          ))}
          <section className="panel warn">
            <h3>Disparity summary</h3>
            {Object.entries(fair.disparities).map(([attr, d]) => (
              <p key={attr}>
                <strong>{attr}</strong>: TPR range {d.tpr_range.toFixed(3)}, selection-rate range{" "}
                {d.selection_rate_range.toFixed(3)} (majority={d.majority_group}). {d.note}
              </p>
            ))}
          </section>
        </>
      )}

      <section className="panel">
        <h3>Evaluation write-up</h3>
        <article className="markdown">
          <pre>{data.evaluation_doc}</pre>
        </article>
      </section>
    </div>
  );
}

function Metric({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div className={`metric ${highlight ? "metric-hi" : ""}`}>
      <span>{label}</span>
      <strong className="mono">{value.toFixed(3)}</strong>
    </div>
  );
}

function FairnessTable({ attr, groups }: { attr: string; groups: FairnessGroup[] }) {
  return (
    <section className="panel">
      <h3>Fairness by {attr}</h3>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Group</th>
              <th>n</th>
              <th>Base rate</th>
              <th>Selection</th>
              <th>TPR</th>
              <th>FPR</th>
              <th>Acc</th>
              <th>F1</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <tr key={g.group}>
                <td>{g.group}</td>
                <td className="mono">{g.support}</td>
                <td className="mono">{g.base_rate.toFixed(3)}</td>
                <td className="mono">{g.selection_rate.toFixed(3)}</td>
                <td className="mono">{g.tpr.toFixed(3)}</td>
                <td className="mono">{g.fpr.toFixed(3)}</td>
                <td className="mono">{g.accuracy.toFixed(3)}</td>
                <td className="mono">{g.f1.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
