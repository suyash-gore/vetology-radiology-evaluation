# Decision Log

| ID | Area | Decision | Rationale | Status |
|---|---|---|---|---|
| D-001 | CLI | Use `argparse` for input and optional output paths. | Enables terminal-based execution. | Implemented |
| D-002 | Excel | Use `openpyxl`. | Supports reading and generating Excel workbooks. | Implemented |
| D-003 | Output | Use the example confusion matrix for structure and formatting. | Maintains the requested output layout. | Implemented |
| D-004 | Conditions | Detect condition names dynamically after the first eight metadata columns. | Avoids hardcoding disease names. | Implemented |
| D-005 | Credentials | Read API credentials from environment variables. | Avoids hardcoding secrets. | Implemented in demo scripts |
| D-006 | Integrations | Keep OpenAI, Gemini, and Hugging Face demos separate. | Allows independent testing. | Implemented |
| D-007 | Documentation | Maintain Markdown in Git and a consolidated Word report. | Supports developer-facing history and formal reporting. | Planned |

## Decision template
- ID and title:
- Date:
- Context/problem:
- Options considered:
- Decision and rationale:
- Consequences/trade-offs:
- Related files:
- Related commit/tag:
