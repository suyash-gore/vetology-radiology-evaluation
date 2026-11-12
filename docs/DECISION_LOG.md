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


## Week 5 decisions — Claude Code rebuild

All Week 5 decisions were reviewed and approved phase by phase. "Preserved" means Week 4 behaviour was kept deliberately.

| ID | Area | Decision | Rationale | Status |
|---|---|---|---|---|
| D-020 | Scope | Rebuild independently under `src/week_05/`; never import or modify `src/week_04/` at runtime (Week 4 is used only by parity tests). | Week 5 assignment; Week 4 remains the historical record. | Implemented |
| D-021 | Prompt | Use Canine Thorax Master Prompt V1.3 byte-for-byte; refuse to load it if its SHA-256 digests change. | Prompt wording is part of the classification method. | Implemented |
| D-022 | LLM configuration | Keep `gpt-4.1-mini`, temperature 0, 90 s timeout, 2 LangChain transport retries, 2 application attempts; same `.env` variables. | Unchanged methodology. | Preserved |
| D-023 | Configuration errors (P6) | Validate the API key and settings before classification; stop the run on a configuration error. | Prevents one failure record per case for a missing key. Classification results unaffected. | Approved; implemented |
| D-024 | LLM client | Reuse one OpenAI client per batch with identical constructor arguments. | Efficiency; request payloads verified identical to Week 4. | Approved; implemented |
| D-025 | Data separation | One loader for both workflows; LLM payload restricted to the three original report fields; reference labels held separately. | Prevents reference-label leakage. | Implemented |
| D-026 | CaseIDs | Keep Week 4 CaseID handling (whole-number decimals become integers; other values kept as read); no stricter validation. | Decided after reviewing; to be revisited only with evidence. | Preserved |
| D-027 | Response key order | Accept any key order and return canonical order. | Week 4 behaviour; stricter checks could change retries and results. | Preserved |
| D-028 | Prediction JSONL (P2) | No provenance fields added; Week 4 record structure kept exactly. | Compatibility with Week 4 prediction files. | Preserved |
| D-029 | Error logging (P3) | Keep Week 4 error logging, including stale failure lines after a later success. | Not approved for change. | Preserved |
| D-030 | Interrupted writes | Start a new line before appending if a JSONL file ends without one. | Week 4 corrupted the next record and reclassified that case on every run. Normal-run output unchanged. | Approved; implemented |
| D-031 | Matrix 1 case count | Matrix 1 batch always processes exactly 100 cases (no `--limit`); Matrix 2 keeps `--limit`. | Week 4 behaviour per workflow. | Preserved |
| D-032 | Metrics | Keep Week 4 formulas, micro/macro aggregation and undefined handling, including undefined F1 when TP = 0 with FP > 0 and FN > 0. | Unchanged methodology; the F1 edge case is documented, not corrected. | Preserved |
| D-033 | Balanced accuracy | Not added to the metric engine or either workbook. | Not part of the Week 4 methodology. | Decided (not implemented) |
| D-034 | Matrix 1 reference loading for evaluation | Reproduce Week 4 `load_matrix1_inputs` (first sheet, all rows, `int()` CaseIDs, no label trimming), separate from the batch loader. | Original Matrix 1 evaluation behaviour. | Implemented |
| D-035 | Unreadable prediction lines (Option B) | Skip only lines that are not valid JSON, record each in the Execution Log, and still enforce exact CaseID matching and all other validation. | Allows evaluation after crash recovery without hiding incomplete predictions. | Approved; implemented |
| D-036 | Matrix 2 case matching | Exact CaseID-set matching; no 100-case rule. | No evidence of a Matrix 2 case-count rule. | Implemented |
| D-037 | Independent reference loading | Each workflow has its own evaluation reference loader; Matrix 1 rules are never applied to Matrix 2 by assumption. | Original Matrix 2 evaluator is not in the repository. | Implemented |
| D-038 | Matrix 1 workbook (D1) | Follow the delivered Matrix 1 workbook's layout and wording; keep Week 4 metric calculations and regression tests. | The delivered workbook is the baseline actually used. | Approved; implemented |
| D-039 | Matrix 2 reference loading (D3) | Use the Week 4 Matrix 2 batch-loader rules (`Sheet1`, first 100 populated rows, trimmed labels); reject a workbook as ambiguous if the alternative Week 4 evaluator-style rules give any different result. | The baseline could not distinguish the two approaches; conflicting results are not chosen silently. | Approved; implemented |
| D-040 | Matrix 2 workbook (D2, D4–D8) | Reproduce the delivered Matrix 2 structure without its Balanced Accuracy row and without macro metrics; generate run-specific wording from results; derive batch details from prediction records and disclose the failure-count source; exclude input file names and timestamps from parity comparisons; sort cases by CaseID. | Parity with the delivered baseline within approved methodology. | Approved; implemented |
| D-041 | Terminology | Keep "Gold Standard" wording in the Matrix 1 workbook (refers to the original Vetology scores) until a change is approved. | Parity with the delivered workbook. | Preserved |
| D-042 | Dependencies | Pin every directly imported package (`langchain-core`, `openai`, `httpx` added at their tested versions). | Reproducibility without relying on transitive installs. | Implemented |
| D-043 | JSONL platform compatibility | Use platform-native newline translation for JSONL writes and platform-aware raw-byte tests; preserve pre-existing bytes during interrupted-write recovery. | Matches Week 4 behavior on the same operating system and supports Windows CRLF without rewriting existing records. | Implemented and locally verified on Windows (2026-11-12) |
