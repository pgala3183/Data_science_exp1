"""Train/test leakage heuristics via lightweight AST + line-order scans."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.audit.fsutil import SourceFile
from app.audit.schemas import Finding

SPLIT_CALL_NAMES = {
    "train_test_split",
    "TimeSeriesSplit",
    "KFold",
    "StratifiedKFold",
    "GroupKFold",
}

SPLIT_ASSIGN_HINT = re.compile(
    r"\b(train_idx|test_idx|val_idx|split_train|time.?based.?split)\b",
    re.IGNORECASE,
)

SCALER_TYPES = {
    "StandardScaler",
    "MinMaxScaler",
    "RobustScaler",
    "MaxAbsScaler",
    "Normalizer",
    "SimpleImputer",
    "KNNImputer",
    "PCA",
    "TruncatedSVD",
    "OneHotEncoder",
    "OrdinalEncoder",
    "LabelEncoder",
    "PolynomialFeatures",
    "CountVectorizer",
    "TfidfVectorizer",
    "KMeans",
}

TARGET_LEAK_HINT = re.compile(
    r"\b(dropoff_datetime|fare_amount|tip_amount|total_amount|trip_speed|"
    r"actual_duration|label_encode.*target|target\.map)\b",
    re.IGNORECASE,
)

TRAIN_SUBSET = re.compile(r"\b(X_train|y_train|train_df|df_train|train_idx)\b")


class _LeakVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.split_lines: list[int] = []
        self.fits: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)
        line = getattr(node, "lineno", 0) or 0
        if name in SPLIT_CALL_NAMES:
            self.split_lines.append(line)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"fit", "fit_transform"}:
            try:
                snippet = ast.unparse(node)[:120]
            except Exception:
                snippet = f".{node.func.attr}(...)"
            self.fits.append((line, snippet))
        # TimeSeriesSplit().split(...) etc.
        if isinstance(node.func, ast.Attribute) and node.func.attr == "split":
            self.split_lines.append(line)
        self.generic_visit(node)


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _lines_with(text: str, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            out.append((i, line.strip()))
    return out


def check(_root: Path, files: list[SourceFile]) -> list[Finding]:
    findings: list[Finding] = []
    saw_any_split = False
    saw_any_fit = False

    for sf in files:
        text = sf.text
        try:
            tree = ast.parse(text)
            visitor = _LeakVisitor()
            visitor.visit(tree)
            fit_sites = visitor.fits
            split_lines = visitor.split_lines
        except SyntaxError:
            fit_sites = []
            split_lines = []

        # Assignment-style split hints (custom pipelines)
        for i, line in enumerate(text.splitlines(), start=1):
            if SPLIT_ASSIGN_HINT.search(line) and "import" not in line:
                split_lines.append(i)

        if split_lines:
            saw_any_split = True
        if fit_sites:
            saw_any_fit = True

        first_split = min(split_lines) if split_lines else None

        if fit_sites and first_split is not None:
            for ln, snip in fit_sites:
                if ln >= first_split:
                    continue
                prior = "\n".join(text.splitlines()[: ln - 1])
                if TRAIN_SUBSET.search(prior):
                    continue
                findings.append(
                    Finding(
                        dimension="leakage",
                        severity="high",
                        rule_id="LEAK_FIT_BEFORE_SPLIT",
                        message=(
                            "Transformer/model `.fit` / `.fit_transform` appears before a "
                            "train/test split call in this file — possible full-dataset fitting."
                        ),
                        file=sf.relative,
                        line=ln,
                        evidence=snip,
                    )
                )
        elif fit_sites and first_split is None and any(t in text for t in SCALER_TYPES):
            for ln, snip in fit_sites:
                if "fit_transform" in snip:
                    findings.append(
                        Finding(
                            dimension="leakage",
                            severity="medium",
                            rule_id="LEAK_FIT_NO_SPLIT_IN_FILE",
                            message=(
                                "Scaler/transformer fit found with no train/test split in this "
                                "file. Confirm fitting is restricted to training rows."
                            ),
                            file=sf.relative,
                            line=ln,
                            evidence=snip,
                        )
                    )
                    break

        for ln, line in _lines_with(text, TARGET_LEAK_HINT):
            findings.append(
                Finding(
                    dimension="leakage",
                    severity="medium",
                    rule_id="LEAK_SUSPICIOUS_TARGET_FEATURE",
                    message=(
                        "Identifier often associated with post-outcome / target-derived "
                        "features detected. Verify it is not used as a model input."
                    ),
                    file=sf.relative,
                    line=ln,
                    evidence=line[:160],
                )
            )

    # Cap duplicate LEAK_FIT_BEFORE_SPLIT per file noise
    seen_files: set[str] = set()
    capped: list[Finding] = []
    for f in findings:
        if f.rule_id == "LEAK_FIT_BEFORE_SPLIT" and f.file:
            key = f.file
            if key in seen_files:
                continue
            seen_files.add(key)
        capped.append(f)
    findings = capped

    if saw_any_fit and not saw_any_split:
        findings.append(
            Finding(
                dimension="leakage",
                severity="low",
                rule_id="LEAK_NO_SPLIT_PROJECT",
                message=(
                    "Project fits estimators but no common train/test split pattern was "
                    "detected across scanned Python files."
                ),
            )
        )

    if not findings:
        findings.append(
            Finding(
                dimension="leakage",
                severity="info",
                rule_id="LEAK_OK",
                message="No high-confidence static leakage patterns detected.",
            )
        )
    return findings
