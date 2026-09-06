export type Method = "kmeans" | "agglomerative";

export type SegmentProfile = {
  cluster_id: number;
  name: string;
  description: string;
  marketing_actions: string[];
  centroid: { Recency: number; Frequency: number; Monetary: number };
  size: number;
};

export type ProjectionPoint = {
  customer_id: number;
  cluster_id: number;
  pc1: number;
  pc2: number;
  Recency: number;
  Frequency: number;
  Monetary: number;
};

export type SegmentsResponse = {
  method: string;
  k: number;
  silhouette: number;
  chosen_reason: string;
  profiles: SegmentProfile[];
  projection: ProjectionPoint[];
  inertia_curve: { k: number; inertia: number | null }[];
  silhouette_curve: { k: number; silhouette: number | null }[];
  alternative_method: string;
  alternative_silhouette: number;
  n_customers: number;
};

export type SegmentCustomers = {
  cluster_id: number;
  name: string;
  total: number;
  customers: {
    customer_id: number;
    Recency: number;
    Frequency: number;
    Monetary: number;
    cluster_id: number;
  }[];
};
