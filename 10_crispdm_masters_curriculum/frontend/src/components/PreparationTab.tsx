import type { PipelinePayload } from "../types";

export function PreparationTab({ data }: { data: PipelinePayload }) {
  return (
    <section className="panel">
      <h2>Data Preparation</h2>
      <p className="lede">
        Documented, reusable sklearn pipeline — imputation, one-hot encoding, and scaling fit on
        train only.
      </p>
      <p className="meta">{data.name}</p>

      <ol className="pipeline">
        {data.steps.map((s, i) => (
          <li key={s.id} className="pipeline-step">
            <span className="step-num">{i + 1}</span>
            <div>
              <strong>{s.title}</strong>
              <p>{s.detail}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className="grid-2">
        <div>
          <h3>Numeric</h3>
          <ul className="chip-list">
            {data.numeric_features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Categorical</h3>
          <ul className="chip-list">
            {data.categorical_features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
