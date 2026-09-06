import { useMemo, useState } from "react";
import type { DimensionId, Finding, Severity } from "../types";

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

const DIM_ORDER: DimensionId[] = [
  "leakage",
  "reproducibility",
  "validation",
  "tests",
  "documentation",
  "fairness",
];

const DIM_LABEL: Record<DimensionId, string> = {
  leakage: "Train/Test Leakage",
  reproducibility: "Reproducibility / Seeds",
  validation: "Data Validation",
  tests: "Test Coverage",
  documentation: "Documentation",
  fairness: "Fairness / Bias",
};

interface Props {
  findings: Finding[];
}

export function FindingsList({ findings }: Props) {
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");

  const grouped = useMemo(() => {
    const filtered =
      severityFilter === "all"
        ? findings
        : findings.filter((f) => f.severity === severityFilter);

    const byDim = new Map<DimensionId, Finding[]>();
    for (const dim of DIM_ORDER) byDim.set(dim, []);
    for (const f of filtered) {
      byDim.get(f.dimension)?.push(f);
    }
    for (const list of byDim.values()) {
      list.sort(
        (a, b) =>
          SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity),
      );
    }
    return byDim;
  }, [findings, severityFilter]);

  return (
    <section className="findings">
      <div className="panel-head">
        <h2>Findings</h2>
        <div className="filters" role="group" aria-label="Severity filter">
          <button
            type="button"
            className={severityFilter === "all" ? "chip active" : "chip"}
            onClick={() => setSeverityFilter("all")}
          >
            All
          </button>
          {SEVERITY_ORDER.map((s) => (
            <button
              key={s}
              type="button"
              className={severityFilter === s ? `chip active sev-${s}` : `chip sev-${s}`}
              onClick={() => setSeverityFilter(s)}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {DIM_ORDER.map((dim) => {
        const items = grouped.get(dim) ?? [];
        if (!items.length) return null;
        return (
          <div key={dim} className="finding-group">
            <h3>{DIM_LABEL[dim]}</h3>
            <ul>
              {items.map((f, i) => (
                <li key={`${f.rule_id}-${f.file}-${f.line}-${i}`} className={`sev-${f.severity}`}>
                  <div className="finding-top">
                    <span className={`badge sev-${f.severity}`}>{f.severity}</span>
                    <code className="rule">{f.rule_id}</code>
                    {(f.file || f.line != null) && (
                      <span className="loc mono">
                        {f.file ?? "—"}
                        {f.line != null ? `:${f.line}` : ""}
                      </span>
                    )}
                  </div>
                  <p>{f.message}</p>
                  {f.evidence && <pre className="evidence">{f.evidence}</pre>}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
