# 04 — Technical Architecture and Reproducibility

Primary sources: KB_09 (architecture), KB_07 §5, KB_10 §5, KB_04 §6, KB_05 §2, KB_08 §5.
Repository anchor: `ceb3f42` on `week-08/research-paper-development`. Line counts and import analyses are *Derived* by earlier sessions (KB_09, KB_10) and were not recounted in Week 8.

## 1. Architecture lineage

| Aspect | Week 4 (`src/week_04`, main) | Week 5 (`src/week_05`) | Week 7 Gemini (`src/week_07` @ `a843a9a`) | Week 7 extension (`ceb3f42`) |
|---|---|---|---|---|
| Structure | Scripts/blocks; separate `matrix_1/` folder; delivery .zip files | Single package, `python -m week_05`, WorkflowSpec, CLI | Package with provider, safety and comparison layers | Application registry over the same package (`--application`) |
| Applications | Canine Thorax | Canine Thorax | Canine Thorax | Canine Thorax, Feline Thorax, Canine Abdomen |
| Model | gpt-4.1-mini | gpt-4.1-mini | gemini-3.8-flash | Gemini (CT); gpt-4.1-mini (FT, CA) |
| Client | New ChatOpenAI per case | One per batch | ChatGoogleGenerativeAI, one per batch | Gemini or OpenAI via `providers.py` |
| Retries | 2 application attempts × LangChain `max_retries=2`; everything retried | Same, plus fail-fast configuration | 2 application attempts × 1 transport attempt; typed fatal/transient/retryable classification; backoff 2 s × 2ⁿ capped at 30 s | Same policy; OpenAI transport retries 0 |
| Prompt integrity | File loaded; no pinning documented | SHA-256 of file and stripped text | Same (verbatim) | Per-application registry; superseded versions retained |
| Evaluators | Matrix 1 evaluator only; **Matrix 2 evaluator source never in the repository** | Both rebuilt; parity with delivered workbooks | Verbatim Week 5 engine | Application-aware wrappers over the verbatim engine |
| Provenance | None beyond JSONL records | JSONL schema only | `run_manifest.json` per workflow | Extended identity (application, keys, prompt, normalisation, provider) |
| Isolation | Not documented | Refuses other workflow folders and `outputs/week_04` | Central write guard; protected roots; ReadOnlyGuard | Isolation by `<application>/<workflow>`, read and write |
| Comparison | — | — | Six-sheet OpenAI-vs-Gemini workbook (CT) | **Not generalised** to FT/CA (TD7) |
| Tests | Standalone scripts (21 test functions) | 338 unittest | 288 | 504 (claimed; see §5) |

Sources: KB_07 Table 16; KB_09 Table 17; KB_10 Tables 7–8, 28.

### 1.1 Code size (Derived by earlier sessions)

| Version | Source modules / lines | Test modules / lines | Total Python lines | Source |
|---|---|---|---|---|
| Week 4 | 12 / 1,535 | 8 / 561 | 2,096 (20 files) | KB_09 T6; KB_10 T28 |
| Week 5 | 20 / 3,173 | 16 / 4,383 | 7,556 (36 files) | KB_09 T6; KB_10 T28 |
| Week 7 Gemini | 28 / 5,281 | 21 / 4,025 | 9,306 (49 files) | same |
| Week 7 extension | 37 / 7,795 | 31 / 6,882 | 14,677 (68 files) | same |

The presentation and Week 5 report use rounded figures (~2,100 and ~7,600 or ~7,560; KB_03 slide 7, KB_04 §1). These are consistent within rounding (C-11).
No version has packaging metadata, CI configuration or a container definition (KB_09 §5.1).

## 2. Implemented pipeline (Week 7 extension; KB_07 §5.11, traced through the code at `ceb3f42`)

1. CLI dispatch (`cli.py`), with `--application` selecting the registry entry.
2. For FT/CA, the application workflow must be stated explicitly; a Matrix 2 batch is refused.
3. Provider resolution (`providers.py`).
4. Output guard (`isolation.py`): writes confined to `outputs/week_07/<application>/`.
5. Load and validate cases (`app_dataset_loader.py`): exactly 100 Matrix 1 cases; labels validated (with Feline normalisation) and then discarded.
6. Prompt and run identity (`prompts/registry.py`, `run_manifest.py`): a pending or modified prompt stops the run before any write.
7. Classify → strict validation → checkpoint: `predictions.jsonl` on success, `errors.jsonl` when attempts are exhausted.
8–14. Evaluation, offline: prediction-source check → ReadOnlyGuard (SHA-256 before and after) → manifest verification → reference loading with workflow rules (Matrix 2 ambiguity guardrail, cross-matrix check) → strict reconciliation → metrics (`metrics.py`, verbatim) → A5 (Matrix 1, six sheets) or A6 (Matrix 2, five sheets) workbook.

Workbook layouts (KB_07 Table 15): the Matrix 1 Confusion Matrix sheet has TP/FN/TN/FP, sensitivity, specificity, checks, ground-truth counts, accuracy, precision, F1 and a TOTAL (micro) row. The Matrix 2 sheet has a "Radiologist Agreement Rate" column set to "N/A" because no separate reference was supplied.

Module catalogue and layering: see KB_09 Tables 7 and 10. Prompt and model integration points: KB_09 Table 8.

## 3. Reproducibility controls (with evidence status)

| Control | Mechanism | Evidence | Status |
|---|---|---|---|
| Same prompt | File and stripped-text SHA-256 pinned; recorded in every manifest | All four manifests list the prompt digests; the Week 8 recomputed file SHA-256 of all six prompt files equals the registry pins | **Verified (W8)** |
| Prompt identical across weeks | Canine Thorax V1.3 byte-identical in `src/week_04`, `src/week_05`, `src/week_07` | SHA-256 `31a7dab6…7ab7b1` (8,715 bytes) for all three | **Verified (W8)** |
| Same input | Input workbook SHA-256 in run identity; evaluation refuses a mismatch | Manifest digests equal the SHA-256 of the supplied bundle workbooks | **Verified (W8 reconciliation)** |
| Same configuration | Model, temperature, transport retries, keys and instruction in identity; resume refused if any changes | `test_app_batch` (KB_07) | Recorded (tests) |
| Deterministic setting | Temperature 0 | Manifests | Verified (W8) |
| Environment record | Package versions per run | Manifests: Python 3.14.6; langchain-openai 1.7.2; openai 3.49.0; langchain-google-genai 4.4.2; google-genai 2.31.0; langchain-core 1.7.7; httpx 0.28.1; openpyxl 3.1.5 | Verified (W8) |
| Unchanged sources during evaluation | ReadOnlyGuard digests | Tests; KB_02 reports evaluation terminal output saying no API call was made and sources were unchanged | Recorded |
| Single retry layer | SDK transport attempts fixed; application owns retries | Manifests: `transport_attempts_per_application_attempt: 1` | Verified (W8) |
| Shared predictions across references (FT/CA) | One batch, cross-matrix CaseID/report-text identity check | Manifest `predictions_reused_by_workflows`; real-data check showed 0 differences (Observed (prior), KB_07 §8.4) | Verified (W8) / Observed (prior) |
| Known non-determinism | Model output varies even at temperature 0 | Separate CT batches on identical text: Week 4 8/2,000 pairs; Week 5 11/2,000; Week 7 Gemini 13/2,000 | **Cross-checked against prediction records** (W8) |

**Week 8 reproducibility check against the supplied artifacts (`files-bundle-01.zip`):**
- The bundle manifests are byte-identical to the committed manifests (EV-R01 to EV-R04).
- The bundle input workbooks match the manifest `input_workbook.sha256` values. The CT Matrix 1 input was supplied under the name `Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx`, but its hash is `3f1a17b7…`, the manifest's `Vetology_Matrix1_First100_Encoded.xlsx`.
- The FT/CA prediction-file hashes equal the KB_02 records. The comparison workbooks' Execution Logs list prediction and error-log hashes that equal the bundle files.
- Independent recomputation from predictions and references reproduced every workbook confusion count. This means the evaluation stack is reproducible **from retained artifacts**. It does **not** mean model outputs are reproducible: separate batches on identical text differ in 8–13 of 2,000 pairs.

**Gaps in reproducibility:**
- Exact model snapshot identifiers are not recorded.
- API request IDs are not recorded.
- Prediction, evaluation and comparison artifacts are gitignored. They are now available as the owner-supplied bundle (hashes in the inventory) but are not version-controlled.
- Only one live run per model and application (except the incidental Week 4 pair).
- `google-genai` docstrings cite 2.34.0, while 2.31.0 was pinned and executed (KB_08 D-02; KB_09 TD4).

## 4. Data protection and security (Demonstrated within the pipeline; not a governance assessment)

- Only three report fields are sent to the model; CaseID is excluded; keys are read by the SDKs from the environment and never stored or logged (KB_07 §5.6, T37).
- `.gitignore` excludes `.env`, `.env.*` (except `.env.example`), `data/`, `datasets/`, `*.xlsx`, `*.xls`, `*.xlsm`, `*.jsonl` and `*.log` (Verified W8).
- The committed manifests contain no key patterns, absolute paths, report text or labels (KB_08 A-21; consistent with the Week 8 inspection of manifest fields).
- Vendor data-processing terms have **not** been assessed (KB_08 T20).

## 5. Software quality evidence (not clinical evidence)

| Suite | Environment | Result | Status | Source |
|---|---|---|---|---|
| Week 4 | Windows (developer) | Matrix 1: 10 tests passed; optional JSON config: 5 offline tests | Recorded | KB_05 T12 |
| Week 5 | Linux, artifacts present, network blocked | 338/338 passed, 0 skipped | Observed (prior) | KB_10 T15; KB_04 T15 |
| Week 5 | Linux, artifacts absent | 338: 329 passed, 9 skipped | Observed (prior) | KB_10 T15; KB_07 T30 |
| Week 5 | Windows 11, Python 3.14.6 (`f20c240`) | 338: 329 passed, 9 skipped (artifact-dependent); earlier runs: 9F/27E, then 7F/1E | Recorded | KB_04 T16; KB_03 §7.3 |
| Week 7 Gemini | Windows (owner) | 288: 282 passed, 6 skipped; local artifact tests 6: 4 passed, 2 skipped | Recorded | KB_08 §8; `docs/testing_log.md` |
| Week 7 Gemini | Linux (Claude) | 288 OK, 5 skipped | Observed (prior) | KB_07 T30; KB_09 T13 |
| Week 7 extension | Claimed at `65274d6` | 504: 499 passed, 5 skipped | Recorded | KB_07 T30; KB_10 T28 |
| Week 7 extension | Linux re-run in a `ceb3f42` export (KB_07) | 504 OK, 6 skipped (Git-dependent test skipped in the export) | Observed (prior) | KB_07 T30 |
| Week 7 extension | Linux re-run without `openai` (KB_09) | 455 run, 2 module import errors, 6 skipped | Observed (prior) | KB_09 T13 |
| Week 5 parity tests in Week 7 | — | 16/16 | Observed (prior) | KB_07 |
| flake8 (max line 100) | Linux | Clean at `a843a9a` and `ceb3f42`; **not rerun on Windows** for Week 5 | Observed (prior) | KB_09; KB_04 |

The skip counts differ because of the environment: artifact availability, a Windows-only symlink skip and Git availability in the export (C-07, C-08, C-09). Week 8 did **not** run any test suite (resource constraint; not needed for any evidence claim here).

## 6. Technical debt and scalability (Derived; proposals only)

From KB_09 Table 21 and Table 20:
- Duplicated verbatim modules (by design).
- Mixed CRLF/LF line endings with no `.gitattributes`.
- Tests depend on private SDK internals.
- Hard-coded 100-case limits.
- Sequential processing that ignores Retry-After.
- Comparison package is not application-aware.
- Hub modules grew large (config 634 lines, cli 569, batch_runner 486).
- No packaging, CI or containers.
- One `requirements.txt` covers Weeks 2–7.
- Weeks 5 and 7 are not merged to `main`.
- Matrix 1 workbook uses "Gold Standard" wording for the Vetology labels.

Throughput: about 20 minutes per 100 Gemini cases (manifest timing). The OpenAI FT/CA batches took about 4.3 and 2.3 minutes (Verified (W8) from manifest timestamps; Derived).
