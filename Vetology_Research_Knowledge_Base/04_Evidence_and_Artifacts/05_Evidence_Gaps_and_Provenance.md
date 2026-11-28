# 05 — Evidence Gaps and Provenance

## 1. Provenance classes (counts from `01_Evidence_Inventory.csv`, 86 rows)

| Class | Meaning | Examples |
|---|---|---|
| Inspected and verified (W8) | File present here; hash computed; contents checked where relevant | 10 source extractions; 4 run manifests; 9 prompt and config files; code, tests and docs (presence and hash) |
| Recorded, not independently verified | Values stated in docs or extractions with no accessible artifact | All confusion counts (EVAL-01–14); agreement (AGR-01/02); test counts |
| Referenced but inaccessible | Artifact known to exist (or claimed) but not available here | All input workbooks, predictions, evaluation and comparison workbooks; Week 4 baselines A1–A6; Week 6 presentation files; programme webpage; Week 4/5 reports |
| Missing | No evidence that it exists | Two Claude extractions; Week 6 feedback record; advisor's original message; FT/CA per-condition metrics; Week 6 one-page outline; peer-review records |
| Conflicting | Sources disagree | C-01 to C-20 in `../03_Consolidated_Knowledge_Base/07_Source_Crosswalk_and_Verification_Register.md` §3 |

## 2. Source package gap

- Six Claude extraction documents were planned; **four were supplied** (KB_07–KB_10). The missing two were not fabricated (EV-S11).
- Companion extraction documents referenced but not supplied: `Vetology_Week07_Gemini_Knowledge_Extraction.docx` (KB_08, KB_09), a companion to KB_10, and `Vetology_Research_Knowledge_Extraction.docx` (KB_03). See EV-S12 and EV-S13.
- **Action:** the user should confirm whether the two missing Claude documents exist and add them to `02_Claude_Extractions/` if so.

## 3. Critical evidence gaps (ranked)

| # | Gap | Effect on the paper | Required action | Expected location |
|---|---|---|---|---|
| G-1 | FT/CA Matrix 1 and Matrix 2 evaluation workbooks not accessible; metrics rely on KB_02 alone; repository docs contradict them (C-01, C-14) | Results for 2 of the 3 required datasets are unverified | Open the four workbooks locally; confirm TP/FN/TN/FP and rates; record workbook SHA-256; if missing, re-run `python -m week_07 evaluate` (offline, no API) | `outputs/week_07/{feline_thorax,canine_abdomen}/matrix_{1,2}/*_evaluation_workbook.xlsx` (developer machine) |
| G-2 | Per-condition confusion counts for all six dataset × matrix combinations | The required Results tables (per-condition sensitivity and specificity) cannot be built | Export Condition Summary sheets from all evaluation workbooks | Same, plus `outputs/week_05/…`, `outputs/week_07/matrix_{1,2}/` |
| G-3 | CT Week 4/5/7 workbooks inaccessible | Headline CT numbers rest on documentation | Re-open or re-evaluate from retained predictions | `data/week_04_baseline/`, `outputs/week_05/`, `outputs/week_07/` |
| G-4 | Gold Standard nature and adjudication (C-03); FT/CA "draft" status | Limitations wording; validity of Matrix 2 | Confirm with Vetology who scored or approved it and how; record the 21-difference resolution | Vetology / user records |
| G-5 | Repository documentation is stale on FT/CA (README L9, L16–17; testing_log L358, L384; CHANGELOG L282–312; project_documentation L504) | Repository contradicts results | Update the docs after G-1 (future task; **not** done in Week 8 to avoid editing outside the knowledge-base scope) | repository docs |
| G-6 | No veterinary adjudication of mismatches | Failure analysis limited to text screening | Adjudication by an expert | — |
| G-7 | No repeat runs / variance estimate (beyond the incidental Week 4 8/2,000) | Limitations | ≥2 runs per model and application, only with approval | — |
| G-8 | Model snapshot IDs, API request IDs and cost not recorded | Reproducibility statement | Recover from provider dashboards if possible; otherwise state as a limitation | provider accounts |
| G-9 | Week 6 feedback, outline and peer-review evidence | Assignment status claims | Recover meeting notes, emails or chat logs | user |
| G-10 | Prompt lineage for FT/CA Week 3 "V1.3" (C-04) | Method section prompt history | Locate the Week 3 Word files | user |
| G-11 | Error text for the three Gemini Matrix 2 trial failures | Completeness of the operational record | Read the local `errors.jsonl` | `outputs/week_07/matrix_2/errors.jsonl` |
| G-12 | Hashes for evaluation and comparison workbooks never recorded | Traceability | Record SHA-256 when they are re-opened | inventory EV-A rows |

## 4. Items the paper must not claim without new evidence

- Any FT/CA number presented as verified (G-1).
- That the Gold Standard is expert or veterinary-radiologist ground truth (G-4, C-03).
- Clinical validity, diagnostic safety, or production or commercial readiness.
- That Claude Code improved model accuracy, or that development time was saved.
- That Week 6 feedback was incorporated, or that peer reviews were completed.
- Novelty against the literature.
- Per-condition Canine Abdomen values from KB_02 Table 12 before re-verification.

## 5. Sensitive-data and secret handling in this knowledge base

- No report text, case-level label tables, patient or clinic identifiers, credentials, API keys or `.env` contents were copied into `03_` or `04_`. A pattern scan of the ten source documents for common key formats found no match.
- The original source documents (`01_`, `02_`) are preserved unmodified, as instructed. KB_05 and KB_06 contain a small number of encoded pilot CaseIDs (1–100 range) and V1.0/V1.1 manual review labels for five selected cases per dataset. These are encoded indices, not patient identifiers, and were **not** reproduced in the consolidated documents.
- No datasets or large artifacts were duplicated into the repository.

## 6. Verification actions completed in Week 8

1. Extracted the source ZIP (10 files) and hashed each document.
2. Confirmed the branch and Git lineage, and resolved the tag identity (C-10).
3. Read all four committed manifests; hashes match KB_02 T14 for FT/CA (C-13 typo resolved).
4. Hashed all prompt files; all match the registry pins; CT V1.3 is identical across three weeks.
5. Recomputed every documented rate from its counts (Derived). All match except the F1 rounding note (C-02).
6. Confirmed that no evaluation workbook or prediction JSONL is present anywhere in this environment.
