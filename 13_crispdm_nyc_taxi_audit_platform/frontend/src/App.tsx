import { useEffect, useState } from "react";
import {
  fetchAudit,
  fetchBusiness,
  fetchEda,
  fetchEvaluate,
  fetchMonitoring,
  fetchPipeline,
  fetchSchema,
} from "./api";
import { AuditTab } from "./components/AuditTab";
import { BusinessTab } from "./components/BusinessTab";
import { DataUnderstandingTab } from "./components/DataUnderstandingTab";
import { DeploymentTab } from "./components/DeploymentTab";
import { EvaluationTab } from "./components/EvaluationTab";
import { ModelingTab } from "./components/ModelingTab";
import { MonitoringTab } from "./components/MonitoringTab";
import { PreparationTab } from "./components/PreparationTab";
import type {
  AuditResponse,
  BusinessPayload,
  EdaPayload,
  EvalPayload,
  MonitoringPayload,
  PipelinePayload,
  SchemaPayload,
} from "./types";

type TabId =
  | "business"
  | "data"
  | "prep"
  | "model"
  | "eval"
  | "deploy"
  | "audit"
  | "monitor";

const TABS: { id: TabId; label: string; phase: string }[] = [
  { id: "business", label: "Business", phase: "1" },
  { id: "data", label: "Data", phase: "2" },
  { id: "prep", label: "Preparation", phase: "3" },
  { id: "model", label: "Modeling", phase: "4" },
  { id: "eval", label: "Evaluation", phase: "5" },
  { id: "deploy", label: "Deployment", phase: "6" },
  { id: "audit", label: "Audit", phase: "G" },
  { id: "monitor", label: "Monitoring", phase: "M" },
];

export default function App() {
  const [tab, setTab] = useState<TabId>("business");
  const [business, setBusiness] = useState<BusinessPayload | null>(null);
  const [eda, setEda] = useState<EdaPayload | null>(null);
  const [pipeline, setPipeline] = useState<PipelinePayload | null>(null);
  const [evalData, setEvalData] = useState<EvalPayload | null>(null);
  const [schema, setSchema] = useState<SchemaPayload | null>(null);
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchBusiness(),
      fetchEda(),
      fetchPipeline(),
      fetchEvaluate(),
      fetchSchema(),
      fetchAudit(),
      fetchMonitoring("moderate", 2500),
    ])
      .then(([b, e, p, ev, s, a, m]) => {
        setBusiness(b);
        setEda(e);
        setPipeline(p);
        setEvalData(ev);
        setSchema(s);
        setAudit(a);
        setMonitoring(m);
      })
      .catch((err) =>
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load — is the API running on :8013?",
        ),
      );
  }, []);

  const ready = business && eda && pipeline && evalData && schema && audit && monitoring;
  const primary = evalData?.primary_model;
  const rmse = primary ? evalData?.metrics[primary]?.rmse : undefined;

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">Experiment 13 · Capstone</p>
        <h1>NYC Taxi Audit Platform</h1>
        <p className="lede">
          CRISP-DM trip-duration modeling with live governance: self-certifying DS audit
          scorecard and feature drift monitoring — the production-minded portfolio piece.
        </p>
        {evalData && audit && (
          <p className="meta">
            train={evalData.n_train.toLocaleString()} · test={evalData.n_test.toLocaleString()} ·
            RMSE={rmse?.toFixed(0) ?? "—"}s · model={primary} · audit={audit.letter_grade} (
            {audit.overall_score}) · drift={monitoring?.overall_status ?? "—"}
          </p>
        )}
      </header>

      <nav className="tabs" aria-label="Platform sections">
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
      {!ready && !error && <p className="muted">Loading platform artifacts…</p>}

      {ready && tab === "business" && <BusinessTab data={business} />}
      {ready && tab === "data" && <DataUnderstandingTab data={eda} />}
      {ready && tab === "prep" && <PreparationTab data={pipeline} />}
      {ready && tab === "model" && <ModelingTab data={evalData} />}
      {ready && tab === "eval" && <EvaluationTab data={evalData} />}
      {ready && tab === "deploy" && <DeploymentTab schema={schema} />}
      {ready && tab === "audit" && <AuditTab data={audit} />}
      {ready && tab === "monitor" && (
        <MonitoringTab initial={monitoring} onRefresh={setMonitoring} />
      )}
    </div>
  );
}
