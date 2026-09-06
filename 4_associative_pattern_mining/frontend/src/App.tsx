import { useEffect, useState } from "react";
import { fetchGraph, fetchItems, fetchRules } from "./api";
import { BasketSimulator } from "./components/BasketSimulator";
import { ForceGraph } from "./components/ForceGraph";
import { RulesTable } from "./components/RulesTable";
import type { Filters, GraphData, RulesResponse } from "./types";
import "./styles.css";

const defaultFilters: Filters = {
  min_support: 0.02,
  min_confidence: 0.25,
  min_lift: 1.2,
  sort_by: "lift",
};

export default function App() {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [page, setPage] = useState(1);
  const [rules, setRules] = useState<RulesResponse | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [catalog, setCatalog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchItems().then(setCatalog).catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    setPage(1);
  }, [filters.min_support, filters.min_confidence, filters.min_lift, filters.sort_by]);

  useEffect(() => {
    setError(null);
    Promise.all([fetchRules(filters, page, 15), fetchGraph(filters)])
      .then(([r, g]) => {
        setRules(r);
        setGraph(g);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [filters, page]);

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 4</p>
        <h1>Associative Pattern Mining</h1>
        <p className="lede">
          Market baskets → Apriori &amp; FP-Growth itemsets → association rules with support,
          confidence, and lift.
        </p>
        {rules && (
          <p className="meta">
            {rules.n_transactions.toLocaleString()} transactions · {rules.n_items} items · serving
            FP-Growth itemsets
          </p>
        )}
      </header>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {graph && <ForceGraph data={graph} />}

      {rules && (
        <RulesTable
          rules={rules.rules}
          total={rules.total}
          page={rules.page}
          pageSize={rules.page_size}
          filters={filters}
          benchmarks={rules.benchmarks}
          onFilters={setFilters}
          onPage={setPage}
        />
      )}

      <BasketSimulator catalog={catalog} />
    </div>
  );
}
