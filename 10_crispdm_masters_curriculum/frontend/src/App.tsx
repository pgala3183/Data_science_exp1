import { useEffect, useState } from "react";
import {
  fetchBusiness,
  fetchEda,
  fetchEvaluate,
  fetchPipeline,
  fetchSchema,
} from "./api";
import { BusinessTab } from "./components/BusinessTab";
import { DataUnderstandingTab } from "./components/DataUnderstandingTab";
import { DeploymentTab } from "./components/DeploymentTab";
import { EvaluationTab } from "./components/EvaluationTab";
import { ModelingTab } from "./components/ModelingTab";
import { PreparationTab } from "./components/PreparationTab";
import type {
  BusinessPayload,
  EdaPayload,
  EvalPayload,
  PipelinePayload,
  SchemaPayload,
} from "./types";

type TabId =
  | "business"
  | "data"
  | "prep"
  | "model"
  | "eval"
  | "deploy";

const TABS: { id: TabId; label: string; phase: string }[] = [
  { id: "business", label: "Business Understanding", phase: "1" },
  { id: "data", label: "Data Understanding", phase: "2" },
  { id: "prep", label: "Data Preparation", phase: "3" },
  { id: "model", label: "Modeling", phase: "4" },
  { id: "eval", label: "Evaluation", phase: "5" },
  { id: "deploy", label: "Deployment", phase: "6" },
];

export default function App() {
  const [tab, setTab] = useState<TabId>("business");
  const [business, setBusiness] = useState<BusinessPayload | null>(null);
  const [eda, setEda] = useState<EdaPayload | null>(null);
  const [pipeline, setPipeline] = useState<PipelinePayload | null>(null);
  const [evalData, setEvalData] = useState<EvalPayload | null>(null);
  const [schema, setSchema] = useState<SchemaPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchBusiness(),
      fetchEda(),
      fetchPipeline(),
      fetchEvaluate(),
      fetchSchema(),
    ])
      .then(([b, e, p, ev, s]) => {
        setBusiness(b);
        setEda(e);
        setPipeline(p);
        setEvalData(ev);
        setSchema(s);
      })
      .catch((err) =>
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load — is the API running on :8010?",
        ),
      );
  }, []);

  const ready = business && eda && pipeline && evalData && schema;
  const auc = evalData?.metrics[evalData.primary_model]?.roc_auc;

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 10 · CRISP-DM</p>
        <h1>Masters Curriculum</h1>
        <p className="lede">
          End-to-end Adult / Census Income project structured on the six CRISP-DM phases, with
          fairness reporting and LSH-backed similar-record search.
        </p>
        {evalData && (
          <p className="meta">
            train={evalData.n_train.toLocaleString()} · test={evalData.n_test.toLocaleString()} ·
            primary AUC={auc?.toFixed(3) ?? "—"} · model={evalData.primary_model}
          </p>
        )}
      </header>

      <nav className="tabs" aria-label="CRISP-DM phases">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            <span className="tab-phase">{t.phase}</span>
            {t.label}
          </button>
        ))}
      </nav>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!ready && !error && <p className="muted">Loading CRISP-DM artifacts…</p>}

      {ready && tab === "business" && <BusinessTab data={business} />}
      {ready && tab === "data" && <DataUnderstandingTab data={eda} />}
      {ready && tab === "prep" && <PreparationTab data={pipeline} />}
      {ready && tab === "model" && <ModelingTab data={evalData} />}
      {ready && tab === "eval" && <EvaluationTab data={evalData} />}
      {ready && tab === "deploy" && <DeploymentTab schema={schema} />}
    </div>
  );
}
