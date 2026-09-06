import { useEffect, useState } from "react";
import { fetchSegmentCustomers, fetchSegments } from "./api";
import { ModelSelectionCharts } from "./components/ModelSelectionCharts";
import { ProjectionScatter } from "./components/ProjectionScatter";
import { SegmentPanel } from "./components/SegmentPanel";
import type { Method, SegmentCustomers, SegmentsResponse } from "./types";
import "./styles.css";

export default function App() {
  const [method, setMethod] = useState<Method>("kmeans");
  const [data, setData] = useState<SegmentsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<number | null>(null);
  const [customers, setCustomers] = useState<SegmentCustomers | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchSegments(method)
      .then((res) => {
        setData(res);
        setSelected(res.profiles[0]?.cluster_id ?? null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"))
      .finally(() => setLoading(false));
  }, [method]);

  useEffect(() => {
    if (selected == null) return;
    fetchSegmentCustomers(selected, method)
      .then(setCustomers)
      .catch(() => setCustomers(null));
  }, [selected, method]);

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 3</p>
        <h1>Customer Segmentation</h1>
        <p className="lede">
          RFM features → K-Means (silhouette-selected k) vs Ward agglomerative, projected with PCA.
        </p>
        <div className="method-toggle" role="group" aria-label="Clustering method">
          <button
            type="button"
            className={method === "kmeans" ? "active" : ""}
            aria-pressed={method === "kmeans"}
            onClick={() => setMethod("kmeans")}
          >
            K-Means
          </button>
          <button
            type="button"
            className={method === "agglomerative" ? "active" : ""}
            aria-pressed={method === "agglomerative"}
            onClick={() => setMethod("agglomerative")}
          >
            Agglomerative
          </button>
        </div>
      </header>

      {loading && <p className="muted">Computing segments…</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {data && !loading && (
        <>
          <p className="meta-line">
            {data.n_customers.toLocaleString()} customers · k={data.k} · silhouette{" "}
            {data.silhouette.toFixed(3)}
          </p>
          <div className="layout">
            <ProjectionScatter
              points={data.projection}
              profiles={data.profiles}
              onSelectCluster={setSelected}
            />
            <ModelSelectionCharts data={data} />
          </div>
          <SegmentPanel
            profiles={data.profiles}
            selectedId={selected}
            customers={customers}
            onSelect={setSelected}
          />
        </>
      )}
    </div>
  );
}
