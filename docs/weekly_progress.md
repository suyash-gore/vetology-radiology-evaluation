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
- Generated the evaluation workbook with Case Predictions, Confusion Matrix, and Execution Log sheets.
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

## Weeks 5–10

Not yet documented as completed in this project record. Add implementation, tests, advisor feedback, decisions, and deliverables as each week's work is performed.


## Week 4 closeout status — 2026-11-08

The Week 4 application and optional JSON prompt-configuration task are implemented and tested. Documentation has been updated to reflect completed work. The remaining adjudication is a separate review dependency, not an unfinished coding task. Git commit/tag closeout is still to be performed.
