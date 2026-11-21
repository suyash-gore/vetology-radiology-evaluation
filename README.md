# Vetology Radiology Evaluation

Python project for the Vetology training assignments. The project processes veterinary radiology reports, uses large language models (LLMs) to classify diagnostic conditions, and evaluates predictions against independently maintained reference labels.

> **Confidentiality:** Do not commit or publish Vetology datasets, manually scored files, prediction outputs containing restricted data, generated evaluation workbooks, patient/clinic identifiers, API credentials, or populated `.env` files. Use only approved data-handling and sharing workflows. Baseline files used for local verification belong in the gitignored `data/` directory.

## Current status

### Week 7 extension — Feline Thorax and Canine Abdomen (implemented; approved prompts registered; live runs to be executed locally)

Week 7 (branch `week-07/feline-thorax-and-canine-abdomen`) now runs three applications on one shared engine, chosen with `--application`. Canine Thorax is still the default.

| Application | Provider / model | Conditions | Prompt | Status |
|---|---|---:|---|---|
| `canine_thorax` | Google Gemini `gemini-3.8-flash` | 20 | Canine Thorax Master Prompt V1.3 (SHA-256 pinned) | Unchanged, existing results kept |
| `feline_thorax` | OpenAI `gpt-4.1-mini` | 21 | Feline Thorax Master Prompt V1.1 (SHA-256 pinned) | Ready; live run not yet executed |
| `canine_abdomen` | OpenAI `gpt-4.1-mini` | 10 | Canine Abdomen Master Prompt V1.2 (SHA-256 pinned) | Ready; live run not yet executed |

- **Predictions:** each new application generates its predictions **once**, from the Matrix 1 workbook, and reuses them for **both** evaluations. Matrix 1 uses the Vetology reference labels, Matrix 2 the Gold Standard labels, and the two reference tracks stay separate.
- **Workbook check:** before the shared predictions serve Matrix 2, the Matrix 2 workbook must hold the same 100 unique CaseIDs, in the same order, with identical report text.
- **Feline Matrix 1 normalisation:** only the columns `pulmonary_nodules`, `esophagitis` and `pneumonia` are mapped (`Normal`→`Negative`, `Abnormal`→`Positive`) before strict validation. Nothing else is ever normalised: no other column, not Feline Matrix 2, not Canine Abdomen.
- **Isolation:** workflows are identified as `<application>/<workflow>`. Each application writes and reads only inside its own `outputs/week_07/<application>/`, and Canine Thorax paths are unchanged.
- **Prompts:** the approved Feline Thorax V1.1 and Canine Abdomen V1.2 files are stored byte-for-byte in `src/week_07/prompts/`. Their file SHA-256, stripped-text SHA-256 and text length are pinned, so any modification makes loading fail. A prompt registered without pins is pending and blocks every batch run.
- **Real input workbooks (validated offline, unmodified):**
  - All four workbooks have the expected headers, worksheet `Sheet1`, and exactly 100 unique integer CaseIDs (1–100).
  - The Gold Standard drafts have trailing blank rows, which are skipped.
  - The batch loader and the evaluation loader agree on every workbook, including the Matrix 2 ambiguity guardrail.
  - Matrix 1 and Matrix 2 have identical cases and report text for both applications.
- **Tests:** 492 Week 7 tests (487 passed, 5 opt-in local tests skipped) and 338 Week 5 tests (329 passed, 9 skipped), with 0 failures and 0 errors; flake8 clean. All run offline with fake model responses.

Details: `docs/project_documentation.md` §18.

### Week 7 — Gemini model evaluation (complete)

An independent Google Gemini pipeline was implemented under `src/week_07/` (branch `week-07/gemini-model-evaluation`). It reruns both Week 5 workflows with Gemini and compares the results with the saved Week 5 OpenAI predictions. `src/week_04/` and `src/week_05/` are unchanged, and Week 7 does not import either at runtime.

- Gemini `gemini-3.8-flash` through LangChain (`langchain-google-genai`) and the Google GenAI SDK, temperature 0, JSON response mode. Canine Thorax Master Prompt V1.3 used byte-for-byte (SHA-256 protected). Model input is limited to the three original report fields.
- Retry policy: one SDK transport attempt per application attempt and up to 2 application attempts per case. Transient errors (HTTP 408/429/5xx, network timeouts) get a bounded backoff. HTTP 400/401/403/404 and configuration errors are fatal: the batch stops.
- Matrix 1 and Matrix 2 stay separate workflows. Week 7 writes only under `outputs/week_07/`, and the Week 5 OpenAI predictions are read-only inputs to the comparison.
- **Tests (local):** 288 run, 282 passed, 6 skipped, 0 failures and 0 errors; flake8 clean. Week 5 regression: 338 run, 329 passed, 9 skipped, 0 failures and 0 errors.
- **Live Gemini execution:** 100 cases × 20 conditions (2,000 paired labels) per matrix. Zero unresolved final failures.

| Workflow (reference) | Model | TP | FN | TN | FP | Accuracy | Sensitivity | Specificity | Precision | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Matrix 1 (original Vetology) | Gemini | 96 | 953 | 924 | 27 | 51.00% | 9.15% | 97.16% | 78.05% | 16.38% |
| Matrix 1 (original Vetology) | OpenAI GPT-4.1 mini (Week 5) | 126 | 923 | 916 | 35 | 52.10% | 12.01% | 96.32% | 78.26% | 20.83% |
| Matrix 2 (Gold Standard) | Gemini | 102 | 56 | 1,822 | 20 | 96.20% | 64.56% | 98.91% | 83.61% | 72.86% |
| Matrix 2 (Gold Standard) | OpenAI GPT-4.1 mini (Week 5) | 126 | 32 | 1,806 | 36 | 96.60% | 79.75% | 98.05% | 77.78% | 78.75% |

- Model agreement (OpenAI vs Gemini, reference not used): Matrix 1 1,940/2,000 (97.00%, 60 disagreements); Matrix 2 1,944/2,000 (97.20%, 56 disagreements).
- In both matrices Gemini had higher specificity and fewer false positives. OpenAI had higher sensitivity, accuracy and F1. High agreement between the models does not mean high accuracy against the reference labels.
- Matrix 1 and Matrix 2 use different reference-label sets, so their results must not be combined. These are pilot results, not evidence of clinical readiness.

Details: `docs/project_documentation.md` §17 and `docs/testing_log.md`.

### Week 5 — Claude Code rebuild (complete)

The Week 4 application was rebuilt independently under `src/week_05/` in six reviewed phases (foundation and configuration; prompt and LLM client; dataset loading; response validation; batch execution; evaluation and workbooks). The Week 4 implementation is unchanged.

- Two independent evaluation workflows: **Matrix 1** (original Vetology scores vs. LLM) and **Matrix 2** (Gold Standard vs. LLM).
- Canine Thorax Master Prompt V1.3 used byte-for-byte, protected by SHA-256 checks; OpenAI `gpt-4.1-mini` via LangChain, unchanged configuration.
- LLM input restricted to the three original radiologist report fields; reference labels held separately and never sent to the model.
- Week 4 prediction JSONL format, retry and checkpoint behaviour preserved, with approved reliability improvements.
- Both Week 4 baselines reproduced exactly from the delivered artifacts:
  - Matrix 1: TP 128, FN 921, TN 913, FP 38 — workbook identical to the delivered Matrix 1 workbook (run-dependent cells excluded).
  - Matrix 2: TP 127, FN 31, TN 1,803, FP 39 — workbook identical to the delivered Matrix 2 workbook except two approved differences.
- **Development-environment verification:** 338 offline tests passed (0 skipped, 0 network connection attempts) when the gitignored baseline artifacts were available; flake8 was clean and Week 4 regression tests passed unchanged.
- **Local Windows verification (2026-11-12):** 338 tests run; 329 passed, 9 skipped, 0 failures and 0 errors. The 9 skipped tests require baseline artifacts that were not present in the local test location. The Windows JSONL compatibility tests passed.
- **Live execution (2026-11-12):** Matrix 1 and Matrix 2 each completed a 100-case OpenAI API batch with 100 successful cases and 0 final failures. Both evaluation workbooks were generated and visually reviewed; both reference-loader comparisons passed.
- **Matrix 1 live evaluation:** TP 126, FN 923, TN 916, FP 35; accuracy 52.10%, sensitivity 12.01%, specificity 96.32%, precision 78.26%, F1 20.83%.
- **Matrix 2 live evaluation:** TP 126, FN 32, TN 1,806, FP 36; accuracy 96.60%, sensitivity 79.75%, specificity 98.05%, precision 77.78%, F1 78.75%.
- The live batch commands made billable OpenAI API requests. Tests, evaluation and reference-loader comparisons did not make API requests. Flake8 was not rerun on the local Windows machine.

Details: `docs/project_documentation.md` §§10–13 and `docs/testing_log.md`.

### Week 4 — First application (historical record)

The first canine thorax application was implemented and run against 100 cases (CaseID 1–100).

Completed and user-verified in Week 4:
- Excel data loading and validation for 100 cases, 20 conditions, and 2,000 Gold Standard labels.
- LLM input restricted to the original radiologist `Findings`, `Conclusions`, and `Recommendations`; CaseID is retained for tracking and is not sent to the model.
- AI-generated report fields and Gold Standard labels are excluded from LLM input.
- V1.3 master classification prompt integrated.
- LangChain/OpenAI client configured using environment variables.
- Strict JSON response validation for the exact 20 condition keys and `Positive`/`Negative` labels.
- Sequential batch processing, retries, checkpointing, restart support, and error logging.
- Live batch completed: 100 successful predictions and zero failed cases.
- Matrix 2 evaluation against the approved Gold Standard generated for 2,000 labels.
- All 70 Matrix 2 prediction/Gold Standard mismatches reviewed provisionally and consolidated in a separate adjudication register.
- Matrix 1 evaluation completed for 100 cases × 20 conditions (2,000 pairs): TP 128, FN 921, TN 913, FP 38; accuracy 52.05%, sensitivity 12.20%, specificity 96.00%, precision 77.11%, F1 21.07%.
- Matrix 1 mismatch/error analysis completed at the text-screening level for all 959 mismatches across all 20 conditions; veterinary adjudication remains pending.
- Week 4 optional JSON prompt-configuration task implemented and locally tested: 5 tests passed.

Matrix 2 aggregate results: accuracy 96.50%, sensitivity 80.38%, specificity 97.88%, precision 76.51%, F1 78.40%; TP 127, FN 31, TN 1,803, FP 39.

These results are pilot evaluations, not evidence of clinical readiness. Conditions with no positive reference cases do not have a meaningful sensitivity estimate. Authorized veterinary adjudication of the mismatch registers remains pending.

## Repository layout

```text
vetology-radiology-evaluation/
├── src/
│   ├── common/
│   ├── week_01/
│   ├── week_02/                      # Week 2 scaffold and provider demonstrations
│   ├── week_03/
│   ├── week_04/                      # Week 4 application (unchanged)
│   │   ├── prompts/                  # V1.3 prompt + loader
│   │   ├── matrix_1/                 # Matrix 1 loader, runners, evaluator, tests, delivery zips
│   │   │   └── tests/
│   │   ├── optional_json_config/     # optional JSON prompt configuration (+ delivery zip)
│   │   │   └── config/canine_thorax_v1_3.json
│   │   ├── week4_block1_data_loader.py, llm_client.py, response_validator.py
│   │   ├── batch_processor.py, run_batch.py, single_case_test.py
│   │   └── test_response_validator.py, test_batch_processor.py, case1_raw_response.json
│   └── week_05/                      # Week 5 independent rebuild
│       ├── __main__.py, cli.py       # python -m week_05 <command>
│       ├── config.py, conditions.py  # settings, workflow specs, 20 condition keys
│       ├── prompts/                  # byte-identical V1.3 prompt + integrity-checked loader
│       ├── llm_client.py             # message construction, OpenAI client
│       ├── dataset_loader.py         # report input / reference-label separation
│       ├── response_validator.py
│       ├── batch_runner.py, jsonl_store.py
│       ├── evaluation/               # metrics, reconciliation, reference loaders,
│       │                             # Matrix 1 and Matrix 2 workbooks, workbook comparison
│       └── tests/                    # offline unit tests + real-artifact tests
│   └── week_07/                      # Week 7 independent Gemini pipeline
│       ├── __main__.py, cli.py       # python -m week_07 <command>
│       ├── config.py, conditions.py  # Gemini settings, retry policy, workflow specs
│       ├── prompts/                  # byte-identical V1.3 prompt + integrity-checked loader
│       ├── llm_client.py             # message construction, LangChain Gemini client
│       ├── error_policy.py           # fatal / transient / retryable error classification
│       ├── dataset_loader.py, response_validator.py
│       ├── batch_runner.py, jsonl_store.py, run_manifest.py
│       ├── isolation.py              # output isolation and read-only source protection
│       ├── evaluation/               # metrics, reference loaders, Matrix 1/2 workbooks
│       ├── comparison/               # OpenAI vs Gemini sources, agreement, six-sheet workbook
│       ├── applications.py           # application registry (canine_thorax, feline_thorax,
│       │                             # canine_abdomen): conditions, provider, prompt, workflows
│       ├── prompts/registry.py       # per-application prompt identity + pinned SHA-256 checks
│       ├── app_dataset_loader.py     # application-aware loading, normalisation, cross-matrix check
│       ├── app_validator.py          # application-aware strict response validation
│       ├── openai_client.py, openai_error_policy.py, providers.py   # OpenAI provider
│       ├── evaluation/app_*.py       # application-aware reference loading and reconciliation
│       └── tests/                    # offline tests + opt-in local artifact tests
├── outputs/week_04/matrix_1/single_case_test.json
├── docs/                             # CHANGELOG, DECISION_LOG, testing_log, weekly_progress,
│                                     # project_documentation
├── data/                             # LOCAL ONLY, gitignored: datasets and baseline artifacts
├── .env.example, .gitignore, requirements.txt, README.md
```

Week 5 writes its outputs to `outputs/week_05/matrix_1/` and `outputs/week_05/matrix_2/`; workbooks and JSONL files are gitignored and must not be committed.

Week 7 writes only under `outputs/week_07/`. For Canine Thorax, `matrix_1/` and `matrix_2/` hold the batch outputs (`predictions.jsonl`, `errors.jsonl`, `run_manifest.json`, evaluation workbook), and `comparison/matrix_1/` and `comparison/matrix_2/` hold the comparison workbooks. Predictions, error logs and workbooks stay local. The two `run_manifest.json` files are execution metadata and are the only generated Week 7 outputs intended for version control.

Feline Thorax and Canine Abdomen each own one folder, `outputs/week_07/<application>/`:
- `predictions/` holds the one shared batch run: `predictions.jsonl`, `errors.jsonl` and `run_manifest.json`.
- `matrix_1/` and `matrix_2/` hold the two separate evaluation workbooks, `<application>_matrix1_evaluation_workbook.xlsx` and `<application>_matrix2_evaluation_workbook.xlsx`.

Output-directory overrides must stay inside the application's own folder.

The 2026-11-12 live execution produced 100 successful predictions for each workflow. Matrix 1 and Matrix 2 results use different reference-label sets and should be interpreted separately, not as a direct like-for-like comparison of model quality. These are pilot evaluations, not evidence of clinical readiness.

## Prerequisites

- Python 3. The Week 5 rebuild was developed and tested on Python 3.13.18 (Linux, cloud environment) and locally executed on Windows 11 with Python 3.14.6. The Week 4 work was also reported on Windows 11 with Python 3.14.6.
- Visual Studio Code or another Python IDE.
- An OpenAI API key and permission/billing access, only for live Week 4/5 classification runs.
- A Google Gemini API key (`GOOGLE_API_KEY`) and billing access, only for live Week 7 batch runs.

## Setup

Run from the repository root.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` pins every package imported directly by the Week 4 and Week 5 code and tests (`openpyxl`, `langchain-openai`, `langchain-core`, `openai`, `httpx`, `python-dotenv`, `flake8`), the Week 7 Gemini packages (`langchain-google-genai`, `google-genai`), and the retained Week 2 demonstration integrations.

## Environment configuration

1. Copy `.env.example` to a local file named `.env` in the repository root.
2. Add your own OpenAI API key (Weeks 4/5) and/or Google Gemini API key (Week 7) to `.env`.
3. Do not share or commit `.env`.

Both the Week 4 client and the Week 5 rebuild use `python-dotenv` to load the root `.env` file (existing environment variables take precedence) and read:

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI credential | Required for live runs |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4.1-mini` |
| `OPENAI_TEMPERATURE` | Sampling temperature | `0` |
| `OPENAI_TIMEOUT_SECONDS` | Request timeout | `90` |
| `OPENAI_MAX_RETRIES` | LangChain transport retry limit | `2` |

Week 5 validates these settings, and the presence of the key, before any classification starts. Never put real keys in `.env.example`, source files, logs, screenshots, or documentation.

Week 7 loads the same root `.env` (existing environment variables take precedence). It reads only the Gemini variables and never reads the OpenAI ones:

| Variable | Purpose | Default |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini credential (read by the SDK from the environment; Week 7 only checks that it is set) | Required for live `batch` runs |
| `GEMINI_MODEL` | Gemini model name | `gemini-3.8-flash` |
| `GEMINI_TEMPERATURE` | Sampling temperature (0 to 2) | `0` |
| `GEMINI_TIMEOUT_SECONDS` | Request timeout (> 0) | `90` |

`GEMINI_MAX_RETRIES` is not supported, and Week 7 refuses to run if it is set. Transport retries are fixed, and application attempts are set with `batch --max-attempts` (default 2).

The Week 7 Feline Thorax and Canine Abdomen applications read only the OpenAI variables, never `GOOGLE_API_KEY`. Canine Thorax, in turn, never needs `OPENAI_API_KEY`.

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI credential (read by the SDK; Week 7 only checks that it is set) | Required for live `batch` runs |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4.1-mini` |
| `OPENAI_TEMPERATURE` | Sampling temperature (0 to 2) | `0` |
| `OPENAI_TIMEOUT_SECONDS` | Request timeout (> 0) | `90` |

Week 7 fixes the OpenAI transport retries at 0, so the batch retry policy is the only retry system. `OPENAI_MAX_RETRIES` (a Week 5 setting) is ignored by Week 7, and `config` reports it as ignored.

## Week 5 — using the rebuilt application

Run commands from the repository root with the project virtual environment active and `src` on `PYTHONPATH`.

PowerShell:
```powershell
$env:PYTHONPATH = "src"
```

macOS/Linux:
```bash
export PYTHONPATH=src
```

Every workflow command needs `--workflow matrix1` or `--workflow matrix2`.

```bash
python -m week_05 config --workflow matrix1                 # show settings (no API request)
python -m week_05 validate-data --workflow matrix2          # load and validate the input workbook
python -m week_05 compare-references --workflow matrix2     # compare the two reference-loading approaches
python -m week_05 evaluate --workflow matrix1               # evaluate saved predictions, write workbook
python -m week_05 batch --workflow matrix1                  # BILLABLE: classify with OpenAI
```

- Default inputs: `data/week_04_inputs/Vetology_Matrix1_First100_Encoded.xlsx` (Matrix 1) and `data/week_04_inputs/1_canine_thorax_gold_standard_score_draft.xlsx` (Matrix 2); override with `--input`.
- `batch` makes billable OpenAI requests for every case without a valid saved prediction. Matrix 1 always processes exactly 100 cases; Matrix 2 accepts `--limit`.
- `evaluate` reads `predictions.jsonl` from the workflow's own output folder unless `--predictions` is given, and writes `matrix1_evaluation_workbook.xlsx` or `Evaluation Workbook v2.xlsx`.
- The workflows never share inputs, reference labels, predictions or outputs; Week 5 refuses to write into the other workflow's folder or into `outputs/week_04/`.

## Week 7 — Gemini evaluation

Run from the repository root with the virtual environment active and `src` on `PYTHONPATH` (see Week 5 above). Every command needs `--workflow matrix1` or `--workflow matrix2`. Run `python -m week_07 <command> --help` to see all options.

```bash
python -m week_07 --help
python -m week_07 config --workflow matrix1                 # resolved model, retry and workflow settings (offline)
python -m week_07 validate-data --workflow matrix2          # load and validate the input workbook (offline)
python -m week_07 compare-references --workflow matrix2     # compare batch and evaluation reference loaders (offline)
python -m week_07 batch --workflow matrix1                  # BILLABLE: classify with Gemini
python -m week_07 evaluate --workflow matrix1               # evaluate saved Gemini predictions, write workbook (offline)
python -m week_07 compare --workflow matrix1                # OpenAI (Week 5) vs Gemini comparison workbook (offline)
```

- **Only `batch` contacts Gemini.** It makes live, billable API requests for every case that has no valid saved prediction, and it resumes from the checkpoint. `config`, `validate-data`, `compare-references`, `evaluate` and `compare` work on local files and saved artifacts and make no API request.
- `batch` options: `--input`, `--sheet`, `--limit` (Matrix 2 only; Matrix 1 always processes exactly 100 cases), `--output-dir` (must be inside `outputs/week_07/`), `--max-attempts` (default 2). A resumed run whose model, settings, prompt or input differs from the `run_manifest.json` identity is refused.
- `evaluate` reads `outputs/week_07/<matrix>/predictions.jsonl` unless `--predictions` is given. Options: `--input`, `--output`, `--model-record`.
- `compare` reads the Week 5 OpenAI predictions (`outputs/week_05/<matrix>/predictions.jsonl`, read-only) and the Week 7 Gemini predictions with their run manifest. It writes `outputs/week_07/comparison/matrix_1/matrix1_openai_vs_gemini_comparison.xlsx` or `outputs/week_07/comparison/matrix_2/matrix2_openai_vs_gemini_comparison.xlsx`. Options: `--openai`, `--gemini`, `--reference`, `--openai-errors`, `--gemini-errors`, `--output`.
- Exit codes: 0 success; 1 `compare-references` found differences; 2 configuration or isolation error; 3 input error; 4 invalid argument; 5 not available; 6 fatal provider error (HTTP 400/401/403/404); 7 a read-only source changed.

### Week 7 — Feline Thorax and Canine Abdomen

Add `--application feline_thorax` or `--application canine_abdomen` to any command. The real input workbooks live outside the repository, so pass each one with `--input`. The fallback location `data/week_07_inputs/` is used only when `--input` is omitted.

```bash
python -m week_07 config        --application feline_thorax --workflow matrix1           # settings, prompt status (offline)
python -m week_07 validate-data --application feline_thorax --workflow matrix1 --input M1.xlsx
python -m week_07 validate-data --application feline_thorax --workflow matrix2 --input M2.xlsx
python -m week_07 compare-references --application feline_thorax --workflow matrix2 --input M2.xlsx
python -m week_07 batch    --application feline_thorax --workflow matrix1 --provider openai --input M1.xlsx --matrix2-input M2.xlsx   # BILLABLE: OpenAI
python -m week_07 evaluate --application feline_thorax --workflow matrix1 --input M1.xlsx
python -m week_07 evaluate --application feline_thorax --workflow matrix2 --input M2.xlsx --prediction-source-input M1.xlsx
```

The same commands work with `--application canine_abdomen`. Notes:

- **Batch:**
  - Runs only for `--workflow matrix1`, the prediction source. A Matrix 2 batch is refused because Matrix 2 reuses the shared predictions.
  - `--limit` is not available.
  - `--provider` must match the application.
  - `--matrix2-input` checks the Matrix 2 workbook against the Matrix 1 input before the run.
  - Live runs need `OPENAI_API_KEY` in the local `.env`. A prompt that fails its integrity check, or a pending prompt, blocks the run before anything is written.
- **Evaluate:**
  - Reads the shared `outputs/week_07/<application>/predictions/predictions.jsonl` and requires its run manifest. The manifest's application, provider, condition keys and prompt must match, and its input digest must equal the Matrix 1 workbook's.
  - For Matrix 2 it also checks the Matrix 1 workbook (`--prediction-source-input`) against the Gold Standard workbook.
  - `--model-record` is not available.
- **Compare:** `compare` (OpenAI vs Gemini) exists only for Canine Thorax.

## Week 4 — first application (historical)

### Data and prompt safeguards

The approved Gold Standard is maintained separately from model inputs and predictions. The LLM receives only the three original radiologist report fields:
- `Findings (original radiologist report)`
- `Conclusions (original radiologist report)`
- `Recommendations (original radiologist report)`

CaseID is used locally for tracking. It is not sent to the LLM. AI-generated report fields and reference labels must not be sent to the LLM.

The V1.3 prompt classifies 20 condition keys independently and requires exact `Positive` or `Negative` labels in JSON. See the prompt file under `src/week_04/prompts/`.

### Run the batch

Check `python src/week_04/run_batch.py --help` (Matrix 2) or `src/week_04/matrix_1/run_matrix1_batch.py` (Matrix 1) before execution.

The Week 4 batch processor:
- processes cases sequentially;
- validates model responses;
- writes successful validated predictions to `predictions.jsonl`;
- retries a failed case up to the attempt limit and writes one record per case that still fails to `errors.jsonl` (failures of individual attempts are logged to the console only);
- skips already completed valid cases on restart.

### Evaluation

- **Matrix 1:** `src/week_04/matrix_1/matrix1_evaluator.py` (default output name `matrix1_evaluation_workbook.xlsx`). The delivered Matrix 1 workbook, `Evaluation_Workbook_v1.xlsx`, has six sheets (Overall Summary, Condition Summary, Case Predictions, Confusion Matrix, Execution Log, Metric Definitions). It was produced by a variant of this evaluator that is not in the repository; it differs from the committed code only in presentation (10 wording changes, row heights, one column width, one font colour).
- **Matrix 2:** no evaluator source exists in the repository; the workbook was produced outside it. The delivered `Evaluation Workbook v2.xlsx` has five sheets (Overall Summary, Condition Summary, Case Predictions, Confusion Matrix, Execution Log). Its Overall Summary reports micro metrics, including precision, F1 and a Balanced Accuracy row (89.13%); it has no macro metrics.

The separately prepared adjudication registers document the mismatches for authorized review. They are review aids, not approved replacement reference labels.

### Week 4 optional JSON configuration

The optional module under `src/week_04/optional_json_config/` stores the existing V1.3 prompt in JSON and reads it through a dedicated loader. It performs local configuration reading/validation only; it does not call an API or execute an LLM.

## Tests

Run from the repository root with the project environment active. With bash, prefix commands with `PYTHONPATH=src` or export it; with PowerShell set `$env:PYTHONPATH = "src"` first.

Week 5 automated tests are offline; they do not require an API key or network access.

Windows PowerShell:
```powershell
python -m unittest discover -s src/week_05/tests -v
```

macOS/Linux:
```bash
PYTHONPATH=src python -m unittest discover -s src/week_05/tests -t src -v
```

Optional lint check:
```bash
python -m flake8 --max-line-length=100 src/week_05
```

The real-artifact tests in `test_baseline_artifacts.py` run only when the baseline files are present in `data/`; otherwise they are skipped with an explanatory message. In the 2026-11-12 local Windows run, 329 tests passed and 9 were skipped because the baseline artifacts were not present in the local test location (338 tests total). The development-environment run passed all 338 tests when those artifacts were available. Flake8 was clean in the development environment; it was not rerun locally on Windows.

Week 7 automated tests are offline too: no API key and no network access needed (the Gemini SDK is exercised through a mock transport).

```bash
python -m unittest discover -s src/week_07/tests -t src -v
python -m flake8 --max-line-length=100 src/week_07
```

The local artifact tests in `test_local_artifacts.py` are opt-in. They run only when `WEEK07_RUN_LOCAL_ARTIFACTS=1` is set on the local machine and the real input and Week 5 prediction files are present. Otherwise they are skipped. They make no API request and write no files.

```powershell
$env:PYTHONPATH = "src"; $env:WEEK07_RUN_LOCAL_ARTIFACTS = "1"
python -m unittest week_07.tests.test_local_artifacts -v
```

In the local Week 7 run, 288 tests ran: 282 passed and 6 were skipped, with 0 failures and 0 errors. One skip is a symlink test that needs privileges on Windows. Five are the opt-in local artifact tests, which skip when the opt-in is not set.

After the Feline Thorax / Canine Abdomen extension and prompt registration, the Week 7 suite has 492 tests. In the Linux development container 487 passed and 5 were skipped (the opt-in local artifact tests), with 0 failures and 0 errors. The new tests use synthetic workbooks and fake model responses; they make no API request.

Week 4 (unchanged; the top-level Week 4 tests are standalone scripts, so `unittest discover` on `src/week_04` finds no tests):

```bash
python src/week_04/test_response_validator.py
python src/week_04/test_batch_processor.py
PYTHONPATH=src python -m unittest discover -s src/week_04/matrix_1 -p "test_*.py"
PYTHONPATH=src python -m unittest discover -s src/week_04/matrix_1/tests -t src/week_04/matrix_1/tests
cd src/week_04/optional_json_config && python -m unittest -v test_prompt_config_loader.py
```

See `docs/testing_log.md` for recorded results and limitations.

## Documentation

- `docs/weekly_progress.md` — assignment progress by week.
- `docs/CHANGELOG.md` — implementation history.
- `docs/DECISION_LOG.md` — technical and evaluation decisions.
- `docs/testing_log.md` — tests, results, and limitations.
- `docs/project_documentation.md` — consolidated technical record.

Do not describe planned or unverified functionality as complete.

## Version control

Each assignment is developed on its own branch: Week 5 on `week-05/claude-code-rebuild` (committed after each reviewed phase; closeout tag `week-05-closeout`), Week 7 on `week-07/gemini-model-evaluation`, and the Week 7 Feline Thorax / Canine Abdomen extension on `week-07/feline-thorax-and-canine-abdomen`. Before committing, inspect staged files and confirm no confidential data, `.env`, datasets, predictions, error logs, or generated workbooks are included. Of the generated Week 7 outputs, only `outputs/week_07/matrix_1/run_manifest.json` and `outputs/week_07/matrix_2/run_manifest.json` are intended for commit, and only after checking their contents.
