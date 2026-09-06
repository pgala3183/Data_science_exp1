const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} failed (${res.status})`);
  return res.json() as Promise<T>;
}

export const api = {
  clt: (body: { dist: string; sample_size: number; n_samples: number }) =>
    post<{
      histogram: { centers: number[]; density: number[] };
      normal_curve: { x: number[]; y: number[] };
      sampling_mean: number;
      sampling_std: number;
      theoretical_se: number;
      population_mean: number;
      example_sample: number[];
    }>("/simulate/clt", body),
  lossSurface: () =>
    get<{ w1: number[]; w2: number[]; z: number[][]; minimum: { w1: number; w2: number } }>(
      "/loss-surface?resolution=50",
    ),
  gd: (body: { w1: number; w2: number; lr: number; steps: number }) =>
    post<{ path: { w1: number; w2: number; loss: number; g1: number; g2: number }[] }>(
      "/gradient-descent",
      body,
    ),
  biasVariance: (body: { degree: number; n_train?: number }) =>
    post<{
      degree: number;
      train_points: { x: number[]; y: number[] };
      truth: { x: number[]; y: number[] };
      fit: { x: number[]; y: number[] };
      error_curves: { degrees: number[]; train_mse: number[]; test_mse: number[] };
      train_mse: number;
      test_mse: number;
    }>("/bias-variance", body),
  roc: (threshold: number) =>
    post<{
      threshold: number;
      confusion: { tp: number; fp: number; tn: number; fn: number };
      precision: number;
      recall: number;
      fpr: number;
      auc: number;
      roc: { threshold: number; fpr: number; tpr: number }[];
      operating_point: { fpr: number; tpr: number };
    }>("/roc", { threshold }),
};
