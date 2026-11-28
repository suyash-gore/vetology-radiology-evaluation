# 03 — Consolidated Knowledge Base

Week 8 consolidation of the Vetology radiology-evaluation research knowledge base. This is **not** the research paper. It turns ten source extraction documents into one traceable reference that later paper drafting can cite.

Prepared: 2026-11-28, on branch `week-08/research-paper-development` (base commit `ceb3f42`).

## 1. Source package

The source package is `Vetology_Research_Knowledge_Base.zip`, attached to the Week 8 conversation. All ten documents were extracted byte-for-byte. Their SHA-256 values are recorded in `../04_Evidence_and_Artifacts/01_Evidence_Inventory.csv` (rows EV-S01 to EV-S10).

| ID | File (as supplied) | Folder | Origin | Main scope |
|---|---|---|---|---|
| KB_01 | KB_01_Research_Paper_Requirements.docx | 01_ChatGPT_Extractions | ChatGPT | Paper requirements, section lengths, strategic direction |
| KB_02 | KB_02_Week_07_Assignment_Review.docx | 01_ChatGPT_Extractions | ChatGPT | Week 7 Feline Thorax / Canine Abdomen review, including evaluation figures |
| KB_03 | KB_03_Week_06_Assignment_Summary.docx | 01_ChatGPT_Extractions | ChatGPT | Week 6 presentation, feedback evidence status, initial outline |
| KB_04 | KB_04_Week_05_Assignment_Review.docx | 01_ChatGPT_Extractions | ChatGPT | Week 5 Claude Code rebuild compared with Week 4 |
| KB_05 | KB_05_Week_04_Assignment_Summary.docx | 01_ChatGPT_Extractions | ChatGPT | Week 4 original application and both matrices |
| KB_06 | KB_06_Week_03_Assignment_Summary.docx | 01_ChatGPT_Extractions | ChatGPT | Week 3 prompt engineering, condition definitions, Gold Standard decisions |
| KB_07 | KB_07_Claude_Week_07_Radiology_Evaluation.docx | 02_Claude_Extractions | Claude Code | Week 7 multi-application extension, provenance, prevalence |
| KB_08 | KB_08_Claude_Week_07_Documentation_Closeout.docx | 02_Claude_Extractions | Claude Code | Week 7 Gemini documentation closeout and accuracy audit |
| KB_09 | KB_09_Claude_Week_07_Architecture_Inspection.docx | 02_Claude_Extractions | Claude Code | Week 7 architecture as implemented |
| KB_10 | KB_10_Claude_Week_05_Repository_Inspection.docx | 02_Claude_Extractions | Claude Code | Week 5 repository inspection and parity evidence |

**Inventory discrepancy.** The original extraction plan expected six Claude documents, but four were supplied (KB_07 to KB_10). The two missing documents were **not** recreated. Several supplied documents mention companion extractions that are not in the package. These may or may not be the missing two:

- `Vetology_Week07_Gemini_Knowledge_Extraction.docx` (cited by KB_08; also called "the companion Week 7 knowledge-extraction document" in KB_09).
- "a companion extraction" (KB_10, §1).
- `Vetology_Research_Knowledge_Extraction.docx` (cited by KB_03 as a secondary source).

All of them are recorded as *referenced but not supplied* in `../04_Evidence_and_Artifacts/05_Evidence_Gaps_and_Provenance.md`.

### 1.1 Week 8 evidence reconciliation (second update)

`files-bundle-01.zip` (42 files) was supplied after consolidation commit `ea92818`. It contains the source and reference workbooks, all evaluation workbooks, prediction records, run manifests, two comparison workbooks, three prompt files and five Week 4/5 technical reports. It was extracted to a temporary location only and is **not committed** (gitignored data types; confidential case-level content). Hashes of all 42 files are recorded in `../04_Evidence_and_Artifacts/01_Evidence_Inventory.csv` (rows EV-B01 to EV-B42).

Outcome:
- All 10 reference-based evaluations and both agreement analyses are now **Verified against the actual workbooks** and **cross-checked against prediction records**. No aggregate value changed.
- C-01 (Feline/Abdomen results) and C-02 (F1 rounding) are resolved.
- The Gold Standard provenance is corrected to the owner's clarification (§4).

## 2. Documents in this folder

| File | Purpose |
|---|---|
| 01_Research_Paper_Requirements.md | Confirmed requirements kept separate from recommendations and open format questions |
| 02_Project_History_and_Methodology.md | Week 1–8 chronology; data, prompt, model and evaluation methodology |
| 03_Results_and_Experimental_Findings.md | All numerical results, kept separate by dataset, workflow, model and run |
| 04_Technical_Architecture_and_Reproducibility.md | Architecture lineage (Week 4 → 5 → 7 → extension) and reproducibility controls |
| 05_Decisions_Limitations_and_Open_Questions.md | Decisions (including rejected ones), limitations, unresolved questions |
| 06_Research_Contributions_and_Application_Potential.md | Candidate contributions (provisional); demonstrated capability kept separate from proposed applications |
| 07_Source_Crosswalk_and_Verification_Register.md | Claim → source → repository → artifact trace; contradiction register |

The evidence registers live in `../04_Evidence_and_Artifacts/`.

## 3. Status vocabulary (used in every document)

Evidence statuses added in the reconciliation (used for numerical results):

| Status | Meaning |
|---|---|
| **Verified against actual workbook** | Value read from a named workbook sheet/cell in `files-bundle-01.zip` |
| **Cross-checked against prediction records** | Confusion counts independently recomputed from `predictions.jsonl` plus the source reference workbook, and equal to the workbook |
| **Supported by manifest** | Batch identity and outcome confirmed by a committed `run_manifest.json` |
| **Documented but not independently verified** | Stated in docs or extractions only |
| **Referenced but unavailable** | Known artifact not supplied |
| **Conflicting** | Sources disagree (07 §3) |
| **Missing** | No evidence located |

Original vocabulary:

| Label | Meaning |
|---|---|
| **Verified (W8)** | Checked in this Week 8 session against a committed repository file, Git metadata or a hash computed here |
| **Observed (prior)** | Recorded by a source extraction as directly inspected or executed in an earlier session (for example a Claude session that read gitignored artifacts); not re-inspected in Week 8 |
| **Recorded** | Stated in repository documentation or a source extraction as a reported result; not independently verified |
| **Derived** | Arithmetic computed from recorded values. A consistency check only, not verification |
| **Proposed** | A recommendation; not implemented |
| **Planned** | Agreed future work |
| **Rejected** | Considered and explicitly declined or superseded |
| **Unresolved** | Open question or conflict with no agreed resolution |
| **Inaccessible** | Referenced artifact exists or existed but is not available in this environment |
| **Missing** | No evidence located |
| **Conflict** | Sources disagree; see the contradiction register (07, §3) |

## 4. Integrity rules applied

1. **Gold Standard provenance (owner clarification, 2026-11-28):** the Gold Standard dataset is *peer-reviewed and agreed upon after discussion*. It is not formal independent expert adjudication, and it is not described as independently assigned by a veterinary radiologist.
1. Matrix 1 (original Vetology reference labels; the workbooks' "GS" wording is legacy terminology only, see 02 §2.2) and Matrix 2 (peer-reviewed Gold Standard reference labels) are never pooled, averaged or compared as if they were one benchmark.
2. Canine Thorax, Feline Thorax and Canine Abdomen are recorded separately.
3. Model-to-model agreement (OpenAI vs Gemini) is never presented as accuracy.
4. Passing tests, HTTP 200 responses and completed batches show that the software ran. They are not evidence of clinical validity. All results are 100-case pilot results.
5. Contradictions are kept and attributed, never silently resolved.
6. No report text, case-level label records, credentials or `.env` contents are copied here. CaseIDs appear only where a source used them as encoded pilot indices; they are not reproduced in this folder.
7. Candidate novelty claims stay provisional until a literature review and verified evidence support them.
