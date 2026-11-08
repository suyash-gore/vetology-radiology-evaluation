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

## Week 4 evaluation details

- Dataset: first 100 canine thorax cases (CaseID 1–100).
- Conditions: 20.
- Total binary labels: 2,000.
- Evaluation reference: approved Gold Standard.
- Confusion counts: TP 127, FN 31, TN 1,803, FP 39.
- Aggregate accuracy: 96.50%.
- Aggregate sensitivity: 80.38%.
- Aggregate specificity: 97.88%.

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
