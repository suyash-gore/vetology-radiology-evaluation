# 04 — Evidence and Artifacts

These registers support the consolidated knowledge base (`../03_Consolidated_Knowledge_Base/`). They **reference** repository paths, commits and hashes. They do not copy datasets, predictions, report text, case-level records, credentials or `.env` contents.

Prepared 2026-11-28 on `week-08/research-paper-development`. The repository base is `ceb3f42` (`ceb3f42c0bf8b66a82dd8ec7d6fc45bd59ec3681`, 2026-11-21 22:31:58 +0530).

## Contents

| File | Content |
|---|---|
| 01_Evidence_Inventory.csv | 86 rows: source extractions (EV-S), run manifests and records (EV-R), prompts and configuration (EV-P), code and tests (EV-C), documentation (EV-D), inaccessible or missing artifacts (EV-A). SHA-256 and size are computed in Week 8 for every file present in this environment |
| 02_Experimental_Run_Register.md | Every identifiable prediction batch (RUN-xx), with manifest reference and verification status |
| 03_Confusion_Matrix_and_Metrics_Register.md | One record per evaluation (EVAL-xx), separated by dataset, matrix, model and run; agreement records (AGR-xx) kept apart |
| 04_Prompts_and_Configurations_Index.md | Prompt versions, hashes, model configurations and the run each was used in |
| 05_Evidence_Gaps_and_Provenance.md | Missing, inaccessible, unverified and conflicting evidence, with actions needed |

## What was inspected in Week 8 (one consolidated pass)

- Git: `git log`, tags, remote branch list. No branch switch; `main`, Week 5 and Week 7 branches were not modified.
- All four committed run manifests: contents read; SHA-256 computed.
- `outputs/week_04/matrix_1/single_case_test.json`: keys only.
- All prompt files in `src/week_04`, `src/week_05`, `src/week_07` (SHA-256).
- Targeted searches of `README.md` and `docs/*.md` for recorded result values and status statements.
- Presence and hashes of the evaluation workbook builders, metric engines, registries and key test modules.
- A search of the filesystem for `*.xlsx` and `predictions*.jsonl`: **none present**. No evaluation workbook or prediction file was accessible.
- **Not done** (by instruction or because unnecessary): no live inference, no rebuild, no test-suite runs, no source-code changes.

## Status vocabulary

As in `../03_Consolidated_Knowledge_Base/00_README.md` §3: Verified (W8), Observed (prior), Recorded, Derived, Inaccessible, Missing, Conflict.

## Storage policy

Large or confidential artifacts (input workbooks, predictions, evaluation and comparison workbooks) are gitignored (`data/`, `*.xlsx`, `*.jsonl`). They are on the developer's machine and must **not** be committed. Their expected paths and recorded hashes are in the inventory, so they can be checked later without placing them in the repository.
