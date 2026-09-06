import { useMemo } from "react";
import type { StackArchitecture } from "../types";

type Props = { architecture: StackArchitecture };

export function StackDiagram({ architecture }: Props) {
  const levels = useMemo(() => {
    return Object.keys(architecture.levels)
      .map(Number)
      .sort((a, b) => a - b)
      .map((lvl) => ({
        level: lvl,
        models: architecture.levels[String(lvl)] ?? [],
      }));
  }, [architecture]);

  return (
    <section className="panel" aria-labelledby="stack-title">
      <h2 id="stack-title">Stacking architecture</h2>
      <p className="hint">
        Base bagged models at L1 feed higher stack levels; weighted ensembles blend their
        predictions.
      </p>
      <div className="stack-flow">
        {levels.map((lvl, idx) => (
          <div key={lvl.level} className="stack-level">
            <h3>
              Level {lvl.level}
              {lvl.models.some((m) => m.includes("Ensemble")) ? " · ensemble" : " · base"}
            </h3>
            <ul>
              {lvl.models.map((m) => (
                <li key={m} className={m.includes("Ensemble") ? "ens" : ""}>
                  {m}
                </li>
              ))}
            </ul>
            {idx < levels.length - 1 && <div className="stack-arrow" aria-hidden>↓ predictions ↓</div>}
          </div>
        ))}
      </div>
      <p className="meta">
        {architecture.edges.length} directed links in the meta-graph (level → next ensemble).
      </p>
    </section>
  );
}
