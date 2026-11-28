# 05 — Evidence Gaps and Provenance

Updated in the Week 8 evidence reconciliation against `files-bundle-01.zip` (42 files; EV-B01–EV-B42). The original `ea92818` gap list is kept below with each item's current status.

## 1. Provenance classes (counts from `01_Evidence_Inventory.csv`, 128 rows)

| Class | Meaning | Examples |
|---|---|---|
| Verified against actual workbook / cross-checked against prediction records | Read from workbook cells and reproduced from predictions plus references | All 10 reference evaluations (EVAL-01, 02, 05–08, 11–14), EVAL-01b, AGR-01/02 |
| Supported by manifest | Batch identity confirmed by committed manifests (byte-identical to the bundle copies) | RUN-05 to RUN-08 |
| Inspected and verified (W8) | File hashed; contents checked where relevant | 10 source extractions; 42 bundle files; prompts; code/docs presence |
| Documented but not independently verified | Docs or extractions only | Test-suite counts; EVAL-03/04 replay workbooks; Week 4 FN text screening; hedged-language heuristic |
| Referenced but unavailable | Known artifact not supplied | Week 4 reconciliation QA and adjudication registers; Week 6 presentation files; programme webpage; sample white paper; Week 3 Word prompt documents (except the CT V1.3 .docx) |
| Missing | No evidence that it exists | Two Claude extractions; Week 6 feedback record; advisor's original message; Week 6 outline; peer-review records; Gold Standard review procedure detail; FT/CA "Week 3 V1.3" prompts |
| Conflicting | Sources disagree | Remaining open conflicts in 07 §3 (C-04, C-05, C-14, C-17–C-20) |

## 2. Source-package gap (unchanged)

- Six Claude extraction documents were planned; four were supplied (KB_07–KB_10). The missing two were not fabricated (EV-S11).
- Companion documents are referenced but not supplied (EV-S12, EV-S13).

## 3. Gap register: original items and current status

| # | Gap (as at `ea92818`) | Current status (W8 reconciliation) | Remaining action |
|---|---|---|---|
| G-1 | FT/CA evaluation workbooks inaccessible; metrics from KB_02 alone (C-01) | **Closed.** All four workbooks verified and reproduced from predictions; values identical to KB_02 | None for the evidence. The repository docs are still stale (G-5) |
| G-2 | Per-condition counts missing for all dataset × matrix combinations | **Closed.** All 10 evaluations are captured in `06_Per_Condition_Results.md` | — |
| G-3 | CT Week 4/5/7 workbooks inaccessible | **Closed** for EVAL-01, 02, 05–08. Week 5 replay workbooks (EVAL-03/04) were not supplied | Optional |
| G-4 | Gold Standard nature and adjudication (C-03) | **Wording resolved** by owner clarification: *peer-reviewed and agreed upon after discussion*. **Still Missing:** participants, discussion or approval procedure, how the 21 CT draft-vs-approved differences were settled, and the final status of the FT/CA "draft" workbooks | Owner / Vetology to document if the paper needs it |
| G-5 | Repository docs stale on FT/CA (`README.md` L9, L16–17; `docs/testing_log.md` L358, L384; CHANGELOG; project_documentation L504) | **Open (Conflicting, C-14).** Not changed in Week 8; outside the knowledge-base scope | Future documentation task |
| G-6 | No veterinary adjudication of mismatches | Open | Expert review |
| G-7 | No repeat runs / variance estimate | Partly informed: separate CT batches on identical text differ in 8, 11 and 13 of 2,000 pairs (cross-checked). No designed repeat-run experiment | Approved repeat runs |
| G-8 | Model snapshot IDs, API request IDs, cost | Open (not in predictions, manifests or workbooks) | State as a limitation |
| G-9 | Week 6 feedback, outline, peer review | Open | Owner records |
| G-10 | FT/CA Week 3 "V1.3" prompt lineage (C-04) | Open. The bundle supplies FT V1.1 and CA V1.2 only, and these equal the registry originals | Locate the Week 3 Word files |
| G-11 | Gemini Matrix 2 trial failure text | **Closed.** CaseID 1: two HTTP 503 errors and one 504 (EV-B40) | — |
| G-12 | Workbook hashes never recorded | **Closed.** All 42 bundle hashes are in the inventory | — |
| G-13 *(new)* | Week 5 replay (EVAL-03/04) and Week 4 adjudication/QA workbooks not supplied | Referenced but unavailable | Optional |
| G-14 *(new)* | Matrix 2 workbooks record no generation timestamp or prompt version | Missing in the artifact. Linkage relies on the shared prediction file and manifest | — |

## 4. Items the paper must not claim without new evidence

- That the Gold Standard is formal independent expert adjudication, or that it was independently assigned by a veterinary radiologist (the owner clarification states peer review and agreement after discussion).
- Clinical validity, diagnostic accuracy on images, diagnostic safety, or production or commercial readiness. These are report-text classification pilots.
- That higher Matrix 2 scores show model improvement. They reflect a different reference set.
- That model agreement (97.00% / 97.20%) is accuracy.
- That high specificity with low sensitivity is strong overall performance.
- That Claude Code improved model accuracy, or that development time was saved.
- That the supplied FT V1.1 or CA V1.2 prompt files produced the reported results.
- That Week 6 feedback was incorporated, that peer reviews were completed, or novelty against the literature.

## 5. Sensitive data and secrets

- The bundle was extracted to a temporary scratch location and **not committed**. No datasets, predictions, workbooks or report text were copied into the repository.
- The knowledge base records only aggregate and per-condition counts and rates, hashes, paths, sheet/cell references and error categories.
- The Week 5 error log contains an authentication-error message. **No key value is present or reproduced**; only the category (HTTP 401, expired key) is recorded.
- Matrix 2 Execution Logs and Case Predictions sheets contain case-level rows. These were not reproduced.
- The original ten extraction documents are unchanged (SHA-256 re-checked before commit).

## 6. Verification actions completed in the Week 8 reconciliation

1. Confirmed the branch is `week-08/research-paper-development` and that `ea92818` is an ancestor. No history rewrite.
2. Extracted the bundle (42 files) to a scratch directory and hashed every file.
3. Read the aggregate and condition-level summaries, confusion matrices and execution logs of 11 evaluation workbooks and 2 comparison workbooks.
4. Recomputed every rate from its counts and reproduced every confusion count from the predictions and reference workbooks (exact).
5. Recomputed both agreement analyses and the three run-to-run comparisons from the prediction files.
6. Compared manifests, prompt files and input workbooks with the committed pins and manifests.
7. Inspected the Matrix 1 terminology (workbook labels, D-041, `matrix1_workbook.py`, `reference_loader.py`, source workbook headers and prevalence).
8. Checked the Week 4 technical report for the F1 discrepancy (C-02).
