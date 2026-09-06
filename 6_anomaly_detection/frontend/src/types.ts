export type Backbone = "isolation_forest" | "lof" | "autoencoder" | "ensemble";

export type EvalResponse = {
  n_train: number;
  n_train_normal_fit: number;
  n_test: number;
  test_anomaly_rate: number;
  split: string;
  metrics: Record<
    string,
    {
      pr_auc: number;
      threshold: number;
      precision: number;
      recall: number;
      confusion_matrix: { labels: number[]; matrix: number[][] };
    }
  >;
  pr_curves: Record<string, { recall: number; precision: number }[]>;
  feature_cols: string[];
  top_anomalies: Record<string, string | number>[];
};

export type ScoreItem = {
  isolation_forest: number;
  lof: number;
  autoencoder: number;
  ensemble: number;
  flagged_by: string[];
};
