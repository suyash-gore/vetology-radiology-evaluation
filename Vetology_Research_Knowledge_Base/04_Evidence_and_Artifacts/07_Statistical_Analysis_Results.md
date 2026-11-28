# 07 — Statistical Analysis Results (Week 8)

Generated 2026-11-28 18:04:30 UTC by `analysis/week08_statistics.py` (seed 20261128, B = 10,000).
Plan: `../03_Consolidated_Knowledge_Base/08_Research_Design_and_Analysis_Plan.md` §6. Deviations: see plan §13.

**Inputs:** owner-supplied, confidential case-level files (not committed). SHA-256 values are listed at the end. Only aggregate statistics are reported here.

**Methods recap:**
- Report-level cluster bootstrap: report (case); all condition labels of a resampled report kept together.
- Intervals: percentile 95% over defined replicates; undefined-replicate count reported.
- Per-condition intervals: 95% Wilson score interval per condition (cases treated as independent).
- F1 = 2TP/(2TP+FP+FN); undefined only when denominator is 0 (plan section 6.2).
- The same resample indices are used for all evaluations, so paired contrasts on identical cases are paired.

**Interpretation:** the cases are the first 100 populated records per dataset, not a random sample. Intervals describe variability conditional on these cases, labels, prompts and runs, and imply no population representativeness or clinical validity. They do not include reference-label uncertainty, run-to-run model variation or model drift.

**Verification:** every evaluation's micro TP/FN/TN/FP was recomputed from predictions plus references and equals the registered counts. The script aborts otherwise.

## 1. Micro (pooled) metrics with 95% report-level bootstrap intervals

| Eval | Run | TP | FN | TN | FP | Accuracy | Sensitivity | Specificity | Precision | F1 |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| EVAL-01 CT Week 4 OpenAI M1 | RUN-02 | 128 | 921 | 913 | 38 | 52.05% (47.15–57.05%) | 12.20% (9.50–14.88%) | 96.00% (94.10–97.66%) | 77.11% (67.11–86.06%) | 21.07% (16.75–25.13%) |
| EVAL-02 CT Week 4 OpenAI M2 | RUN-01 | 127 | 31 | 1803 | 39 | 96.50% (95.55–97.40%) | 80.38% (73.24–86.67%) | 97.88% (97.12–98.57%) | 76.51% (70.15–82.39%) | 78.40% (72.84–82.97%) |
| EVAL-05 CT Week 5 OpenAI M1 | RUN-03 | 126 | 923 | 916 | 35 | 52.10% (47.20–57.15%) | 12.01% (9.28–14.67%) | 96.32% (94.48–97.88%) | 78.26% (68.45–87.15%) | 20.83% (16.46–24.88%) |
| EVAL-06 CT Week 5 OpenAI M2 | RUN-04 | 126 | 32 | 1806 | 36 | 96.60% (95.65–97.50%) | 79.75% (72.53–86.14%) | 98.05% (97.29–98.73%) | 77.78% (71.34–83.89%) | 78.75% (73.15–83.47%) |
| EVAL-07 CT Week 7 Gemini M1 | RUN-05 | 96 | 953 | 924 | 27 | 51.00% (45.90–56.30%) | 9.15% (7.06–11.30%) | 97.16% (95.61–98.47%) | 78.05% (67.29–87.62%) | 16.38% (12.86–19.85%) |
| EVAL-08 CT Week 7 Gemini M2 | RUN-06 | 102 | 56 | 1822 | 20 | 96.20% (95.15–97.20%) | 64.56% (56.73–72.44%) | 98.91% (98.43–99.35%) | 83.61% (76.86–89.57%) | 72.86% (66.19–78.91%) |
| EVAL-11 FT Week 7 OpenAI M1 | RUN-07 | 29 | 505 | 1529 | 37 | 74.19% (70.48–77.71%) | 5.43% (2.85–7.99%) | 97.64% (96.69–98.49%) | 43.94% (25.40–60.87%) | 9.67% (5.15–13.96%) |
| EVAL-12 FT Week 7 OpenAI M2 | RUN-07 | 58 | 59 | 1975 | 8 | 96.81% (95.95–97.62%) | 49.57% (37.27–61.16%) | 99.60% (99.29–99.85%) | 87.88% (78.66–95.59%) | 63.39% (51.66–72.63%) |
| EVAL-13 CA Week 7 OpenAI M1 | RUN-08 | 34 | 246 | 697 | 23 | 73.10% (69.60–76.40%) | 12.14% (8.41–16.05%) | 96.81% (95.28–98.15%) | 59.65% (45.76–73.33%) | 20.18% (14.46–25.77%) |
| EVAL-14 CA Week 7 OpenAI M2 | RUN-08 | 53 | 28 | 915 | 4 | 96.80% (95.70–97.90%) | 65.43% (54.55–75.61%) | 99.56% (99.12–99.89%) | 92.98% (86.49–98.31%) | 76.81% (68.42–83.93%) |

Undefined micro replicates: none in any evaluation or metric.

## 2. Macro averages (defined conditions only) with bootstrap intervals

The macro value is the mean of the **defined** condition values. The included/excluded counts refer to the point estimate. In bootstrap replicates the contributing set varies (min–median–max shown), so these intervals are conditional on definedness and approximate.

| Eval | Metric | Macro | Included / excluded | 95% CI | Contributing conditions in replicates (min / median / max) |
|---|---|---|---|---|---|
| EVAL-01 | sensitivity | 13.01% | 20 / 0 | 10.09–15.91% | 20 / 20 / 20 |
| EVAL-01 | specificity | 95.68% | 20 / 0 | 93.74–97.40% | 20 / 20 / 20 |
| EVAL-01 | precision | 80.51% | 17 / 3 | 69.13–89.80% | 11 / 16 / 17 |
| EVAL-01 | f1 | 19.30% | 20 / 0 | 15.41–22.58% | 20 / 20 / 20 |
| EVAL-02 | sensitivity | 80.18% | 16 / 4 | 72.06–92.15% | 9 / 14 / 16 |
| EVAL-02 | specificity | 97.86% | 20 / 0 | 97.09–98.55% | 20 / 20 / 20 |
| EVAL-02 | precision | 54.87% | 17 / 3 | 47.36–66.02% | 11 / 16 / 17 |
| EVAL-02 | f1 | 57.06% | 18 / 2 | 47.47–65.77% | 11 / 17 / 18 |
| EVAL-05 | sensitivity | 12.72% | 20 / 0 | 9.80–15.61% | 20 / 20 / 20 |
| EVAL-05 | specificity | 96.06% | 20 / 0 | 94.22–97.68% | 20 / 20 / 20 |
| EVAL-05 | precision | 80.87% | 17 / 3 | 69.29–90.28% | 10 / 16 / 17 |
| EVAL-05 | f1 | 18.88% | 20 / 0 | 14.98–22.20% | 20 / 20 / 20 |
| EVAL-06 | sensitivity | 82.65% | 16 / 4 | 73.22–91.31% | 9 / 14 / 16 |
| EVAL-06 | specificity | 98.02% | 20 / 0 | 97.26–98.71% | 20 / 20 / 20 |
| EVAL-06 | precision | 58.39% | 17 / 3 | 50.21–70.19% | 10 / 16 / 17 |
| EVAL-06 | f1 | 60.30% | 18 / 2 | 50.06–69.00% | 10 / 17 / 18 |
| EVAL-07 | sensitivity | 9.89% | 20 / 0 | 7.64–12.20% | 20 / 20 / 20 |
| EVAL-07 | specificity | 97.10% | 20 / 0 | 95.59–98.42% | 20 / 20 / 20 |
| EVAL-07 | precision | 85.06% | 16 / 4 | 72.97–92.14% | 9 / 15 / 16 |
| EVAL-07 | f1 | 15.24% | 20 / 0 | 11.95–18.18% | 20 / 20 / 20 |
| EVAL-08 | sensitivity | 73.64% | 16 / 4 | 61.27–82.75% | 9 / 14 / 16 |
| EVAL-08 | specificity | 98.90% | 20 / 0 | 98.40–99.34% | 20 / 20 / 20 |
| EVAL-08 | precision | 71.37% | 16 / 4 | 61.03–83.56% | 9 / 15 / 16 |
| EVAL-08 | f1 | 63.37% | 17 / 3 | 49.60–74.19% | 9 / 16 / 17 |
| EVAL-11 | sensitivity | 10.80% | 21 / 0 | 6.53–14.10% | 16 / 21 / 21 |
| EVAL-11 | specificity | 97.83% | 21 / 0 | 96.94–98.63% | 21 / 21 / 21 |
| EVAL-11 | precision | 53.30% | 11 / 10 | 32.88–68.50% | 6 / 10 / 11 |
| EVAL-11 | f1 | 11.34% | 21 / 0 | 5.82–15.22% | 17 / 21 / 21 |
| EVAL-12 | sensitivity | 73.16% | 11 / 10 | 61.40–85.34% | 5 / 10 / 11 |
| EVAL-12 | specificity | 99.56% | 21 / 0 | 99.16–99.85% | 21 / 21 / 21 |
| EVAL-12 | precision | 83.93% | 11 / 10 | 75.00–96.33% | 6 / 10 / 11 |
| EVAL-12 | f1 | 75.09% | 11 / 10 | 60.66–83.51% | 6 / 10 / 11 |
| EVAL-13 | sensitivity | 12.69% | 10 / 0 | 8.57–17.02% | 10 / 10 / 10 |
| EVAL-13 | specificity | 96.81% | 10 / 0 | 95.22–98.19% | 10 / 10 / 10 |
| EVAL-13 | precision | 57.92% | 10 / 0 | 41.99–72.54% | 7 / 10 / 10 |
| EVAL-13 | f1 | 20.18% | 10 / 0 | 13.69–25.33% | 10 / 10 / 10 |
| EVAL-14 | sensitivity | 79.46% | 10 / 0 | 70.49–86.75% | 7 / 10 / 10 |
| EVAL-14 | specificity | 99.57% | 10 / 0 | 99.12–99.90% | 10 / 10 / 10 |
| EVAL-14 | precision | 93.26% | 10 / 0 | 85.96–99.07% | 7 / 10 / 10 |
| EVAL-14 | f1 | 83.83% | 10 / 0 | 74.68–88.31% | 7 / 10 / 10 |

Macro F1 here uses the plan definition (2TP/(2TP+FP+FN)), so it can differ from the workbook macro F1, which excluded conditions where P or S was undefined. The workbook values remain the historical record.

## 3. Paired reference-workflow contrasts (identical predictions)

Matrix 2 minus Matrix 1, same prediction set, same resampled reports. This is the controlled reference-effect design (plan §5.2).

| Contrast | Accuracy | Sensitivity | Specificity | Precision | F1 |
|---|---|---|---|---|---|
| FT: M2 (EVAL-12) minus M1 (EVAL-11), identical predictions RUN-07 | +22.62 pp (+18.95 to +26.38) | +44.14 pp (+33.45 to +54.38) | +1.96 pp (+1.15 to +2.86) | +43.94 pp (+26.15 to +63.16) | +53.72 pp (+44.41 to +61.59) |
| CA: M2 (EVAL-14) minus M1 (EVAL-13), identical predictions RUN-08 | +23.70 pp (+20.20 to +27.30) | +53.29 pp (+43.82 to +62.76) | +2.76 pp (+1.43 to +4.27) | +33.33 pp (+17.74 to +49.02) | +56.63 pp (+48.57 to +64.80) |

## 4. Agreement between the two reference-label sets (Matrix 1 vs Matrix 2, same cases)

| Dataset | Pairs | Raw agreement | Cohen's κ (95% CI, 2,000 report-level resamples) | M1 Pos / M2 Neg | M1 Neg / M2 Pos |
|---|---:|---|---|---:|---:|
| CT | 2,000 | 51.55% | 0.069 (0.041–0.097) | 930 | 39 |
| FT | 2,100 | 72.71% | 0.031 (-0.008–0.067) | 495 | 78 |
| CA | 1,000 | 72.50% | 0.129 (0.077–0.183) | 237 | 38 |

Per-condition reference agreement is in the JSON file (`reference_label_agreement.*.per_condition`).

## 5. Canine Thorax model comparison (Week 5 gpt-4.1-mini vs Week 7 gemini-3.8-flash) — CT only

Agreement is model–model concordance, **not accuracy**. McNemar tests use exact binomial tests of discordant **correctness** per condition across 100 cases, with Holm adjustment within each matrix; they are exploratory. Single run per model, and the confounders in plan §5.2 apply.

### M1 (EVAL-05 vs EVAL-07)

- Prediction agreement: 1,940/2,000 (97.00%); Cohen's κ 0.773 (95% CI 0.716–0.822).
- Testable conditions (≥1 discordant correctness pair): 13 of 20.
- Paired differences (Gemini − OpenAI): accuracy -1.10 pp (-2.05 to -0.20); sensitivity -2.86 pp (-4.22 to -1.55); specificity +0.84 pp (-0.13 to +1.96); precision -0.21 pp (-5.95 to +5.87); f1 -4.44 pp (-6.53 to -2.38).

| Condition | OpenAI-only correct | Gemini-only correct | Exact McNemar p | Holm p | Agreement | κ |
|---|---:|---:|---|---|---|---|
| perihilar_infiltrate | 1 | 2 | 1.0000 | 1.0000 | 97.00% | -0.014 |
| pneumonia | 2 | 0 | 0.5000 | 1.0000 | 98.00% | 0.847 |
| bronchitis | 12 | 2 | 0.0129 | 0.1682 | 86.00% | 0.367 |
| interstitial | 3 | 1 | 0.6250 | 1.0000 | 96.00% | 0.901 |
| diseased_lungs | 11 | 6 | 0.3323 | 1.0000 | 83.00% | 0.589 |
| hypo_plastic_trachea | 0 | 0 | not testable | — | 100.00% | undef. |
| cardiomegaly | 6 | 2 | 0.2891 | 1.0000 | 92.00% | 0.627 |
| pulmonary_nodules | 0 | 0 | not testable | — | 100.00% | 1.000 |
| pleural_effusion | 0 | 1 | 1.0000 | 1.0000 | 99.00% | 0.662 |
| rtm | 0 | 0 | not testable | — | 100.00% | 1.000 |
| focal_caudodorsal_lung | 1 | 0 | 1.0000 | 1.0000 | 99.00% | 0.795 |
| focal_perihilar | 0 | 0 | not testable | — | 100.00% | undef. |
| pulmonary_hypoinflation | 1 | 2 | 1.0000 | 1.0000 | 97.00% | 0.840 |
| right_sided_cardiomegaly | 0 | 0 | not testable | — | 100.00% | 1.000 |
| pericardial_effusion | 0 | 0 | not testable | — | 100.00% | 1.000 |
| bronchiectasis | 0 | 0 | not testable | — | 100.00% | undef. |
| pulmonary_vessel_enlargement | 1 | 0 | 1.0000 | 1.0000 | 99.00% | 0.662 |
| left_sided_cardiomegaly | 1 | 2 | 1.0000 | 1.0000 | 97.00% | 0.886 |
| thoracic_lymphadenopathy | 1 | 0 | 1.0000 | 1.0000 | 99.00% | 0.795 |
| esophagitis | 1 | 1 | 1.0000 | 1.0000 | 98.00% | 0.000 |

### M2 (EVAL-06 vs EVAL-08)

- Prediction agreement: 1,944/2,000 (97.20%); Cohen's κ 0.788 (95% CI 0.735–0.839).
- Testable conditions (≥1 discordant correctness pair): 14 of 20.
- Paired differences (Gemini − OpenAI): accuracy -0.40 pp (-1.20 to +0.35); sensitivity -15.19 pp (-23.17 to -7.14); specificity +0.87 pp (+0.38 to +1.41); precision +5.83 pp (+0.85 to +10.52); f1 -5.89 pp (-11.79 to -0.20).

| Condition | OpenAI-only correct | Gemini-only correct | Exact McNemar p | Holm p | Agreement | κ |
|---|---:|---:|---|---|---|---|
| perihilar_infiltrate | 0 | 2 | 0.5000 | 1.0000 | 98.00% | 0.492 |
| pneumonia | 0 | 2 | 0.5000 | 1.0000 | 98.00% | 0.847 |
| bronchitis | 6 | 8 | 0.7905 | 1.0000 | 86.00% | 0.319 |
| interstitial | 2 | 0 | 0.5000 | 1.0000 | 98.00% | 0.951 |
| diseased_lungs | 14 | 3 | 0.0127 | 0.1782 | 83.00% | 0.580 |
| hypo_plastic_trachea | 0 | 0 | not testable | — | 100.00% | undef. |
| cardiomegaly | 6 | 1 | 0.1250 | 1.0000 | 93.00% | 0.682 |
| pulmonary_nodules | 0 | 0 | not testable | — | 100.00% | 1.000 |
| pleural_effusion | 1 | 0 | 1.0000 | 1.0000 | 99.00% | 0.662 |
| rtm | 1 | 0 | 1.0000 | 1.0000 | 99.00% | 0.904 |
| focal_caudodorsal_lung | 0 | 1 | 1.0000 | 1.0000 | 99.00% | 0.795 |
| focal_perihilar | 0 | 0 | not testable | — | 100.00% | undef. |
| pulmonary_hypoinflation | 2 | 1 | 1.0000 | 1.0000 | 97.00% | 0.840 |
| right_sided_cardiomegaly | 0 | 0 | not testable | — | 100.00% | 1.000 |
| pericardial_effusion | 0 | 0 | not testable | — | 100.00% | 1.000 |
| bronchiectasis | 0 | 0 | not testable | — | 100.00% | undef. |
| pulmonary_vessel_enlargement | 0 | 1 | 1.0000 | 1.0000 | 99.00% | 0.662 |
| left_sided_cardiomegaly | 0 | 2 | 0.5000 | 1.0000 | 98.00% | 0.926 |
| thoracic_lymphadenopathy | 0 | 1 | 1.0000 | 1.0000 | 99.00% | 0.795 |
| esophagitis | 0 | 2 | 0.5000 | 1.0000 | 98.00% | 0.000 |

## 6. Canine Thorax run-to-run consistency (temperature 0; separate executions on identical report text)

| Comparison | Differing pairs | Cases affected | Pos→Neg | Neg→Pos | κ |
|---|---:|---:|---:|---:|---|
| Week 4: RUN-02 (M1 batch) vs RUN-01 (M2 batch) | 8 / 2,000 | 6 | 4 | 4 | 0.974 |
| Week 5: RUN-03 (M1 batch) vs RUN-04 (M2 batch) | 11 / 2,000 | 8 | 5 | 6 | 0.963 |
| Week 7 Gemini: RUN-05 vs RUN-06 | 13 / 2,000 | 11 | 7 | 6 | 0.943 |
| Week 4 vs Week 5, M1 workflow: RUN-02 vs RUN-03 | 13 / 2,000 | 10 | 9 | 4 | 0.957 |
| Week 4 vs Week 5, M2 workflow: RUN-01 vs RUN-04 | 8 / 2,000 | 6 | 6 | 2 | 0.973 |

The Week 4 vs Week 5 rows compare different application versions on the same workflow inputs (a quasi-repeat, plan §5.2). Conditions affected are in the JSON file.

## 7. Decision D-A — compatibility check for CT common-batch rescoring

- CaseIDs identical and in the same order in the M1 and M2 workbooks: **True**
- Report text identical (Findings, Conclusions, Recommendations), all 100 cases: **True**
- Condition keys identical and in the same order: **True**
- RUN-03: 100 success records × 20 keys; RUN-04: 100 × 20
- **Compatible: True**

**Exploratory rescoring of both Week 5 batches.** This is not a selection: D-A remains an owner decision. These are new, additional analyses, and they do not replace EVAL-05 or EVAL-06.

| Rescoring | TP | FN | TN | FP | Accuracy | Sensitivity | Specificity | Precision | F1 |
|---|---:|---:|---:|---:|---|---|---|---|---|
| RUN-03 predictions scored against M2 (Gold Standard) | 125 | 33 | 1806 | 36 | 96.55% | 79.11% | 98.05% | 77.64% | 78.37% |
| RUN-04 predictions scored against M1 (Vetology) | 124 | 925 | 913 | 38 | 51.85% | 11.82% | 96.00% | 76.54% | 20.48% |

Paired M2 − M1 contrast on RUN-03 predictions (same prediction set; analogous to the FT/CA design): accuracy +44.45 pp (+39.45 to +49.35); sensitivity +67.10 pp (+60.62 to +73.30); specificity +1.73 pp (+0.14 to +3.48); precision -0.62 pp (-12.24 to +11.52); f1 +57.54 pp (+51.84 to +63.07).

## 8. Per-condition results with 95% Wilson intervals

Sens = TP/(TP+FN); Spec = TN/(TN+FP); Prec = TP/(TP+FP). "undef." = zero denominator. Bootstrap-undefined counts (out of B) show how often a metric was undefined in resamples.

### EVAL-01 — CT Week 4 OpenAI M1

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| perihilar_infiltrate | 57 / 43 | 2 | 1.75% (0.31–9.29%) | 97.67% (87.94–99.59%) | 50.00% (9.45–90.55%) | 3.39% | 0 / 1343 / 0 |
| pneumonia | 47 / 53 | 8 | 14.89% (7.41–27.69%) | 98.11% (90.06–99.67%) | 87.50% (52.91–97.76%) | 25.45% | 0 / 3 / 0 |
| bronchitis | 63 / 37 | 19 | 23.81% (14.99–35.64%) | 89.19% (75.29–95.71%) | 78.95% (56.67–91.49%) | 36.59% | 0 / 0 / 0 |
| interstitial | 59 / 41 | 30 | 32.20% (21.69–44.90%) | 73.17% (58.07–84.30%) | 63.33% (45.51–78.13%) | 42.70% | 0 / 0 / 0 |
| diseased_lungs | 63 / 37 | 33 | 41.27% (29.96–53.58%) | 81.08% (65.80–90.52%) | 78.79% (62.25–89.32%) | 54.17% | 0 / 0 / 0 |
| hypo_plastic_trachea | 35 / 65 | 0 | 0.00% (0.00–9.89%) | 100.00% (94.42–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| cardiomegaly | 29 / 71 | 16 | 41.38% (25.51–59.26%) | 94.37% (86.39–97.79%) | 75.00% (50.50–89.82%) | 53.33% | 0 / 0 / 0 |
| pulmonary_nodules | 62 / 38 | 8 | 11.29% (5.58–21.52%) | 97.37% (86.51–99.53%) | 87.50% (52.91–97.76%) | 20.00% | 0 / 1 / 0 |
| pleural_effusion | 60 / 40 | 1 | 1.67% (0.29–8.86%) | 100.00% (91.24–100.00%) | 100.00% (20.65–100.00%) | 3.28% | 0 / 3675 / 0 |
| rtm | 55 / 45 | 6 | 7.27% (2.86–17.26%) | 95.56% (85.17–98.77%) | 66.67% (30.00–90.32%) | 13.11% | 0 / 22 / 0 |
| focal_caudodorsal_lung | 47 / 53 | 5 | 10.64% (4.63–22.59%) | 100.00% (93.24–100.00%) | 100.00% (56.55–100.00%) | 19.23% | 0 / 68 / 0 |
| focal_perihilar | 58 / 42 | 0 | 0.00% (0.00–6.21%) | 100.00% (91.62–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_hypoinflation | 72 / 28 | 11 | 13.89% (7.72–23.71%) | 96.43% (82.29–99.37%) | 90.91% (62.26–98.38%) | 24.10% | 0 / 0 / 0 |
| right_sided_cardiomegaly | 32 / 68 | 3 | 6.25% (1.73–20.15%) | 98.53% (92.13–99.74%) | 66.67% (20.77–93.85%) | 11.43% | 0 / 498 / 0 |
| pericardial_effusion | 24 / 76 | 1 | 4.17% (0.74–20.24%) | 100.00% (95.19–100.00%) | 100.00% (20.65–100.00%) | 8.00% | 0 / 3598 / 0 |
| bronchiectasis | 67 / 33 | 0 | 0.00% (0.00–5.42%) | 100.00% (89.57–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_vessel_enlargement | 52 / 48 | 2 | 3.85% (1.06–12.98%) | 100.00% (92.59–100.00%) | 100.00% (34.24–100.00%) | 7.41% | 0 / 1364 / 0 |
| left_sided_cardiomegaly | 28 / 72 | 15 | 39.29% (23.57–57.59%) | 94.44% (86.57–97.82%) | 73.33% (48.05–89.10%) | 51.16% | 0 / 0 / 0 |
| thoracic_lymphadenopathy | 82 / 18 | 4 | 4.88% (1.91–11.88%) | 100.00% (82.41–100.00%) | 100.00% (51.01–100.00%) | 9.30% | 0 / 159 / 0 |
| esophagitis | 57 / 43 | 2 | 1.75% (0.31–9.29%) | 97.67% (87.94–99.59%) | 50.00% (9.45–90.55%) | 3.39% | 0 / 1344 / 0 |

### EVAL-02 — CT Week 4 OpenAI M2

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| perihilar_infiltrate | 2 / 98 | 2 | 0.00% (0.00–65.76%) | 97.96% (92.86–99.44%) | 0.00% (0.00–65.76%) | 0.00% | 1328 / 1343 / 182 |
| pneumonia | 6 / 94 | 8 | 100.00% (60.97–100.00%) | 97.87% (92.57–99.41%) | 75.00% (40.93–92.85%) | 85.71% | 16 / 3 / 3 |
| bronchitis | 15 / 85 | 19 | 60.00% (35.75–80.18%) | 88.24% (79.68–93.48%) | 47.37% (27.33–68.29%) | 52.94% | 0 / 0 / 0 |
| interstitial | 28 / 72 | 29 | 96.43% (82.29–99.37%) | 97.22% (90.43–99.23%) | 93.10% (78.04–98.09%) | 94.74% | 0 / 0 / 0 |
| diseased_lungs | 48 / 52 | 34 | 70.83% (56.82–81.76%) | 100.00% (93.12–100.00%) | 100.00% (89.85–100.00%) | 82.93% | 0 / 0 / 0 |
| hypo_plastic_trachea | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| cardiomegaly | 19 / 81 | 16 | 78.95% (56.67–91.49%) | 98.77% (93.33–99.78%) | 93.75% (71.67–98.89%) | 85.71% | 0 / 0 / 0 |
| pulmonary_nodules | 6 / 94 | 8 | 83.33% (43.65–96.99%) | 96.81% (91.03–98.91%) | 62.50% (30.57–86.32%) | 71.43% | 24 / 1 / 1 |
| pleural_effusion | 1 / 99 | 1 | 100.00% (20.65–100.00%) | 100.00% (96.26–100.00%) | 100.00% (20.65–100.00%) | 100.00% | 3675 / 3675 / 3675 |
| rtm | 2 / 98 | 6 | 100.00% (34.24–100.00%) | 95.92% (89.97–98.40%) | 33.33% (9.68–70.00%) | 50.00% | 1286 / 22 / 22 |
| focal_caudodorsal_lung | 1 / 99 | 4 | 100.00% (20.65–100.00%) | 96.97% (91.47–98.96%) | 25.00% (4.56–69.94%) | 40.00% | 3681 / 194 / 194 |
| focal_perihilar | 2 / 98 | 0 | 0.00% (0.00–65.76%) | 100.00% (96.23–100.00%) | undef. (—) | 0.00% | 1328 / 10000 / 1328 |
| pulmonary_hypoinflation | 9 / 91 | 11 | 100.00% (70.09–100.00%) | 97.80% (92.34–99.40%) | 81.82% (52.30–94.86%) | 90.00% | 0 / 0 / 0 |
| right_sided_cardiomegaly | 1 / 99 | 3 | 100.00% (20.65–100.00%) | 97.98% (92.93–99.44%) | 33.33% (6.15–79.23%) | 50.00% | 3677 / 498 / 498 |
| pericardial_effusion | 0 / 100 | 1 | undef. (—) | 99.00% (94.55–99.82%) | 0.00% (0.00–79.35%) | 0.00% | 10000 / 3598 / 3598 |
| bronchiectasis | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| pulmonary_vessel_enlargement | 1 / 99 | 2 | 100.00% (20.65–100.00%) | 98.99% (94.50–99.82%) | 50.00% (9.45–90.55%) | 66.67% | 3677 / 1364 / 1364 |
| left_sided_cardiomegaly | 15 / 85 | 16 | 93.33% (70.18–98.81%) | 97.65% (91.82–99.35%) | 87.50% (63.98–96.50%) | 90.32% | 0 / 0 / 0 |
| thoracic_lymphadenopathy | 2 / 98 | 4 | 100.00% (34.24–100.00%) | 97.96% (92.86–99.44%) | 50.00% (15.00–85.00%) | 66.67% | 1305 / 159 / 159 |
| esophagitis | 0 / 100 | 2 | undef. (—) | 98.00% (93.00–99.45%) | 0.00% (0.00–65.76%) | 0.00% | 10000 / 1344 / 1344 |

### EVAL-05 — CT Week 5 OpenAI M1

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| perihilar_infiltrate | 57 / 43 | 2 | 1.75% (0.31–9.29%) | 97.67% (87.94–99.59%) | 50.00% (9.45–90.55%) | 3.39% | 0 / 1343 / 0 |
| pneumonia | 47 / 53 | 8 | 14.89% (7.41–27.69%) | 98.11% (90.06–99.67%) | 87.50% (52.91–97.76%) | 25.45% | 0 / 3 / 0 |
| bronchitis | 63 / 37 | 19 | 23.81% (14.99–35.64%) | 89.19% (75.29–95.71%) | 78.95% (56.67–91.49%) | 36.59% | 0 / 0 / 0 |
| interstitial | 59 / 41 | 28 | 32.20% (21.69–44.90%) | 78.05% (63.30–88.00%) | 67.86% (49.34–82.07%) | 43.68% | 0 / 0 / 0 |
| diseased_lungs | 63 / 37 | 34 | 44.44% (32.85–56.68%) | 83.78% (68.86–92.35%) | 82.35% (66.49–91.65%) | 57.73% | 0 / 0 / 0 |
| hypo_plastic_trachea | 35 / 65 | 0 | 0.00% (0.00–9.89%) | 100.00% (94.42–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| cardiomegaly | 29 / 71 | 16 | 41.38% (25.51–59.26%) | 94.37% (86.39–97.79%) | 75.00% (50.50–89.82%) | 53.33% | 0 / 0 / 0 |
| pulmonary_nodules | 62 / 38 | 8 | 11.29% (5.58–21.52%) | 97.37% (86.51–99.53%) | 87.50% (52.91–97.76%) | 20.00% | 0 / 1 / 0 |
| pleural_effusion | 60 / 40 | 1 | 1.67% (0.29–8.86%) | 100.00% (91.24–100.00%) | 100.00% (20.65–100.00%) | 3.28% | 0 / 3675 / 0 |
| rtm | 55 / 45 | 6 | 7.27% (2.86–17.26%) | 95.56% (85.17–98.77%) | 66.67% (30.00–90.32%) | 13.11% | 0 / 22 / 0 |
| focal_caudodorsal_lung | 47 / 53 | 3 | 6.38% (2.19–17.16%) | 100.00% (93.24–100.00%) | 100.00% (43.85–100.00%) | 12.00% | 0 / 457 / 0 |
| focal_perihilar | 58 / 42 | 0 | 0.00% (0.00–6.21%) | 100.00% (91.62–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_hypoinflation | 72 / 28 | 11 | 13.89% (7.72–23.71%) | 96.43% (82.29–99.37%) | 90.91% (62.26–98.38%) | 24.10% | 0 / 0 / 0 |
| right_sided_cardiomegaly | 32 / 68 | 3 | 6.25% (1.73–20.15%) | 98.53% (92.13–99.74%) | 66.67% (20.77–93.85%) | 11.43% | 0 / 498 / 0 |
| pericardial_effusion | 24 / 76 | 1 | 4.17% (0.74–20.24%) | 100.00% (95.19–100.00%) | 100.00% (20.65–100.00%) | 8.00% | 0 / 3598 / 0 |
| bronchiectasis | 67 / 33 | 0 | 0.00% (0.00–5.42%) | 100.00% (89.57–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_vessel_enlargement | 52 / 48 | 2 | 3.85% (1.06–12.98%) | 100.00% (92.59–100.00%) | 100.00% (34.24–100.00%) | 7.41% | 0 / 1364 / 0 |
| left_sided_cardiomegaly | 28 / 72 | 14 | 35.71% (20.71–54.17%) | 94.44% (86.57–97.82%) | 71.43% (45.35–88.28%) | 47.62% | 0 / 0 / 0 |
| thoracic_lymphadenopathy | 82 / 18 | 3 | 3.66% (1.25–10.21%) | 100.00% (82.41–100.00%) | 100.00% (43.85–100.00%) | 7.06% | 0 / 453 / 0 |
| esophagitis | 57 / 43 | 2 | 1.75% (0.31–9.29%) | 97.67% (87.94–99.59%) | 50.00% (9.45–90.55%) | 3.39% | 0 / 1344 / 0 |

### EVAL-06 — CT Week 5 OpenAI M2

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| perihilar_infiltrate | 2 / 98 | 3 | 50.00% (9.45–90.55%) | 97.96% (92.86–99.44%) | 33.33% (6.15–79.23%) | 40.00% | 1328 / 512 / 182 |
| pneumonia | 6 / 94 | 8 | 100.00% (60.97–100.00%) | 97.87% (92.57–99.41%) | 75.00% (40.93–92.85%) | 85.71% | 16 / 3 / 3 |
| bronchitis | 15 / 85 | 18 | 60.00% (35.75–80.18%) | 89.41% (81.09–94.33%) | 50.00% (29.03–70.97%) | 54.55% | 0 / 0 / 0 |
| interstitial | 28 / 72 | 30 | 100.00% (87.94–100.00%) | 97.22% (90.43–99.23%) | 93.33% (78.68–98.15%) | 96.55% | 0 / 0 / 0 |
| diseased_lungs | 48 / 52 | 33 | 68.75% (54.67–80.05%) | 100.00% (93.12–100.00%) | 100.00% (89.57–100.00%) | 81.48% | 0 / 0 / 0 |
| hypo_plastic_trachea | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| cardiomegaly | 19 / 81 | 15 | 73.68% (51.21–88.19%) | 98.77% (93.33–99.78%) | 93.33% (70.18–98.81%) | 82.35% | 0 / 0 / 0 |
| pulmonary_nodules | 6 / 94 | 8 | 83.33% (43.65–96.99%) | 96.81% (91.03–98.91%) | 62.50% (30.57–86.32%) | 71.43% | 24 / 1 / 1 |
| pleural_effusion | 1 / 99 | 1 | 100.00% (20.65–100.00%) | 100.00% (96.26–100.00%) | 100.00% (20.65–100.00%) | 100.00% | 3675 / 3675 / 3675 |
| rtm | 2 / 98 | 6 | 100.00% (34.24–100.00%) | 95.92% (89.97–98.40%) | 33.33% (9.68–70.00%) | 50.00% | 1286 / 22 / 22 |
| focal_caudodorsal_lung | 1 / 99 | 3 | 100.00% (20.65–100.00%) | 97.98% (92.93–99.44%) | 33.33% (6.15–79.23%) | 50.00% | 3681 / 522 / 522 |
| focal_perihilar | 2 / 98 | 0 | 0.00% (0.00–65.76%) | 100.00% (96.23–100.00%) | undef. (—) | 0.00% | 1328 / 10000 / 1328 |
| pulmonary_hypoinflation | 9 / 91 | 11 | 100.00% (70.09–100.00%) | 97.80% (92.34–99.40%) | 81.82% (52.30–94.86%) | 90.00% | 0 / 0 / 0 |
| right_sided_cardiomegaly | 1 / 99 | 3 | 100.00% (20.65–100.00%) | 97.98% (92.93–99.44%) | 33.33% (6.15–79.23%) | 50.00% | 3677 / 498 / 498 |
| pericardial_effusion | 0 / 100 | 1 | undef. (—) | 99.00% (94.55–99.82%) | 0.00% (0.00–79.35%) | 0.00% | 10000 / 3598 / 3598 |
| bronchiectasis | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| pulmonary_vessel_enlargement | 1 / 99 | 2 | 100.00% (20.65–100.00%) | 98.99% (94.50–99.82%) | 50.00% (9.45–90.55%) | 66.67% | 3677 / 1364 / 1364 |
| left_sided_cardiomegaly | 15 / 85 | 15 | 86.67% (62.12–96.26%) | 97.65% (91.82–99.35%) | 86.67% (62.12–96.26%) | 86.67% | 0 / 0 / 0 |
| thoracic_lymphadenopathy | 2 / 98 | 3 | 100.00% (34.24–100.00%) | 98.98% (94.44–99.82%) | 66.67% (20.77–93.85%) | 80.00% | 1305 / 453 / 453 |
| esophagitis | 0 / 100 | 2 | undef. (—) | 98.00% (93.00–99.45%) | 0.00% (0.00–65.76%) | 0.00% | 10000 / 1344 / 1344 |

### EVAL-07 — CT Week 7 Gemini M1

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| perihilar_infiltrate | 57 / 43 | 1 | 1.75% (0.31–9.29%) | 100.00% (91.80–100.00%) | 100.00% (20.65–100.00%) | 3.45% | 0 / 3645 / 0 |
| pneumonia | 47 / 53 | 6 | 10.64% (4.63–22.59%) | 98.11% (90.06–99.67%) | 83.33% (43.65–96.99%) | 18.87% | 0 / 16 / 0 |
| bronchitis | 63 / 37 | 5 | 4.76% (1.63–13.09%) | 94.59% (82.30–98.50%) | 60.00% (23.07–88.24%) | 8.82% | 0 / 54 / 0 |
| interstitial | 59 / 41 | 28 | 30.51% (20.25–43.15%) | 75.61% (60.66–86.17%) | 64.29% (45.83–79.29%) | 41.38% | 0 / 0 / 0 |
| diseased_lungs | 63 / 37 | 23 | 31.75% (21.59–44.00%) | 91.89% (78.70–97.20%) | 86.96% (67.87–95.46%) | 46.51% | 0 / 0 / 0 |
| hypo_plastic_trachea | 35 / 65 | 0 | 0.00% (0.00–9.89%) | 100.00% (94.42–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| cardiomegaly | 29 / 71 | 8 | 20.69% (9.85–38.39%) | 97.18% (90.30–99.22%) | 75.00% (40.93–92.85%) | 32.43% | 0 / 2 / 0 |
| pulmonary_nodules | 62 / 38 | 8 | 11.29% (5.58–21.52%) | 97.37% (86.51–99.53%) | 87.50% (52.91–97.76%) | 20.00% | 0 / 1 / 0 |
| pleural_effusion | 60 / 40 | 2 | 3.33% (0.92–11.36%) | 100.00% (91.24–100.00%) | 100.00% (34.24–100.00%) | 6.45% | 0 / 1344 / 0 |
| rtm | 55 / 45 | 6 | 7.27% (2.86–17.26%) | 95.56% (85.17–98.77%) | 66.67% (30.00–90.32%) | 13.11% | 0 / 22 / 0 |
| focal_caudodorsal_lung | 47 / 53 | 2 | 4.26% (1.17–14.25%) | 100.00% (93.24–100.00%) | 100.00% (34.24–100.00%) | 8.16% | 0 / 1325 / 0 |
| focal_perihilar | 58 / 42 | 0 | 0.00% (0.00–6.21%) | 100.00% (91.62–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_hypoinflation | 72 / 28 | 10 | 13.89% (7.72–23.71%) | 100.00% (87.94–100.00%) | 100.00% (72.25–100.00%) | 24.39% | 0 / 1 / 0 |
| right_sided_cardiomegaly | 32 / 68 | 3 | 6.25% (1.73–20.15%) | 98.53% (92.13–99.74%) | 66.67% (20.77–93.85%) | 11.43% | 0 / 498 / 0 |
| pericardial_effusion | 24 / 76 | 1 | 4.17% (0.74–20.24%) | 100.00% (95.19–100.00%) | 100.00% (20.65–100.00%) | 8.00% | 0 / 3598 / 0 |
| bronchiectasis | 67 / 33 | 0 | 0.00% (0.00–5.42%) | 100.00% (89.57–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_vessel_enlargement | 52 / 48 | 1 | 1.92% (0.34–10.12%) | 100.00% (92.59–100.00%) | 100.00% (20.65–100.00%) | 3.77% | 0 / 3677 / 0 |
| left_sided_cardiomegaly | 28 / 72 | 17 | 42.86% (26.51–60.93%) | 93.06% (84.75–97.00%) | 70.59% (46.87–86.72%) | 53.33% | 0 / 0 / 0 |
| thoracic_lymphadenopathy | 82 / 18 | 2 | 2.44% (0.67–8.46%) | 100.00% (82.41–100.00%) | 100.00% (34.24–100.00%) | 4.76% | 0 / 1305 / 0 |
| esophagitis | 57 / 43 | 0 | 0.00% (0.00–6.31%) | 100.00% (91.80–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |

### EVAL-08 — CT Week 7 Gemini M2

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| perihilar_infiltrate | 2 / 98 | 1 | 50.00% (9.45–90.55%) | 100.00% (96.23–100.00%) | 100.00% (20.65–100.00%) | 66.67% | 1328 / 3645 / 1328 |
| pneumonia | 6 / 94 | 6 | 100.00% (60.97–100.00%) | 100.00% (96.07–100.00%) | 100.00% (60.97–100.00%) | 100.00% | 16 / 16 / 16 |
| bronchitis | 15 / 85 | 4 | 20.00% (7.05–45.19%) | 98.82% (93.63–99.79%) | 75.00% (30.06–95.44%) | 31.58% | 0 / 181 / 0 |
| interstitial | 28 / 72 | 28 | 92.86% (77.35–98.02%) | 97.22% (90.43–99.23%) | 92.86% (77.35–98.02%) | 92.86% | 0 / 0 / 0 |
| diseased_lungs | 48 / 52 | 22 | 45.83% (32.58–59.71%) | 100.00% (93.12–100.00%) | 100.00% (85.13–100.00%) | 62.86% | 0 / 0 / 0 |
| hypo_plastic_trachea | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| cardiomegaly | 19 / 81 | 10 | 47.37% (27.33–68.29%) | 98.77% (93.33–99.78%) | 90.00% (59.59–98.21%) | 62.07% | 0 / 1 / 0 |
| pulmonary_nodules | 6 / 94 | 8 | 83.33% (43.65–96.99%) | 96.81% (91.03–98.91%) | 62.50% (30.57–86.32%) | 71.43% | 24 / 1 / 1 |
| pleural_effusion | 1 / 99 | 2 | 100.00% (20.65–100.00%) | 98.99% (94.50–99.82%) | 50.00% (9.45–90.55%) | 66.67% | 3675 / 1344 / 1344 |
| rtm | 2 / 98 | 5 | 50.00% (9.45–90.55%) | 95.92% (89.97–98.40%) | 20.00% (3.62–62.45%) | 28.57% | 1286 / 62 / 22 |
| focal_caudodorsal_lung | 1 / 99 | 2 | 100.00% (20.65–100.00%) | 98.99% (94.50–99.82%) | 50.00% (9.45–90.55%) | 66.67% | 3681 / 1325 / 1325 |
| focal_perihilar | 2 / 98 | 0 | 0.00% (0.00–65.76%) | 100.00% (96.23–100.00%) | undef. (—) | 0.00% | 1328 / 10000 / 1328 |
| pulmonary_hypoinflation | 9 / 91 | 10 | 88.89% (56.50–98.01%) | 97.80% (92.34–99.40%) | 80.00% (49.02–94.33%) | 84.21% | 0 / 1 / 0 |
| right_sided_cardiomegaly | 1 / 99 | 3 | 100.00% (20.65–100.00%) | 97.98% (92.93–99.44%) | 33.33% (6.15–79.23%) | 50.00% | 3677 / 498 / 498 |
| pericardial_effusion | 0 / 100 | 1 | undef. (—) | 99.00% (94.55–99.82%) | 0.00% (0.00–79.35%) | 0.00% | 10000 / 3598 / 3598 |
| bronchiectasis | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| pulmonary_vessel_enlargement | 1 / 99 | 1 | 100.00% (20.65–100.00%) | 100.00% (96.26–100.00%) | 100.00% (20.65–100.00%) | 100.00% | 3677 / 3677 / 3677 |
| left_sided_cardiomegaly | 15 / 85 | 17 | 100.00% (79.61–100.00%) | 97.65% (91.82–99.35%) | 88.24% (65.66–96.71%) | 93.75% | 0 / 0 / 0 |
| thoracic_lymphadenopathy | 2 / 98 | 2 | 100.00% (34.24–100.00%) | 100.00% (96.23–100.00%) | 100.00% (34.24–100.00%) | 100.00% | 1305 / 1305 / 1305 |
| esophagitis | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |

### EVAL-11 — FT Week 7 OpenAI M1

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| pulmonary_nodules | 6 / 94 | 5 | 16.67% (3.01–56.35%) | 95.74% (89.56–98.33%) | 20.00% (3.62–62.45%) | 18.18% | 17 / 61 / 0 |
| esophagitis | 59 / 41 | 0 | 0.00% (0.00–6.11%) | 100.00% (91.43–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pneumonia | 51 / 49 | 0 | 0.00% (0.00–7.00%) | 100.00% (92.73–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| bronchitis | 14 / 86 | 11 | 28.57% (11.72–54.65%) | 91.86% (84.14–96.00%) | 36.36% (15.17–64.62%) | 32.00% | 0 / 0 / 0 |
| interstitial | 19 / 81 | 9 | 15.79% (5.52–37.57%) | 92.59% (84.77–96.56%) | 33.33% (12.06–64.58%) | 21.43% | 0 / 1 / 0 |
| diseased_lungs | 33 / 67 | 19 | 30.30% (17.38–47.34%) | 86.57% (76.40–92.77%) | 52.63% (31.71–72.67%) | 38.46% | 0 / 0 / 0 |
| hypo_plastic_trachea | 12 / 88 | 0 | 0.00% (0.00–24.25%) | 100.00% (95.82–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| cardiomegaly | 4 / 96 | 11 | 75.00% (30.06–95.44%) | 91.67% (84.41–95.72%) | 27.27% (9.75–56.56%) | 40.00% | 160 / 0 / 0 |
| pleural_effusion | 28 / 72 | 3 | 10.71% (3.71–27.20%) | 100.00% (94.93–100.00%) | 100.00% (43.85–100.00%) | 19.35% | 0 / 493 / 0 |
| perihilar_infiltrate | 54 / 46 | 0 | 0.00% (0.00–6.64%) | 100.00% (92.29–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| rtm | 21 / 79 | 0 | 0.00% (0.00–15.46%) | 100.00% (95.36–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| focal_caudodorsal_lung | 38 / 62 | 1 | 0.00% (0.00–9.18%) | 98.39% (91.41–99.71%) | 0.00% (0.00–79.35%) | 0.00% | 0 / 3586 / 0 |
| right_sided_cardiomegaly | 5 / 95 | 0 | 0.00% (0.00–43.45%) | 100.00% (96.11–100.00%) | undef. (—) | 0.00% | 61 / 10000 / 61 |
| focal_perihilar | 52 / 48 | 0 | 0.00% (0.00–6.88%) | 100.00% (92.59–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| left_sided_cardiomegaly | 5 / 95 | 0 | 0.00% (0.00–43.45%) | 100.00% (96.11–100.00%) | undef. (—) | 0.00% | 53 / 10000 / 53 |
| bronchiectasis | 26 / 74 | 0 | 0.00% (0.00–12.87%) | 100.00% (95.06–100.00%) | undef. (—) | 0.00% | 0 / 10000 / 0 |
| pulmonary_vessel_enlargement | 5 / 95 | 3 | 40.00% (11.76–76.93%) | 98.95% (94.28–99.81%) | 66.67% (20.77–93.85%) | 50.00% | 53 / 494 / 24 |
| thoracic_lymphadenopathy | 46 / 54 | 1 | 2.17% (0.38–11.34%) | 100.00% (93.36–100.00%) | 100.00% (20.65–100.00%) | 4.26% | 0 / 3577 / 0 |
| pulmonary_hypoinflation | 32 / 68 | 1 | 3.12% (0.55–15.74%) | 100.00% (94.65–100.00%) | 100.00% (20.65–100.00%) | 6.06% | 0 / 3566 / 0 |
| pericardial_effusion | 2 / 98 | 0 | 0.00% (0.00–65.76%) | 100.00% (96.23–100.00%) | undef. (—) | 0.00% | 1340 / 10000 / 1340 |
| Fe_Alveolar | 22 / 78 | 2 | 4.55% (0.81–21.80%) | 98.72% (93.09–99.77%) | 50.00% (9.45–90.55%) | 8.33% | 0 / 1332 / 0 |

### EVAL-12 — FT Week 7 OpenAI M2

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| pulmonary_nodules | 5 / 95 | 5 | 80.00% (37.55–96.38%) | 98.95% (94.28–99.81%) | 80.00% (37.55–96.38%) | 80.00% | 56 / 61 / 18 |
| esophagitis | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| pneumonia | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| bronchitis | 38 / 62 | 11 | 28.95% (17.00–44.76%) | 100.00% (94.17–100.00%) | 100.00% (74.12–100.00%) | 44.90% | 0 / 0 / 0 |
| interstitial | 6 / 94 | 9 | 100.00% (60.97–100.00%) | 96.81% (91.03–98.91%) | 66.67% (35.42–87.94%) | 80.00% | 18 / 1 / 1 |
| diseased_lungs | 46 / 54 | 19 | 39.13% (26.39–53.54%) | 98.15% (90.23–99.67%) | 94.74% (75.36–99.06%) | 55.38% | 0 / 0 / 0 |
| hypo_plastic_trachea | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| cardiomegaly | 10 / 90 | 11 | 90.00% (59.59–98.21%) | 97.78% (92.26–99.39%) | 81.82% (52.30–94.86%) | 85.71% | 0 / 0 / 0 |
| pleural_effusion | 3 / 97 | 3 | 100.00% (43.85–100.00%) | 100.00% (96.19–100.00%) | 100.00% (43.85–100.00%) | 100.00% | 493 / 493 / 493 |
| perihilar_infiltrate | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| rtm | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| focal_caudodorsal_lung | 1 / 99 | 1 | 0.00% (0.00–79.35%) | 98.99% (94.50–99.82%) | 0.00% (0.00–79.35%) | 0.00% | 3672 / 3586 / 1285 |
| right_sided_cardiomegaly | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| focal_perihilar | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| left_sided_cardiomegaly | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| bronchiectasis | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| pulmonary_vessel_enlargement | 3 / 97 | 3 | 100.00% (43.85–100.00%) | 100.00% (96.19–100.00%) | 100.00% (43.85–100.00%) | 100.00% | 494 / 494 / 494 |
| thoracic_lymphadenopathy | 1 / 99 | 1 | 100.00% (20.65–100.00%) | 100.00% (96.26–100.00%) | 100.00% (20.65–100.00%) | 100.00% | 3577 / 3577 / 3577 |
| pulmonary_hypoinflation | 1 / 99 | 1 | 100.00% (20.65–100.00%) | 100.00% (96.26–100.00%) | 100.00% (20.65–100.00%) | 100.00% | 3566 / 3566 / 3566 |
| pericardial_effusion | 0 / 100 | 0 | undef. (—) | 100.00% (96.30–100.00%) | undef. (—) | undef. | 10000 / 10000 / 10000 |
| Fe_Alveolar | 3 / 97 | 2 | 66.67% (20.77–93.85%) | 100.00% (96.19–100.00%) | 100.00% (34.24–100.00%) | 80.00% | 458 / 1332 / 458 |

### EVAL-13 — CA Week 7 OpenAI M1

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| gastritis | 29 / 71 | 9 | 20.69% (9.85–38.39%) | 95.77% (88.30–98.55%) | 66.67% (35.42–87.94%) | 31.58% | 0 / 0 / 0 |
| ascites | 19 / 81 | 4 | 15.79% (5.52–37.57%) | 98.77% (93.33–99.78%) | 75.00% (30.06–95.44%) | 26.09% | 0 / 175 / 0 |
| colitis | 25 / 75 | 8 | 12.00% (4.17–29.96%) | 93.33% (85.32–97.12%) | 37.50% (13.68–69.43%) | 18.18% | 0 / 2 / 0 |
| liver_mass | 13 / 87 | 2 | 15.38% (4.33–42.23%) | 100.00% (95.77–100.00%) | 100.00% (34.24–100.00%) | 26.67% | 0 / 1319 / 0 |
| pancreatitis | 75 / 25 | 3 | 2.67% (0.73–9.21%) | 96.00% (80.46–99.29%) | 66.67% (20.77–93.85%) | 5.13% | 0 / 472 / 0 |
| microhepatia | 14 / 86 | 6 | 7.14% (1.27–31.47%) | 94.19% (87.10–97.49%) | 16.67% (3.01–56.35%) | 10.00% | 0 / 24 / 0 |
| small_intestinal_obstruction | 21 / 79 | 8 | 19.05% (7.67–40.00%) | 94.94% (87.69–98.01%) | 50.00% (21.52–78.48%) | 27.59% | 0 / 1 / 0 |
| splenic_mass | 18 / 82 | 3 | 5.56% (0.99–25.76%) | 97.56% (91.54–99.33%) | 33.33% (6.15–79.23%) | 9.52% | 0 / 466 / 0 |
| splenomegaly | 19 / 81 | 3 | 5.26% (0.94–24.64%) | 97.53% (91.44–99.32%) | 33.33% (6.15–79.23%) | 9.09% | 0 / 467 / 0 |
| hepatomegaly | 47 / 53 | 11 | 23.40% (13.60–37.22%) | 100.00% (93.24–100.00%) | 100.00% (74.12–100.00%) | 37.93% | 0 / 0 / 0 |

### EVAL-14 — CA Week 7 OpenAI M2

| Condition | Ref + / − | Pred + | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 | Undefined replicates (sens / prec / F1) |
|---|---|---:|---|---|---|---|---|
| gastritis | 16 / 84 | 9 | 56.25% (33.18–76.90%) | 100.00% (95.63–100.00%) | 100.00% (70.09–100.00%) | 72.00% | 0 / 0 / 0 |
| ascites | 5 / 95 | 4 | 80.00% (37.55–96.38%) | 100.00% (96.11–100.00%) | 100.00% (51.01–100.00%) | 88.89% | 51 / 175 / 51 |
| colitis | 24 / 76 | 8 | 33.33% (17.97–53.29%) | 100.00% (95.19–100.00%) | 100.00% (67.56–100.00%) | 50.00% | 0 / 2 / 0 |
| liver_mass | 2 / 98 | 2 | 100.00% (34.24–100.00%) | 100.00% (96.23–100.00%) | 100.00% (34.24–100.00%) | 100.00% | 1319 / 1319 / 1319 |
| pancreatitis | 4 / 96 | 3 | 50.00% (15.00–85.00%) | 98.96% (94.33–99.82%) | 66.67% (20.77–93.85%) | 57.14% | 166 / 472 / 58 |
| microhepatia | 6 / 94 | 6 | 100.00% (60.97–100.00%) | 100.00% (96.07–100.00%) | 100.00% (60.97–100.00%) | 100.00% | 24 / 24 / 24 |
| small_intestinal_obstruction | 8 / 92 | 8 | 75.00% (40.93–92.85%) | 97.83% (92.42–99.40%) | 75.00% (40.93–92.85%) | 75.00% | 6 / 1 / 0 |
| splenic_mass | 3 / 97 | 3 | 100.00% (43.85–100.00%) | 100.00% (96.19–100.00%) | 100.00% (43.85–100.00%) | 100.00% | 466 / 466 / 466 |
| splenomegaly | 3 / 97 | 3 | 100.00% (43.85–100.00%) | 100.00% (96.19–100.00%) | 100.00% (43.85–100.00%) | 100.00% | 467 / 467 / 467 |
| hepatomegaly | 10 / 90 | 11 | 100.00% (72.25–100.00%) | 98.89% (93.97–99.80%) | 90.91% (62.26–98.38%) | 95.24% | 0 / 0 / 0 |

## 9. Input file hashes (SHA-256)

| File (relative to bundle root) | SHA-256 |
|---|---|
| `Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx` | `3f1a17b7046b2e1ff7e7d857e24b2f421f56392040a624b90836818b1176ef25` |
| `outputs/week_04/matrix_1/predictions.jsonl` | `78814024fade03cc1e0a673166efca8cfe473a6977d44f632b20d3583052c8c1` |
| `1_canine_thorax_gold_standard_score_draft.xlsx` | `d1fab50ee938f0608d7487f87e6650a28846cc5253dd6f170dce3fa990896fa4` |
| `outputs/week_04/canine_thorax/predictions.jsonl` | `70fe93918f2e941fec32fe065c17841ce325faa6fa40daafbf17b6f3ae092f70` |
| `outputs/week_05/matrix_1/predictions.jsonl` | `c50d9d9799f8bab1ef16caa007cb6bda39bb91bf6f156d684e3e2700e97c781d` |
| `outputs/week_05/matrix_2/predictions.jsonl` | `5b14a3ad77a3dec3d35490695a07dea1cbccd8c7cc1b338841c0fc0491de0038` |
| `outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_1/predictions.jsonl` | `7ebf010b673990ea47d09331f3bfe0cfdd20cf7f13c62324eae8e76fa5335e81` |
| `outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_2/predictions.jsonl` | `5d0a160b31584bde3da01832a5b93ca678e8bbd35659b8fc51aee1b335cf6603` |
| `2_feline_thorax_raw_data_encoded.xlsx` | `ef8fcc979132b59d26f37ecae04c2331ad97b37247d123e72556a655a3815516` |
| `outputs/week_07/2nd application/feline_thorax/predictions/predictions.jsonl` | `c103885357a3d22e6d4215c91238f5f5b3bd3c3b09b2c9733871de0274bf8df1` |
| `2_feline_thorax_gold_standard_score_draft.xlsx` | `c01a6e4b67fb629929f873340bbf8626f57e50e975660a62a264a77614d55136` |
| `3_canine_abdomen_raw_data_encoded.xlsx` | `583e7523abb30794cdabe745820a27c896ff0d8ddab5803c54511b8b747a5efe` |
| `outputs/week_07/3rd application/canine_abdomen/predictions/predictions.jsonl` | `61e151c4cf0548df0483561e6a9a5e44ccbcb5cf4b1c244f475d2fff80e69f6e` |
| `3_canine_abdomen_gold_standard_score_draft.xlsx` | `95e053a48e9a8bf15cbbf794c12bb026f499029ade5824dfdee161ce8d2bd054` |
