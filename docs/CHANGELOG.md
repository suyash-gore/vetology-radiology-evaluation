# Changelog

This file records meaningful implementation and documentation changes. Week 4 closeout updates reflect the verified project state as of 2026-11-08.

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
- Matrix 1 evaluation workbook and consolidated mismatch/error analysis for 100 cases and 20 conditions.
- Master adjudication register covering all 959 Matrix 1 mismatch pairs.
- Condition/family-level text-screening investigations across all 20 conditions.
- Optional JSON prompt-configuration module under `src/week_04/optional_json_config/`.

### Verified
- Block 1 data validation passed: 100 cases, 20 conditions, and 2,000 Gold Standard labels.
- Prompt integration test passed: 20 condition keys and V1.3 prompt loaded.
- Single-case OpenAI request returned a response.
- All Block 4 response-validator tests passed.
- Offline batch-processor tests passed for successful checkpointing, restart skipping, retry handling, and failure logging.
- Live batch completed with 100 successful predictions and zero final failures.
- Matrix 2 aggregate evaluation: accuracy 96.50%, sensitivity 80.38%, specificity 97.88%; TP 127, FN 31, TN 1,803, FP 39.
- Matrix 2: all 70 mismatches were reconciled to the original Block 6 mismatch source and included in its master register.
- Matrix 1: 2,000 prediction/reference pairs evaluated; TP 128, FN 921, TN 913, FP 38; accuracy 52.05%, sensitivity 12.20%, specificity 96.00%, precision 77.11%, and F1 21.07%.
- Matrix 1: all 959 mismatch pairs (921 FN and 38 FP) were included in the consolidated error-analysis workflow; text screening was completed across all 20 conditions. Veterinary adjudication remains pending.
- Optional JSON configuration: V1.3 prompt stored in `config/canine_thorax_v1_3.json`; local loader and five offline unit tests added. User ran the tests locally: 5 passed, 0 failed.

### Pending / limitations
- Veterinary adjudication of the Matrix 1 mismatch register remains pending. Text screening is not clinical adjudication; do not alter the baseline Gold Standard or original predictions without authorized approval.
- The Matrix 2 70-mismatch review also remains provisional pending authorized adjudication.
- Both evaluations are pilot comparisons and do not establish clinical readiness.
- Conditions with zero positive reference labels do not support a meaningful sensitivity estimate.

## Documentation update — 2026-11-03

- Updated README, requirements, environment example, ignore rules, decision log, testing log, weekly progress, and technical documentation to reflect Week 4.
- Git commits/tags remain deferred until project closeout.


## Week 4 optional task — JSON prompt configuration

### Added
- `src/week_04/optional_json_config/config/canine_thorax_v1_3.json` containing the existing V1.3 system prompt and configuration metadata.
- `src/week_04/optional_json_config/prompt_config_loader.py` to read and validate the JSON configuration and return the system prompt.
- `src/week_04/optional_json_config/test_prompt_config_loader.py` with offline unit tests.
- `src/week_04/optional_json_config/README.md` documenting scope and execution.

### Verified
- Five local unit tests passed: configuration load, prompt retrieval, missing file, invalid JSON, and missing required fields.
- No API calls, dataset processing, or LLM execution are part of this optional task.
- The existing Matrix 1 prompt integration and V1.3 prompt were not modified.

## Week 4 closeout — 2026-11-08

- Completed the Week 4 implementation, evaluation, quality checks, error-screening work, and optional JSON prompt-configuration task.
- Git commits and tags remain to be performed by the user after reviewing staged files and excluding confidential data.
