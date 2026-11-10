# Testing Log

This log distinguishes user-reported live tests, offline tests, and work that has not yet been verified. Do not infer a successful test from the existence of a script or output file.

| Week / Block | Component | Test / evidence | Result | Notes |
|---|---|---|---|---|
| 2 | `main.py` | Run against canine thorax workbook | Passed (user-reported) | Detected 20 condition columns and generated output workbook. |
| 2 | `main.py` | Inspect output layout | Passed (user-reported) | Visually matched the example structure. |
| 2 | `main.py` | `python main.py --help` | Passed (user-reported) | Input and optional output arguments displayed. |
| 2 | Week 2 scripts | Flake8 | Passed (user-reported) | Reported after line-length corrections. |
| 3 | V1.3 prompt loader | Load prompt and inspect condition keys | Passed (user-reported) | Prompt loaded; 20 conditions detected. |
| 4 / Block 1 | Data loader | Validate first 100 cases and Gold Standard | Passed (user-reported) | 100 cases, 20 conditions, 2,000 labels; LLM payload restricted to original report fields. |
| 4 / Block 2 | Prompt integration | Load V1.3 prompt | Passed (user-reported) | Prompt length reported as 8,710 characters; 20 condition keys. |
| 4 / Block 3 | LangChain/OpenAI | Single-case live API request (CaseID 1) | Passed (user-reported) | HTTP 200 and response returned. This was a billable API call. |
| 4 / Block 4 | Response validator | Valid response and invalid-format test cases | Passed (user-reported) | Checked exact keys, canonical order, missing/unexpected keys, invalid labels, markdown fences, non-object JSON, and duplicate keys. |
| 4 / Block 5 | Batch processor | Offline tests for checkpoint, restart, retry, and error logging | Passed (assistant-run offline tests) | No API request in these tests. |
| 4 / Block 5 | Live batch | Process first 100 cases | Passed (user-reported) | 100 successful predictions, zero final failures; one case needed a second application attempt. Transport-level retries may add HTTP attempts. |
| 4 / Block 6 | Matrix 2 evaluation | Compare 100-case predictions with approved Gold Standard | Completed (user-reported deliverable) | 2,000 labels; accuracy 96.50%, sensitivity 80.38%, specificity 97.88%; TP 127, FN 31, TN 1,803, FP 39. |
| 4 | Mismatch review | Review and reconcile all mismatches | Completed provisionally | 70 unique mismatches: 31 FN and 39 FP. Authorized adjudication is still pending. |
| 4 | Matrix 1 evaluation | Evaluate 100 cases × 20 conditions against the maintained reference labels | Completed | TP 128, FN 921, TN 913, FP 38; accuracy 52.05%, sensitivity 12.20%, specificity 96.00%, precision 77.11%, F1 21.07%. |
| 4 | Matrix 1 mismatch screening | Screen mismatch report text across all 20 conditions | Completed (text screening) | 959 mismatches: 921 FN and 38 FP. Screening is not veterinary adjudication. |
| 4 | JSON prompt configuration | `python -m unittest -v test_prompt_config_loader.py` from `src/week_04/optional_json_config` | Passed (user-reported) | Five tests passed locally; no API calls or LLM execution. |
| 4 | Authorized adjudication | Veterinary review of Matrix 1 and Matrix 2 mismatch registers | Pending | Do not revise baseline Gold Standard or predictions without approval. |

## Week 4 evaluation details (Matrix 2: Gold Standard vs LLM)

- Dataset: first 100 canine thorax cases (CaseID 1–100).
- Conditions: 20.
- Total binary labels: 2,000.
- Evaluation reference: approved Gold Standard.
- Confusion counts: TP 127, FN 31, TN 1,803, FP 39.
- Aggregate accuracy: 96.50%.
- Aggregate sensitivity: 80.38%.
- Aggregate specificity: 97.88%.
- Aggregate precision: 76.51%; F1: 78.40% (as recorded in the delivered Matrix 2 workbook, together with a Balanced Accuracy row of 89.13%).

These are aggregate pilot metrics. The label distribution is imbalanced, and sensitivity is not meaningful for conditions with no positive Gold Standard cases. The results do not establish clinical readiness.

## Test recording template

For each new test, record:
- Date:
- Component:
- Command / procedure:
- Expected result:
- Actual result:
- Status: Passed / Failed / Not tested:
- Error and resolution:
- Evidence / output filename:
- Related commit/tag:


## Week 4 optional JSON configuration — detailed test evidence

**Component:** `src/week_04/optional_json_config/prompt_config_loader.py`

**User-reported command (run from the optional task directory):**

```powershell
python -m unittest -v test_prompt_config_loader.py
```

**Actual result:** 5 tests passed, 0 failures.

| Test | Expected behavior | Result |
|---|---|---|
| `test_loads_v13_configuration` | Load metadata, V1.3 version, 20 condition keys, valid labels, and non-empty prompt | Passed |
| `test_load_system_prompt_returns_prompt_text` | Return the prompt string from JSON | Passed |
| `test_missing_configuration_raises_file_not_found` | Raise `FileNotFoundError` for a missing file | Passed |
| `test_invalid_json_raises_value_error` | Raise `ValueError` for malformed JSON | Passed |
| `test_missing_required_field_raises_value_error` | Reject configuration missing required fields | Passed |

**Scope limitation:** These tests verify local JSON configuration loading and validation only. They do not test API connectivity, LLM behavior, classification quality, or dataset processing.


## Week 5 — Claude Code rebuild: verification record (2026-11-10)

All Week 5 tests are offline. No live OpenAI API request was made during Week 5 development or verification (live testing was not approved). Results below were run by the assistant in the cloud environment (Python 3.13.18, Linux).

### Final test suite (authoritative)

| Check | Command | Result |
|---|---|---|
| Week 5 unit and integration tests | `PYTHONPATH=src python -m unittest discover -s src/week_05/tests -t src` | **338 tests passed**: 0 failures, 0 errors, 0 skipped |
| Network isolation | Same suite with socket connections blocked | 338 passed; **0 network connection attempts** |
| Code style | `python -m flake8 --max-line-length=100 src/week_05` | Clean |
| Real-data tests without data | `test_baseline_artifacts.py` with the baseline files absent | All 9 skipped with an explanatory message (no failure) |

The suite covers configuration and fail-fast checks; prompt integrity and byte-identical message construction (compared with Week 4 and with the request body LangChain would send); dataset loading and reference-label separation; response validation (outcomes and error messages identical to Week 4 on curated and randomised inputs); batch retries, checkpoints, interrupted runs and byte-identical JSONL output (compared with the Week 4 batch processor); metric calculations (identical to Week 4, including undefined values); both workbook layouts; and real-data verification.

Deliberate-deviation checks were run at each phase: known faults were injected at runtime (for example, changing the F1 edge case, reintroducing the Balanced Accuracy row, disabling the Matrix 2 ambiguity guard, reverting a Matrix 1 workbook wording) and the tests failed each time, confirming they detect regressions.

### Week 4 regression tests (unchanged code)

| Test | Result |
|---|---|
| `python src/week_04/test_response_validator.py` | Passed |
| `python src/week_04/test_batch_processor.py` | Passed |
| `src/week_04/matrix_1` unittest discovery (13 tests) | Passed |
| `src/week_04/matrix_1/tests` evaluator tests | Passed |
| `optional_json_config` loader tests (5 tests) | Passed |

### Real-data baseline verification

Performed on the delivered Week 4 artifacts held locally in the gitignored `data/` folder (never committed): the two input workbooks, the two Week 4 `predictions.jsonl` files and the two delivered evaluation workbooks. Their SHA-256 digests are checked before and after the tests to confirm they are unchanged. No artifact content is reproduced here.

| Workflow | Reproduced counts | Rates | Workbook comparison |
|---|---|---|---|
| Matrix 1 (original Vetology scores vs LLM) | TP 128, FN 921, TN 913, FP 38 | Accuracy 52.05%, sensitivity 12.20%, specificity 96.00%, precision 77.11%, F1 21.07% | Identical to the delivered Matrix 1 workbook in every value and format; excluded run-dependent cells: Execution Log B3, B4, B14 (input file names, generation time) |
| Matrix 2 (Gold Standard vs LLM) | TP 127, FN 31, TN 1,803, FP 39 | Accuracy 96.50%, sensitivity 80.38%, specificity 97.88%, precision 76.51%, F1 78.40% | Identical to the delivered Matrix 2 workbook except the two approved differences below; excluded run-dependent cells: Execution Log B3, B4 (input file names) |

Approved Matrix 2 workbook differences:
1. The Overall Summary "Balanced Accuracy" row is not produced (balanced accuracy is not part of the methodology). The comparison removes that row from an in-memory copy of the delivered workbook; the file itself is not changed.
2. Execution Log cell C8 states the failure-count source: "Source: prediction records only. No errors.jsonl was supplied, so failures recorded only in an errors file are not counted."

Further checks:
- Matrix 1 per-condition metrics are identical to the Week 4 `calculate_condition_metrics` output.
- Both reference-loading approaches select identical cases and labels on both input workbooks.
- The F1 edge case (TP = 0 with FP > 0 and FN > 0) occurs once in Matrix 2 (perihilar_infiltrate); F1 is blank, as in the delivered workbook.
- The Matrix 1 and Matrix 2 prediction files differ on 8 of 2,000 case-condition pairs (6 cases; 4 Positive→Negative and 4 Negative→Positive; both files contain 166 positive predictions). This is recorded as observed run-to-run variation; neither file was altered.

### Limitations of the Week 5 verification
- No live API run: classification behaviour of the rebuilt client was verified only by comparing the exact request content with Week 4.
- No `errors.jsonl` was supplied for either Week 4 run; failure counts are derived from prediction records only.
- Byte-level JSONL parity was tested with LF line endings; the Week 4 prediction files use Windows CRLF line endings (read correctly by Week 5).
- Real-data tests require the gitignored baseline files and are skipped elsewhere.
