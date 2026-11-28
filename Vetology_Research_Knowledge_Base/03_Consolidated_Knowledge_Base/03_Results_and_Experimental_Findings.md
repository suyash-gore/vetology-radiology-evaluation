# 03 — Results and Experimental Findings

Every numerical result is listed separately by **dataset → reference track → model → run**. The evaluation IDs (EVAL-xx) and run IDs (RUN-xx) match `../04_Evidence_and_Artifacts/02_Experimental_Run_Register.md` and `03_Confusion_Matrix_and_Metrics_Register.md`. Per-condition tables for every evaluation are in `../04_Evidence_and_Artifacts/06_Per_Condition_Results.md`.

> **Week 8 reconciliation (supersedes the earlier "unverified" status).** The owner supplied `files-bundle-01.zip` with the actual evaluation workbooks, prediction records, manifests and reference workbooks. For **all ten reference-based evaluations** (EVAL-01, 02, 05, 06, 07, 08, 11, 12, 13, 14):
> 1. Aggregate and condition-level counts and rates were read from the workbook cells.
> 2. TP+FN+TN+FP was checked against cases × conditions.
> 3. Every rate was recomputed independently from the counts.
> 4. Every confusion count was independently recomputed from the matching `predictions.jsonl` and the source reference workbook.
>
> **Everything matched exactly. No aggregate figure in the earlier knowledge base changed.** The only change is evidence status: values move from *Recorded / unverified* to **Verified against actual workbook** and **Cross-checked against prediction records**. The bundle itself is not committed; workbook paths are given relative to the bundle root `files-bundle-01/`.
>
> All results are 100-case pilots that classify **written radiology reports**. They are not image interpretation, clinical diagnosis or clinical validation. Matrix 1 (original Vetology labels) and Matrix 2 (peer-reviewed Gold Standard, agreed after discussion) are never pooled. High specificity with low sensitivity is not strong overall diagnostic performance.

## 1. Canine Thorax (20 conditions; 2,000 case–condition pairs per matrix)

Reference prevalence (Verified, workbook `Positive/Negative Ground Truth` columns): Matrix 1 has 1,049 positive and 951 negative labels. Matrix 2 has 158 positive and 1,842 negative.

### 1.1 Aggregate (micro) results

| Eval ID | Week / run | Ref. | Model | TP | FN | TN | FP | Acc. | Sens. | Spec. | Prec. | F1 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-01 | Week 4 delivered workbook (RUN-02, 7 Nov) | M1 | gpt-4.1-mini | 128 | 921 | 913 | 38 | 52.05% | 12.20% | 96.00% | 77.11% | 21.07% | **Verified + cross-checked** |
| EVAL-02 | Week 4 delivered workbook (RUN-01, 3 Nov) | M2 | gpt-4.1-mini | 127 | 31 | 1,803 | 39 | 96.50% | 80.38% | 97.88% | 76.51% | **78.40%** (workbook display; Week 4 report gave 78.39%, see §1.2) | **Verified + cross-checked** |
| EVAL-03 / 04 | Week 5 replay of Week 4 predictions (parity) | M1 / M2 | (Week 4 predictions) | as EVAL-01 / 02 | | | | | | | | | Observed (prior), KB_10; consistent with EVAL-01/02 |
| EVAL-05 | Week 5 live (RUN-03, 12 Nov) | M1 | gpt-4.1-mini | 126 | 923 | 916 | 35 | 52.10% | 12.01% | 96.32% | 78.26% | 20.83% | **Verified + cross-checked** |
| EVAL-06 | Week 5 live (RUN-04, 12 Nov) | M2 | gpt-4.1-mini | 126 | 32 | 1,806 | 36 | 96.60% | 79.75% | 98.05% | 77.78% | 78.75% | **Verified + cross-checked** |
| EVAL-07 | Week 7 Gemini (RUN-05, 20 Nov) | M1 | gemini-3.8-flash | 96 | 953 | 924 | 27 | 51.00% | 9.15% | 97.16% | 78.05% | 16.38% | **Verified + cross-checked + manifest** |
| EVAL-08 | Week 7 Gemini (RUN-06, 20 Nov) | M2 | gemini-3.8-flash | 102 | 56 | 1,822 | 20 | 96.20% | 64.56% | 98.91% | 83.61% | 72.86% | **Verified + cross-checked + manifest** |

Matrix 1 macro averages (Verified; Overall Summary B15:B19):

| Eval | Accuracy | Sensitivity | Specificity | Precision | F1 |
|---|---|---|---|---|---|
| EVAL-01 | 52.05% | 13.01% | 95.68% | 80.51% | 22.71% |
| EVAL-05 | 52.10% | 12.72% | 96.06% | 80.87% | 22.21% |
| EVAL-07 | 51.00% | 9.89% | 97.10% | 85.06% | 19.06% |

Matrix 2 workbooks compute no macro averages. The Week 4 Matrix 2 workbook also shows a Balanced Accuracy of 89.13% (Overall Summary B8). This is not part of the later methodology.

The bundle also holds a second Week 4 Matrix 1 workbook, `outputs/week_04/matrix_1/matrix1_evaluation_workbook.xlsx` (EVAL-01b, generated 06:02:57 UTC on 7 Nov). It was built from the same predictions about 17 minutes after the delivered A5 workbook (05:46:24 UTC). **All counts and metrics are identical to EVAL-01.** Only presentation and log text differ, consistent with KB_10's finding that the delivered A5 differs from the committed evaluator in text and formatting. It is not a separate experiment.

### 1.2 Week 4 Matrix 2 F1 rounding (C-02, now resolved)

- The workbook stores F1 = 0.7839506172839507 (`Week 4 … Confusion Matrix 2.xlsx`, Overall Summary B7, format `0.00%`), which displays as **78.40%**.
- The Week 4 technical report (`files-bundle-01/Week_4_Original_Application_Technical_Report.docx`, table entry "F1-score (derived) 78.39%") recomputed F1 from the counts and reported a truncated value.
- **Verified value: 78.40% (78.3951% unrounded).** The historical report value of 78.39% is preserved as a report-side rounding difference, not a different result.

### 1.3 Canine Thorax: other findings

| Finding | Value | Status |
|---|---|---|
| Run-to-run variation between the Week 4 Matrix 1 (A3) and Matrix 2 (A4) prediction files, run separately on identical report text | 8 of 2,000 pairs differ (6 cases); 166 positive predictions in each | **Cross-checked against prediction records** (W8) |
| Same comparison, Week 5 live runs (Matrix 1 vs Matrix 2 batches) | 11 of 2,000 pairs differ (8 cases); 161 vs 162 positive predictions | **New (W8), cross-checked** |
| Same comparison, Week 7 Gemini runs | 13 of 2,000 pairs differ (11 cases); 123 vs 122 positive predictions | **New (W8), cross-checked** |
| Week 4 Matrix 2 batch | 99 first-attempt completions, 1 case needed 2 attempts | Verified (workbook Overall Summary; prediction `attempts` field) |
| Week 5 Matrix 1 `errors.jsonl` | 100 failure records, all HTTP 401 (expired API key) from an aborted attempt at 09:54–09:55 UTC, superseded by the successful batch at 09:57–10:01 UTC; 0 final failures | **Verified (W8)**; earlier docs said only "superseded" |
| Week 7 Gemini Matrix 2 `errors.jsonl` | 3 failure records for CaseID 1 (2 × HTTP 503 UNAVAILABLE, 1 × HTTP 504 DEADLINE_EXCEEDED), matching the three failed trial runs in the manifest; superseded | **Verified (W8)** |
| Week 4 Matrix 1 / 2 mismatches | 959 (921 FN + 38 FP) / 70 (31 FN + 39 FP) | Verified (counts); screening and adjudication status Recorded only |
| Week 4 Matrix 1 FN text screening (254 pairs; 705 unscreened) | — | Recorded (KB_05); not veterinary adjudication |

### 1.4 Model-to-model agreement (Canine Thorax; NOT accuracy)

Week 7 Gemini vs Week 5 OpenAI predictions. **Reference labels are not used.** Agreement says nothing about correctness.

| ID | Inputs | Agreement | Disagreements (cases) | OpenAI / Gemini positive predictions | Status |
|---|---|---|---|---|---|
| AGR-01 | Matrix 1 workflow | 1,940 / 2,000 = 97.00% | 60 (37 cases) | 161 / 123 | **Verified** (`matrix1_openai_vs_gemini_comparison.xlsx`, Model Agreement row 22; Execution Log B31) + **cross-checked** from prediction files |
| AGR-02 | Matrix 2 workflow | 1,944 / 2,000 = 97.20% | 56 (33 cases) | 162 / 122 | **Verified** (`matrix2_…comparison.xlsx`, Model Agreement row 22) + **cross-checked** |

The comparison workbooks also hold *reference-based* counts for the same pairs. These are kept separate from agreement and are identical to EVAL-05/07 and EVAL-06/08:

| Matrix | Both correct | Only OpenAI correct | Only Gemini correct | Both wrong |
|---|---|---|---|---|
| M1 | 1,001 | 41 | 19 | 939 |
| M2 | 1,900 | 32 | 24 | 44 |

(Overall Comparison B22:B25 for M1 and B17:B20 for M2.) The comparison Execution Logs list prediction-file SHA-256 values that equal the bundle files and record no API requests.

### 1.5 Interpretations in the sources (not verified conclusions)

- Matrix 1 vs Matrix 2 differences reflect **different reference sets and prevalence**, not a model change.
- Week 4 vs Week 5 live differences come from separate live runs and do not isolate a Claude Code effect.
- On Canine Thorax, Gemini had higher specificity and precision and lower sensitivity than GPT-4.1 mini. This is a single run per model with no significance test.

## 2. Feline Thorax (21 conditions; 2,100 pairs per matrix)

Batch RUN-07 (manifest Verified): 100/100 succeeded; gpt-4.1-mini; temperature 0.0; prompt V1.2. One shared prediction set is scored against both references.

| Eval ID | Ref. | TP | FN | TN | FP | Acc. | Sens. | Spec. | Prec. | F1 | Macro Sens / Spec / Prec / F1 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-11 | M1 Vetology (3 columns normalised) | 29 | 505 | 1,529 | 37 | 74.19% | 5.43% | 97.64% | 43.94% | 9.67% | 10.80% / 97.83% / 53.30% / 23.81% | **Verified + cross-checked + manifest** |
| EVAL-12 | M2 Gold Standard | 58 | 59 | 1,975 | 8 | 96.81% | 49.57% | 99.60% | 87.88% | 63.39% | — | **Verified + cross-checked + manifest** |

- These values are identical to the preliminary KB_02 values, so **C-01 is resolved**: the evaluations were run and the workbooks exist (as gitignored outputs on the developer's machine).
- Matrix 2: **10 of 21 conditions have zero Gold Standard positives** (esophagitis, pneumonia, hypo_plastic_trachea, perihilar_infiltrate, rtm, right_sided_cardiomegaly, focal_perihilar, left_sided_cardiomegaly, bronchiectasis, pericardial_effusion), so sensitivity is undefined for them.
- In both matrices the model made no positive predictions for 10 conditions (precision undefined), and F1 is undefined for 11.
- Matrix 1: TP = 0 (sensitivity 0%) for 11 of 21 conditions, including esophagitis (59 reference positives), perihilar_infiltrate (54) and focal_perihilar (52). See 06 for the full tables.
- Reference prevalence per condition matches KB_07 Table 26 exactly (Verified).

## 3. Canine Abdomen (10 conditions; 1,000 pairs per matrix)

Batch RUN-08 (manifest Verified): 100/100 succeeded; gpt-4.1-mini; temperature 0.0; prompt V1.4; one shared prediction set.

| Eval ID | Ref. | TP | FN | TN | FP | Acc. | Sens. | Spec. | Prec. | F1 | Macro Sens / Spec / Prec / F1 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-13 | M1 Vetology | 34 | 246 | 697 | 23 | 73.10% | 12.14% | 96.81% | 59.65% | 20.18% | 12.69% / 96.81% / 57.92% / 20.18% | **Verified + cross-checked + manifest** |
| EVAL-14 | M2 Gold Standard | 53 | 28 | 915 | 4 | 96.80% | 65.43% | 99.56% | 92.98% | 76.81% | — | **Verified + cross-checked + manifest** |

- Identical to the preliminary KB_02 values (C-01 resolved).
- The per-condition positive counts, sensitivity and F1 previously reported in KB_02 Table 12 match the workbook in all 10 conditions × 6 values (**Verified**). Per-condition TP/FN/TN/FP and specificity, which were missing before, are now recorded in 06.
- No Abdomen condition has zero reference positives in either matrix. Several Matrix 2 conditions have 2–4 positives (liver_mass 2, splenic_mass 3, splenomegaly 3, pancreatitis 4), so their 100% sensitivity values are unstable.
- Matrix 1 pancreatitis: 75 reference positives, 2 TP (sensitivity 2.67%).
- The hedged-language heuristic (KB_07 §8.5) remains Observed (prior), indicative only.

## 4. Cross-dataset observations (require validation)

| Observation | Status |
|---|---|
| In all three datasets the Matrix 1 Vetology labels contain far more positives than the Gold Standard (CT 1,049 vs 158; FT 534 vs 117; CA 280 vs 81) | **Verified** (workbooks and source workbooks) |
| Sensitivity is much higher against Matrix 2 than Matrix 1 in every dataset; specificity ≥ 96% everywhere. This reflects the reference set, not model improvement | Verified counts; interpretation |
| High accuracy partly reflects negative-dominant references; report sensitivity, precision and F1 alongside accuracy | Interpretation |
| Cross-application comparison is confounded by different prompt uncertainty policies | Observed (prior), KB_07 §7.2 |
| Run-to-run variation at temperature 0: 8, 11 and 13 of 2,000 pairs between separate CT batches on identical report text | Cross-checked (W8) |
| No confidence intervals, significance tests, inter-rater reliability or formal independent adjudication exist | Missing |

## 5. Not results

- Week 3 V1.0/V1.1 manual prompt reviews (consistency only).
- Test-suite pass counts (software quality only).
- The offline fake-classifier pipeline run (KB_07 §8.6).
- Model agreement (AGR-01/02) is not accuracy.
- A completed batch (manifest) on its own is not proof that its evaluation was done. The FT/CA evaluations are now proven by the workbooks themselves.
