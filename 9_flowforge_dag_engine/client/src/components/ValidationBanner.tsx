import type { ValidateResult } from "../types";

interface Props {
  result: ValidateResult | null;
}

export function ValidationBanner({ result }: Props) {
  if (!result) {
    return (
      <div className="banner banner--neutral">
        Connect nodes into a DAG, then validate. Cycles block execution.
      </div>
    );
  }

  if (result.valid) {
    return (
      <div className="banner banner--ok">
        Valid DAG — topological order:{" "}
        <code>{(result.order ?? []).join(" → ")}</code>
      </div>
    );
  }

  return (
    <div className="banner banner--err" role="alert">
      <strong>Cycle detected.</strong> {result.error}
      {result.cycleHint && result.cycleHint.length > 0 ? (
        <>
          {" "}
          Nodes involved: <code>{result.cycleHint.join(", ")}</code>
        </>
      ) : null}
    </div>
  );
}
