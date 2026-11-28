# 03 — Confusion Matrix and Metrics Register

One record per distinct evaluation. Datasets, reference tracks (Matrix 1 = original Vetology labels; Matrix 2 = Gold Standard labels), models, prompts and runs are **never combined**. Agreement records (AGR) are kept separate from reference-based evaluations.

> **No workbook was accessible in Week 8. Every count below is *documented but unverified* in this session.** Where an earlier Claude session read the artifact directly, the status says *Observed (prior)*. Rates were recomputed from the recorded counts (*Derived* check) and match to 2 d.p. unless a conflict is noted. No missing value has been filled in.

## Canine Thorax: 100 cases × 20 conditions

### EVAL-01 — Canine Thorax · Matrix 1 (Vetology) · Week 4 original application
- **Model:** gpt-4.1-mini (OpenAI via LangChain ChatOpenAI). **Prompt:** Canine Thorax V1.3, file `31a7dab6…7ab7b1`. **Run:** RUN-02 (7 Nov 2026). No manifest.
- **Counts:** TP 128 · FN 921 · TN 913 · FP 38 (N = 2,000; reference + 1,049 / − 951).
- **Rates:** Acc 52.05% · Sens 12.20% · Spec 96.00% · Prec 77.11% · F1 21.07%. Macro (from the A5 replay): Acc 52.05, Sens 13.01, Spec 95.68, Prec 80.51, F1 22.71.
- **Evidence:** delivered workbook A5 `Evaluation_Workbook_v1.xlsx` (sha `7237d3cf…`, Inaccessible); `docs/testing_log.md`; KB_05 T5–6, KB_04 T6, KB_03 §6.1, KB_10 T12.
- **Status:** Recorded; Observed (prior) via the Week 5 replay. **Unverified in Week 8.**

### EVAL-02 — Canine Thorax · Matrix 2 (Gold Standard) · Week 4 original application
- **Model / prompt:** as EVAL-01. **Run:** RUN-01 (3 Nov 2026).
- **Counts:** TP 127 · FN 31 · TN 1,803 · FP 39 (N = 2,000; reference + 158 / − 1,842).
- **Rates:** Acc 96.50% · Sens 80.38% · Spec 97.88% · Prec 76.51% · **F1 78.40% (workbook/docs) vs 78.39% (Week 4 report): Conflict C-02**. Derived F1 = 78.3951%. The delivered workbook also shows Balanced Accuracy 89.13% (not part of the methodology).
- **Evidence:** A6 `Evaluation Workbook v2.xlsx` (sha `2ff2bffa…`, Inaccessible); `docs/testing_log.md` L35; KB_05 T8–9; KB_10 T12.
- **Status:** Recorded; Observed (prior) via replay. **Unverified in Week 8.** Matrix 2 evaluator source never existed in the repository.

### EVAL-03 / EVAL-04 — Canine Thorax · Matrix 1 / Matrix 2 · Week 5 evaluator replay of Week 4 predictions (parity check)
- Same predictions as EVAL-01/02 (A3, A4), evaluated by `src/week_05` at `874aaea`/`a938cde`.
- **Counts identical** to EVAL-01 / EVAL-02. Workbooks matched A5 exactly (excluding dynamic cells) and A6 except two approved differences: no Balanced Accuracy row, and Execution Log C8 note.
- **Status:** Observed (prior) (KB_10 §8.1–8.2). This verifies the **software**, not the model.

### EVAL-05 — Canine Thorax · Matrix 1 (Vetology) · Week 5 live
- **Model:** gpt-4.1-mini · **Prompt:** V1.3 · **Run:** RUN-03 (12 Nov 2026).
- **Counts:** TP 126 · FN 923 · TN 916 · FP 35. **Rates:** Acc 52.10% · Sens 12.01% · Spec 96.32% · Prec 78.26% · F1 20.83%.
- **Evidence:** `outputs/week_05/matrix_1/matrix1_evaluation_workbook.xlsx` (Inaccessible); `docs/project_documentation.md` §11.6; KB_04 T13; KB_03 §6.2; KB_10 T14.
- **Status:** Recorded. **Unverified.**

### EVAL-06 — Canine Thorax · Matrix 2 (Gold Standard) · Week 5 live
- **Model / prompt:** as EVAL-05. **Run:** RUN-04 (12 Nov 2026).
- **Counts:** TP 126 · FN 32 · TN 1,806 · FP 36. **Rates:** Acc 96.60% · Sens 79.75% · Spec 98.05% · Prec 77.78% · F1 78.75%.
- **Evidence:** `outputs/week_05/matrix_2/Evaluation Workbook v2.xlsx` (Inaccessible); same documents.
- **Status:** Recorded. **Unverified.**

### EVAL-07 — Canine Thorax · Matrix 1 (Vetology) · Week 7 Gemini
- **Model:** gemini-3.8-flash · **Prompt:** V1.3 (pins in the manifest) · **Run:** RUN-05, manifest EV-R01 (Verified W8).
- **Counts:** TP 96 · FN 953 · TN 924 · FP 27. **Rates:** Acc 51.00% · Sens 9.15% · Spec 97.16% · Prec 78.05% · F1 16.38%.
- **Evidence:** `outputs/week_07/matrix_1/matrix1_evaluation_workbook.xlsx` (Inaccessible); `README.md`; `docs/CHANGELOG.md` L185; `docs/testing_log.md`; KB_08 T9–10; KB_09 T14.
- **Status:** Recorded (user-reported metrics, arithmetic re-derived by KB_08). Batch Verified (W8); **metrics unverified**.

### EVAL-08 — Canine Thorax · Matrix 2 (Gold Standard) · Week 7 Gemini
- **Model / prompt:** as EVAL-07 · **Run:** RUN-06 (main run plus checkpointed trial), manifest EV-R02 (Verified W8).
- **Counts:** TP 102 · FN 56 · TN 1,822 · FP 20. **Rates:** Acc 96.20% · Sens 64.56% · Spec 98.91% · Prec 83.61% · F1 72.86%.
- **Evidence:** `outputs/week_07/matrix_2/Evaluation Workbook v2.xlsx` (Inaccessible); `docs/CHANGELOG.md` L186.
- **Status:** Recorded; batch Verified (W8); **metrics unverified**.

### AGR-01 / AGR-02 — Canine Thorax · model-to-model agreement (NOT accuracy)
- Week 7 Gemini (RUN-05/06) vs Week 5 OpenAI (RUN-03/04) predictions; **reference labels not used**.
- AGR-01 (Matrix 1 inputs): 1,940/2,000 = 97.00%, 60 disagreements. AGR-02 (Matrix 2 inputs): 1,944/2,000 = 97.20%, 56 disagreements.
- **Evidence:** comparison workbooks `outputs/week_07/comparison/matrix_1|2/…openai_vs_gemini_comparison.xlsx` (Inaccessible; inspected by the user only); `docs/testing_log.md` L208–209.
- **Status:** Recorded. **Unverified.**

### Canine Thorax per-condition results
**Missing in all accessible evidence.** Per-condition counts exist only inside the gitignored workbooks (KB_07 §5.14 note; KB_08 §16.2).

## Feline Thorax: 100 cases × 21 conditions

### EVAL-11 — Feline Thorax · Matrix 1 (Vetology, three columns normalised) · Week 7 OpenAI
- **Model:** gpt-4.1-mini · **Prompt:** Feline Thorax V1.2, file `9bbd36c4…1c418f25` · **Run:** RUN-07, manifest EV-R03 (Verified W8). Execution date of the evaluation: 2026-11-21 (KB_02; time not recorded).
- **Counts:** TP 29 · FN 505 · TN 1,529 · FP 37 (N = 2,100; reference + 534 / − 1,566).
- **Rates:** Acc 74.19% · Sens 5.43% · Spec 97.64% · Prec 43.94% · F1 9.67%.
- **Evidence location (expected):** `outputs/week_07/feline_thorax/matrix_1/feline_thorax_matrix1_evaluation_workbook.xlsx` (**Inaccessible**). **Single source:** KB_02 T10 (retained ChatGPT conversation output).
- **Status:** **Documented but unverified. Conflict C-01:** KB_07, KB_08, KB_09 and KB_10 record that no FT evaluation metrics exist in the repository. Derived checks are consistent: TP+FN matches KB_07's observed prevalence (534); predicted positives are 66 in both matrices.

### EVAL-12 — Feline Thorax · Matrix 2 (Gold Standard) · Week 7 OpenAI
- **Model / prompt / run:** as EVAL-11 (same shared predictions; no second batch).
- **Counts:** TP 58 · FN 59 · TN 1,975 · FP 8 (N = 2,100; reference + 117 / − 1,983).
- **Rates:** Acc 96.81% · Sens 49.57% · Spec 99.60% · Prec 87.88% · F1 63.39%.
- **Evidence location (expected):** `outputs/week_07/feline_thorax/matrix_2/feline_thorax_matrix2_evaluation_workbook.xlsx` (**Inaccessible**). Single source: KB_02 T10.
- **Status:** **Documented but unverified (C-01).** 10 of 21 conditions have zero Gold Standard positives, so per-condition sensitivity is undefined for them.

### Feline Thorax per-condition results
**Missing.** KB_02 §9.4 states that no reliable condition-level table was preserved.

## Canine Abdomen: 100 cases × 10 conditions

### EVAL-13 — Canine Abdomen · Matrix 1 (Vetology) · Week 7 OpenAI
- **Model:** gpt-4.1-mini · **Prompt:** Canine Abdomen V1.4, file `9336be3f…7b2a254c` · **Run:** RUN-08, manifest EV-R04 (Verified W8). Evaluation date 2026-11-21 (KB_02).
- **Counts:** TP 34 · FN 246 · TN 697 · FP 23 (N = 1,000; reference + 280 / − 720).
- **Rates:** Acc 73.10% · Sens 12.14% · Spec 96.81% · Prec 59.65% · F1 20.18%.
- **Evidence location (expected):** `outputs/week_07/canine_abdomen/matrix_1/canine_abdomen_matrix1_evaluation_workbook.xlsx` (**Inaccessible**). Single source: KB_02 T11 (user-supplied terminal output).
- **Status:** **Documented but unverified (C-01).** Derived checks are consistent (prevalence 280 matches KB_07 Table 27; predicted positives are 57 in both matrices).

### EVAL-14 — Canine Abdomen · Matrix 2 (Gold Standard) · Week 7 OpenAI
- **Model / prompt / run:** as EVAL-13 (shared predictions).
- **Counts:** TP 53 · FN 28 · TN 915 · FP 4 (N = 1,000; reference + 81 / − 919).
- **Rates:** Acc 96.80% · Sens 65.43% · Spec 99.56% · Prec 92.98% · F1 76.81%.
- **Evidence:** expected `outputs/week_07/canine_abdomen/matrix_2/canine_abdomen_matrix2_evaluation_workbook.xlsx` (**Inaccessible**). Terminal INFO log 2026-11-21 22:21:19 (KB_02 §1).
- **Status:** **Documented but unverified (C-01).**

### Canine Abdomen per-condition results
KB_02 Table 12 reports **positive-label count, sensitivity and F1 per condition only**, from an earlier ChatGPT review of the workbooks. Per-condition TP/FN/TN/FP and specificity were **not reported** and are **not derived here**. Status: Recorded (prior review); **re-verification against the workbooks is required**. Do not cite these values in the paper until that is done.

## Summary count

| Category | Records |
|---|---|
| Reference-based evaluations (distinct dataset × matrix × model × run) | 10: EVAL-01, 02, 05, 06, 07, 08, 11, 12, 13, 14 |
| Software parity replays (same predictions as EVAL-01/02) | 2: EVAL-03, 04 |
| Model-agreement analyses (not accuracy) | 2: AGR-01, 02 |
| Evaluations with any count verified against a workbook in Week 8 | **0** |
| Evaluations whose underlying prediction batch is verified by a committed manifest in Week 8 | 6: EVAL-07, 08, 11, 12, 13, 14 |
| Completed prediction batches with **unverified** evaluation metrics | RUN-07 (EVAL-11/12), RUN-08 (EVAL-13/14): KB_02 reports metrics, but the repository has none |
