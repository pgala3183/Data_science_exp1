import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { CLUSTER_COLORS } from "../colors";
import type { ProjectionPoint, SegmentProfile } from "../types";

type Props = {
  points: ProjectionPoint[];
  profiles: SegmentProfile[];
  onSelectCluster: (id: number) => void;
};

function Tip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ProjectionPoint }> }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="tooltip">
      <strong>Customer {p.customer_id}</strong>
      <div>Cluster {p.cluster_id}</div>
      <div>R {p.Recency.toFixed(0)}d · F {p.Frequency} · M ${p.Monetary.toFixed(0)}</div>
    </div>
  );
}

export function ProjectionScatter({ points, profiles, onSelectCluster }: Props) {
  const byCluster = profiles.map((p) => ({
    id: p.cluster_id,
    name: p.name,
    data: points.filter((pt) => pt.cluster_id === p.cluster_id),
  }));

  return (
    <section className="panel chart-panel" aria-labelledby="proj-title">
      <div className="panel-head">
        <h2 id="proj-title">PCA projection of RFM</h2>
        <p className="muted">Click a cluster in the legend cards below to inspect customers.</p>
      </div>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={360}>
          <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d6d3d1" />
            <XAxis type="number" dataKey="pc1" name="PC1" tick={{ fontSize: 11 }} />
            <YAxis type="number" dataKey="pc2" name="PC2" tick={{ fontSize: 11 }} />
            <ZAxis range={[40, 40]} />
            <Tooltip content={<Tip />} cursor={{ strokeDasharray: "3 3" }} />
            {byCluster.map((c, i) => (
              <Scatter
                key={c.id}
                name={c.name}
                data={c.data}
                fill={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                onClick={() => onSelectCluster(c.id)}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <ul className="legend">
        {byCluster.map((c, i) => (
          <li key={c.id}>
            <button type="button" onClick={() => onSelectCluster(c.id)}>
              <span className="swatch" style={{ background: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }} />
              {c.name} ({c.data.length})
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
