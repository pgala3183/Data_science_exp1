"""Reproducibility / random seed checks."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.fsutil import SourceFile
from app.schemas import Finding

SEED_CALL = re.compile(
    r"\b(random_state\s*=|np\.random\.seed\s*\(|numpy\.random\.seed\s*\(|"
    r"random\.seed\s*\(|torch\.manual_seed\s*\(|torch\.cuda\.manual_seed|"
    r"SEED\s*=|RANDOM_STATE\s*=|rng\s*=\s*np\.random\.default_rng)\b"
)

# Constructors that usually accept random_state
# Estimators / helpers where omitting random_state commonly hurts reproducibility.
# (Deterministic linear models like default Ridge/Lasso are intentionally omitted.)
RANDOM_CTORS = {
    "train_test_split",
    "KMeans",
    "MiniBatchKMeans",
    "RandomForestClassifier",
    "RandomForestRegressor",
    "ExtraTreesClassifier",
    "ExtraTreesRegressor",
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "HistGradientBoostingClassifier",
    "HistGradientBoostingRegressor",
    "LogisticRegression",
    "PCA",
    "TruncatedSVD",
    "TSNE",
    "BernoulliRBM",
    "MLPClassifier",
    "MLPRegressor",
    "BaggingClassifier",
    "BaggingRegressor",
    "AdaBoostClassifier",
    "AdaBoostRegressor",
    "IsolationForest",
    "SGDClassifier",
    "SGDRegressor",
    "ShuffleSplit",
    "StratifiedShuffleSplit",
}


class _RandomStateVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.missing: list[tuple[int, str]] = []
        self.present: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)
        if name in RANDOM_CTORS:
            has_rs = any(
                (kw.arg == "random_state") for kw in node.keywords if kw.arg is not None
            )
            # train_test_split also accepts shuffle=False which is deterministic
            if name == "train_test_split" and not has_rs:
                for kw in node.keywords:
                    if kw.arg == "shuffle" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                        has_rs = True
            line = getattr(node, "lineno", 0) or 0
            if has_rs:
                self.present.append((line, name))
            else:
                self.missing.append((line, name))
        self.generic_visit(node)


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def check(_root: Path, files: list[SourceFile]) -> list[Finding]:
    findings: list[Finding] = []
    any_seed = False
    missing_count = 0

    for sf in files:
        if SEED_CALL.search(sf.text):
            any_seed = True

        try:
            tree = ast.parse(sf.text)
        except SyntaxError:
            continue
        visitor = _RandomStateVisitor()
        visitor.visit(tree)
        for ln, name in visitor.missing[:8]:
            missing_count += 1
            findings.append(
                Finding(
                    dimension="reproducibility",
                    severity="medium",
                    rule_id="SEED_MISSING_RANDOM_STATE",
                    message=f"`{name}(...)` called without `random_state` / deterministic flag.",
                    file=sf.relative,
                    line=ln,
                    evidence=name,
                )
            )
        if visitor.present:
            any_seed = True

    if not any_seed:
        findings.append(
            Finding(
                dimension="reproducibility",
                severity="high",
                rule_id="SEED_NONE_PROJECT",
                message=(
                    "No `random_state`, `SEED`, `np.random.seed`, or `torch.manual_seed` "
                    "usage detected in the project."
                ),
            )
        )

    # Cap noisy medium findings
    medium = [f for f in findings if f.rule_id == "SEED_MISSING_RANDOM_STATE"]
    if len(medium) > 6:
        findings = [f for f in findings if f.rule_id != "SEED_MISSING_RANDOM_STATE"] + medium[:6]
        findings.append(
            Finding(
                dimension="reproducibility",
                severity="low",
                rule_id="SEED_MISSING_TRUNCATED",
                message=f"{missing_count} calls missing random_state; showing first 6.",
            )
        )

    if not findings:
        findings.append(
            Finding(
                dimension="reproducibility",
                severity="info",
                rule_id="SEED_OK",
                message="Seed / random_state usage looks present.",
            )
        )
    return findings
