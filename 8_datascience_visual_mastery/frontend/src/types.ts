export type QuizQuestion = {
  id: string;
  prompt: string;
  choices: string[];
  answer: number;
  explain: string;
};

export const CONCEPT_META = [
  { id: "bayes", title: "Bayes' Theorem", blurb: "Prior × evidence → posterior" },
  { id: "clt", title: "Central Limit Theorem", blurb: "Why averages look Gaussian" },
  {
    id: "gradient-descent",
    title: "Gradient Descent",
    blurb: "Rolling downhill on a loss surface",
  },
  {
    id: "bias-variance",
    title: "Bias–Variance",
    blurb: "Underfit vs overfit as degree grows",
  },
  { id: "roc", title: "Confusion & ROC", blurb: "Thresholds trade precision and recall" },
] as const;

export type ConceptId = (typeof CONCEPT_META)[number]["id"];
