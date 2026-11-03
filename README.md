# Vetology Radiology Evaluation

Python project for the Vetology training assignments. The project processes veterinary radiology reports, uses large language models (LLMs) to classify diagnostic conditions, and evaluates predictions against an independently maintained Gold Standard.

> **Confidentiality:** Do not commit or publish Vetology datasets, manually scored files, prediction outputs containing restricted data, patient/clinic identifiers, API credentials, or populated `.env` files. Use only approved data-handling and sharing workflows.

## Current status

### Week 4 — First application

The first canine thorax application has been implemented and run against 100 cases (CaseID 1–100).

Completed and user-verified:
- Excel data loading and validation for 100 cases, 20 conditions, and 2,000 Gold Standard labels.
- LLM input restricted to the original radiologist `Findings`, `Conclusions`, and `Recommendations`; CaseID is retained for tracking and is not sent to the model.
- AI-generated report fields and Gold Standard labels are excluded from LLM input.
- V1.3 master classification prompt integrated.
- LangChain/OpenAI client configured using environment variables.
- Strict JSON response validation for the exact 20 condition keys and `Positive`/`Negative` labels.
- Sequential batch processing, retries, checkpointing, restart support, and error logging.
- Live batch completed: 100 successful predictions and zero failed cases.
- Matrix 2 evaluation against the approved Gold Standard generated for 2,000 labels.
- All 70 prediction/Gold Standard mismatches reviewed provisionally and consolidated in a separate adjudication register.

Matrix 2 aggregate results:
- Accuracy: 96.50%
- Sensitivity: 80.38%
- Specificity: 97.88%
- TP: 127; FN: 31; TN: 1,803; FP: 39

**Still outstanding for Week 4:**
- Matrix 1: original radiologist report versus the second AI report.
- Authorized adjudication of the 70 mismatches. The existing Gold Standard and original predictions must remain unchanged until approved.
- Optional task: move prompt configuration into JSON and test loading/execution from that configuration.

These results are a pilot evaluation against the approved project Gold Standard, not evidence of clinical readiness. Conditions with no positive reference cases do not have a meaningful sensitivity estimate.

## Repository layout

The project is organized by assignment week, with shared utilities and documentation kept separately.

```text
VETOLOGY-RADIOLOGY/
├── src/
│   ├── common/
│   ├── week_01/
│   ├── week_02/
│   ├── week_03/
│   └── week_04/
│       ├── prompts/
│       ├── week4_block1_data_loader.py
│       ├── llm_client.py
│       ├── single_case_test.py
│       ├── response_validator.py
│       ├── test_response_validator.py
│       ├── batch_processor.py
│       └── run_batch.py
├── docs/
│   ├── CHANGELOG.md
│   ├── DECISION_LOG.md
│   ├── project_documentation.md
│   ├── testing_log.md
│   └── weekly_progress.md
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

The structure above records the known project modules. Keep it synchronized with the actual repository as files are added or renamed.

## Prerequisites

- Windows 11 (the reported development environment)
- Python (Python 3.14.6 was reported during setup; verify compatibility if recreating the environment)
- Visual Studio Code or another Python IDE
- An OpenAI API key and permission/billing access for API execution

## Setup (Windows PowerShell)

Run from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, select `.venv` through the VS Code Python interpreter selector or follow your organization's approved execution-policy process.

## Environment configuration

1. Copy `.env.example` to a local file named `.env` in the repository root.
2. Add your own OpenAI API key to `.env`.
3. Do not share or commit `.env`.

The Week 4 client uses `python-dotenv` to load the root `.env` file and reads these settings:

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI credential | Required |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4.1-mini` |
| `OPENAI_TEMPERATURE` | Sampling temperature | `0` |
| `OPENAI_TIMEOUT_SECONDS` | Request timeout | `90` |
| `OPENAI_MAX_RETRIES` | Client retry limit | `2` |

Never put real keys in `.env.example`, source files, logs, screenshots, or documentation.

## Week 4 — first application

### Data and prompt safeguards

The approved Gold Standard is maintained separately from model inputs and predictions. The LLM receives only the three original radiologist report fields:
- `Findings (original radiologist report)`
- `Conclusions (original radiologist report)`
- `Recommendations (original radiologist report)`

CaseID is used locally for tracking. It is not sent to the LLM. AI-generated report fields and Gold Standard labels must not be sent to the LLM.

The V1.3 prompt classifies 20 condition keys independently and requires exact `Positive` or `Negative` labels in JSON. See the prompt file under `src/week_04/prompts/`.

### Run the batch

The batch runner accepts the project’s configured dataset and output paths. Check the current command-line help or function signature in `src/week_04/run_batch.py` before execution; paths and arguments may be adjusted as the project evolves.

The batch processor:
- processes cases sequentially;
- validates model responses;
- writes successful validated predictions to JSONL;
- logs failed attempts separately;
- supports retries and restart/checkpoint behavior.

Do not place confidential input workbooks or generated prediction files in the repository.

### Evaluation

The completed Matrix 2 evaluation compares model predictions against the approved Gold Standard for 100 cases and 20 conditions (2,000 labels). The generated evaluation workbook contains:
1. `Case Predictions`
2. `Confusion Matrix`
3. `Execution Log`

The separately prepared adjudication register documents the 70 mismatches for authorized review. It is a review aid, not an automatically approved replacement Gold Standard.

### Week 4 remaining work

1. Generate Matrix 1 (original radiologist report versus the second AI report).
2. Obtain authorized decisions on the mismatch register; preserve the baseline evaluation until decisions are approved.
3. Optional: implement JSON-based prompt configuration and test it.

## Tests

The Week 4 response-validator tests cover valid responses and rejection of malformed JSON, duplicate keys, missing/unexpected keys, invalid labels, and markdown-fenced output. Offline batch-processor tests cover checkpointing, restart behavior, retries, and error logging. The 100-case live batch and Matrix 2 evaluation were also completed.

See `docs/testing_log.md` for the recorded evidence and limitations. Run tests from the repository root using the project virtual environment. Example:

```powershell
python -m unittest discover -s src/week_04 -p "test_*.py"
```

If test discovery or import paths differ in your local checkout, use the test module's documented invocation and record the actual command and result.

## Documentation

- `docs/weekly_progress.md` — assignment progress by week.
- `docs/CHANGELOG.md` — implementation history.
- `docs/DECISION_LOG.md` — technical and evaluation decisions.
- `docs/testing_log.md` — tests, results, and limitations.
- `docs/project_documentation.md` — consolidated technical record.

Update these files when implementation or assignment status changes. Do not describe planned or unverified functionality as complete.

## Version control

Git milestone commits/tags were deferred during the implementation work and should be completed during the project closeout. Before committing, inspect staged files and confirm no confidential data, `.env`, datasets, predictions, or restricted outputs are included.
