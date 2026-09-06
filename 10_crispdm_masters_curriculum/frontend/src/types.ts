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
  positive_rate: number;
  missingness: { column: string; missing: number; missing_pct: number }[];
  numeric_summary: {
    column: string;
    mean: number | null;
    std: number | null;
    min: number | null;
    median: number | null;
    max: number | null;
  }[];
  categorical_summary: {
    column: string;
    n_unique: number;
    top: { value: string; count: number }[];
  }[];
  correlation: { columns: string[]; matrix: (number | null)[][] };
  target_by_sex: { group: string; n: number; gt_50k_rate: number }[];
  target_by_race: { group: string; n: number; gt_50k_rate: number }[];
  target_by_education: { group: string; n: number; gt_50k_rate: number }[];
};

export type PipelinePayload = {
  name: string;
  steps: { id: string; title: string; detail: string }[];
  numeric_features: string[];
  categorical_features: string[];
};

export type ModelMetrics = {
  accuracy: number;
  f1: number;
  roc_auc: number;
  confusion_matrix: { labels: string[]; matrix: number[][] };
  roc_curve: { fpr: number[]; tpr: number[] };
};

export type FairnessGroup = {
  group: string;
  support: number;
  base_rate: number;
  selection_rate: number;
  tpr: number;
  fpr: number;
  accuracy: number;
  f1: number;
  mean_prob_gt_50k: number;
};

export type EvalPayload = {
  n_train: number;
  n_test: number;
  positive_label: string;
  cv: Record<
    string,
    {
      cv_folds: number;
      roc_auc_mean: number;
      roc_auc_std: number;
      f1_mean: number;
      f1_std: number;
    }
  >;
  metrics: Record<string, ModelMetrics>;
  fairness: Record<
    string,
    {
      by_attribute: Record<string, FairnessGroup[]>;
      disparities: Record<
        string,
        {
          majority_group: string;
          tpr_range: number;
          selection_rate_range: number;
          note: string;
        }
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
};

export type PredictResult = {
  prediction: string;
  probability_gt_50k: number;
  model: string;
  probabilities: Record<string, number>;
};

export type SimilarNeighbor = {
  rank: number;
  cosine_similarity: number;
  income: string;
  record: Record<string, string | number | null>;
};

export type SimilarResult = {
  query_prediction: string | null;
  query_probability_gt_50k: number | null;
  neighbors: SimilarNeighbor[];
  lsh_candidates_scanned: number;
  method: string;
};
