# Weekly Progress

## Week 1 — Prepare test data

### Completed
- Selected the canine thorax dataset for the first application.
- Prepared the first 100 cases (CaseID 1–100).
- Created a separate manual-scoring dataset retaining original radiologist report fields and condition labels.
- Established the approved Gold Standard: 100 cases × 20 conditions = 2,000 binary labels.
- Compared the manual scoring draft with the approved Gold Standard and identified 21 label differences.
- Adopted the approved Gold Standard as the Week 4 evaluation reference.

### Notes / limitations
- Existing legacy Abnormal/Normal labels are not treated as ground truth.
- The approved Gold Standard remains separate from LLM inputs.

## Week 2 — Scaffolding and API demonstrations

### Completed (user-verified)
- Command-line Excel-processing scaffold accepts an input workbook path and optional output path.
- Input workbook is read and condition headers are detected dynamically after the first eight metadata columns.
- Output workbook is generated in the example confusion-matrix structure and visually checked.
- Command-line help and optional output argument checked.
- Explanatory comments added to the Week 2 scripts.
- Flake8 checks reported as passing.

### Pending / historical scope
- The Week 2 output was a structural scaffold; it did not calculate confusion-matrix counts.
- Git milestone and tag were deferred.

## Week 3 — Prompt design and Gold Standard

### Completed
- Developed and integrated the V1.3 canine thorax master prompt.
- Defined 20 condition keys and exact `Positive` / `Negative` output labels.
- Documented prompt interpretation rules, including possible/suspected findings, explicit negation, recommendations, RTM, and independent `diseased_lungs` classification.
- Established the approved 100-case Gold Standard.
- Confirmed that only original radiologist Findings, Conclusions, and Recommendations are sent to the LLM.

### Pending / not confirmed
- Formal peer review of prompts and peer scoring was not confirmed in the project record.

## Week 4 — First GPT application

### Completed
- Implemented and tested the data loader for 100 cases, 20 conditions, and 2,000 Gold Standard labels.
- Integrated the V1.3 prompt loader.
- Implemented LangChain/OpenAI client configuration using environment variables and `python-dotenv`.
- Completed a live single-case API test.
- Implemented strict JSON response validation and passed its test suite.
- Implemented sequential batch processing with retries, checkpointing, restart support, and error logging.
- Completed the live 100-case batch: 100 successful predictions and zero final failures.
- Generated Matrix 2 comparing LLM predictions with the approved Gold Standard.
- Generated the Matrix 2 evaluation workbook (`Evaluation Workbook v2.xlsx`) with five sheets: Overall Summary, Condition Summary, Case Predictions, Confusion Matrix, and Execution Log. *(Corrected in the Week 5 closeout: previously listed as three sheets.)*
- Completed provisional review of all 70 mismatches and consolidated them into a master adjudication register.

### Matrix 2 results
- Total labels: 2,000.
- TP: 127.
- FN: 31.
- TN: 1,803.
- FP: 39.
- Accuracy: 96.50%.
- Sensitivity: 80.38%.
- Specificity: 97.88%.

### Matrix 1 evaluation and error analysis
- Completed the 100-case, 20-condition evaluation: 2,000 prediction/reference pairs.
- Confusion counts: TP 128, FN 921, TN 913, FP 38.
- Aggregate metrics: accuracy 52.05%, sensitivity 12.20%, specificity 96.00%, precision 77.11%, F1 21.07%.
- Consolidated 959 mismatches (921 FN and 38 FP) into the error-analysis workflow.
- Completed text-based screening across all 20 conditions. Screening findings remain provisional and are not veterinary adjudications.

### Optional task — JSON prompt configuration (completed)
- Created a separate module at `src/week_04/optional_json_config/`.
- Stored the exact operational Canine Thorax Master Prompt V1.3 in `config/canine_thorax_v1_3.json`.
- Implemented a JSON configuration loader with basic structure and version validation.
- Added five offline unit tests covering successful loading and expected error handling.
- User ran the tests locally: 5 passed, 0 failed.
- No API calls, dataset loading, or LLM execution were performed for this optional task.

### Remaining / limitations
- Authorized veterinary adjudication of mismatch registers remains pending. Preserve original reference labels and baseline predictions until approved.
- Matrix 1 and Matrix 2 results are pilot evaluations and do not establish clinical readiness.

### Limitations
- Mismatch assessments are provisional, not veterinary adjudications.
- Aggregate results are a pilot evaluation and do not establish clinical readiness.
- Sensitivity is not meaningful for conditions with zero positive reference cases.

## Week 5 — Claude Code rebuild

### Completed
- Rebuilt the Week 4 application independently under `src/week_05/` using Claude Code, in six reviewed and committed phases:
  1. Foundation and configuration — condition keys, Week 4 model settings, separate Matrix 1 / Matrix 2 workflow configurations, CLI.
  2. Prompt and LLM client — exact V1.3 prompt with integrity checks; Week 4 message construction reproduced byte-for-byte.
  3. Dataset loading — report input and reference labels kept separate; Week 4 cleaning and validation reproduced.
  4. Response validation — Week 4 output contract and error messages.
  5. Batch execution — Week 4 retry, checkpoint and JSONL behaviour, plus approved fail-fast and crash-recovery improvements.
  6. Evaluation and workbooks — Week 4 metrics; independent Matrix 1 and Matrix 2 reference loading and workbooks; verification against the delivered baselines.
- Reproduced both Week 4 baselines from the delivered artifacts: Matrix 1 TP 128, FN 921, TN 913, FP 38; Matrix 2 TP 127, FN 31, TN 1,803, FP 39.
- Matrix 1 workbook identical to the delivered workbook; Matrix 2 workbook identical except two approved differences (no Balanced Accuracy row; failure-count source disclosure in the Execution Log).
- 338 offline tests passed in the Linux development environment with baseline artifacts present (0 skipped, 0 network connection attempts); flake8 was clean there; Week 4 regression tests passed unchanged. The 9 real-artifact tests skip when the gitignored baseline files are absent.
- Completed the local Windows test suite on 2026-11-12 (Windows 11, Python 3.14.6): 338 tests run, 329 passed, 9 skipped, 0 failures and 0 errors. The skipped tests required baseline artifacts not present in the local test location. Windows JSONL compatibility tests passed. Flake8 was not rerun locally.
- Completed live OpenAI API batch executions on 2026-11-12: Matrix 1, 100 succeeded and 0 failed; Matrix 2, 100 succeeded and 0 failed. Both evaluation workbooks were generated and visually reviewed, and both reference-loader comparisons passed.
- Matrix 1 live evaluation: TP 126, FN 923, TN 916, FP 35; accuracy 52.10%, sensitivity 12.01%, specificity 96.32%, precision 78.26%, F1 20.83%.
- Matrix 2 live evaluation: TP 126, FN 32, TN 1,806, FP 36; accuracy 96.60%, sensitivity 79.75%, specificity 98.05%, precision 77.78%, F1 78.75%.
- Declared all directly imported dependencies in `requirements.txt`; corrected nine documentation inconsistencies.
- Detailed prediction-level error analysis and veterinary adjudication were outside the scope of the Week 5 live-execution closeout.

### Limitations / open items
- The Matrix 2 reference-loading rules are inferred from the delivered artifacts (the original Matrix 2 evaluator is not in the repository); ambiguous future workbooks are rejected rather than resolved silently.
- The delivered Matrix 1 workbook was produced by an evaluator variant not in the repository; the delivered Matrix 2 workbook's history (created by an external tool, modified four days later) cannot be fully established.
- No Week 4 `errors.jsonl` files were available; failure counts come from prediction records only.
- The two Week 4 prediction files differ on 8 of 2,000 case-condition pairs (run-to-run variation, documented, not altered).
- Veterinary adjudication of the mismatch registers remains pending.

## Weeks 6–10

Not yet documented as completed in this project record. Add implementation, tests, advisor feedback, decisions, and deliverables as each week's work is performed.

*Update (2026-11-21):* Week 7 is completed and recorded in its own section below. Weeks 6 and 8–10 remain undocumented as completed.


## Week 4 closeout status — 2026-11-08

The Week 4 application and optional JSON prompt-configuration task are implemented and tested. Documentation has been updated to reflect completed work. The remaining adjudication is a separate review dependency, not an unfinished coding task. Git commit/tag closeout is still to be performed.


## Week 7 — Gemini model evaluation

### Completed
- Implemented an independent Google Gemini pipeline under `src/week_07/` (branch `week-07/gemini-model-evaluation`). Weeks 4 and 5 were unchanged, and there is no runtime dependency on either.
- Integrated Gemini `gemini-3.8-flash` via LangChain (`langchain-google-genai`) and the Google GenAI SDK, at temperature 0, with the unchanged, SHA-256-protected Canine Thorax Master Prompt V1.3. Model input is limited to the original Findings, Conclusions and Recommendations; reference labels are held separately.
- Added a bounded retry policy with fatal, transient and retryable error classification, and per-workflow run manifests recording provenance.
- Kept Matrix 1 and Matrix 2 as separate workflows with isolated `outputs/week_07/` folders. The Week 5 OpenAI predictions were used as read-only comparison inputs.
- Added evaluation and the six-sheet OpenAI-vs-Gemini comparison workbook (`python -m week_07 compare`).
- Tests: 288 Week 7 tests run, 282 passed, 6 skipped, 0 failures and 0 errors. Opt-in local artifact tests: 6 run, 4 passed, 2 skipped. Week 5 regression: 338 run, 329 passed, 9 skipped. Flake8 clean.
- Live Gemini execution: 100 cases × 20 conditions per matrix, zero unresolved final failures.
  - Matrix 1 (original Vetology reference): Gemini TP 96, FN 953, TN 924, FP 27; accuracy 51.00%, sensitivity 9.15%, specificity 97.16%, precision 78.05%, F1 16.38%. Week 5 OpenAI: accuracy 52.10%, sensitivity 12.01%, specificity 96.32%, precision 78.26%, F1 20.83%. Agreement 97.00% (60 disagreements).
  - Matrix 2 (Gold Standard reference): Gemini TP 102, FN 56, TN 1,822, FP 20; accuracy 96.20%, sensitivity 64.56%, specificity 98.91%, precision 83.61%, F1 72.86%. Week 5 OpenAI: accuracy 96.60%, sensitivity 79.75%, specificity 98.05%, precision 77.78%, F1 78.75%. Agreement 97.20% (56 disagreements).
- Deliverables: `src/week_07/`; two comparison workbooks (local only); two run manifests; updated documentation and `requirements.txt` (`google-genai==2.31.0` pinned).

### Limitations / open items
- In both matrices Gemini was more specific (fewer false positives), and OpenAI was more sensitive with higher accuracy and F1. High agreement between the models does not imply accuracy against the reference labels.
- Matrix 1 and Matrix 2 use different reference-label sets and must not be combined. These are pilot results, not evidence of clinical readiness.
- Veterinary adjudication of the model disagreements and mismatches remains pending.

## Week 7 extension — Feline Thorax and Canine Abdomen

### Completed
- Made the Week 7 engine application-aware with a registry of three applications (branch `week-07/feline-thorax-and-canine-abdomen`):
  - `canine_thorax`: Gemini, 20 conditions, V1.3. Unchanged; still the default.
  - `feline_thorax`: OpenAI `gpt-4.1-mini`, 21 conditions.
  - `canine_abdomen`: OpenAI `gpt-4.1-mini`, 10 conditions.
- Added the OpenAI provider, with one transport attempt per application attempt so the existing batch retry policy stays the only retry system. Each provider requires only its own API key.
- Shared predictions: each new application predicts its 100 Matrix 1 cases once and reuses the predictions for the Matrix 1 (Vetology) and Matrix 2 (Gold Standard) evaluations. The tracks stay separate. Matrix 2 reuse requires identical CaseIDs, order and report text.
- Feline Matrix 1 normalisation: `Normal`/`Abnormal` → `Negative`/`Positive` for `pulmonary_nodules`, `esophagitis` and `pneumonia` only. All other labels are validated strictly.
- Isolation by `<application>/<workflow>`: each application is confined to `outputs/week_07/<application>/` for writes and prediction reads, and Canine Thorax paths are unchanged.
- Matrix 1 and Matrix 2 evaluation workbooks use application-specific condition rows, headers and counts, prompt records and dataset names. The CLI gained `--application`, `--provider`, `--matrix2-input` and `--prediction-source-input`, and existing commands are unchanged.
- Validated the four supplied real workbooks offline:
  - each has `Sheet1` and the expected headers;
  - 100 unique CaseIDs (1–100) each, with the Gold Standard blank rows skipped;
  - the loaders agree and the Matrix 2 guardrail passes;
  - the normalisation counts were correct;
  - the two matrices have identical cases and report text in both applications.
- Tests: Week 7 501 run (496 passed, 5 skipped), Week 5 338 run (329 passed, 9 skipped), 0 failures; flake8 clean.

### Limitations / open items
- The approved prompts were supplied (Feline Thorax V1.1, Canine Abdomen V1.2) and then corrected with the owner's approval.
  - **Feline Thorax V1.2:** the JSON output example is now valid JSON.
  - **Canine Abdomen V1.3:** the uncertainty rules are consistent.
  - Both corrected versions are active and pinned; the originals are kept for provenance.
- **The live OpenAI runs have not been executed yet**; they are to be run locally.
- **No Feline Thorax or Canine Abdomen model results exist yet.** The offline end-to-end run used a fake classifier and is not an evaluation result.
- The live runs need `OPENAI_API_KEY` in the local `.env`.
