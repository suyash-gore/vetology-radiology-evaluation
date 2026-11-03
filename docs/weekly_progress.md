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

### Remaining required work
- Generate Matrix 1: original radiologist report versus the second AI report.
- Obtain authorized adjudication decisions for the 70 mismatches. Preserve the original Gold Standard and baseline predictions until approved.

### Optional work
- Implement JSON-based prompt configuration.
- Update the application to load prompt settings from JSON.
- Test JSON configuration loading and prompt execution.

### Limitations
- Mismatch assessments are provisional, not veterinary adjudications.
- Aggregate results are a pilot evaluation and do not establish clinical readiness.
- Sensitivity is not meaningful for conditions with zero positive reference cases.

## Weeks 5–10

Not yet documented as completed in this project record. Add implementation, tests, advisor feedback, decisions, and deliverables as each week's work is performed.
