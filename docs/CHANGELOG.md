# Changelog

This file records meaningful implementation and documentation changes. Dates below reflect the project update record available at the time of writing (2026-11-03).

## Week 2 — Scaffolding

### Added
- Command-line Excel-processing scaffold in `src/week_02/main.py`.
- Separate LangChain demonstration scripts for OpenAI, Gemini, and Hugging Face.
- Explanatory comments and docstrings across the Week 2 scripts.

### Verified
- Input workbook read successfully; 20 condition columns detected in the tested canine thorax workbook.
- Output workbook layout visually checked against the example format.
- Command-line help and optional output argument checked.
- Flake8 checks reported as passing after line-length corrections.

### Historical limitation
- The Week 2 scaffold generated the output structure; it did not calculate confusion-matrix counts. This limitation applies to that scaffold, not to the later Week 4 evaluation workflow.

## Week 3 — Prompt design and Gold Standard preparation

### Added / established
- V1.3 canine thorax master classification prompt for 20 conditions.
- Positive/Negative binary evaluation labels.
- Approved Gold Standard reference for CaseID 1–100, with 20 labels per case (2,000 labels).
- Data-handling rule: only original radiologist Findings, Conclusions, and Recommendations are sent to the LLM; CaseID is local tracking metadata.

## Week 4 — First GPT application and evaluation

### Added
- `src/week_04/week4_block1_data_loader.py` for dataset loading and validation.
- Prompt loader and V1.3 prompt integration under `src/week_04/prompts/`.
- `src/week_04/llm_client.py` for LangChain/OpenAI interaction.
- `src/week_04/single_case_test.py` for a single-case API test.
- `src/week_04/response_validator.py` and its tests for strict JSON response validation.
- `src/week_04/batch_processor.py` and `src/week_04/run_batch.py` for sequential batch execution, retries, checkpointing, restart support, and error logging.
- Matrix 2 evaluation workbook for 100 cases, 20 conditions, and 2,000 labels.
- Detailed mismatch analysis and a consolidated master adjudication register for 70 mismatches.

### Verified
- Block 1 data validation passed: 100 cases, 20 conditions, and 2,000 Gold Standard labels.
- Prompt integration test passed: 20 condition keys and V1.3 prompt loaded.
- Single-case OpenAI request returned a response.
- All Block 4 response-validator tests passed.
- Offline batch-processor tests passed for successful checkpointing, restart skipping, retry handling, and failure logging.
- Live batch completed with 100 successful predictions and zero final failures.
- Matrix 2 aggregate evaluation: accuracy 96.50%, sensitivity 80.38%, specificity 97.88%; TP 127, FN 31, TN 1,803, FP 39.
- All 70 mismatches were reconciled to the original Block 6 mismatch source and included in the master register.

### Pending / limitations
- Matrix 1 (original radiologist report versus second AI report) has not been confirmed as generated.
- Authorized adjudication of the 70 mismatches is pending. Do not alter the baseline Gold Standard or original predictions before approval.
- Optional Week 4 JSON prompt configuration has not been implemented or verified.
- Matrix 2 is a pilot comparison against the approved project Gold Standard, not a clinical-readiness assessment.
- Conditions with zero positive reference labels do not support a meaningful sensitivity estimate.

## Documentation update — 2026-11-03

- Updated README, requirements, environment example, ignore rules, decision log, testing log, weekly progress, and technical documentation to reflect Week 4.
- Git commits/tags remain deferred until project closeout.
