# 03 — Results and Experimental Findings

Every numerical result is listed separately by **dataset → reference track → model → run**. The evaluation IDs (EVAL-xx) and run IDs (RUN-xx) match `../04_Evidence_and_Artifacts/02_Experimental_Run_Register.md` and `03_Confusion_Matrix_and_Metrics_Register.md`.

> **Week 8 verification status of results.** No prediction JSONL file or evaluation workbook was available in this environment: they are gitignored and kept on the developer's machine. **No confusion count below was re-verified in Week 8 against a workbook.** The counts are *Recorded* (or *Observed (prior)* where an earlier Claude session read the artifacts). Week 8 did (a) verify the committed run manifests, prompt hashes and input hashes, and (b) recompute every rate from its recorded counts as a **Derived** consistency check. Every recomputed rate matched the recorded rate at 2 d.p., except the F1 rounding conflict in §1.2.
>
> All results are 100-case pilot results. They are not clinical validation. Never pool Matrix 1 with Matrix 2.

## 1. Canine Thorax (20 conditions; 2,000 case–condition pairs per matrix)

Reference prevalence (Derived from recorded counts; matches KB_03 slide 8): Matrix 1 has 1,049 positive and 951 negative labels. Matrix 2 has 158 positive and 1,842 negative.

### 1.1 Aggregate (micro) results

| Eval ID | Week / run | Ref. | Model | TP | FN | TN | FP | Acc. | Sens. | Spec. | Prec. | F1 | Status | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-01 | Week 4 delivered (RUN-02, 7 Nov) | M1 | gpt-4.1-mini | 128 | 921 | 913 | 38 | 52.05% | 12.20% | 96.00% | 77.11% | 21.07% | Recorded; replay Observed (prior) | KB_05 T5–6; KB_04 T6; KB_03 §6.1; KB_10 T12; `docs/testing_log.md` |
| EVAL-02 | Week 4 delivered (RUN-01, 3 Nov) | M2 | gpt-4.1-mini | 127 | 31 | 1,803 | 39 | 96.50% | 80.38% | 97.88% | 76.51% | **78.40% / 78.39% (Conflict C-02)** | Recorded; replay Observed (prior) | KB_05 T8–9; KB_04 T6; KB_10 T12; `docs/testing_log.md` L35 |
| EVAL-03 | Week 5 replay of Week 4 predictions (parity) | M1 | (Week 4 predictions) | 128 | 921 | 913 | 38 | 52.05% | 12.20% | 96.00% | 77.11% | 21.07% | Observed (prior), exact vs delivered workbook A5 | KB_10 T12–13; KB_04 T12 |
| EVAL-04 | Week 5 replay of Week 4 predictions (parity) | M2 | (Week 4 predictions) | 127 | 31 | 1,803 | 39 | 96.50% | 80.38% | 97.88% | 76.51% | 78.40% | Observed (prior), exact vs A6 except two approved differences | KB_10 T12–13; KB_04 T12 |
| EVAL-05 | Week 5 live (RUN-03, 12 Nov) | M1 | gpt-4.1-mini | 126 | 923 | 916 | 35 | 52.10% | 12.01% | 96.32% | 78.26% | 20.83% | Recorded | KB_04 T13; KB_03 §6.2; KB_10 T14; `docs/project_documentation.md` §11.6 |
| EVAL-06 | Week 5 live (RUN-04, 12 Nov) | M2 | gpt-4.1-mini | 126 | 32 | 1,806 | 36 | 96.60% | 79.75% | 98.05% | 77.78% | 78.75% | Recorded | same |
| EVAL-07 | Week 7 Gemini (RUN-05, 20 Nov) | M1 | gemini-3.8-flash | 96 | 953 | 924 | 27 | 51.00% | 9.15% | 97.16% | 78.05% | 16.38% | Recorded; batch Verified (W8, manifest) | KB_08 T9–10; KB_09 T14; KB_07 T23; `README.md`; `docs/CHANGELOG.md` L185 |
| EVAL-08 | Week 7 Gemini (RUN-06, 20 Nov) | M2 | gemini-3.8-flash | 102 | 56 | 1,822 | 20 | 96.20% | 64.56% | 98.91% | 83.61% | 72.86% | Recorded; batch Verified (W8, manifest) | same; `docs/CHANGELOG.md` L186 |

Matrix 1 macro averages for EVAL-03 (Observed (prior), KB_10 §8.1): accuracy 52.05%, sensitivity 13.01%, specificity 95.68%, precision 80.51%, F1 22.71%. These are identical to the delivered workbook A5.

### 1.2 Week 4 Matrix 2 F1 rounding conflict (C-02)

- 78.39% is the value in the Week 4 technical report, explicitly marked as derived from counts (KB_05 T9; KB_04 T6; KB_03 §6.1).
- 78.40% is the value in the delivered Matrix 2 workbook, the Week 5 parity table and the repository documentation (KB_04 T12; KB_10 T12; `docs/testing_log.md` L35, L110; `README.md` L99).
- Week 8 Derived check: 2×127 / (2×127 + 39 + 31) = 254/324 = 0.783951, which is **78.40%** at 2 d.p. The paper should state its rounding convention. The 78.39% value appears to be a truncation, but **that explanation is unconfirmed**.

### 1.3 Canine Thorax: other findings

| Finding | Value | Status | Source |
|---|---|---|---|
| Run-to-run variation between the two Week 4 prediction files (Matrix 1 file A3 and Matrix 2 file A4, run separately on identical report text, temperature 0) | 8 of 2,000 pairs differ (6 cases; 4 Positive→Negative, 4 Negative→Positive); both files contain 166 positive predictions | Observed (prior); Recorded | KB_10 §18; `docs/testing_log.md` L120 |
| Week 4 Matrix 1 mismatches | 959 (921 FN, 38 FP); text screening only | Recorded | KB_05 §7.3, §9.1 |
| Week 4 Matrix 1 FN text screening | 254 FN pairs screened across four conditions (thoracic_lymphadenopathy 78, bronchiectasis 67, pleural_effusion 59, pulmonary_vessel_enlargement 50); 705 mismatches unscreened | Recorded; **not veterinary adjudication** | KB_05 Table 11 |
| Week 4 Matrix 2 mismatches | 70 (31 FN, 39 FP); provisional review only; adjudication pending | Recorded | KB_05 §8.4; KB_07 T24 |
| Week 4 Matrix 2 Balanced Accuracy (delivered workbook only; not computed by later code) | 89.13% | Recorded | KB_07 T23 note; `README.md` L344 |
| Week 4 Matrix 2 batch | 100 successes; one case needed a second application attempt | Recorded | KB_04 §4.1 |
| Week 4 Matrix 1 batch | 100 × HTTP 200; 0 retries, 0 failures, 0 skips | Recorded | KB_05 T7 |
| Week 5 live batches | 100/100 succeeded in each workflow; Matrix 1 `errors.jsonl` has 100 lines (append-only, superseded attempts; **not** 100 final failures) | Recorded | KB_04 T14; KB_08 D-05 |

### 1.4 Model-to-model agreement (Canine Thorax; NOT accuracy)

Week 7 Gemini vs Week 5 OpenAI predictions. **Reference labels are not used.** Agreement says nothing about correctness.

| ID | Workflow | Agreement | Disagreements | Status | Source |
|---|---|---|---|---|---|
| AGR-01 | Matrix 1 inputs | 1,940 / 2,000 = 97.00% | 60 | Recorded (comparison workbooks inspected by the user; Inaccessible here) | KB_08 §8; KB_09 T14; `docs/testing_log.md` L208 |
| AGR-02 | Matrix 2 inputs | 1,944 / 2,000 = 97.20% | 56 | Recorded | same, L209 |

### 1.5 Interpretations in the sources (not verified conclusions)

- Matrix 1 vs Matrix 2 differences reflect **different reference sets and prevalence**, not a model change (KB_03 §5.4; KB_04 §7.3).
- Week 4 vs Week 5 live differences come from separate live runs and do **not** isolate a Claude Code effect (KB_03 §6.3; KB_04 §14).
- On Canine Thorax, Gemini was more specific and GPT-4.1 mini more sensitive. This is documented from a single run per model and is not significance-tested (KB_07 T37).

## 2. Feline Thorax (21 conditions; 2,100 pairs per matrix)

### 2.1 Batch (RUN-07): Verified (W8) against the committed manifest

The shared prediction batch ran 2026-11-21 16:22:06 → 16:26:24 UTC with gpt-4.1-mini, temperature 0.0, prompt Feline Thorax V1.2, input SHA-256 `ef8fcc97…3815516`. Result: 100 total, 100 succeeded, 0 failed, 0 skipped, 0 transient backoffs.

### 2.2 Evaluation results (single source: KB_02; NOT in the repository)

| Eval ID | Ref. | TP | FN | TN | FP | Acc. | Sens. | Spec. | Prec. | F1 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-11 | M1 Vetology (after normalisation) | 29 | 505 | 1,529 | 37 | 74.19% | 5.43% | 97.64% | 43.94% | 9.67% | **Recorded, unverified** (Conflict C-01) |
| EVAL-12 | M2 Gold Standard | 58 | 59 | 1,975 | 8 | 96.81% | 49.57% | 99.60% | 87.88% | 63.39% | **Recorded, unverified** (Conflict C-01) |

KB_02 §9.1 records these as retained from earlier evaluation output in the ChatGPT conversation. The workbooks (`outputs/week_07/feline_thorax/matrix_1|2/…_evaluation_workbook.xlsx`) are gitignored and **were not available to KB_07 or to Week 8**. KB_07, KB_08, KB_09 and KB_10 all state that no Feline evaluation metrics exist in the repository.

Week 8 Derived consistency checks (not verification):
- All rates recompute from the counts.
- TP+FN = 534 (M1) and 117 (M2). These match the reference-positive prevalence that KB_07 observed directly in the uploaded workbooks (Table 26).
- TP+FP = 66 in both matrices, as expected when one shared prediction set is scored against two references.

### 2.3 Condition-level data

- **Reference prevalence per condition** (Observed (prior), KB_07 Table 26): Matrix 1 has 534 positives and Matrix 2 has 117. In the Matrix 2 Gold Standard, **10 of 21 conditions have zero positives** (esophagitis, pneumonia, hypo_plastic_trachea, perihilar_infiltrate, rtm, right_sided_cardiomegaly, focal_perihilar, left_sided_cardiomegaly, bronchiectasis, pericardial_effusion), so Matrix 2 sensitivity is undefined for those conditions.
- Feline Matrix 1 normalisation counts (KB_02 §8.1; consistent with KB_07): pulmonary_nodules 6 Abnormal / 94 Normal; esophagitis 59 / 41; pneumonia 51 / 49.
- **Per-condition confusion counts and metrics: Missing** (KB_02 §9.4: "must be extracted directly from the workbook; do not infer").

## 3. Canine Abdomen (10 conditions; 1,000 pairs per matrix)

### 3.1 Batch (RUN-08): Verified (W8) against the committed manifest

The shared prediction batch ran 2026-11-21 16:42:21 → 16:44:40 UTC with gpt-4.1-mini, temperature 0.0, prompt Canine Abdomen V1.4, input SHA-256 `583e7523…2a5efe`. Result: 100 total, 100 succeeded, 0 failed, 0 skipped, 0 backoffs.
This closes the gap KB_02 §8.2 flagged ("full batch log not present"): the manifest records the batch outcome. API request IDs are still not recorded.

### 3.2 Evaluation results (single source: KB_02 terminal output; NOT in the repository)

| Eval ID | Ref. | TP | FN | TN | FP | Acc. | Sens. | Spec. | Prec. | F1 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EVAL-13 | M1 Vetology | 34 | 246 | 697 | 23 | 73.10% | 12.14% | 96.81% | 59.65% | 20.18% | **Recorded, unverified** (C-01) |
| EVAL-14 | M2 Gold Standard | 53 | 28 | 915 | 4 | 96.80% | 65.43% | 99.56% | 92.98% | 76.81% | **Recorded, unverified** (C-01) |

KB_02 describes these as reported directly in user-supplied terminal output (Matrix 2 INFO log 2026-11-21 22:21:19). Derived checks: the rates recompute. TP+FN = 280 / 81 matches the prevalence KB_07 observed (Table 27). TP+FP = 57 in both matrices (consistent with shared predictions).

### 3.3 Condition-level data (prior ChatGPT workbook review; re-verification required)

KB_02 Table 12 reports, **per condition, positive-label counts, sensitivity and F1 only**. TP/FN/TN/FP and specificity per condition were not stated. Status: **Recorded, unverified.** The values are not reproduced in the evidence register as confusion counts. Points the sources highlight:
- Matrix 1 pancreatitis: 75 reference positives, reported sensitivity 2.67%.
- Matrix 1 splenic_mass (5.56%) and splenomegaly (5.26%) also have very low sensitivity.
- Several Matrix 2 conditions have 2–3 positives, so their reported 100% sensitivity/F1 values are unstable.
- Matrix 2 colitis sensitivity was 33.33%.

Reference prevalence per condition (Observed (prior), KB_07 Table 27): Matrix 1 = 280 positives; Matrix 2 = 81. No Abdomen Gold Standard condition has zero positives.

Hedged-language heuristic (Observed (prior), indicative only; KB_07 §8.5): of 48 hedged-only Conclusions mentions, 34 are Gold Standard Positive. Up to about 34 of 81 Gold Standard positives (~42%) depend on hedged-only wording. This evidence supported the inclusive V1.3/V1.4 policy. It is not adjudication.

## 4. Cross-dataset observations (all require validation)

| Observation | Basis | Status |
|---|---|---|
| In all three datasets the Matrix 1 Vetology labels contain far more positives than the Gold Standard (CT 1,049 vs 158; FT 534 vs 117; CA 280 vs 81) | KB_07 §8.3 (FT and CA Observed (prior)); CT Derived | Observed / Derived |
| Sensitivity is much higher against Matrix 2 than against Matrix 1 in every dataset; specificity is high in every row | Recorded counts above | Recorded (FT/CA unverified) |
| High accuracy partly reflects negative-dominant references; report sensitivity and F1 alongside accuracy | KB_03 §6.1; KB_02 §16.1 | Interpretation |
| Cross-application comparison is confounded by different uncertainty policies (CT inclusive, FT conservative, CA scoped-inclusive) | KB_07 §7.2 | Observed (prior) |
| No confidence intervals, significance tests, inter-rater reliability or veterinary adjudication exist for any dataset | KB_02 §18; KB_07 §16 | Missing |

## 5. Not results

- Week 3 V1.0 vs V1.1 manual prompt reviews (five cases per dataset, no label changes) show consistency only. They are not accuracy results (KB_06 §11.4).
- Test-suite pass counts (see 04 §5) are software-quality evidence only.
- An offline end-to-end run on the real Feline/Abdomen workbooks used a fake classifier. Its "accuracy" measures the pipeline and was deliberately not reported (KB_07 §8.6).
