# 06 — Per-Condition Results (supplementary to 03_Confusion_Matrix_and_Metrics_Register.md)

Generated in Week 8 from the **actual evaluation workbooks** in `files-bundle-01.zip` (the bundle is not committed; paths are relative to the bundle root `files-bundle-01/`).

**Verification applied to every table below.**

- **Verified against actual workbook:** counts and rates read from the `Condition Summary` sheet, rows 2…n+1, columns A–M (Condition, TP, FN, TN, FP, Total, Positive/Negative Ground Truth, Accuracy, Sensitivity, Specificity, Precision, F1). Counts also match the `Confusion Matrix` sheet cell for cell.
- **Cross-checked against prediction records:** TP/FN/TN/FP were independently recomputed from the matching `predictions.jsonl` and the source reference workbook. The first 100 populated rows were joined by CaseID; for Feline Matrix 1 only, the three Normal/Abnormal columns were normalised. Every condition matches exactly.
- Every rate was recomputed from the counts and matches the stored value (tolerance 1e-9).

Rates are shown at 2 d.p. using round-half-up, matching the workbooks' `0.00%` display format; the workbooks store full precision. **undef.** = a zero denominator, left blank in the workbook and never counted as 0. Every condition row sums to 100 cases.

> Matrix 1 and Matrix 2 use different reference-label sources and are never combined. These are 100-case report-text classification pilots, not clinical validation.

## EVAL-11 — Feline Thorax · Matrix 1 — original Vetology labels (3 columns Normal/Abnormal normalised) · Week 7 shared batch (21 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_07/2nd application/feline_thorax/matrix_1/feline_thorax_matrix1_evaluation_workbook.xlsx` — sheet `Condition Summary`, A2:M22; total row 23 (`TOTAL`).
- Predictions: `files-bundle-01/outputs/week_07/2nd application/feline_thorax/predictions/predictions.jsonl`. Reference: `files-bundle-01/2_feline_thorax_raw_data_encoded.xlsx`. Model: gpt-4.1-mini. Prompt: V1.2.
- Conditions with zero reference positives: none.
- Undefined sensitivity: 0; undefined precision (no positive predictions): 10; undefined F1: 11.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pulmonary_nodules | 1 | 5 | 90 | 4 | 6 | 94 | 91.00% | 16.67% | 95.74% | 20.00% | 18.18% |
| esophagitis | 0 | 59 | 41 | 0 | 59 | 41 | 41.00% | 0.00% | 100.00% | undef. | undef. |
| pneumonia | 0 | 51 | 49 | 0 | 51 | 49 | 49.00% | 0.00% | 100.00% | undef. | undef. |
| bronchitis | 4 | 10 | 79 | 7 | 14 | 86 | 83.00% | 28.57% | 91.86% | 36.36% | 32.00% |
| interstitial | 3 | 16 | 75 | 6 | 19 | 81 | 78.00% | 15.79% | 92.59% | 33.33% | 21.43% |
| diseased_lungs | 10 | 23 | 58 | 9 | 33 | 67 | 68.00% | 30.30% | 86.57% | 52.63% | 38.46% |
| hypo_plastic_trachea | 0 | 12 | 88 | 0 | 12 | 88 | 88.00% | 0.00% | 100.00% | undef. | undef. |
| cardiomegaly | 3 | 1 | 88 | 8 | 4 | 96 | 91.00% | 75.00% | 91.67% | 27.27% | 40.00% |
| pleural_effusion | 3 | 25 | 72 | 0 | 28 | 72 | 75.00% | 10.71% | 100.00% | 100.00% | 19.35% |
| perihilar_infiltrate | 0 | 54 | 46 | 0 | 54 | 46 | 46.00% | 0.00% | 100.00% | undef. | undef. |
| rtm | 0 | 21 | 79 | 0 | 21 | 79 | 79.00% | 0.00% | 100.00% | undef. | undef. |
| focal_caudodorsal_lung | 0 | 38 | 61 | 1 | 38 | 62 | 61.00% | 0.00% | 98.39% | 0.00% | undef. |
| right_sided_cardiomegaly | 0 | 5 | 95 | 0 | 5 | 95 | 95.00% | 0.00% | 100.00% | undef. | undef. |
| focal_perihilar | 0 | 52 | 48 | 0 | 52 | 48 | 48.00% | 0.00% | 100.00% | undef. | undef. |
| left_sided_cardiomegaly | 0 | 5 | 95 | 0 | 5 | 95 | 95.00% | 0.00% | 100.00% | undef. | undef. |
| bronchiectasis | 0 | 26 | 74 | 0 | 26 | 74 | 74.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 2 | 3 | 94 | 1 | 5 | 95 | 96.00% | 40.00% | 98.95% | 66.67% | 50.00% |
| thoracic_lymphadenopathy | 1 | 45 | 54 | 0 | 46 | 54 | 55.00% | 2.17% | 100.00% | 100.00% | 4.26% |
| pulmonary_hypoinflation | 1 | 31 | 68 | 0 | 32 | 68 | 69.00% | 3.13% | 100.00% | 100.00% | 6.06% |
| pericardial_effusion | 0 | 2 | 98 | 0 | 2 | 98 | 98.00% | 0.00% | 100.00% | undef. | undef. |
| Fe_Alveolar | 1 | 21 | 77 | 1 | 22 | 78 | 78.00% | 4.55% | 98.72% | 50.00% | 8.33% |
| **TOTAL (micro)** | 29 | 505 | 1529 | 37 | 534 | 1566 | 74.19% | 5.43% | 97.64% | 43.94% | 9.67% |

## EVAL-12 — Feline Thorax · Matrix 2 — peer-reviewed Gold Standard · Week 7 shared batch (21 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_07/2nd application/feline_thorax/matrix_2/feline_thorax_matrix2_evaluation_workbook.xlsx` — sheet `Condition Summary`, A2:M22; total row 23 (`MICRO TOTAL`).
- Predictions: `files-bundle-01/outputs/week_07/2nd application/feline_thorax/predictions/predictions.jsonl`. Reference: `files-bundle-01/2_feline_thorax_gold_standard_score_draft.xlsx`. Model: gpt-4.1-mini. Prompt: V1.2.
- Conditions with zero reference positives: esophagitis, pneumonia, hypo_plastic_trachea, perihilar_infiltrate, rtm, right_sided_cardiomegaly, focal_perihilar, left_sided_cardiomegaly, bronchiectasis, pericardial_effusion.
- Undefined sensitivity: 10; undefined precision (no positive predictions): 10; undefined F1: 11.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pulmonary_nodules | 4 | 1 | 94 | 1 | 5 | 95 | 98.00% | 80.00% | 98.95% | 80.00% | 80.00% |
| esophagitis | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| pneumonia | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| bronchitis | 11 | 27 | 62 | 0 | 38 | 62 | 73.00% | 28.95% | 100.00% | 100.00% | 44.90% |
| interstitial | 6 | 0 | 91 | 3 | 6 | 94 | 97.00% | 100.00% | 96.81% | 66.67% | 80.00% |
| diseased_lungs | 18 | 28 | 53 | 1 | 46 | 54 | 71.00% | 39.13% | 98.15% | 94.74% | 55.38% |
| hypo_plastic_trachea | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| cardiomegaly | 9 | 1 | 88 | 2 | 10 | 90 | 97.00% | 90.00% | 97.78% | 81.82% | 85.71% |
| pleural_effusion | 3 | 0 | 97 | 0 | 3 | 97 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| perihilar_infiltrate | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| rtm | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| focal_caudodorsal_lung | 0 | 1 | 98 | 1 | 1 | 99 | 98.00% | 0.00% | 98.99% | 0.00% | undef. |
| right_sided_cardiomegaly | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| focal_perihilar | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| left_sided_cardiomegaly | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| bronchiectasis | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 3 | 0 | 97 | 0 | 3 | 97 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| thoracic_lymphadenopathy | 1 | 0 | 99 | 0 | 1 | 99 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| pulmonary_hypoinflation | 1 | 0 | 99 | 0 | 1 | 99 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| pericardial_effusion | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| Fe_Alveolar | 2 | 1 | 97 | 0 | 3 | 97 | 99.00% | 66.67% | 100.00% | 100.00% | 80.00% |
| **MICRO TOTAL (micro)** | 58 | 59 | 1975 | 8 | 117 | 1983 | 96.81% | 49.57% | 99.60% | 87.88% | 63.39% |

## EVAL-13 — Canine Abdomen · Matrix 1 — original Vetology labels · Week 7 shared batch (21 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_07/3rd application/canine_abdomen/matrix_1/canine_abdomen_matrix1_evaluation_workbook.xlsx` — sheet `Condition Summary`, A2:M11; total row 12 (`TOTAL`).
- Predictions: `files-bundle-01/outputs/week_07/3rd application/canine_abdomen/predictions/predictions.jsonl`. Reference: `files-bundle-01/3_canine_abdomen_raw_data_encoded.xlsx`. Model: gpt-4.1-mini. Prompt: V1.4.
- Conditions with zero reference positives: none.
- Undefined sensitivity: 0; undefined precision (no positive predictions): 0; undefined F1: 0.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gastritis | 6 | 23 | 68 | 3 | 29 | 71 | 74.00% | 20.69% | 95.77% | 66.67% | 31.58% |
| ascites | 3 | 16 | 80 | 1 | 19 | 81 | 83.00% | 15.79% | 98.77% | 75.00% | 26.09% |
| colitis | 3 | 22 | 70 | 5 | 25 | 75 | 73.00% | 12.00% | 93.33% | 37.50% | 18.18% |
| liver_mass | 2 | 11 | 87 | 0 | 13 | 87 | 89.00% | 15.38% | 100.00% | 100.00% | 26.67% |
| pancreatitis | 2 | 73 | 24 | 1 | 75 | 25 | 26.00% | 2.67% | 96.00% | 66.67% | 5.13% |
| microhepatia | 1 | 13 | 81 | 5 | 14 | 86 | 82.00% | 7.14% | 94.19% | 16.67% | 10.00% |
| small_intestinal_obstruction | 4 | 17 | 75 | 4 | 21 | 79 | 79.00% | 19.05% | 94.94% | 50.00% | 27.59% |
| splenic_mass | 1 | 17 | 80 | 2 | 18 | 82 | 81.00% | 5.56% | 97.56% | 33.33% | 9.52% |
| splenomegaly | 1 | 18 | 79 | 2 | 19 | 81 | 80.00% | 5.26% | 97.53% | 33.33% | 9.09% |
| hepatomegaly | 11 | 36 | 53 | 0 | 47 | 53 | 64.00% | 23.40% | 100.00% | 100.00% | 37.93% |
| **TOTAL (micro)** | 34 | 246 | 697 | 23 | 280 | 720 | 73.10% | 12.14% | 96.81% | 59.65% | 20.18% |

## EVAL-14 — Canine Abdomen · Matrix 2 — peer-reviewed Gold Standard · Week 7 shared batch (21 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_07/3rd application/canine_abdomen/matrix_2/canine_abdomen_matrix2_evaluation_workbook.xlsx` — sheet `Condition Summary`, A2:M11; total row 12 (`MICRO TOTAL`).
- Predictions: `files-bundle-01/outputs/week_07/3rd application/canine_abdomen/predictions/predictions.jsonl`. Reference: `files-bundle-01/3_canine_abdomen_gold_standard_score_draft.xlsx`. Model: gpt-4.1-mini. Prompt: V1.4.
- Conditions with zero reference positives: none.
- Undefined sensitivity: 0; undefined precision (no positive predictions): 0; undefined F1: 0.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gastritis | 9 | 7 | 84 | 0 | 16 | 84 | 93.00% | 56.25% | 100.00% | 100.00% | 72.00% |
| ascites | 4 | 1 | 95 | 0 | 5 | 95 | 99.00% | 80.00% | 100.00% | 100.00% | 88.89% |
| colitis | 8 | 16 | 76 | 0 | 24 | 76 | 84.00% | 33.33% | 100.00% | 100.00% | 50.00% |
| liver_mass | 2 | 0 | 98 | 0 | 2 | 98 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| pancreatitis | 2 | 2 | 95 | 1 | 4 | 96 | 97.00% | 50.00% | 98.96% | 66.67% | 57.14% |
| microhepatia | 6 | 0 | 94 | 0 | 6 | 94 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| small_intestinal_obstruction | 6 | 2 | 90 | 2 | 8 | 92 | 96.00% | 75.00% | 97.83% | 75.00% | 75.00% |
| splenic_mass | 3 | 0 | 97 | 0 | 3 | 97 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| splenomegaly | 3 | 0 | 97 | 0 | 3 | 97 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| hepatomegaly | 10 | 0 | 89 | 1 | 10 | 90 | 99.00% | 100.00% | 98.89% | 90.91% | 95.24% |
| **MICRO TOTAL (micro)** | 53 | 28 | 915 | 4 | 81 | 919 | 96.80% | 65.43% | 99.56% | 92.98% | 76.81% |

## EVAL-01 — Canine Thorax · Matrix 1 — original Vetology labels · Week 4 original application (delivered workbook A5)

- Workbook: `files-bundle-01/Week 4 1st Application (using canine thorax) Evaluation Workbook Confusion Matrix 1.xlsx` — sheet `Condition Summary`, A2:M21; total row 22 (`TOTAL`).
- Predictions: `files-bundle-01/outputs/week_04/matrix_1/predictions.jsonl`. Reference: `files-bundle-01/Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx`. Model: gpt-4.1-mini. Prompt: V1.3.
- Conditions with zero reference positives: none.
- Undefined sensitivity: 0; undefined precision (no positive predictions): 3; undefined F1: 3.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| perihilar_infiltrate | 1 | 56 | 42 | 1 | 57 | 43 | 43.00% | 1.75% | 97.67% | 50.00% | 3.39% |
| pneumonia | 7 | 40 | 52 | 1 | 47 | 53 | 59.00% | 14.89% | 98.11% | 87.50% | 25.45% |
| bronchitis | 15 | 48 | 33 | 4 | 63 | 37 | 48.00% | 23.81% | 89.19% | 78.95% | 36.59% |
| interstitial | 19 | 40 | 30 | 11 | 59 | 41 | 49.00% | 32.20% | 73.17% | 63.33% | 42.70% |
| diseased_lungs | 26 | 37 | 30 | 7 | 63 | 37 | 56.00% | 41.27% | 81.08% | 78.79% | 54.17% |
| hypo_plastic_trachea | 0 | 35 | 65 | 0 | 35 | 65 | 65.00% | 0.00% | 100.00% | undef. | undef. |
| cardiomegaly | 12 | 17 | 67 | 4 | 29 | 71 | 79.00% | 41.38% | 94.37% | 75.00% | 53.33% |
| pulmonary_nodules | 7 | 55 | 37 | 1 | 62 | 38 | 44.00% | 11.29% | 97.37% | 87.50% | 20.00% |
| pleural_effusion | 1 | 59 | 40 | 0 | 60 | 40 | 41.00% | 1.67% | 100.00% | 100.00% | 3.28% |
| rtm | 4 | 51 | 43 | 2 | 55 | 45 | 47.00% | 7.27% | 95.56% | 66.67% | 13.11% |
| focal_caudodorsal_lung | 5 | 42 | 53 | 0 | 47 | 53 | 58.00% | 10.64% | 100.00% | 100.00% | 19.23% |
| focal_perihilar | 0 | 58 | 42 | 0 | 58 | 42 | 42.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_hypoinflation | 10 | 62 | 27 | 1 | 72 | 28 | 37.00% | 13.89% | 96.43% | 90.91% | 24.10% |
| right_sided_cardiomegaly | 2 | 30 | 67 | 1 | 32 | 68 | 69.00% | 6.25% | 98.53% | 66.67% | 11.43% |
| pericardial_effusion | 1 | 23 | 76 | 0 | 24 | 76 | 77.00% | 4.17% | 100.00% | 100.00% | 8.00% |
| bronchiectasis | 0 | 67 | 33 | 0 | 67 | 33 | 33.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 2 | 50 | 48 | 0 | 52 | 48 | 50.00% | 3.85% | 100.00% | 100.00% | 7.41% |
| left_sided_cardiomegaly | 11 | 17 | 68 | 4 | 28 | 72 | 79.00% | 39.29% | 94.44% | 73.33% | 51.16% |
| thoracic_lymphadenopathy | 4 | 78 | 18 | 0 | 82 | 18 | 22.00% | 4.88% | 100.00% | 100.00% | 9.30% |
| esophagitis | 1 | 56 | 42 | 1 | 57 | 43 | 43.00% | 1.75% | 97.67% | 50.00% | 3.39% |
| **TOTAL (micro)** | 128 | 921 | 913 | 38 | 1049 | 951 | 52.05% | 12.20% | 96.00% | 77.11% | 21.07% |

## EVAL-02 — Canine Thorax · Matrix 2 — peer-reviewed Gold Standard · Week 4 original application (delivered workbook A6)

- Workbook: `files-bundle-01/Week 4 1st Application (using canine thorax) Evaluation Workbook Confusion Matrix 2.xlsx` — sheet `Condition Summary`, A2:M21; total row 22 (`MICRO TOTAL`).
- Predictions: `files-bundle-01/outputs/week_04/canine_thorax/predictions.jsonl`. Reference: `files-bundle-01/1_canine_thorax_gold_standard_score_draft.xlsx`. Model: gpt-4.1-mini. Prompt: V1.3.
- Conditions with zero reference positives: hypo_plastic_trachea, pericardial_effusion, bronchiectasis, esophagitis.
- Undefined sensitivity: 4; undefined precision (no positive predictions): 3; undefined F1: 6.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| perihilar_infiltrate | 0 | 2 | 96 | 2 | 2 | 98 | 96.00% | 0.00% | 97.96% | 0.00% | undef. |
| pneumonia | 6 | 0 | 92 | 2 | 6 | 94 | 98.00% | 100.00% | 97.87% | 75.00% | 85.71% |
| bronchitis | 9 | 6 | 75 | 10 | 15 | 85 | 84.00% | 60.00% | 88.24% | 47.37% | 52.94% |
| interstitial | 27 | 1 | 70 | 2 | 28 | 72 | 97.00% | 96.43% | 97.22% | 93.10% | 94.74% |
| diseased_lungs | 34 | 14 | 52 | 0 | 48 | 52 | 86.00% | 70.83% | 100.00% | 100.00% | 82.93% |
| hypo_plastic_trachea | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| cardiomegaly | 15 | 4 | 80 | 1 | 19 | 81 | 95.00% | 78.95% | 98.77% | 93.75% | 85.71% |
| pulmonary_nodules | 5 | 1 | 91 | 3 | 6 | 94 | 96.00% | 83.33% | 96.81% | 62.50% | 71.43% |
| pleural_effusion | 1 | 0 | 99 | 0 | 1 | 99 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| rtm | 2 | 0 | 94 | 4 | 2 | 98 | 96.00% | 100.00% | 95.92% | 33.33% | 50.00% |
| focal_caudodorsal_lung | 1 | 0 | 96 | 3 | 1 | 99 | 97.00% | 100.00% | 96.97% | 25.00% | 40.00% |
| focal_perihilar | 0 | 2 | 98 | 0 | 2 | 98 | 98.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_hypoinflation | 9 | 0 | 89 | 2 | 9 | 91 | 98.00% | 100.00% | 97.80% | 81.82% | 90.00% |
| right_sided_cardiomegaly | 1 | 0 | 97 | 2 | 1 | 99 | 98.00% | 100.00% | 97.98% | 33.33% | 50.00% |
| pericardial_effusion | 0 | 0 | 99 | 1 | 0 | 100 | 99.00% | undef. | 99.00% | 0.00% | undef. |
| bronchiectasis | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 1 | 0 | 98 | 1 | 1 | 99 | 99.00% | 100.00% | 98.99% | 50.00% | 66.67% |
| left_sided_cardiomegaly | 14 | 1 | 83 | 2 | 15 | 85 | 97.00% | 93.33% | 97.65% | 87.50% | 90.32% |
| thoracic_lymphadenopathy | 2 | 0 | 96 | 2 | 2 | 98 | 98.00% | 100.00% | 97.96% | 50.00% | 66.67% |
| esophagitis | 0 | 0 | 98 | 2 | 0 | 100 | 98.00% | undef. | 98.00% | 0.00% | undef. |
| **MICRO TOTAL (micro)** | 127 | 31 | 1803 | 39 | 158 | 1842 | 96.50% | 80.38% | 97.88% | 76.51% | 78.40% |

## EVAL-05 — Canine Thorax · Matrix 1 — original Vetology labels · Week 5 live run (12 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_05/matrix_1/matrix1_evaluation_workbook.xlsx` — sheet `Condition Summary`, A2:M21; total row 22 (`TOTAL`).
- Predictions: `files-bundle-01/outputs/week_05/matrix_1/predictions.jsonl`. Reference: `files-bundle-01/Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx`. Model: gpt-4.1-mini. Prompt: V1.3.
- Conditions with zero reference positives: none.
- Undefined sensitivity: 0; undefined precision (no positive predictions): 3; undefined F1: 3.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| perihilar_infiltrate | 1 | 56 | 42 | 1 | 57 | 43 | 43.00% | 1.75% | 97.67% | 50.00% | 3.39% |
| pneumonia | 7 | 40 | 52 | 1 | 47 | 53 | 59.00% | 14.89% | 98.11% | 87.50% | 25.45% |
| bronchitis | 15 | 48 | 33 | 4 | 63 | 37 | 48.00% | 23.81% | 89.19% | 78.95% | 36.59% |
| interstitial | 19 | 40 | 32 | 9 | 59 | 41 | 51.00% | 32.20% | 78.05% | 67.86% | 43.68% |
| diseased_lungs | 28 | 35 | 31 | 6 | 63 | 37 | 59.00% | 44.44% | 83.78% | 82.35% | 57.73% |
| hypo_plastic_trachea | 0 | 35 | 65 | 0 | 35 | 65 | 65.00% | 0.00% | 100.00% | undef. | undef. |
| cardiomegaly | 12 | 17 | 67 | 4 | 29 | 71 | 79.00% | 41.38% | 94.37% | 75.00% | 53.33% |
| pulmonary_nodules | 7 | 55 | 37 | 1 | 62 | 38 | 44.00% | 11.29% | 97.37% | 87.50% | 20.00% |
| pleural_effusion | 1 | 59 | 40 | 0 | 60 | 40 | 41.00% | 1.67% | 100.00% | 100.00% | 3.28% |
| rtm | 4 | 51 | 43 | 2 | 55 | 45 | 47.00% | 7.27% | 95.56% | 66.67% | 13.11% |
| focal_caudodorsal_lung | 3 | 44 | 53 | 0 | 47 | 53 | 56.00% | 6.38% | 100.00% | 100.00% | 12.00% |
| focal_perihilar | 0 | 58 | 42 | 0 | 58 | 42 | 42.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_hypoinflation | 10 | 62 | 27 | 1 | 72 | 28 | 37.00% | 13.89% | 96.43% | 90.91% | 24.10% |
| right_sided_cardiomegaly | 2 | 30 | 67 | 1 | 32 | 68 | 69.00% | 6.25% | 98.53% | 66.67% | 11.43% |
| pericardial_effusion | 1 | 23 | 76 | 0 | 24 | 76 | 77.00% | 4.17% | 100.00% | 100.00% | 8.00% |
| bronchiectasis | 0 | 67 | 33 | 0 | 67 | 33 | 33.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 2 | 50 | 48 | 0 | 52 | 48 | 50.00% | 3.85% | 100.00% | 100.00% | 7.41% |
| left_sided_cardiomegaly | 10 | 18 | 68 | 4 | 28 | 72 | 78.00% | 35.71% | 94.44% | 71.43% | 47.62% |
| thoracic_lymphadenopathy | 3 | 79 | 18 | 0 | 82 | 18 | 21.00% | 3.66% | 100.00% | 100.00% | 7.06% |
| esophagitis | 1 | 56 | 42 | 1 | 57 | 43 | 43.00% | 1.75% | 97.67% | 50.00% | 3.39% |
| **TOTAL (micro)** | 126 | 923 | 916 | 35 | 1049 | 951 | 52.10% | 12.01% | 96.32% | 78.26% | 20.83% |

## EVAL-06 — Canine Thorax · Matrix 2 — peer-reviewed Gold Standard · Week 5 live run (12 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_05/matrix_2/Evaluation Workbook v2.xlsx` — sheet `Condition Summary`, A2:M21; total row 22 (`MICRO TOTAL`).
- Predictions: `files-bundle-01/outputs/week_05/matrix_2/predictions.jsonl`. Reference: `files-bundle-01/1_canine_thorax_gold_standard_score_draft.xlsx`. Model: gpt-4.1-mini. Prompt: V1.3.
- Conditions with zero reference positives: hypo_plastic_trachea, pericardial_effusion, bronchiectasis, esophagitis.
- Undefined sensitivity: 4; undefined precision (no positive predictions): 3; undefined F1: 5.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| perihilar_infiltrate | 1 | 1 | 96 | 2 | 2 | 98 | 97.00% | 50.00% | 97.96% | 33.33% | 40.00% |
| pneumonia | 6 | 0 | 92 | 2 | 6 | 94 | 98.00% | 100.00% | 97.87% | 75.00% | 85.71% |
| bronchitis | 9 | 6 | 76 | 9 | 15 | 85 | 85.00% | 60.00% | 89.41% | 50.00% | 54.55% |
| interstitial | 28 | 0 | 70 | 2 | 28 | 72 | 98.00% | 100.00% | 97.22% | 93.33% | 96.55% |
| diseased_lungs | 33 | 15 | 52 | 0 | 48 | 52 | 85.00% | 68.75% | 100.00% | 100.00% | 81.48% |
| hypo_plastic_trachea | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| cardiomegaly | 14 | 5 | 80 | 1 | 19 | 81 | 94.00% | 73.68% | 98.77% | 93.33% | 82.35% |
| pulmonary_nodules | 5 | 1 | 91 | 3 | 6 | 94 | 96.00% | 83.33% | 96.81% | 62.50% | 71.43% |
| pleural_effusion | 1 | 0 | 99 | 0 | 1 | 99 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| rtm | 2 | 0 | 94 | 4 | 2 | 98 | 96.00% | 100.00% | 95.92% | 33.33% | 50.00% |
| focal_caudodorsal_lung | 1 | 0 | 97 | 2 | 1 | 99 | 98.00% | 100.00% | 97.98% | 33.33% | 50.00% |
| focal_perihilar | 0 | 2 | 98 | 0 | 2 | 98 | 98.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_hypoinflation | 9 | 0 | 89 | 2 | 9 | 91 | 98.00% | 100.00% | 97.80% | 81.82% | 90.00% |
| right_sided_cardiomegaly | 1 | 0 | 97 | 2 | 1 | 99 | 98.00% | 100.00% | 97.98% | 33.33% | 50.00% |
| pericardial_effusion | 0 | 0 | 99 | 1 | 0 | 100 | 99.00% | undef. | 99.00% | 0.00% | undef. |
| bronchiectasis | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 1 | 0 | 98 | 1 | 1 | 99 | 99.00% | 100.00% | 98.99% | 50.00% | 66.67% |
| left_sided_cardiomegaly | 13 | 2 | 83 | 2 | 15 | 85 | 96.00% | 86.67% | 97.65% | 86.67% | 86.67% |
| thoracic_lymphadenopathy | 2 | 0 | 97 | 1 | 2 | 98 | 99.00% | 100.00% | 98.98% | 66.67% | 80.00% |
| esophagitis | 0 | 0 | 98 | 2 | 0 | 100 | 98.00% | undef. | 98.00% | 0.00% | undef. |
| **MICRO TOTAL (micro)** | 126 | 32 | 1806 | 36 | 158 | 1842 | 96.60% | 79.75% | 98.05% | 77.78% | 78.75% |

## EVAL-07 — Canine Thorax · Matrix 1 — original Vetology labels · Week 7 Gemini run (20 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_1/matrix1_evaluation_workbook.xlsx` — sheet `Condition Summary`, A2:M21; total row 22 (`TOTAL`).
- Predictions: `files-bundle-01/outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_1/predictions.jsonl`. Reference: `files-bundle-01/Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx`. Model: gemini-3.8-flash. Prompt: V1.3.
- Conditions with zero reference positives: none.
- Undefined sensitivity: 0; undefined precision (no positive predictions): 4; undefined F1: 4.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| perihilar_infiltrate | 1 | 56 | 43 | 0 | 57 | 43 | 44.00% | 1.75% | 100.00% | 100.00% | 3.45% |
| pneumonia | 5 | 42 | 52 | 1 | 47 | 53 | 57.00% | 10.64% | 98.11% | 83.33% | 18.87% |
| bronchitis | 3 | 60 | 35 | 2 | 63 | 37 | 38.00% | 4.76% | 94.59% | 60.00% | 8.82% |
| interstitial | 18 | 41 | 31 | 10 | 59 | 41 | 49.00% | 30.51% | 75.61% | 64.29% | 41.38% |
| diseased_lungs | 20 | 43 | 34 | 3 | 63 | 37 | 54.00% | 31.75% | 91.89% | 86.96% | 46.51% |
| hypo_plastic_trachea | 0 | 35 | 65 | 0 | 35 | 65 | 65.00% | 0.00% | 100.00% | undef. | undef. |
| cardiomegaly | 6 | 23 | 69 | 2 | 29 | 71 | 75.00% | 20.69% | 97.18% | 75.00% | 32.43% |
| pulmonary_nodules | 7 | 55 | 37 | 1 | 62 | 38 | 44.00% | 11.29% | 97.37% | 87.50% | 20.00% |
| pleural_effusion | 2 | 58 | 40 | 0 | 60 | 40 | 42.00% | 3.33% | 100.00% | 100.00% | 6.45% |
| rtm | 4 | 51 | 43 | 2 | 55 | 45 | 47.00% | 7.27% | 95.56% | 66.67% | 13.11% |
| focal_caudodorsal_lung | 2 | 45 | 53 | 0 | 47 | 53 | 55.00% | 4.26% | 100.00% | 100.00% | 8.16% |
| focal_perihilar | 0 | 58 | 42 | 0 | 58 | 42 | 42.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_hypoinflation | 10 | 62 | 28 | 0 | 72 | 28 | 38.00% | 13.89% | 100.00% | 100.00% | 24.39% |
| right_sided_cardiomegaly | 2 | 30 | 67 | 1 | 32 | 68 | 69.00% | 6.25% | 98.53% | 66.67% | 11.43% |
| pericardial_effusion | 1 | 23 | 76 | 0 | 24 | 76 | 77.00% | 4.17% | 100.00% | 100.00% | 8.00% |
| bronchiectasis | 0 | 67 | 33 | 0 | 67 | 33 | 33.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 1 | 51 | 48 | 0 | 52 | 48 | 49.00% | 1.92% | 100.00% | 100.00% | 3.77% |
| left_sided_cardiomegaly | 12 | 16 | 67 | 5 | 28 | 72 | 79.00% | 42.86% | 93.06% | 70.59% | 53.33% |
| thoracic_lymphadenopathy | 2 | 80 | 18 | 0 | 82 | 18 | 20.00% | 2.44% | 100.00% | 100.00% | 4.76% |
| esophagitis | 0 | 57 | 43 | 0 | 57 | 43 | 43.00% | 0.00% | 100.00% | undef. | undef. |
| **TOTAL (micro)** | 96 | 953 | 924 | 27 | 1049 | 951 | 51.00% | 9.15% | 97.16% | 78.05% | 16.38% |

## EVAL-08 — Canine Thorax · Matrix 2 — peer-reviewed Gold Standard · Week 7 Gemini run (20 Nov 2026)

- Workbook: `files-bundle-01/outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_2/Evaluation Workbook v2.xlsx` — sheet `Condition Summary`, A2:M21; total row 22 (`MICRO TOTAL`).
- Predictions: `files-bundle-01/outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_2/predictions.jsonl`. Reference: `files-bundle-01/1_canine_thorax_gold_standard_score_draft.xlsx`. Model: gemini-3.8-flash. Prompt: V1.3.
- Conditions with zero reference positives: hypo_plastic_trachea, pericardial_effusion, bronchiectasis, esophagitis.
- Undefined sensitivity: 4; undefined precision (no positive predictions): 4; undefined F1: 5.

| Condition | TP | FN | TN | FP | Ref + | Ref − | Acc | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| perihilar_infiltrate | 1 | 1 | 98 | 0 | 2 | 98 | 99.00% | 50.00% | 100.00% | 100.00% | 66.67% |
| pneumonia | 6 | 0 | 94 | 0 | 6 | 94 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| bronchitis | 3 | 12 | 84 | 1 | 15 | 85 | 87.00% | 20.00% | 98.82% | 75.00% | 31.58% |
| interstitial | 26 | 2 | 70 | 2 | 28 | 72 | 96.00% | 92.86% | 97.22% | 92.86% | 92.86% |
| diseased_lungs | 22 | 26 | 52 | 0 | 48 | 52 | 74.00% | 45.83% | 100.00% | 100.00% | 62.86% |
| hypo_plastic_trachea | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| cardiomegaly | 9 | 10 | 80 | 1 | 19 | 81 | 89.00% | 47.37% | 98.77% | 90.00% | 62.07% |
| pulmonary_nodules | 5 | 1 | 91 | 3 | 6 | 94 | 96.00% | 83.33% | 96.81% | 62.50% | 71.43% |
| pleural_effusion | 1 | 0 | 98 | 1 | 1 | 99 | 99.00% | 100.00% | 98.99% | 50.00% | 66.67% |
| rtm | 1 | 1 | 94 | 4 | 2 | 98 | 95.00% | 50.00% | 95.92% | 20.00% | 28.57% |
| focal_caudodorsal_lung | 1 | 0 | 98 | 1 | 1 | 99 | 99.00% | 100.00% | 98.99% | 50.00% | 66.67% |
| focal_perihilar | 0 | 2 | 98 | 0 | 2 | 98 | 98.00% | 0.00% | 100.00% | undef. | undef. |
| pulmonary_hypoinflation | 8 | 1 | 89 | 2 | 9 | 91 | 97.00% | 88.89% | 97.80% | 80.00% | 84.21% |
| right_sided_cardiomegaly | 1 | 0 | 97 | 2 | 1 | 99 | 98.00% | 100.00% | 97.98% | 33.33% | 50.00% |
| pericardial_effusion | 0 | 0 | 99 | 1 | 0 | 100 | 99.00% | undef. | 99.00% | 0.00% | undef. |
| bronchiectasis | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| pulmonary_vessel_enlargement | 1 | 0 | 99 | 0 | 1 | 99 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| left_sided_cardiomegaly | 15 | 0 | 83 | 2 | 15 | 85 | 98.00% | 100.00% | 97.65% | 88.24% | 93.75% |
| thoracic_lymphadenopathy | 2 | 0 | 98 | 0 | 2 | 98 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| esophagitis | 0 | 0 | 100 | 0 | 0 | 100 | 100.00% | undef. | 100.00% | undef. | undef. |
| **MICRO TOTAL (micro)** | 102 | 56 | 1822 | 20 | 158 | 1842 | 96.20% | 64.56% | 98.91% | 83.61% | 72.86% |
