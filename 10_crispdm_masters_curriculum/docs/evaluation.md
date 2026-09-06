# Phase 5 — Evaluation Write-up

## Assessment against business success criteria

Evaluation uses a stratified hold-out split (20%) after fitting imputation, encoding, and scaling on the training fold only. Two classifiers are compared:

1. **Logistic regression** — linear baseline (interpretable coefficients on the transformed space).
2. **HistGradientBoosting** — stronger non-linear model with early stopping.

Cross-validation (stratified 5-fold) on the training set estimates generalization before the final hold-out report.

### Typical outcomes on Adult Income

| Metric | Logistic regression | HistGradientBoosting |
|--------|---------------------|----------------------|
| Accuracy | ~0.84–0.86 | ~0.86–0.88 |
| F1 (>50K) | ~0.65–0.68 | ~0.68–0.72 |
| ROC-AUC | ~0.89–0.91 | ~0.91–0.93 |

Exact numbers are produced at train time and served from `/evaluate`. HistGradientBoosting usually clears the ROC-AUC ≥ 0.85 and F1 ≥ 0.60 gates and beats the logistic baseline.

## Confusion matrix interpretation

False negatives (true `>50K` predicted `<=50K`) matter for opportunity screening — qualified individuals may be under-ranked. False positives matter for cost-sensitive underwriting. Threshold = 0.5 is reported for transparency; a business could retune on validation F1 or cost.

## Fairness check (honest disparities)

We compute, for each group of **sex** and **race** on the hold-out set:

- **Support** — group size
- **Base rate** — empirical P(`>50K`)
- **Selection rate** — P(predict `>50K`)
- **TPR / FPR** — true/false positive rates
- **Accuracy / F1** within group

### What we typically observe

- **Sex:** Men have a higher base rate of `>50K` in this historical census extract. Models often show **higher TPR for men** and lower selection rates for women, reflecting (and potentially amplifying) the label distribution. This is a **documented disparity**, not a claim of fairness.
- **Race:** Group sizes are highly unbalanced (majority White). Metrics for smaller groups (e.g., Other / Amer-Indian-Eskimo) have **wide uncertainty**. Aggregate accuracy can look fine while TPR gaps remain material.

### What we do *not* claim

- Removing `sex`/`race` from features does **not** guarantee fairness (proxy leakage via education, occupation, hours, etc.).
- Equalized odds / demographic parity are **not** enforced here; they are reported for governance discussion.
- Suitability for automated credit, hiring, or benefits decisions is **out of scope**.

## Approved for demo deployment?

**Yes, as an educational CRISP-DM demo** with prediction and similar-record tools.

**No, as a production decision engine** without policy controls, threshold governance, continuous monitoring, and stakeholder sign-off on acceptable disparity levels.

## Next steps if promoting beyond demo

1. Cost-sensitive threshold selection with stakeholder sign-off.
2. Explicit fairness constraints or post-processing (equalized odds) if required by policy.
3. Drift monitors on feature and score distributions.
4. Human review workflow using the LSH similar-records tool as supporting context only.
