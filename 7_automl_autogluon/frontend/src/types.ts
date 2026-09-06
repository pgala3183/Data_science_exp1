export type SchemaField = {
  name: string;
  type: "number" | "categorical";
  example?: string | number;
  categories?: string[];
};

export type LeaderboardRow = {
  model: string;
  score_val: number | null;
  score_test: number | null;
  fit_time: number | null;
  pred_time_val: number | null;
  pred_time_test: number | null;
  stack_level: number;
};

export type StackArchitecture = {
  levels: Record<string, string[]>;
  nodes: { id: string; level: number; ensemble: boolean }[];
  edges: { from: string; to: string }[];
};

export type LeaderboardResponse = {
  leaderboard: LeaderboardRow[];
  best_model: string;
  eval_metric: string;
  n_train: number;
  n_test: number;
  test_roc_auc: number;
  test_accuracy: number;
  presets: string;
  num_bag_folds: number;
  num_stack_levels: number;
  stack_architecture: StackArchitecture;
  schema: SchemaField[];
  class_labels: string[];
  positive_class: string;
};

export type PredictResponse = {
  prediction: string;
  probabilities: Record<string, number>;
  best_model: string;
  per_model_predictions: Record<string, string>;
};

export type ExplainResponse = {
  method: string;
  features: { feature: string; importance: number; stddev: number | null }[];
  error: string | null;
};
