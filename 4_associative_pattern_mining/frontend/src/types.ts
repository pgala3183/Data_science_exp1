export type Rule = {
  antecedents: string[];
  consequents: string[];
  support: number;
  confidence: number;
  lift: number;
};

export type RulesResponse = {
  total: number;
  page: number;
  page_size: number;
  sort_by: string;
  rules: Rule[];
  n_transactions: number;
  n_items: number;
  benchmarks: { algorithm: string; seconds: number; n_itemsets: number; peak_note: string }[];
};

export type GraphData = {
  nodes: { id: string; label: string; count: number }[];
  edges: { source: string; target: string; lift: number; confidence: number; support: number }[];
};

export type Filters = {
  min_support: number;
  min_confidence: number;
  min_lift: number;
  sort_by: "lift" | "confidence" | "support";
};

export type RecommendItem = {
  item: string;
  score: number;
  lift: number;
  confidence: number;
  support: number;
  rule: { antecedents: string[]; consequents: string[] };
};
