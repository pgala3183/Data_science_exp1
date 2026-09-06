"""README / environment documentation checks."""

from __future__ import annotations

import re
from pathlib import Path

from app.audit.fsutil import SourceFile, find_readme, has_env_spec
from app.audit.schemas import Finding

REQUIRED_SECTIONS = {
    "problem": re.compile(r"(problem\s+statement|overview|what\s+this|purpose|goal)", re.I),
    "dataset": re.compile(r"(dataset|data\s+source|data\s*&|inputs?)", re.I),
    "how_to_run": re.compile(r"(how\s+to\s+run|getting\s+started|quickstart|install|usage)", re.I),
    "methodology": re.compile(r"(method|model|pipeline|approach|crisp|architecture)", re.I),
}


def check(root: Path, _files: list[SourceFile]) -> list[Finding]:
    findings: list[Finding] = []
    readme = find_readme(root)

    if readme is None:
        findings.append(
            Finding(
                dimension="documentation",
                severity="critical",
                rule_id="DOC_NO_README",
                message="No README file found at project root.",
            )
        )
    else:
        rel = str(readme.relative_to(root)).replace("\\", "/")
        text = readme.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 200:
            findings.append(
                Finding(
                    dimension="documentation",
                    severity="high",
                    rule_id="DOC_README_TOO_SHORT",
                    message="README exists but is very short (<200 characters).",
                    file=rel,
                    line=1,
                )
            )
        missing = [name for name, pat in REQUIRED_SECTIONS.items() if not pat.search(text)]
        for name in missing:
            findings.append(
                Finding(
                    dimension="documentation",
                    severity="medium",
                    rule_id=f"DOC_MISSING_SECTION_{name.upper()}",
                    message=f"README appears to lack a '{name.replace('_', ' ')}' section.",
                    file=rel,
                    line=1,
                )
            )
        if not missing and len(text.strip()) >= 200:
            findings.append(
                Finding(
                    dimension="documentation",
                    severity="info",
                    rule_id="DOC_README_OK",
                    message="README present with expected section signals.",
                    file=rel,
                    line=1,
                )
            )

    ok, env_path = has_env_spec(root)
    if not ok:
        findings.append(
            Finding(
                dimension="documentation",
                severity="high",
                rule_id="DOC_NO_ENV_SPEC",
                message=(
                    "No environment specification found (requirements.txt, "
                    "environment.yml, pyproject.toml, Pipfile, …)."
                ),
            )
        )
    else:
        findings.append(
            Finding(
                dimension="documentation",
                severity="info",
                rule_id="DOC_ENV_SPEC_OK",
                message=f"Environment spec found: {env_path}",
                file=env_path,
            )
        )

    return findings
