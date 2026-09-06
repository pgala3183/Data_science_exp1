import { useMemo } from "react";
import type { AttentionPayload } from "../types";

type Props = {
  attention: AttentionPayload | null;
  error: string | null;
};

export function AttentionHeatmap({ attention, error }: Props) {
  const cells = useMemo(() => {
    if (!attention) return null;
    const m = attention.matrix_avg_heads;
    // Downsample large matrices for display
    const maxN = 48;
    const n = m.length;
    const step = Math.max(1, Math.ceil(n / maxN));
    const sampled: number[][] = [];
    for (let i = 0; i < n; i += step) {
      const row: number[] = [];
      for (let j = 0; j < n; j += step) {
        row.push(m[i][j]);
      }
      sampled.push(row);
    }
    return sampled;
  }, [attention]);

  if (error) {
    return <p className="muted">{error}</p>;
  }
  if (!cells) {
    return <p className="muted">Generate a reply on the Chat page to capture last-layer attention.</p>;
  }

  return (
    <div className="heatmap-wrap">
      <p className="muted">
        Last-layer attention averaged over {attention!.n_heads} heads (seq={attention!.seq_len}
        ). Brighter = higher weight. Causal mask → upper triangle is empty.
      </p>
      <div
        className="heatmap"
        style={{ gridTemplateColumns: `repeat(${cells[0].length}, 10px)` }}
        role="img"
        aria-label="Attention weight heatmap"
      >
        {cells.flatMap((row, i) =>
          row.map((v, j) => (
            <span
              key={`${i}-${j}`}
              title={`${v.toFixed(3)}`}
              style={{ background: `rgba(34, 211, 238, ${Math.min(1, v * 3)})` }}
            />
          )),
        )}
      </div>
    </div>
  );
}
