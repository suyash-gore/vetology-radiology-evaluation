# Vetology Radiology Evaluation

Repository for Vetology training assignments involving radiology-report data processing, language-model integrations, and evaluation workflows.

## Project overview

This repository contains the code and documentation developed across the weekly Vetology training assignments. The project is organized by assignment week, with a separate location for reusable utilities and project documentation.

## Current project status

### Week 2

- A command-line Excel-processing scaffold is implemented in `src/week_02/main.py`.
- The program accepts an input Excel workbook path and can optionally accept an output path.
- It reads the active worksheet's header row and identifies condition columns dynamically after the first eight metadata columns.
- It generates an output workbook following the supplied confusion-matrix example structure.
- The output currently provides the confusion-matrix layout and formulas; it does **not** calculate or populate TP, FN, TN, or FP counts.
- Separate LangChain demonstration scripts are present for OpenAI GPT, Google Gemini, and Hugging Face Mistral.
- Explanatory comments have been added, and Flake8 checks have been reported as passing.
- Live API calls have not yet been verified; they are pending organizational credentials, billing/access guidance, and model/provider availability.

### Week 3

The `src/week_03/` directory is reserved for condition-specific prompts, prompt testing, and evaluation work. Work should be documented as it is implemented.

### Shared utilities

The `src/common/` directory is reserved for utilities that are genuinely reusable across assignment weeks. Code should only be moved here when there is a clear reuse case.

## Repository structure

```text
vetology-radiology-evaluation/
├── src/
│   ├── week_02/
│   │   ├── main.py
│   │   ├── test_openai_api.py
│   │   ├── test_gemini_api.py
│   │   └── test_huggingface_mistral.py
│   ├── week_03/
│   │   └── .gitkeep
│   └── common/
│       └── .gitkeep
├── docs/
│   ├── project_documentation.md
│   ├── CHANGELOG.md
│   ├── DECISION_LOG.md
│   ├── testing_log.md
│   └── weekly_progress.md
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

The `.gitkeep` files keep the currently empty `week_03` and `common` directories visible in Git. They can be removed once those directories contain tracked project files.

## Prerequisites

- Python installed on your machine.
- Git for version control.
- Visual Studio Code or another Python-compatible editor is recommended.

The project has been developed and tested in a Windows PowerShell environment using a Python virtual environment.

## Setup

Run the following commands from the repository root.

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, use an approved local execution-policy approach or activate the environment through the VS Code Python interpreter selector.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` records the direct dependencies and versions currently identified for the project. Update it when new direct dependencies are introduced.

## Environment configuration and API credentials

The `.env.example` file documents the environment variable names used by the API demonstration scripts:

```text
OPENAI_API_KEY=
GOOGLE_API_KEY=
HUGGINGFACEHUB_API_TOKEN=
```

To configure credentials:

1. Make a private local copy named `.env` if you use a local environment-file workflow.
2. Add the appropriate credentials to your local configuration.
3. Ensure `.env` is never committed to Git.

**Important:** The current API scripts read credentials from environment variables. A plain `.env` file is not automatically loaded by Python unless a dotenv-loading mechanism is added. You can instead set the variables in your terminal/session or configure them through your development environment. Never put real credentials in `.env.example` or in source code.

Live API testing remains pending until the required organizational access and provider availability are confirmed.

## Week 2: Excel scaffold

Run the command-line program from the repository root:

```powershell
python src/week_02/main.py "path\to\input.xlsx"
```

To specify an output workbook path:

```powershell
python src/week_02/main.py "path\to\input.xlsx" -o "path\to\output.xlsx"
```

If `-o` is omitted, the program creates an output file using the input file's name with the `_confusion_matrix.xlsx` suffix.

The current scaffold identifies condition names dynamically from the input workbook. It assumes the first eight columns contain metadata and report fields, with condition columns following them.

The generated workbook contains the confusion-matrix structure and formulas. Actual confusion-matrix counts and derived evaluation results are not populated by the current scaffold.

Use authorized test data when testing. Do not add raw or manually labelled datasets to the repository unless sharing has been explicitly approved.

## API demonstration scripts

The following scripts are located in `src/week_02/`:

| Script | Purpose |
|---|---|
| `test_openai_api.py` | Demonstrates a LangChain connection to an OpenAI model. |
| `test_gemini_api.py` | Demonstrates a LangChain connection to a Google Gemini model. |
| `test_huggingface_mistral.py` | Demonstrates a LangChain connection to a hosted Hugging Face Mistral model. |

These are separate API demonstration scripts. Their presence does not mean that live API execution has been successfully verified.

## Code quality checks

Run Flake8 against the Week 2 Python scripts from the repository root:

```powershell
python -m flake8 src/week_02/
```

Run the command-line help check:

```powershell
python src/week_02/main.py --help
```

Record test commands, outcomes, and any limitations in `docs/testing_log.md`.

## Documentation and version control

Project documentation is maintained in `docs/`:

- `project_documentation.md` — consolidated technical project documentation.
- `CHANGELOG.md` — chronological record of meaningful changes.
- `DECISION_LOG.md` — technical decisions, rationale, alternatives, and consequences.
- `testing_log.md` — test commands, results, and outstanding verification.
- `weekly_progress.md` — progress against weekly assignment requirements.

Use meaningful Git commits for changes and milestone tags for significant weekly baselines. Keep the documentation aligned with the actual implementation and distinguish completed, pending, and planned work.

## Security and data handling

Do not commit or publish:

- API keys, tokens, passwords, or populated `.env` files.
- Raw radiology datasets or manually labelled datasets.
- Patient-identifiable, confidential, or otherwise restricted Vetology information.
- Local virtual environments or generated files that are not intended to be version-controlled.

Follow organizational authorization and data-handling requirements before sharing project files or data with collaborators.
