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
| 4 | Matrix 1 | Original radiologist report vs. second AI report | Not confirmed / pending | Separate Week 4 assignment requirement. |
| 4 | JSON prompt configuration | Load prompt from JSON configuration | Not implemented / pending | Optional “as time permits” task. |
| 4 | Authorized adjudication | Final review of 70 mismatches | Pending | Do not revise baseline Gold Standard or predictions without approval. |

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
