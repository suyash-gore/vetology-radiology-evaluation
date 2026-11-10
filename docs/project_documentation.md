# Vetology Radiology Evaluation — Technical Documentation

This document is the working technical record for the Vetology training project. It distinguishes implemented and tested functionality from pending tasks, and distinguishes three things that are easy to confuse:

- **the original Week 4 implementation** (`src/week_04/`) and its behaviour;
- **the delivered Week 4 baseline workbooks** (the evaluation files actually produced in Week 4, some by code not in the repository);
- **the independent Week 5 rebuild** (`src/week_05/`) and its approved differences.

Statements corrected during the Week 5 closeout are marked *(corrected in Week 5 closeout)*. Do not describe untested integrations or unfinished functionality as complete.

## 1. Project background and objectives

The project evaluates whether LLMs can classify diagnostic conditions from veterinary radiology reports. The workflow includes:
- preparing and validating report datasets;
- maintaining manual/approved reference labels separately;
- designing condition-specific prompts;
- calling LLMs from Python;
- validating structured model output;
- comparing predictions against reference labels;
- reviewing errors and documenting limitations.

The training program ultimately covers three input datasets, application rebuilding, presentations, and a research paper. The current implementation is the canine thorax application (Week 4) and its independent rebuild (Week 5).

## 2. Dataset overview and data handling

### 2.1 Evaluation sample
- Dataset: canine thorax radiology reports.
- Sample: CaseID 1–100 (100 cases).
- Conditions: 20; reference labels: 2,000 binary labels per workflow.
- Evaluation convention: `Positive` / `Negative`.
- Two independent evaluation workflows, each with its own input and reference labels:
  - **Matrix 1 — original Vetology scoring vs LLM:** `Vetology_Matrix1_First100_Encoded.xlsx`; the 20 original Vetology condition scores are the reference labels.
  - **Matrix 2 — Gold Standard vs LLM:** `1_canine_thorax_gold_standard_score_draft.xlsx`; the 20 approved Gold Standard scores are the reference labels.

Reference labels are kept separate from LLM inputs and prediction outputs. Existing legacy Abnormal/Normal labels are not treated as ground truth. The separate manually scored dataset is not an input to either workflow.

### 2.2 LLM input boundary
Only the original radiologist report fields are sent to the model:
- `Findings (original radiologist report)`
- `Conclusions (original radiologist report)`
- `Recommendations (original radiologist report)`

CaseID is retained locally for tracking and is not sent to the LLM. AI-generated report fields, the Original Radiologist field and all reference labels are excluded from LLM input. *(Corrected in Week 5 closeout: this section previously described the AI-generated report as part of a "separate Matrix 1 comparison"; Matrix 1 compares LLM predictions with the original Vetology scores.)*

The report fields are identical in both input workbooks, so both workflows send the model the same report text; only the reference labels differ.

### 2.3 Classification convention
The V1.3 prompt requires all 20 conditions to be independently classified using exact `Positive` or `Negative` labels. Important rules include:
- Possible or suspected target condition is Positive.
- A condition not mentioned is Negative under the binary output convention.
- A recommendation to investigate alone does not make a condition Positive unless the report describes it as possible/suspected.
- Explicit negation remains Negative unless a separate unresolved positive statement requires review.
- RTM means redundant tracheal membrane; do not infer it from tracheal narrowing or collapse.
- `diseased_lungs` is independent and is not automatically derived from other labels.

The exact prompt is maintained under `src/week_04/prompts/` and copied byte-for-byte to `src/week_05/prompts/`.

## 3. Development environment

| | Week 4 | Week 5 rebuild |
|---|---|---|
| OS | Windows 11 | Linux (Claude Code cloud environment) |
| Python | 3.14.6 (reported during setup) | 3.13.18 |
| IDE / tool | Visual Studio Code | Claude Code |
| Virtual environment | `.venv` (also previously referred to as `venv1`) | Environment packages installed from `requirements.txt` |

Both use `gpt-4.1-mini` through `langchain-openai`, with `python-dotenv` for configuration. `requirements.txt` pins every directly imported package (`openpyxl`, `langchain-openai`, `langchain-core`, `openai`, `httpx`, `python-dotenv`, `flake8`) and the retained Week 2 demonstration integrations. *(Corrected in Week 5 closeout: `langchain-core`, `openai` and `httpx` were previously used without being declared.)*

## 4. Week 2 implementation — historical scaffold

The Week 2 scaffold used `argparse` for input and optional output paths and `openpyxl` for workbook processing. It detected condition headers after the first eight metadata columns and generated a workbook matching the supplied confusion-matrix example structure.

The scaffold's output layout was verified, but the Week 2 scaffold did not calculate TP, FN, TN, or FP counts. Its confusion-matrix column layout (including "Ground Truth Check" and "Radiologist Agreement Rate") reappears in the delivered Matrix 2 workbook.

Separate Week 2 LangChain demonstration scripts were created for OpenAI, Gemini, and Hugging Face. Their existence does not establish that every provider integration was live-tested.

## 5. Week 3 prompt development

The V1.3 master prompt was prepared for 20 canine thorax conditions. The prompt loader test reported 8,710 characters and 20 condition keys.

The project uses strict JSON output with exactly the expected condition keys and exact `Positive` / `Negative` values. No explanatory prose is expected in the model response.

## 6. Week 4 application architecture (original implementation)

### 6.1 Data loaders
`src/week_04/week4_block1_data_loader.py` (Matrix 2) and `src/week_04/matrix_1/matrix1_data_loader.py` (Matrix 1) load the first 100 cases, validate the original report fields and condition labels, and keep reference labels separately for evaluation. The LLM payload contains only the three original radiologist report fields.

### 6.2 Prompt loader
`src/week_04/prompts/` contains the V1.3 prompt and prompt-loading module.

### 6.3 LLM client
`src/week_04/llm_client.py` uses LangChain's `ChatOpenAI`. Configuration is read from environment variables: `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4.1-mini`), `OPENAI_TEMPERATURE` (default `0`), `OPENAI_TIMEOUT_SECONDS` (default `90`), `OPENAI_MAX_RETRIES` (default `2`). The root `.env` is loaded with `python-dotenv`. `single_case_test.py` was used for a live single-case test (HTTP 200).

### 6.4 Structured response validation
`src/week_04/response_validator.py` validates: a syntactically valid JSON object; exactly the 20 expected keys; no duplicate keys; exact `Positive`/`Negative` values; no markdown fences or extra prose. Key order in the response is not enforced; the validated output is returned in canonical order.

### 6.5 Batch processing
`src/week_04/batch_processor.py`, with `run_batch.py` (Matrix 2) and `matrix_1/run_matrix1_batch.py` (Matrix 1):
- processes cases sequentially and sends only the restricted report payload;
- validates each response;
- writes successful validated predictions to `predictions.jsonl`;
- makes up to two application-level attempts per case; when a case fails all attempts, writes one failure record to `errors.jsonl` (failures of individual attempts are logged to the console only) *(corrected in Week 5 closeout: previously described as writing "failed attempts" to the errors file)*;
- skips already completed valid cases on restart and retries failed cases on a later run.

The live 100-case batch completed with 100 successful predictions and zero final failures; one case required a second application-level attempt. LangChain transport-level retries may create additional HTTP attempts.

## 7. Week 4 evaluation and delivered baseline workbooks

### 7.1 Matrix 2 — Gold Standard vs LLM

| Metric | Value |
|---|---:|
| Total labels | 2,000 |
| TP / FN / TN / FP | 127 / 31 / 1,803 / 39 |
| Accuracy | 96.50% |
| Sensitivity | 80.38% |
| Specificity | 97.88% |
| Precision | 76.51% |
| F1 | 78.40% |

No Matrix 2 evaluator source exists in the repository; the workbook was produced outside it. The delivered workbook, `Evaluation Workbook v2.xlsx`, has **five** sheets: Overall Summary, Condition Summary, Case Predictions, Confusion Matrix, and Execution Log. Its Overall Summary reports micro metrics (including precision, F1 and a Balanced Accuracy row of 89.13%), evaluation counts and batch details; it contains no macro metrics. *(Corrected in Week 5 closeout: previously listed as three sheets.)*

### 7.2 Matrix 1 — original Vetology scores vs LLM

| Metric | Value |
|---|---:|
| Total pairs | 2,000 |
| TP / FN / TN / FP | 128 / 921 / 913 / 38 |
| Accuracy | 52.05% |
| Sensitivity | 12.20% |
| Specificity | 96.00% |
| Precision | 77.11% |
| F1 | 21.07% |

Matrix 1 was completed in Week 4 using `src/week_04/matrix_1/` (a fresh 100-case batch and `matrix1_evaluator.py`). *(Corrected in Week 5 closeout: an earlier section described Matrix 1 as an original-report vs AI-report comparison whose generation "remains pending".)*

The delivered workbook, `Evaluation_Workbook_v1.xlsx` (code default name `matrix1_evaluation_workbook.xlsx`), has six sheets: Overall Summary, Condition Summary, Case Predictions, Confusion Matrix, Execution Log, Metric Definitions. Its numbers match the committed evaluator exactly, but it was produced by a variant of the evaluator that is not in the repository: compared with the committed code it has 10 different fixed wordings, row-1 height 28 (code: 30), Overall Summary column C width 55 (code: 58) and a dark font colour on the Overall Summary header row.

The 959 Matrix 1 mismatches (921 FN and 38 FP) were consolidated into the error-analysis workflow and screened across all 20 conditions. Text screening is not veterinary adjudication: a mismatch between report text and a reference label does not by itself establish that the reference label is wrong.

### 7.3 Mismatch review and adjudication
There are 70 unique Matrix 2 mismatches (31 FN, 39 FP), reviewed provisionally and consolidated in `vetology_week4_master_adjudication_register.xlsx`. The original Block 6 Mismatch Review was used as the authoritative source for Gold Standard label, prediction and mismatch type, after a condition-specific `diseased_lungs` review workbook was found to contain inconsistent labels.

The registers are review aids, not approved replacement reference labels. Authorized adjudication is pending. If a reviewer approves corrections, preserve the original baseline and create a separately versioned adjudicated reference before recalculating metrics.

## 8. Week 4 optional task — JSON prompt configuration

### 8.1 Purpose and scope
The optional assignment asks the application to read prompts from a JSON configuration file. It was implemented as an isolated module under `src/week_04/optional_json_config/`, using the existing V1.3 prompt without revision.

### 8.2 Files
- `config/canine_thorax_v1_3.json` — prompt metadata, the 20 condition keys, valid labels, and the V1.3 system prompt text.
- `prompt_config_loader.py` — reads and validates the JSON file and returns the system prompt.
- `test_prompt_config_loader.py` — offline unit tests.
- The module README is included only in the delivery zip `Vetology_Week4_Optional_JSON_Prompt_Config.zip`; it is not a separate file in the repository.

### 8.3 Execution boundary
The module only reads and validates a local JSON configuration. It does not call an API, execute an LLM, load the dataset, generate predictions, or modify the Matrix 1 workflow.

### 8.4 Test result
`python -m unittest -v test_prompt_config_loader.py` from `src/week_04/optional_json_config`: 5 tests passed (user-reported in Week 4; also passing in the Week 5 regression run).

## 9. Technical decisions

Refer to `DECISION_LOG.md`. Week 4 decisions include Positive/Negative labels only, reference labels maintained separately, restricted original-report-only LLM input, exact JSON schema validation, sequential checkpointed batch execution, and preservation of baseline results pending adjudication. Week 5 decisions are D-020 to D-042.

## 10. Week 5 rebuild — architecture and behaviour

### 10.1 Scope and process
The Week 4 application was rebuilt independently under `src/week_05/` with Claude Code, in six phases, each reviewed and committed on branch `week-05/claude-code-rebuild`:

| Phase | Content | Checkpoint |
|---|---|---|
| 1 | Foundation and configuration | `d62470f` (with phases 2–3) |
| 2 | Prompt integration and LLM client | `d62470f` |
| 3 | Dataset loading and reference-label separation | `d62470f` |
| 4 | Response validation | `f670f26` |
| 5 | Batch execution, retries, checkpoints | `dfdd3ec` |
| 6 | Evaluation, workbooks, baseline verification | `ecc8153` (interim), `874aaea` (final) |

`src/week_04/` was not modified. Week 5 does not import Week 4 at runtime; Week 4 is used only in parity tests. No live OpenAI API request was made during Week 5.

### 10.2 Architecture

| Module | Responsibility |
|---|---|
| `config.py` | Model settings from the environment and `.env`; per-workflow configuration (inputs, reference description, outputs, case-count rules) |
| `conditions.py` | The 20 condition keys in canonical order; `Positive` / `Negative` |
| `prompts/` | Byte-identical V1.3 prompt and integrity-checked loader |
| `llm_client.py` | Message construction and the OpenAI client |
| `dataset_loader.py` | Batch input loading; report fields and reference labels kept separate |
| `response_validator.py` | V1.3 output contract |
| `batch_runner.py`, `jsonl_store.py` | Batch execution, retries, checkpoints, JSONL records |
| `evaluation/metrics.py` | Shared metric engine |
| `evaluation/reference_loader.py` | Per-workflow evaluation reference loaders |
| `evaluation/reconcile.py` | Prediction-file validation and CaseID alignment |
| `evaluation/matrix1_workbook.py`, `evaluation/matrix2_workbook.py` | Independent workbook generators |
| `evaluation/workbook_compare.py` | Cell-by-cell workbook comparison (values and formatting) |
| `cli.py`, `__main__.py` | `python -m week_05` commands: `config`, `validate-data`, `batch`, `evaluate`, `compare-references` |

### 10.3 Workflows and data separation
- Matrix 1 and Matrix 2 have separate configurations, inputs, reference labels, prediction files, output folders (`outputs/week_05/matrix_1`, `outputs/week_05/matrix_2`) and workbooks. Week 5 refuses to write into the other workflow's folder or into `outputs/week_04/`, and refuses to evaluate predictions taken from the other workflow's folder.
- The batch loader reproduces Week 4 cleaning and validation: `Sheet1`, columns located by header name, rows in worksheet order, blank-CaseID rows skipped, duplicate CaseIDs rejected, text trimmed, labels exactly `Positive`/`Negative` after trimming, first 100 cases. Matrix 1 requires exactly 100 cases; Matrix 2 warns when fewer are found.
- Cases expose only `findings`, `conclusions` and `recommendations` to the classifier. Reference labels are held in a separate read-only structure and never passed to the batch runner.

### 10.4 Prompt integrity and LLM configuration
- The V1.3 prompt file is byte-identical to Week 4 (8,715 bytes; SHA-256 `31a7dab6…`). The text sent to the model is the stripped file (8,710 characters; SHA-256 `97ad5b74…`). Loading fails if either digest changes.
- Messages are identical to Week 4: the V1.3 system message, and a human message with a fixed instruction and `FINDINGS:` / `CONCLUSIONS:` / `RECOMMENDATIONS:` sections, where an empty field becomes `[Not provided]`. The request body LangChain would send was verified identical to Week 4.
- Settings: `gpt-4.1-mini`, temperature 0, 90-second timeout, 2 LangChain transport retries; 2 application-level attempts per case. One client is reused for the whole batch.
- The API key and settings are validated before any classification; the key is never stored, printed or passed explicitly (LangChain reads it from the environment).

### 10.5 Response validation
Same contract and error messages as Week 4: a non-blank string containing exactly one JSON object; no duplicate keys at any depth; exactly the 20 keys; values exactly `Positive` or `Negative`. Any key order is accepted; output is in canonical order. Validation never sees CaseIDs or reference labels.

### 10.6 Batch execution, retries, checkpoints and JSONL
- Success record: `case_id`, `status` ("success"), `attempts`, `completed_at_utc`, `predictions`. Failure record (`errors.jsonl`): `case_id`, `status` ("failed"), `attempts`, `failed_at_utc`, `error`. Field order, UTC ISO-8601 timestamps and serialisation are byte-identical to Week 4; no fields were added.
- A case is skipped when `str(case_id)` already has a valid success record. Invalid checkpoint lines are ignored with a warning and the case is classified again.
- Each case gets up to 2 attempts (classifier call plus validation), with no wait between attempts. If all fail, one failure record is written and the batch continues. Failed cases are retried on a later run; stale failure lines are kept (Week 4 behaviour).
- Approved improvements: configuration errors stop the run before or during classification instead of producing a failure per case; after an interrupted write (file not ending with a newline), a newline is written before appending, so the next record stays readable.

### 10.7 Evaluation methodology (shared by both workflows; unchanged from Week 4)
- TP, FN, TN, FP per condition; accuracy, sensitivity, specificity, precision and F1. A ratio with a zero denominator is undefined and left blank, never treated as zero.
- F1 is undefined when precision or sensitivity is undefined or both are zero — so TP = 0 with FP > 0 and FN > 0 gives an undefined F1 (preserved Week 4 behaviour, documented, not corrected).
- Micro averages: counts summed across conditions, then the formulas. Macro averages (Matrix 1 only): unweighted mean of the defined condition values.
- Balanced accuracy is not computed.
- Prediction files must contain only successful records with exactly the 20 keys and valid labels, one per CaseID, and the CaseID sets of predictions and reference labels must match exactly. Only lines that are not valid JSON (interrupted writes) are skipped; each is listed in the Execution Log. Matrix 1 additionally requires exactly 100 cases; Matrix 2 has no case-count rule.

## 11. Week 5 workbooks and baseline verification

### 11.1 Baseline artifacts
The delivered Week 4 artifacts — the two input workbooks, the two Week 4 prediction files and the two delivered evaluation workbooks — were inspected and used for verification. They are confidential, held locally in the gitignored `data/` folder, never committed, and checked by SHA-256 before and after testing. This document reproduces no artifact content.

Inspection findings:
- Both input workbooks contain exactly 100 populated cases (CaseIDs 1–100, whole numbers, no duplicates, labels without stray spaces). The Gold Standard workbook's sheet extends to row 4,000, but all rows after the 100 cases are blank.
- The delivered Matrix 1 workbook was built from the Matrix 1 inputs and Matrix 1 predictions; the delivered Matrix 2 workbook from the Gold Standard inputs and Matrix 2 predictions.
- Both Week 4 prediction files contain 100 successful, valid records; one Matrix 2 case took two attempts. They use Windows CRLF line endings.
- The two prediction files differ on 8 of 2,000 case-condition pairs (6 cases), documented as run-to-run variation.
- No `errors.jsonl` file was available for either run.

### 11.2 Matrix 1 evaluation
- Reference loading reproduces the Week 4 `load_matrix1_inputs` rules: first worksheet, all rows, `int()` CaseIDs, labels not trimmed.
- Workbook: layout and wording of the delivered Matrix 1 workbook (decision D-038), including the existing "Gold Standard" wording for the Matrix 1 reference labels.

### 11.3 Matrix 2 reference loading — inference and ambiguity guard
The original Matrix 2 evaluator is not in the repository, so its loading rules were inferred. On the delivered inputs, the Week 4 Matrix 2 batch-loader rules (`Sheet1`, first 100 populated rows, trimmed labels) and the Week 4 evaluator-style rules (first sheet, all rows, `int()` CaseIDs, no trimming) select identical cases and labels, so the artifacts cannot distinguish them. Week 5 uses the batch-loader rules and **rejects as ambiguous** any workbook on which the two approaches would differ (extra populated rows, padded labels, non-integer CaseIDs, a different first sheet, or either approach failing), listing the differences. `python -m week_05 compare-references` shows the comparison.

### 11.4 Matrix 2 workbook and approved differences
The Matrix 2 workbook reproduces the delivered structure: five sheets, micro metrics only, Week 2 confusion-matrix columns, batch details and a per-case table derived from the prediction records, cases sorted by CaseID, and run-specific wording generated from the results. Two approved differences:
1. The Overall Summary **Balanced Accuracy row is not produced**.
2. Execution Log cell **C8** states the failure-count source: failures are counted from prediction records only, because no `errors.jsonl` was supplied.

### 11.5 Results

| | Matrix 1 | Matrix 2 |
|---|---|---|
| TP / FN / TN / FP | 128 / 921 / 913 / 38 | 127 / 31 / 1,803 / 39 |
| Accuracy / Sensitivity / Specificity / Precision / F1 | 52.05 / 12.20 / 96.00 / 77.11 / 21.07 % | 96.50 / 80.38 / 97.88 / 76.51 / 78.40 % |
| Workbook vs delivered baseline | Identical (excluding input file names and generation time) | Identical except the two approved differences (excluding input file names) |

## 12. Testing and validation

- **Week 4:** see `testing_log.md` for the recorded data-loader, prompt, live single-case, validator, offline batch, live batch, evaluation and JSON-configuration results.
- **Week 5:** 338 offline tests pass with 0 failures, 0 skipped and 0 network connection attempts; flake8 is clean (`--max-line-length=100`). The Week 4 regression tests pass unchanged. Deliberate-deviation checks confirmed that the tests detect regressions. Commands are listed in the README; results in `testing_log.md`.

## 13. Problems, resolutions, and limitations

### Recorded resolutions
- Week 4: the mismatch register was reconciled against the original Block 6 source after inconsistencies were found in a condition-specific review workbook.
- Week 5: a Week 4 defect that corrupted the next JSONL record after an interrupted write was fixed in the rebuild (approved); nine documentation inconsistencies were corrected (see `CHANGELOG.md`).

### Limitations
- The evaluation uses 100 reports and 2,000 labels per workflow from one dataset; class imbalance affects aggregate accuracy; sensitivity is not meaningful for conditions with zero positive reference cases. The results do not establish clinical readiness.
- Mismatch review is provisional until authorized veterinary adjudication.
- Matrix 2 reference-loading rules are inferred from the delivered artifacts; ambiguous workbooks are rejected rather than resolved.
- The delivered Matrix 1 workbook was produced by an evaluator variant not in the repository; the delivered Matrix 2 workbook was created by an external tool and modified four days later, so its history cannot be fully established.
- No Week 4 `errors.jsonl` was available; failure counts are derived from prediction records only.
- Model outputs vary between runs (8 of 2,000 pairs differ between the two Week 4 runs).
- No live API run was made in Week 5; the rebuilt client's request content was verified identical to Week 4 instead.
- Byte-level JSONL parity was tested with LF line endings only; the Week 4 files use CRLF.
- Preserved Week 4 behaviours: no backoff between retries; stale failure lines remain in `errors.jsonl`; in Matrix 1 evaluation a non-integral CaseID such as 5.7 would be truncated to 5 (not present in the data).

## 14. Advisor feedback

Record only feedback actually received. No new advisor feedback is asserted in this update.

## 15. Week-by-week history and future work

See `weekly_progress.md`. Later program work includes the presentation, the two remaining datasets, multi-dataset evaluation, the research paper, the final presentation, and closeout. Authorized veterinary adjudication of the mismatch registers remains pending; preserve baseline labels and predictions until approved.

## 16. Security and repository hygiene

Do not commit or publish:
- API keys, tokens, populated `.env` files;
- raw Vetology datasets, manually scored datasets, or the baseline artifacts in `data/`;
- prediction files or generated evaluation workbooks;
- patient or clinic identifiers;
- local virtual environments.

`*.xlsx`, `*.jsonl` and `data/` are gitignored. Check `git status` and staged files before every commit.
