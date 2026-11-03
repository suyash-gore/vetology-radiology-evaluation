# Vetology Radiology Evaluation — Technical Documentation

This document is the working technical record for the Vetology training project. It distinguishes implemented and tested functionality from pending tasks. Do not describe untested integrations or unfinished functionality as complete.

## 1. Project background and objectives

The project evaluates whether LLMs can classify diagnostic conditions from veterinary radiology reports. The workflow includes:
- preparing and validating report datasets;
- maintaining manual/approved reference labels separately;
- designing condition-specific prompts;
- calling LLMs from Python;
- validating structured model output;
- comparing predictions against a Gold Standard;
- reviewing errors and documenting limitations.

The training program ultimately covers three input datasets, application rebuilding, presentations, and a research paper. The current documented implementation is the first canine thorax application.

## 2. Dataset overview and data handling

### 2.1 Week 4 evaluation sample
- Dataset: canine thorax radiology reports.
- Sample: CaseID 1–100 (100 cases).
- Conditions: 20.
- Reference labels: 2,000 binary labels.
- Evaluation convention: `Positive` / `Negative`.
- Approved reference: `1_canine_thorax_gold_standard_score_draft.xlsx`.

The approved Gold Standard is kept separate from LLM inputs and prediction outputs. Existing legacy Abnormal/Normal labels are not treated as ground truth.

### 2.2 LLM input boundary
Only the original radiologist report fields are sent to the model:
- `Findings (original radiologist report)`
- `Conclusions (original radiologist report)`
- `Recommendations (original radiologist report)`

CaseID is retained locally for tracking and is not sent to the LLM. AI-generated report fields and Gold Standard labels are excluded from LLM input. This separation avoids reference-label leakage and prevents the model from seeing the second AI report used in the separate Matrix 1 comparison.

### 2.3 Classification convention
The V1.3 prompt requires all 20 conditions to be independently classified using exact `Positive` or `Negative` labels. Important rules include:
- Possible or suspected target condition is Positive.
- A condition not mentioned is Negative under the binary output convention.
- A recommendation to investigate alone does not make a condition Positive unless the report describes it as possible/suspected.
- Explicit negation remains Negative unless a separate unresolved positive statement requires review.
- RTM means redundant tracheal membrane; do not infer it from tracheal narrowing or collapse.
- `diseased_lungs` is independent and is not automatically derived from other labels.

The exact final prompt is maintained under `src/week_04/prompts/`.

## 3. Development environment

- OS: Windows 11.
- IDE: Visual Studio Code.
- Python version reported during setup: 3.14.6.
- Virtual environment: `.venv` (current project context also previously referred to `venv1`; confirm the actual local environment name when reproducing).
- Repository: `VETOLOGY-RADIOLOGY`.
- OpenAI model configured: `gpt-4.1-mini`.
- LangChain integration: `langchain-openai`.
- Environment loading: `python-dotenv`.

Verify Python and package compatibility when recreating the environment. The project dependency file records direct packages.

## 4. Week 2 implementation — historical scaffold

The Week 2 scaffold used `argparse` for input and optional output paths and `openpyxl` for workbook processing. It detected condition headers after the first eight metadata columns and generated a workbook matching the supplied confusion-matrix example structure.

The scaffold's output layout was verified, but the Week 2 scaffold did not calculate TP, FN, TN, or FP counts. This historical limitation should not be confused with the later Week 4 Matrix 2 evaluation, which did calculate aggregate confusion counts.

Separate Week 2 LangChain demonstration scripts were created for OpenAI, Gemini, and Hugging Face. Their existence does not establish that every provider integration was live-tested.

## 5. Week 3 prompt development

The V1.3 master prompt was prepared for 20 canine thorax conditions. It is loaded through the prompt module under `src/week_04/prompts/`. The prompt loader test reported 8,710 characters and 20 condition keys.

The project uses strict JSON output with exactly the expected condition keys and exact `Positive` / `Negative` values. No explanatory prose is expected in the model response.

## 6. Week 4 application architecture

### 6.1 Data loader
`src/week_04/week4_block1_data_loader.py`

Loads the first 100 cases, validates the expected original report fields and condition labels, and constructs a local `CaseReport` representation. Gold Standard labels are retained separately for evaluation. The LLM payload contains only the three original radiologist report fields.

### 6.2 Prompt loader
`src/week_04/prompts/`

Contains the V1.3 prompt and prompt-loading module. The prompt is loaded separately from the LLM client.

### 6.3 LLM client
`src/week_04/llm_client.py`

Uses LangChain's `ChatOpenAI` integration. Configuration is read from environment variables:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-4.1-mini`)
- `OPENAI_TEMPERATURE` (default `0`)
- `OPENAI_TIMEOUT_SECONDS` (default `90`)
- `OPENAI_MAX_RETRIES` (default `2`)

The root `.env` is loaded using `python-dotenv`. Never record or commit the actual API key.

`single_case_test.py` was used for a live single-case test. A response was returned successfully (HTTP 200).

### 6.4 Structured response validation
`src/week_04/response_validator.py`

Validates:
- syntactically valid JSON object;
- exactly the 20 expected keys;
- no missing or unexpected keys;
- no duplicate keys;
- exact `Positive` or `Negative` values;
- no markdown fences or extra prose;
- canonical condition-key ordering in the normalized output.

The Block 4 test suite passed the recorded positive and negative test cases.

### 6.5 Batch processing
`src/week_04/batch_processor.py` and `src/week_04/run_batch.py`

The batch workflow:
- processes cases sequentially;
- sends only the restricted report payload;
- validates each response;
- writes successful validated predictions to a JSONL results file;
- writes failed attempts to a separate errors JSONL file;
- retries failed cases;
- skips already completed valid cases on restart.

The live 100-case batch completed with 100 successful predictions and zero final failures. One case required a second application-level attempt. LangChain transport-level retries may create additional HTTP attempts beyond the application-level attempt count.

## 7. Week 4 evaluation

### 7.1 Matrix 2
The completed Matrix 2 compares the 100-case LLM predictions against the approved Gold Standard.

| Metric | Value |
|---|---:|
| Total labels | 2,000 |
| TP | 127 |
| FN | 31 |
| TN | 1,803 |
| FP | 39 |
| Accuracy | 96.50% |
| Sensitivity | 80.38% |
| Specificity | 97.88% |

The evaluation workbook contains:
1. `Case Predictions`
2. `Confusion Matrix`
3. `Execution Log`

### 7.2 Matrix 1
Week 4 separately requires comparison of the original radiologist report against the second AI report. Generation of this matrix has not been confirmed and remains pending.

### 7.3 Mismatch review and adjudication
There are 70 unique CaseID-condition mismatches: 31 false negatives and 39 false positives. They were reviewed provisionally and consolidated in `vetology_week4_master_adjudication_register.xlsx`.

The original Block 6 Mismatch Review was used as the authoritative source for the Gold Standard label, model prediction, and mismatch type. A condition-specific `diseased_lungs` review workbook contained inconsistent labels; the master register was reconciled against the original Block 6 source.

The register is a review aid, not an approved replacement Gold Standard. Authorized adjudication is pending. Do not overwrite the original Gold Standard or predictions. If a reviewer approves corrections, preserve the original baseline and create a separately versioned adjudicated reference before recalculating metrics.

## 8. Technical decisions

Refer to `DECISION_LOG.md`. Key decisions include:
- Positive/Negative labels only;
- approved Gold Standard maintained separately;
- restricted original-report-only LLM input;
- exact JSON schema validation;
- sequential checkpointed batch execution;
- preservation of baseline results pending authorized adjudication.

## 9. Testing and validation

Refer to `testing_log.md`. Recorded tests include:
- data loader validation;
- prompt loading;
- live single-case OpenAI request;
- response-validator positive/negative tests;
- offline batch processor tests;
- live 100-case batch;
- Matrix 2 evaluation;
- mismatch reconciliation.

Matrix 1 and optional JSON prompt configuration remain pending.

## 10. Problems, resolutions, and limitations

### Recorded resolution
The mismatch register was reconciled against the original Block 6 mismatch source after inconsistencies were identified in one condition-specific review workbook.

### Limitations
- The evaluation uses 100 reports and 2,000 labels from one input dataset.
- The approved reference is a project Gold Standard, not independently established expert ground truth in this record.
- Mismatch review is provisional until authorized adjudication.
- Class imbalance affects interpretation of aggregate accuracy.
- Sensitivity is not meaningful for conditions with zero positive reference cases.
- Model outputs can vary across runs; the reported run is the baseline run.
- The results do not establish clinical readiness.

## 11. Advisor feedback

Record only feedback actually received. No new advisor feedback is asserted in this update.

## 12. Week-by-week history and future work

See `weekly_progress.md`.

Immediate Week 4 outstanding work:
1. Generate Matrix 1 (original radiologist report versus second AI report).
2. Obtain authorized adjudication decisions for the 70 mismatches.
3. Optional: implement and test JSON-based prompt configuration.

Later program work includes the Claude Code rebuild, presentation, two remaining datasets, multi-dataset evaluation, research paper, final presentation, and closeout.

## 13. Security and repository hygiene

Do not commit or publish:
- API keys, tokens, populated `.env` files;
- raw Vetology datasets or manually scored datasets;
- restricted predictions or evaluation files unless explicitly approved;
- patient or clinic identifiers;
- local virtual environments.

Check `git status` and staged files before every commit. Git commits and tags were deferred and are to be completed during project closeout.
