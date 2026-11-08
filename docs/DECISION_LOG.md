# Decision Log

Decisions are recorded to preserve the reasoning behind data handling, implementation, and evaluation choices. Status refers to the current project record.

| ID | Area | Decision | Rationale | Status |
|---|---|---|---|---|
| D-001 | CLI | Use `argparse` for input and optional output paths in the Week 2 scaffold. | Supports terminal-based execution. | Implemented |
| D-002 | Excel | Use `openpyxl` for workbook processing. | Supports reading and generating Excel workbooks. | Implemented |
| D-003 | Output | Use the supplied example confusion-matrix workbook as the structural/formatting reference. | Maintains the requested output layout. | Implemented |
| D-004 | Conditions | Week 2 scaffold detects condition names dynamically after the first eight metadata columns. | Avoids hardcoding condition names in that scaffold. | Implemented |
| D-005 | Credentials | Read API credentials from environment variables; Week 4 loads the root `.env` with `python-dotenv`. | Avoids hardcoding secrets and supports local configuration. | Implemented |
| D-006 | Integrations | Keep the Week 2 OpenAI, Gemini, and Hugging Face demonstrations separate. | Allows independent experimentation. | Implemented |
| D-007 | Documentation | Maintain Markdown documentation for project history, decisions, testing, and progress. | Provides an auditable development record. | Implemented |
| D-008 | Evaluation labels | Use exactly `Positive` and `Negative`; do not treat legacy Abnormal/Normal labels as ground truth. | Keeps the evaluation aligned with the approved binary scoring convention. | Adopted |
| D-009 | Gold Standard | Use the approved canine thorax Gold Standard for CaseID 1–100 as the Week 4 evaluation reference. | Establishes one consistent reference for the baseline evaluation. | Adopted |
| D-010 | LLM input | Send only original radiologist Findings, Conclusions, and Recommendations to the LLM; retain CaseID locally for tracking. Exclude AI-generated report fields and Gold Standard labels. | Prevents reference-label leakage and avoids using the second AI report as model input. | Implemented |
| D-011 | Prompt interpretation | Use the V1.3 master prompt rules for all 20 conditions, including the possible/suspected finding rule and condition-specific constraints. | Makes classification behavior explicit and consistent. | Implemented |
| D-012 | Structured output | Require strict JSON with exactly the 20 expected condition keys and exact `Positive`/`Negative` values. | Enables deterministic validation and downstream evaluation. | Implemented |
| D-013 | Batch processing | Process cases sequentially and checkpoint validated successes; retry failed cases and log errors separately. | Supports recoverability and prevents completed cases from being unnecessarily reprocessed. | Implemented |
| D-014 | Evaluation baseline | Preserve original predictions and approved Gold Standard while mismatches are reviewed. | Provisional review is not an authorized correction to the reference labels. | Active |
| D-015 | Mismatch review | Use the original Block 6 Mismatch Review source as the authoritative source for Gold Standard, prediction, and mismatch type in the consolidated 70-row register. | A condition-specific review workbook contained inconsistent Gold Standard entries; the original evaluation mismatch source was cross-checked. | Implemented |
| D-016 | Week 4 optional configuration | Store the existing V1.3 prompt in a JSON configuration file and load it through a dedicated local loader; do not make API calls for this optional task. | Satisfies the optional “read prompts from a JSON configuration file” requirement while keeping the task isolated from the live LLM workflow. | Implemented and locally tested |
| D-017 | Week 4 Matrix 1 | Preserve Matrix 1 as a separate evaluation artifact and keep its predictions, reference labels, and mismatch register traceable. | Maintains a distinct evaluation record and prevents confusion with Matrix 2. | Implemented; veterinary adjudication pending |
| D-018 | JSON configuration scope | The optional JSON module performs local file reading and configuration validation only; it does not load data, call an API, or execute an LLM. | The requested optional task is specifically prompt configuration, not a second LLM integration. | Implemented |
| D-019 | Prompt integrity | Reuse the exact operational Master Prompt V1.3 text in the JSON configuration; do not revise prompt wording or create a new prompt version. | Keeps the optional task focused on configuration format rather than prompt development. | Implemented |

## Decision template

- ID and title:
- Date:
- Context/problem:
- Options considered:
- Decision and rationale:
- Consequences/trade-offs:
- Related files:
- Related commit/tag:


## Week 4 closeout decisions

- The optional JSON prompt configuration is kept in its own `src/week_04/optional_json_config/` directory and does not alter the existing Matrix 1 implementation.
- The JSON loader validates required configuration fields, V1.3 version, 20 condition keys, and the `Positive` / `Negative` label set.
- Five offline unit tests are required for this module; no API credentials are needed to run them.
- Error-screening notes and provisional root-cause categories must not be treated as veterinary adjudication or as authorization to change reference labels.
