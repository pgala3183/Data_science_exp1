import type { AuditResponse } from "../types";

interface Props {
  result: AuditResponse;
}

export function GradeSummary({ result }: Props) {
  const tone =
    result.letter_grade === "A" || result.letter_grade === "B"
      ? "good"
      : result.letter_grade === "C"
        ? "mid"
        : "bad";

  return (
    <div className={`grade-card grade-${tone}`}>
      <div className="grade-letter" aria-label={`Letter grade ${result.letter_grade}`}>
        {result.letter_grade}
      </div>
      <div className="grade-meta">
        <p className="grade-score">{result.overall_score}/100 overall</p>
        <p className="grade-name">{result.project_name}</p>
        <p className="grade-path mono">{result.project_path}</p>
        <p className="grade-files">{result.files_scanned} Python files scanned</p>
      </div>
    </div>
  );
}
