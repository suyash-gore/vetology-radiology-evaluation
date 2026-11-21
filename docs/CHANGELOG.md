# Changelog

This file records meaningful implementation and documentation changes. Week 4 entries reflect the verified project state as of 2026-11-08; Week 5 development closeout was recorded on 2026-11-10, followed by Windows portability and live-execution updates on 2026-11-12.

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


## Week 5 — Claude Code rebuild (2026-11-10)

Independent rebuild of the Week 4 application under `src/week_05/`, developed with Claude Code on branch `week-05/claude-code-rebuild`. `src/week_04/` was not modified. At the 2026-11-10 development closeout, no live OpenAI API request had been made; separate live workflow executions were completed on 2026-11-12 and are recorded below.

### Added (by phase)
- **Phase 1 — Foundation and configuration** (`config.py`, `conditions.py`, `cli.py`): single source for the 20 condition keys and `Positive`/`Negative`; Week 4 model settings and `.env` handling; separate Matrix 1 and Matrix 2 workflow configurations with isolated outputs under `outputs/week_05/`.
- **Phase 2 — Prompt and LLM client** (`prompts/`, `llm_client.py`): byte-identical copy of Canine Thorax Master Prompt V1.3 guarded by SHA-256 checks; system and human messages reproduced byte-for-byte from Week 4, including `[Not provided]` for empty fields; payload restricted to the three original report fields.
- **Phase 3 — Dataset loading** (`dataset_loader.py`): one loader for both workflows reproducing Week 4 cleaning and validation; reference labels stored separately and read-only.
- **Phase 4 — Response validation** (`response_validator.py`): Week 4 output contract with identical error messages.
- **Phase 5 — Batch execution** (`batch_runner.py`, `jsonl_store.py`): Week 4 retry and checkpoint semantics and byte-identical JSONL records.
- **Phase 6 — Evaluation and workbooks** (`evaluation/`): shared Week 4 metric engine; separate Matrix 1 and Matrix 2 reference loaders and workbook generators; workbook comparison tool; verification against the delivered Week 4 baseline artifacts.
- CLI commands `config`, `validate-data`, `batch`, `evaluate`, `compare-references` (`python -m week_05`).
- 338 offline tests, including real-artifact tests that run only when the gitignored baseline files are present.

### Changed relative to Week 4 (all approved)
- Missing API key or invalid settings are detected before any classification instead of producing a failure record per case; a configuration error during a run stops the run.
- One OpenAI client is reused for the whole batch instead of one per case (identical request configuration).
- Crash recovery: if a JSONL file ends without a newline (interrupted write), a newline is written before appending, so the new record stays readable. Week 4 appended onto the partial line, which made that case be reclassified on every later run.
- Matrix 1 batch processes exactly 100 cases with no configurable limit; Matrix 2 keeps `--limit`.
- Evaluation skips only prediction lines that are not valid JSON (interrupted writes), listing each in the Execution Log; all other invalid content is still rejected.
- Matrix 1 workbook follows the delivered Matrix 1 baseline layout and wording; Matrix 2 workbook follows the delivered Matrix 2 baseline structure except the two approved differences below.
- Matrix 2 reference loading uses the Week 4 Matrix 2 batch-loader rules with an ambiguity guard.

### Verified
- Matrix 1 reproduced from the baseline artifacts: TP 128, FN 921, TN 913, FP 38; workbook identical to the delivered Matrix 1 workbook (input file names and generation timestamp excluded).
- Matrix 2 reproduced: TP 127, FN 31, TN 1,803, FP 39; workbook identical to the delivered Matrix 2 workbook except: (1) the Overall Summary "Balanced Accuracy" row is not produced; (2) Execution Log cell C8 states the failure-count source (input file names excluded).
- 338 tests passed with network access blocked: 0 failures, 0 skipped, 0 connection attempts; flake8 clean. Week 4 regression tests pass unchanged.

### Dependencies
- `requirements.txt` now pins every directly imported package: added `langchain-core==1.7.7` (imported by `llm_client.py`), `openai==3.49.0` and `httpx==0.28.1` (imported by the offline tests). These are the versions already installed and tested; no other version changed.

### Checkpoint commits
`d62470f` (Phases 1–3), `f670f26` (Phase 4), `dfdd3ec` (Phase 5), `ecc8153` (Phase 6 interim), `874aaea` (Phase 6 final), followed by this documentation and dependency update.

## Documentation corrections — Week 5 closeout (2026-11-10)

Corrected statements found during the Week 5 documentation audit. Historical Week 4 facts were kept; only inaccurate descriptions were fixed.
1. Matrix 1 was described in `project_documentation.md` as "original report vs second AI report… pending"; it is original Vetology scores vs LLM and was completed in Week 4.
2. Section numbering in `project_documentation.md` was inconsistent.
3. The delivered Matrix 2 workbook has five sheets (not three) and includes precision, F1 and a Balanced Accuracy row.
4. The README test command `unittest discover -s src/week_04` runs no tests; working commands are now documented.
5. The README repository layout listed a non-existent `optional_json_config/README.md` and omitted `matrix_1/` and `week_05/`.
6. The Week 4 batch was described as logging "failed attempts" separately; it writes one record per case that fails all attempts, and logs individual attempt failures to the console only.
7. Workbook naming: the delivered Matrix 1 workbook is `Evaluation_Workbook_v1.xlsx` (code default `matrix1_evaluation_workbook.xlsx`) and was produced by an evaluator variant not in the repository; no Matrix 2 evaluator source exists.
8. The Python environment now records both Week 4 (3.14.6, Windows) and Week 5 (3.13.18, Linux) versions.
9. `requirements.txt` did not declare `langchain-core`, `openai` or `httpx`, which are imported directly.


## Week 5 portability corrections — 2026-11-12

- Removed the forced LF newline override from the JSONL writer. Appends now use the platform-native text newline translation, preserving byte-level compatibility with Week 4 on the same platform (including CRLF on Windows).
- Made JSONL raw-byte expectations platform-aware while retaining checks that pre-existing file bytes are not rewritten during interrupted-write recovery.
- Closed synthetic test workbooks explicitly and added garbage collection before temporary-directory cleanup in the Week 4 parity test fixture, avoiding Windows file-handle cleanup failures without modifying Week 4.
- Corrected the evaluation package description and clarified that the 338-test development result used available baseline artifacts; nine artifact tests skip when those gitignored files are absent.
- The complete local Windows suite subsequently ran on 2026-11-12: 338 tests, 329 passed, 9 skipped, 0 failures and 0 errors. The 9 skips were real-artifact tests requiring baseline files absent from the local test location. Flake8 was not rerun locally; the earlier clean flake8 result applies to the Linux development environment.


## Week 5 local Windows verification and live execution — 2026-11-12

### Verified
- Completed the full local Windows Week 5 test suite on Windows 11 with Python 3.14.6: 338 tests run, 329 passed, 9 skipped, 0 failures and 0 errors. The 9 skipped tests require gitignored baseline artifacts that were not present in the local test location.
- Windows JSONL compatibility tests passed as part of the full suite. The JSONL writer uses platform-native newline translation, and interrupted-write recovery preserves existing file bytes.
- Matrix 1 live batch: 100 cases succeeded, 0 final failures. Evaluation counts: TP 126, FN 923, TN 916, FP 35; accuracy 52.10%, sensitivity 12.01%, specificity 96.32%, precision 78.26%, F1 20.83%.
- Matrix 2 live batch: 100 cases succeeded, 0 final failures. Evaluation counts: TP 126, FN 32, TN 1,806, FP 36; accuracy 96.60%, sensitivity 79.75%, specificity 98.05%, precision 77.78%, F1 78.75%.
- Both evaluation workbooks were generated and visually reviewed. Both `compare-references` checks passed: batch and evaluation loaders selected identical cases, order and labels for each workflow.
- Live batch commands made OpenAI API requests. Evaluation and reference-loader comparison commands did not make API requests. Reference labels were not sent to the model; input remained restricted to the three original radiologist report fields.

### Scope note
- Detailed prediction-level error analysis and veterinary adjudication were not undertaken as part of this Week 5 closeout. The Matrix 1 and Matrix 2 evaluations use different reference-label sets and should be interpreted separately.
- Flake8 was not rerun on the local Windows machine; the previously recorded clean result is from the Linux development environment.


## Week 7 — Gemini model evaluation closeout (2026-11-21)

An independent Google Gemini evaluation pipeline was built under `src/week_07/` on branch `week-07/gemini-model-evaluation`. `src/week_04/` and `src/week_05/` were not modified. Week 7 does not import `week_04` or `week_05` at runtime; only the parity tests do.

### Added
- **Independent implementation** (`src/week_07/`): configuration and workflow specs, a byte-identical V1.3 prompt and integrity-checked loader, a LangChain Gemini client, dataset loading, response validation, batch execution and JSONL checkpointing, the run manifest, output isolation, evaluation and comparison.
- **Gemini integration:** `ChatGoogleGenerativeAI` from `langchain-google-genai`, on the Google GenAI SDK (`google-genai`). Settings: model `gemini-3.8-flash`, temperature 0, 90-second timeout, `application/json` response MIME type, no response schema. The settings come from `GEMINI_MODEL`, `GEMINI_TEMPERATURE` and `GEMINI_TIMEOUT_SECONDS`. `GOOGLE_API_KEY` must be set; the SDK reads it from the environment and Week 7 never stores or prints it. `GEMINI_MAX_RETRIES` is refused.
- **Retry and error classification** (`error_policy.py`, `batch_runner.py`): one SDK transport attempt per application attempt and up to 2 application attempts per case (`batch --max-attempts`). Errors are classified by SDK exception class and HTTP status code; exception messages are never parsed:
  - fatal (HTTP 400/401/403/404 and configuration errors): not retried, the batch stops, and the case stays pending;
  - transient (HTTP 408/429/500/502/503/504 and network timeouts or network errors): bounded exponential backoff before the next attempt (base 2 s, factor 2, maximum 30 s; 2 s with the default two attempts);
  - all other errors, including validation failures: retried immediately, as in Week 5.
- **Separate Matrix 1 and Matrix 2 workflows:** each has its own input, reference labels, `outputs/week_07/matrix_1|matrix_2/` folder, run manifest, evaluation workbook and comparison folder. The isolation guard refuses writes outside `outputs/week_07/` and writes into `outputs/week_04/`, `outputs/week_05/`, `data/`, `src/`, `.git` or the other workflow's folders.
- **Prompt integrity:** Canine Thorax Master Prompt V1.3 is used byte-for-byte. It is the same prompt as Weeks 4/5, with no Gemini-specific wording. Loading fails if the file SHA-256 or the stripped-text SHA-256 changes.
- **Run manifest** (`run_manifest.json`, one per workflow): it records provenance without changing the Week 4/5 JSONL record schema. Contents: workflow, provider, model, temperature, prompt version and digests, input file name, digest and worksheet; and for each run, timestamps, status, retry policy, package versions and summary counts. A resumed run with a different identity is refused. The manifest never contains the API key, report text or reference labels.
- **Evaluation** (`python -m week_07 evaluate`): the Week 5 metric engine, reference loaders and Matrix 1/Matrix 2 workbook layouts, applied to the Gemini predictions.
- **OpenAI vs Gemini comparison** (`python -m week_07 compare`): reads the saved Week 5 OpenAI predictions and the Week 7 Gemini predictions as read-only sources (SHA-256-checked before and after) and writes a six-sheet workbook per workflow: Overall Comparison, Condition Comparison, Model Agreement, Case Disagreements, Execution Log, Metric Definitions. Error-log records are classified as superseded (a later success exists) or unresolved; any unresolved failure makes the comparison refuse.
- CLI commands `config`, `validate-data`, `batch`, `evaluate`, `compare-references`, `compare` (`python -m week_07`).
- 288 offline tests (Gemini SDK exercised through a mock transport), including opt-in local artifact tests.

### Verified
- Week 7 tests (local): 288 run; 282 passed, 6 skipped (1 Windows symlink-privilege test and 5 opt-in local artifact tests), 0 failures and 0 errors. Flake8 clean on `src/week_07`.
- Local artifact tests (opt-in): 6 run; 4 passed, 2 skipped. The real Matrix 1 error log (Week 5 OpenAI run) held 100 historical failure records, all superseded by later successful predictions, with zero unresolved. The reference loaders agreed on the real inputs. The replay reproduced the Week 5 counts for both workflows.
- Week 5 regression: 338 run; 329 passed, 9 skipped (baseline artifacts absent from the local test location), 0 failures and 0 errors.
- `python -m week_07 --help` and `config` for both workflows completed successfully.
- Live Gemini batches: 100 cases × 20 conditions (2,000 paired labels) per workflow, zero unresolved final failures.
  - Matrix 1 (original Vetology reference): TP 96, FN 953, TN 924, FP 27; accuracy 51.00%, sensitivity 9.15%, specificity 97.16%, precision 78.05%, F1 16.38%. Agreement with Week 5 OpenAI: 1,940/2,000 (97.00%), 60 disagreements.
  - Matrix 2 (Gold Standard reference): TP 102, FN 56, TN 1,822, FP 20; accuracy 96.20%, sensitivity 64.56%, specificity 98.91%, precision 83.61%, F1 72.86%. Agreement with Week 5 OpenAI: 1,944/2,000 (97.20%), 56 disagreements.
- Both six-sheet comparison workbooks were generated and inspected, and their aggregates reconciled with the CLI results.
- The two run manifests (`outputs/week_07/matrix_1/run_manifest.json`, `outputs/week_07/matrix_2/run_manifest.json`) are kept as execution-metadata artifacts. Predictions, error logs and workbooks stay local and gitignored.

### Dependencies
- Added `google-genai==2.31.0`, which `error_policy.py` and the offline tests import directly. This is the locally tested version, within the `langchain-google-genai==4.4.2` requirement (`>=2.20.0,<3`). Its `httpx>=0.28.1,<1` requirement is met by the existing `httpx==0.28.1` pin.
- `langchain-google-genai==4.4.2` is now documented as a Week 7 dependency as well as a Week 2 one. No other version changed.

### Scope note
- These are pilot results on one 100-case sample. Matrix 1 and Matrix 2 use different reference-label sets and are reported separately. Veterinary adjudication was outside the scope of this closeout.
