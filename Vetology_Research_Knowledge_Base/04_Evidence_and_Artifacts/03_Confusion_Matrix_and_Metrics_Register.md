# 03 — Confusion Matrix and Metrics Register

One record per distinct evaluation. Datasets, reference tracks, models, prompts and runs are **never combined**:
- **Matrix 1** = original Vetology reference labels.
- **Matrix 2** = Gold Standard reference labels, peer-reviewed and agreed upon after discussion (owner clarification).

Agreement records (AGR) are kept separate from reference-based evaluations. **Per-condition tables for every evaluation are in `06_Per_Condition_Results.md`.**

> **Week 8 reconciliation status.** Every record below was checked against the actual workbook from `files-bundle-01.zip`. Paths are relative to the bundle root `files-bundle-01/`; inventory IDs EV-Bxx; the bundle is not committed. For each workbook:
> 1. Aggregate and condition counts and rates were read.
> 2. TP+FN+TN+FP was checked against cases × conditions (every condition row = 100).
> 3. Every rate was recomputed from the counts (all match, tolerance 1e-9).
> 4. The `Condition Summary` and `Confusion Matrix` sheets were compared (identical counts).
> 5. Every count was **independently recomputed from `predictions.jsonl` and the source reference workbook** (exact match).
>
> **Rounding convention:** workbooks store full-precision ratios with number format `0.00%`, i.e. round half-up to 2 d.p. Undefined ratios are blank cells, never 0.
>
> **Status key:** VW = Verified against actual workbook; XP = Cross-checked against prediction records; MF = Supported by manifest; DOC = Documented but not independently verified.

## Cell-reference conventions

| Layout | Used by | Aggregate cells |
|---|---|---|
| Matrix 1 (A5) | EVAL-01, 01b, 05, 07, 11, 13 | `Overall Summary` B6:B9 = TP, FN, TN, FP; B10:B14 = micro Acc, Sens, Spec, Prec, F1; B15:B19 = macro. `Condition Summary` TOTAL row = n+2 |
| Matrix 2 (A6), Week 4 | EVAL-02 | `Overall Summary` B3:B7 = Acc, Sens, Spec, Prec, F1; B8 = Balanced Accuracy; B11:B14 = TP, FN, TN, FP. `Condition Summary` MICRO TOTAL row 22 |
| Matrix 2 (A6), Weeks 5 and 7 | EVAL-06, 08, 12, 14 | `Overall Summary` B3:B7 = rates; B10:B13 = TP, FN, TN, FP (no Balanced Accuracy row). `Condition Summary` MICRO TOTAL row = n+2 |

## Canine Thorax: 100 cases × 20 conditions (N = 2,000 per matrix)

| ID | Experiment | Ref. | Model / prompt | Run | TP | FN | TN | FP | Acc | Sens | Spec | Prec | F1 | Workbook (EV-B) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-01 | Week 4 original (delivered A5) | M1 (+1,049 / −951) | gpt-4.1-mini / V1.3 | RUN-02 | 128 | 921 | 913 | 38 | 52.05% | 12.20% | 96.00% | 77.11% | 21.07% | `Week 4 1st Application (using canine thorax) Evaluation Workbook Confusion Matrix 1.xlsx` (B10) | VW, XP (predictions B19) |
| EVAL-01b | Week 4 committed-evaluator variant (same predictions) | M1 | same | RUN-02 | 128 | 921 | 913 | 38 | identical to EVAL-01 (micro and macro) | | | | | `outputs/week_04/matrix_1/matrix1_evaluation_workbook.xlsx` (B18) | VW, XP. Not a separate experiment |
| EVAL-02 | Week 4 original (delivered A6) | M2 (+158 / −1,842) | gpt-4.1-mini / V1.3 | RUN-01 | 127 | 31 | 1,803 | 39 | 96.50% | 80.38% | 97.88% | 76.51% | **78.40%** (B7 = 0.7839506; Week 4 report: 78.39%) | `…Confusion Matrix 2.xlsx` (B11) | VW, XP (predictions B17). Balanced Accuracy 89.13% (B8) |
| EVAL-03 / 04 | Week 5 replay of Week 4 predictions | M1 / M2 | — | — | as EVAL-01 / 02 | | | | | | | | | Replay workbooks not supplied | Observed (prior), KB_10; consistent |
| EVAL-05 | Week 5 live | M1 | gpt-4.1-mini / V1.3 | RUN-03 | 126 | 923 | 916 | 35 | 52.10% | 12.01% | 96.32% | 78.26% | 20.83% | `outputs/week_05/matrix_1/matrix1_evaluation_workbook.xlsx` (B22) | VW, XP (B23) |
| EVAL-06 | Week 5 live | M2 | gpt-4.1-mini / V1.3 | RUN-04 | 126 | 32 | 1,806 | 36 | 96.60% | 79.75% | 98.05% | 77.78% | 78.75% | `outputs/week_05/matrix_2/Evaluation Workbook v2.xlsx` (B24) | VW, XP (B25) |
| EVAL-07 | Week 7 Gemini | M1 | gemini-3.8-flash / V1.3 | RUN-05 | 96 | 953 | 924 | 27 | 51.00% | 9.15% | 97.16% | 78.05% | 16.38% | `outputs/week_07/week 5 rebuild with different llm (gemini flash)/matrix_1/matrix1_evaluation_workbook.xlsx` (B36) | VW, XP (B37), MF (B38 = EV-R01) |
| EVAL-08 | Week 7 Gemini | M2 | gemini-3.8-flash / V1.3 | RUN-06 | 102 | 56 | 1,822 | 20 | 96.20% | 64.56% | 98.91% | 83.61% | 72.86% | `…/matrix_2/Evaluation Workbook v2.xlsx` (B39) | VW, XP (B41), MF (B42 = EV-R02) |

Matrix 1 macro (`Overall Summary` B15:B19; Acc / Sens / Spec / Prec / F1):
- EVAL-01: 52.05 / 13.01 / 95.68 / 80.51 / 22.71%
- EVAL-05: 52.10 / 12.72 / 96.06 / 80.87 / 22.21%
- EVAL-07: 51.00 / 9.89 / 97.10 / 85.06 / 19.06%

Undefined values and zero-positive conditions:
- **Matrix 2:** 4 conditions have zero Gold Standard positives (hypo_plastic_trachea, pericardial_effusion, bronchiectasis, esophagitis), so sensitivity is undefined. Undefined F1: EVAL-02 6, EVAL-06 5, EVAL-08 5.
- **Matrix 1:** no zero-positive conditions. Precision is undefined for 3 conditions (EVAL-01, 05) or 4 (EVAL-07) because those runs made no positive predictions for them.

Execution Log facts:
- Evaluations generated at 2026-11-07 05:46:24 UTC (EVAL-01), 2026-11-12 10:04:10 (EVAL-05) and 2026-11-20 17:27:57 (EVAL-07). The Matrix 2 workbooks carry no timestamp.
- First-attempt completions: EVAL-02 99/100 (1 case needed 2 attempts); EVAL-06 100/100; EVAL-08 99/100.
- The Week 4 Matrix 2 workbook records "Radiologist agreement: Not calculated".

### AGR-01 / AGR-02 — model-to-model agreement (NOT accuracy; reference not used)

| ID | Workflow inputs | Agreement | Disagreements | Cases with ≥1 disagreement | Workbook | Status |
|---|---|---|---|---|---|---|
| AGR-01 | Matrix 1 | 1,940 / 2,000 = 97.00% | 60 | 37 | `outputs/week_07/comparison between openai gpt 4.1 mini  vs. gemini flash/matrix_1/matrix1_openai_vs_gemini_comparison.xlsx` (B34), Model Agreement row 22; Case Disagreements 60 rows; generated 2026-11-20 17:29:21 UTC | VW, XP (B23 vs B37) |
| AGR-02 | Matrix 2 | 1,944 / 2,000 = 97.20% | 56 | 33 | `…/matrix_2/matrix2_openai_vs_gemini_comparison.xlsx` (B35), Model Agreement row 22; Case Disagreements 56 rows; 17:29:29 UTC | VW, XP (B25 vs B41) |

The comparison workbooks' reference-based sections (Condition Comparison MICRO TOTAL, Overall Comparison) equal EVAL-05/07 (M1) and EVAL-06/08 (M2) exactly. Joint correctness:
- M1: both correct 1,001; only OpenAI 41; only Gemini 19; both wrong 939.
- M2: 1,900 / 32 / 24 / 44.

Comparison Execution Logs:
- 0 API requests.
- Read-only verification PASS.
- Recorded source hashes equal the bundle files.
- Week 5 OpenAI model identity "inferred from configuration, not embedded in prediction file".

## Feline Thorax: 100 cases × 21 conditions (N = 2,100 per matrix)

| ID | Ref. | Model / prompt | Run | TP | FN | TN | FP | Acc | Sens | Spec | Prec | F1 | Workbook (EV-B) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-11 | M1 Vetology (+534 / −1,566; 3 columns normalised) | gpt-4.1-mini / V1.2 (Execution Log B13) | RUN-07 | 29 | 505 | 1,529 | 37 | 74.19% | 5.43% | 97.64% | 43.94% | 9.67% | `outputs/week_07/2nd application/feline_thorax/matrix_1/feline_thorax_matrix1_evaluation_workbook.xlsx` (B26); generated 2026-11-21 16:35:36 UTC | VW, XP (B28), MF (B29 = EV-R03) |
| EVAL-12 | M2 Gold Standard (+117 / −1,983) | same | RUN-07 (shared) | 58 | 59 | 1,975 | 8 | 96.81% | 49.57% | 99.60% | 87.88% | 63.39% | `…/matrix_2/feline_thorax_matrix2_evaluation_workbook.xlsx` (B27) | VW, XP, MF |

- **Preliminary values (KB_02) confirmed exactly.**
- EVAL-11 macro: Acc 74.19, Sens 10.80, Spec 97.83, Prec 53.30, F1 23.81%.
- Undefined: precision for 10 conditions in both matrices (no positive predictions); F1 for 11. Matrix 2 also has 10 zero-positive conditions with undefined sensitivity (listed in 06).
- The model made positive predictions for 11 of 21 conditions, 66 positive labels in total. Identical predictions underlie both matrices.

## Canine Abdomen: 100 cases × 10 conditions (N = 1,000 per matrix)

| ID | Ref. | Model / prompt | Run | TP | FN | TN | FP | Acc | Sens | Spec | Prec | F1 | Workbook (EV-B) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-13 | M1 Vetology (+280 / −720) | gpt-4.1-mini / V1.4 (Execution Log B13) | RUN-08 | 34 | 246 | 697 | 23 | 73.10% | 12.14% | 96.81% | 59.65% | 20.18% | `outputs/week_07/3rd application/canine_abdomen/matrix_1/canine_abdomen_matrix1_evaluation_workbook.xlsx` (B30); generated 2026-11-21 16:50:16 UTC | VW, XP (B32), MF (B33 = EV-R04) |
| EVAL-14 | M2 Gold Standard (+81 / −919) | same | RUN-08 (shared) | 53 | 28 | 915 | 4 | 96.80% | 65.43% | 99.56% | 92.98% | 76.81% | `…/matrix_2/canine_abdomen_matrix2_evaluation_workbook.xlsx` (B31) | VW, XP, MF |

- **Preliminary values (KB_02) confirmed exactly**, including all 60 per-condition values in KB_02 Table 12.
- EVAL-13 macro: Acc 73.10, Sens 12.69, Spec 96.81, Prec 57.92, F1 20.18%.
- No undefined metrics and no zero-positive conditions in either matrix.

## Summary count

| Category | Records | Verified against workbook (W8) |
|---|---|---|
| Reference-based evaluations (distinct dataset × matrix × model × run) | 10: EVAL-01, 02, 05, 06, 07, 08, 11, 12, 13, 14 | **10 / 10** (+ cross-checked from predictions) |
| Duplicate workbook of an existing evaluation | 1: EVAL-01b | Verified; identical |
| Software parity replays | 2: EVAL-03, 04 | Workbooks not supplied; Observed (prior) |
| Model-agreement analyses (not accuracy) | 2: AGR-01, 02 | **2 / 2** |
| Aggregate values changed from the `ea92818` knowledge base | **0** (F1 78.40% vs 78.39% resolved as a rounding difference; historical value preserved) | — |
