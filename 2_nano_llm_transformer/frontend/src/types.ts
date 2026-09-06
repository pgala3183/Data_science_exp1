export type GenSettings = {
  temperature: number;
  top_p: number;
  top_k: number;
  max_tokens: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type ModelInfo = {
  params: number;
  checkpoint: string;
  stage: string | null;
  config: Record<string, number | boolean>;
  meta: Record<string, unknown>;
};

export type AttentionPayload = {
  seq_len: number;
  n_heads: number;
  last_query_avg_over_heads: number[];
  matrix_avg_heads: number[][];
};
