export type Accuracies = {
  multimodal: number;
  image_only: number;
  text_only: number;
  tabular_only: number;
};

export type MetricsResponse = {
  label: string;
  n_train: number;
  n_test: number;
  class_labels: string[];
  accuracies: Accuracies;
  best_baseline: string;
  best_baseline_accuracy: number;
  multimodal_accuracy: number;
  lift_vs_best_baseline: number;
  modalities: {
    image: string;
    text: string;
    tabular: string[];
  };
  notes: string;
};

export type DemoSample = {
  description: string;
  price: number;
  rating: number;
  brand_tier: string;
  weight_oz: number;
  is_fragile: number;
  true_category?: string;
  image_url: string;
};

export type PredictSide = {
  prediction: string;
  probabilities: Record<string, number>;
};

export type PredictResponse = {
  multimodal: PredictSide;
  baselines: {
    image_only: PredictSide;
    text_only: PredictSide;
    tabular_only: PredictSide;
  };
  holdout_accuracies: Accuracies;
  lift_vs_best_baseline: number;
  best_baseline: string;
};
