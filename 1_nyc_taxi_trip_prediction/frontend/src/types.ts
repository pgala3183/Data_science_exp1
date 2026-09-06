export type LatLng = { lat: number; lng: number };

export type FeatureContribution = {
  feature: string;
  importance: number;
};

export type PredictResponse = {
  predicted_duration_seconds: number;
  predicted_duration_minutes: number;
  confidence_interval_95_seconds: [number, number];
  model_name: string;
  top_features: FeatureContribution[];
  haversine_km: number;
};

export type ModelMetrics = {
  best_model_name: string;
  residual_std: number;
  n_train: number;
  n_test: number;
  split: string;
  target: string;
  models: Array<{
    name: string;
    rmse: number;
    mae: number;
    r2: number;
    feature_importances: Record<string, number>;
  }>;
};
