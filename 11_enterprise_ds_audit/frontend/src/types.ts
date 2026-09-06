export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type DimensionId =
  | "leakage"
  | "reproducibility"
  | "validation"
  | "tests"
  | "documentation"
  | "fairness";

export interface Finding {
  dimension: DimensionId;
  severity: Severity;
  rule_id: string;
  message: string;
  file: string | null;
  line: number | null;
  evidence: string | null;
}

export interface DimensionScore {
  dimension: DimensionId;
  label: string;
  score: number;
  finding_count: number;
}

export interface AuditResponse {
  project_path: string;
  project_name: string;
  overall_score: number;
  letter_grade: string;
  dimensions: DimensionScore[];
  findings: Finding[];
  files_scanned: number;
  notes: string[];
}
