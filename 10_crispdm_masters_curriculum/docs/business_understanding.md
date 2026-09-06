# Phase 1 — Business Understanding

## Business objective

Public agencies and lenders often need a **screening model** that estimates whether an adult’s annual income exceeds $50K, using census-style demographics and employment attributes. The goal is not to replace case review, but to:

1. Prioritize outreach or underwriting queues.
2. Quantify which factors associate with income bracket in historical data.
3. Surface fairness risks before any operational use.

This project uses the UCI **Adult / Census Income** dataset (OpenML id 1590) as a stand-in for that problem.

## Data-mining goals

| Goal | Description |
|------|-------------|
| Primary | Binary classification: `income` ∈ {`<=50K`, `>50K`} |
| Secondary | Rank individuals by predicted P(`>50K`) for triage |
| Exploratory | Explain disparities across sensitive attributes (sex, race) |
| Deployment | Serve predictions and **similar historical records** (LSH) for case analogy |

## Success criteria

| Criterion | Target | Rationale |
|-----------|--------|-----------|
| Discrimination | Hold-out **ROC-AUC ≥ 0.85** | Separates brackets better than a weak baseline |
| Balanced quality | Hold-out **F1 (positive = >50K) ≥ 0.60** | Class imbalance (~24% positive); accuracy alone is misleading |
| Baseline beat | Gradient boosting beats logistic regression on ROC-AUC | Confirms non-linear signal is worth the complexity |
| Fairness transparency | Report per-group TPR / FPR / selection rate for **sex** and **race** | Do not deploy without documenting disparities |
| Similarity utility | Median cosine similarity of top-5 neighbors ≥ 0.7 on held-out probes | Analog retrieval is useful for human review |

## Business constraints & ethics

- **Protected attributes** (`sex`, `race`) may appear in census features. We **measure** group performance differences honestly; we do **not** claim the model is fair or suitable for automated decisions.
- Features such as `fnlwgt` are sampling weights, not causal drivers — kept for reproducibility with the classic Adult benchmark, but interpreted cautiously.
- Any real deployment would require legal review, human-in-the-loop policy, and monitoring for drift.

## CRISP-DM mapping

| Phase | Artifact in this repo |
|-------|------------------------|
| Business Understanding | This document; `/business` API summary |
| Data Understanding | `/eda` + Data Understanding UI tab |
| Data Preparation | `app/preparation.py` + pipeline diagram |
| Modeling | Logistic regression + HistGradientBoosting + CV |
| Evaluation | `/evaluate`, fairness tables, `docs/evaluation.md` |
| Deployment | `/predict`, `/similar` (cosine + custom LSH), Deployment tab |

## Stakeholders

- **Model owners** — need metrics and fairness reports.
- **Analysts** — need EDA and similar-case retrieval.
- **Compliance** — need explicit documentation of disparities and limitations.
