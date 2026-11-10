# Vetology Radiology Evaluation

Python project for the Vetology training assignments. The project processes veterinary radiology reports, uses large language models (LLMs) to classify diagnostic conditions, and evaluates predictions against independently maintained reference labels.

> **Confidentiality:** Do not commit or publish Vetology datasets, manually scored files, prediction outputs containing restricted data, generated evaluation workbooks, patient/clinic identifiers, API credentials, or populated `.env` files. Use only approved data-handling and sharing workflows. Baseline files used for local verification belong in the gitignored `data/` directory.

## Current status

### Week 5 — Claude Code rebuild (complete)

The Week 4 application was rebuilt independently under `src/week_05/` in six reviewed phases (foundation and configuration; prompt and LLM client; dataset loading; response validation; batch execution; evaluation and workbooks). The Week 4 implementation is unchanged.

- Two independent evaluation workflows: **Matrix 1** (original Vetology scores vs. LLM) and **Matrix 2** (Gold Standard vs. LLM).
- Canine Thorax Master Prompt V1.3 used byte-for-byte, protected by SHA-256 checks; OpenAI `gpt-4.1-mini` via LangChain, unchanged configuration.
- LLM input restricted to the three original radiologist report fields; reference labels held separately and never sent to the model.
- Week 4 prediction JSONL format, retry and checkpoint behaviour preserved, with approved reliability improvements.
- Both Week 4 baselines reproduced exactly from the delivered artifacts:
  - Matrix 1: TP 128, FN 921, TN 913, FP 38 — workbook identical to the delivered Matrix 1 workbook (run-dependent cells excluded).
  - Matrix 2: TP 127, FN 31, TN 1,803, FP 39 — workbook identical to the delivered Matrix 2 workbook except two approved differences.
- **338 offline tests pass** (0 skipped, 0 network connection attempts); flake8 clean; Week 4 regression tests pass unchanged.
- No live OpenAI API request was made during Week 5 development or verification.

Details: `docs/project_documentation.md` §10–§13 and `docs/testing_log.md`.

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
├── outputs/week_04/matrix_1/single_case_test.json
├── docs/                             # CHANGELOG, DECISION_LOG, testing_log, weekly_progress,
│                                     # project_documentation
├── data/                             # LOCAL ONLY, gitignored: datasets and baseline artifacts
├── .env.example, .gitignore, requirements.txt, README.md
```

Week 5 writes its outputs to `outputs/week_05/matrix_1/` and `outputs/week_05/matrix_2/`; workbooks and JSONL files are gitignored and must not be committed.

## Prerequisites

- Python 3. The Week 4 work was reported on Python 3.14.6 (Windows 11). The Week 5 rebuild was developed and tested on Python 3.13.18 (Linux, cloud environment); the Week 4 regression tests also pass there.
- Visual Studio Code or another Python IDE.
- An OpenAI API key and permission/billing access, only for live classification runs.

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

`requirements.txt` pins every package imported directly by the Week 4 and Week 5 code and tests (`openpyxl`, `langchain-openai`, `langchain-core`, `openai`, `httpx`, `python-dotenv`, `flake8`) plus the retained Week 2 demonstration integrations.

## Environment configuration

1. Copy `.env.example` to a local file named `.env` in the repository root.
2. Add your own OpenAI API key to `.env`.
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

## Week 5 — using the rebuilt application

All commands run from the repository root with `src` on `PYTHONPATH`
(PowerShell: `$env:PYTHONPATH = "src"`; bash: `export PYTHONPATH=src`). Every command needs `--workflow matrix1` or `--workflow matrix2`.

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

Week 5 (338 offline tests; no API key or network needed):

```bash
PYTHONPATH=src python -m unittest discover -s src/week_05/tests -t src -v
python -m flake8 --max-line-length=100 src/week_05
```

The real-data tests in `test_baseline_artifacts.py` run only when the baseline files are present in `data/`; otherwise they are skipped with an explanatory message.

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

Week 5 work is on the `week-05/claude-code-rebuild` branch, committed after each reviewed phase. Before committing, inspect staged files and confirm no confidential data, `.env`, datasets, predictions, or generated workbooks are included.
