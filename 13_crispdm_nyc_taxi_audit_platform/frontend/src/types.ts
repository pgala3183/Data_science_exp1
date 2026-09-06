export type BusinessPayload = {
  phase: string;
  title: string;
  objective: string;
  success_criteria: { metric: string; target: string }[];
  markdown: string;
};

export type EdaPayload = {
  n_rows: number;
  n_cols: number;
  label: string;
  label_counts: Record<string, number>;
  mean_duration: number;
  median_duration: number;
  missingness: { column: string; missing: number; missing_pct: number }[];
  numeric_summary: {
    column: string;
    mean: number | null;
    std: number | null;
    min: number | null;
    median: number | null;
    max: number | null;
  }[];
  correlation: { columns: string[]; matrix: (number | null)[][] };
  duration_by_hour: { group: string; n: number; mean_duration: number }[];
  duration_by_weekend: { group: string; n: number; mean_duration: number }[];
  duration_by_rush: { group: string; n: number; mean_duration: number }[];
};

export type PipelinePayload = {
  name: string;
  steps: { id: string; title: string; detail: string }[];
  numeric_features: string[];
  categorical_features: string[];
};

export type ModelMetric = {
  name: string;
  rmse: number;
  mae: number;
  r2: number;
  feature_importances: Record<string, number>;
};

export type FairnessGroup = {
  group: string;
  support: number;
  mean_duration: number;
  mae: number;
  rmse: number;
  mean_residual: number;
};

export type EvalPayload = {
  n_train: number;
  n_test: number;
  target: string;
  split: string;
  cv: Record<
    string,
    {
      cv_folds: number;
      rmse_mean: number;
      rmse_std: number;
    }
  >;
  metrics: Record<string, ModelMetric>;
  residuals: Record<
    string,
    {
      mean: number;
      std: number;
      p05: number;
      p50: number;
      p95: number;
      histogram: { counts: number[]; bin_edges: number[] };
    }
  >;
  fairness: Record<
    string,
    {
      by_attribute: Record<string, FairnessGroup[]>;
      disparities: Record<
        string,
        { majority_group: string; mae_range: number; note: string }
      >;
    }
  >;
  primary_model: string;
  pipeline: PipelinePayload;
  evaluation_doc: string;
};

export type SchemaPayload = {
  label: string;
  feature_cols: string[];
  example: Record<string, string | number | null>;
  models: string[];
  primary_model: string;
};

export type PredictResult = {
  predicted_duration_seconds: number;
  predicted_duration_minutes: number;
  confidence_interval_95_seconds: [number, number];
  model_name: string;
  top_features: { feature: string; importance: number }[];
  haversine_km: number;
};

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type DimensionId =
  | "leakage"
  | "reproducibility"
  | "validation"
  | "tests"
  | "documentation"
  | "fairness";

export type Finding = {
  dimension: DimensionId;
  severity: Severity;
  rule_id: string;
  message: string;
  file: string | null;
  line: number | null;
  evidence: string | null;
};

export type DimensionScore = {
  dimension: DimensionId;
  label: string;
  score: number;
  finding_count: number;
};

export type AuditResponse = {
  project_path: string;
  project_name: string;
  overall_score: number;
  letter_grade: string;
  dimensions: DimensionScore[];
  findings: Finding[];
  files_scanned: number;
  notes: string[];
};

export type DriftFeature = {
  feature: string;
  psi: number;
  ks_statistic: number;
  ks_pvalue: number;
  train_mean: number;
  batch_mean: number;
  mean_shift: number;
  status: "green" | "yellow" | "red";
};

export type MonitoringPayload = {
  drift_mode: string;
  n_train_ref: number;
  n_batch: number;
  overall_status: "green" | "yellow" | "red";
  thresholds: Record<string, number>;
  summary: {
    red: number;
    yellow: number;
    green: number;
    flagged_features: string[];
  };
  features: DriftFeature[];
  notes: string[];
};
