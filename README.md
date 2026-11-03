# Vetology Radiology Evaluation

## Overview
Repository for the Vetology training assignments involving radiology-report data processing, language-model integrations, and evaluation workflows.

## Current Week 2 status
- Command-line Excel-processing scaffold implemented.
- Reads an input workbook and detects condition headers after the first eight metadata columns.
- Generates an output workbook following the supplied example confusion-matrix structure.
- Separate LangChain demonstration scripts prepared for OpenAI GPT, Google Gemini, and Hugging Face Mistral.
- Explanatory comments added; Flake8 checks reported as passing.
- Live API calls remain untested pending organizational credentials, billing/access guidance, and model availability.
- Confusion-matrix counts are not calculated by the current scaffold.

## Initial repository layout
```text
vetology-radiology-evaluation/
├── main.py
├── test_openai_api.py
├── test_gemini_api.py
├── test_huggingface_mistral.py
├── docs/
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```
Update this tree if/when the actual repository is reorganized into week-specific folders.

## Running the scaffold
```powershell
python main.py "path\to\input.xlsx"
python main.py "path\to\input.xlsx" -o "path\to\output.xlsx"
```

## Quality check
```powershell
flake8 main.py test_openai_api.py test_gemini_api.py test_huggingface_mistral.py
```

## Security
Do not commit API keys, `.env` files, raw datasets, manually labelled datasets, or confidential Vetology information without explicit authorization.
