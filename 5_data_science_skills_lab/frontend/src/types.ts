export type Skill = {
  id: string;
  name: string;
  category: string;
  difficulty: string;
  dataset: string;
  description: string;
  snippet: string;
  script: string;
};

export type RunResult = {
  kind: string;
  title?: string;
  metrics?: Record<string, unknown>;
  rows?: Record<string, unknown>[];
  series?: Record<string, unknown>[];
  chart_type?: string;
  x_key?: string;
  y_key?: string;
  y_keys?: string[];
  chart?: {
    chart_type: string;
    series: Record<string, unknown>[];
    x_key: string;
    y_key?: string;
    y_keys?: string[];
  };
  table?: Record<string, unknown>[];
  sample_columns?: string[];
};
