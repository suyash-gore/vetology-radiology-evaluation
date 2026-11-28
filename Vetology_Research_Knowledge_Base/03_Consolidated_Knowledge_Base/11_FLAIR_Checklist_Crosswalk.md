# 11 — FLAIR Checklist Crosswalk (INCOMPLETE: Appendix S1 not yet retrieved)

**Status: blocked on source access.** This crosswalk must use the **original FLAIR Appendix S1**:
- Kottlors J, et al. *Radiology*. 2026;318(2):e250913. https://doi.org/10.1148/radiol.250913
- Appendix S1: https://pubs.rsna.org/doi/suppl/10.1148/radiol.250913/suppl_file/ry250913suppa1.pdf

In this session `pubs.rsna.org` returned a bot-protection challenge (HTTP 403), so **the Appendix S1 text could not be read**. To avoid inventing checklist wording:
- **Exact item titles and requirement texts are NOT reproduced here.**
- For the 15 items whose topic the project owner described, the topic is shown, labelled *owner-described topic (unverified against Appendix S1)*, and mapped provisionally.
- The other 17 items are listed by ID with title and requirement marked **"to be transcribed from Appendix S1"**. Their status is **pending**.

**FLAIR is used as voluntary reporting guidance, not as a mandatory journal requirement. This document does not claim FLAIR compliance.**

**To complete:** supply the Appendix S1 PDF in the repository or the scratch area, or confirm that the RSNA site is reachable. The crosswalk will then be completed item by item from the original text.

**Item count (structure as stated by the owner, unverified):** 32 items in six categories:

| Category | Item IDs | Count |
|---|---|---|
| 1 | 1.1–1.9 | 9 |
| 2 | 2.1–2.7 | 7 |
| 3 | 3.1–3.6 | 6 |
| 4 | 4.1–4.2 | 2 |
| 5 | 5.1–5.3 | 3 |
| 6 | 6.1–6.5 | 5 |
| **Total** | | **32** |

Category names are **to be transcribed**.

**Status vocabulary:**
- **Documented**: the knowledge base already holds the information needed to report the item.
- **Partially documented**: some, but not all, of it is held.
- **Missing**: none of it is held.
- **Not applicable**.
- **Pending**: the item wording is unavailable, so it cannot be assessed.

**Mapped documents (relative to `03_Consolidated_Knowledge_Base/`):** `08_Research_Design_and_Analysis_Plan.md` (08), `02_Project_History_and_Methodology.md` (02), `04_Technical_Architecture_and_Reproducibility.md` (04), `05_Decisions_Limitations_and_Open_Questions.md` (05), `09_Literature_Evidence_Matrix.md` (09), and the registers under `../04_Evidence_and_Artifacts/`.

---

## Crosswalk

| ID | Exact item title (Appendix S1) | Requirement (concise) | Mapping in our documentation | Status | Open question / evidence required |
|---|---|---|---|---|---|
| 1.1 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 1.2 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 1.3 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 1.4 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 1.5 | *To be transcribed.* Owner-described topic: separation of prompt-optimisation and evaluation data | Report whether data used to develop/optimise prompts were separate from evaluation data (provisional reading) | 09 §8.2 (prompt-development provenance); KB_06 §11 (V1.0/V1.1 review cases: CT/FT 3, 4, 5, 7, 8; CA 13–17); KB_07 §8.5 / `03_Results…` §3 (hedged-language heuristic over evaluation reference labels informed CA V1.3/V1.4) | Partially documented | Whether the review cases and the heuristic used the same 100-case evaluation sets (P-6). If they did, this is a **potential leakage limitation** to disclose. Unlike Wulcan et al. (L05), no separate tuning set was used |
| 1.6 | *To be transcribed.* Owner-described topic: model identity and exact version | Report the model name and exact version | 08 §5.1; manifests (`../04_…/02_Experimental_Run_Register.md`): `gpt-4.1-mini`, `gemini-3.8-flash` | Partially documented | **Exact snapshot identifiers not recorded** (05 G-8). Recover them from provider records if possible; otherwise disclose |
| 1.7 | *To be transcribed.* Owner-described topic: model access method and dates | Report how the model was accessed (API, provider, library) and when | 08 §5.1; run register (UTC run windows: 3, 7 and 12 Nov 2026 for OpenAI CT; 20 Nov for Gemini CT; 21 Nov for FT/CA); LangChain wrappers; package versions in manifests | Partially documented | Week 4/5 have no manifests (dates come from prediction timestamps). API endpoint and region, and the account tier, are undocumented |
| 1.8 | *To be transcribed.* Owner-described topic: model versioning and drift | Address version changes and drift over the study period | 08 §5.2, §8.1, §8.5 (unknown snapshots; Week 4 vs Week 5 quasi-repeat) | Partially documented | No drift assessment. Runs span 3–21 Nov 2026; whether the alias pointed to the same snapshot is unknown |
| 1.9 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 2.1 | *To be transcribed.* Owner-described topic: prompt-engineering process and rationale | Describe how prompts were developed and why | 02 §3.1–3.3; 09 §8.2 (textbooks T01–T10, NotebookLM, ChatGPT, Dr. Parin Candy, Tech Advisor, version history); 04_Prompts index | Partially documented | Source-to-rule traceability absent. Textbook use is documented only for CT V1.3. FT/CA development provenance needs confirmation (P-1–P-5) |
| 2.2 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 2.3 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 2.4 | *To be transcribed.* Owner-described topic: full prompt reporting | Provide the full prompt text | Pinned prompt files `src/week_07/prompts/*.txt` with SHA-256 (`../04_…/04_Prompts_and_Configurations_Index.md`). The human-instruction template is in the manifests. An appendix is required by `01_Research_Paper_Requirements.md` | Documented (available); inclusion in the paper planned | Confirm the appendix length is acceptable to the venue; confirm no confidential content |
| 2.5 | *To be transcribed.* Owner-described topic: reporting style of source text | Describe the style, structure and language of the input text | 02 §2 (three original radiologist fields; empty → `[Not provided]`); KB_07 §8.4 (empty sections: FT 6, CA 3) | Partially documented | Report structure, length distribution, language, templated vs free text, and number of radiologists are not described |
| 2.6 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 2.7 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 3.1 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 3.2 | *To be transcribed.* Owner-described topic: reliability and robustness | Assess the reliability/robustness of outputs | 08 RQ5, §6.6 (CT incidental repeats 8/11/13 of 2,000); strict JSON validation; retry policy | Partially documented | No designed repeat runs, prompt perturbation or robustness testing (cf. L05, L10) |
| 3.3 | *To be transcribed.* Owner-described topic: stochastic output behaviour | Report settings affecting stochasticity and the observed variability | Temperature 0 (manifests); 08 §6.6 | Partially documented | Seeds and other sampling parameters not set or recorded. Variability measured for CT only |
| 3.4 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 3.5 | *To be transcribed.* Owner-described topic: performance metrics | Define and report the performance metrics | 08 §6.2 (definitions incl. F1 = 2TP/(2TP+FP+FN)); verified counts and rates (`../04_…/03_…Register.md`, `06_Per_Condition_Results.md`) | Documented (definitions and values); intervals planned | The F1 convention differs from the workbooks for some conditions (08 §6.2). Intervals not yet computed |
| 3.6 | *To be transcribed.* Owner-described topic: performance-evaluation procedures and evaluator expertise | Describe how outputs were evaluated and the expertise of those producing the reference | 08 §4 (Matrix 1: original Vetology labels; Matrix 2: peer-reviewed, discussion-agreed Gold Standard); automated comparison pipeline (04) | Partially documented | **Gold Standard participants, expertise and procedure undocumented (GS-1–GS-7).** Matrix 1 label origin unknown (GS-8). Must not be described as radiologist adjudication |
| 4.1 | *To be transcribed.* Owner-described topic: ethics | Ethics approval / waiver, consent, data governance | 08 §10 (ethics statement requires author confirmation); confidentiality controls (04 §4) | Missing | Ethics or approval status, data-use permission from Vetology, and an anonymisation statement are all needed |
| 4.2 | *To be transcribed.* Owner-described topic: data/code transparency | Availability of data and code | Code in the GitHub repository (branches; `main` lacks Weeks 5/7); prompts and manifests committed; data and outputs withheld (confidential) | Partially documented | A formal availability statement is needed. Decide the merge to `main` and a citable release. Confirm what can be shared |
| 5.1 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 5.2 | *To be transcribed.* Owner-described topic: risks and unintended consequences | Discuss potential harms and unintended consequences | 06 (no clinical readiness claimed); 08 §1, §8 | Partially documented | No explicit risk analysis (e.g. missed findings at low sensitivity, automation bias, reliance on unvalidated references) |
| 5.3 | *To be transcribed.* Owner-described topic: limitations, uncertainty and bias | Report limitations, uncertainty and potential biases | 08 §8 (internal/external/construct/statistical/reproducibility); 05 §2 | Documented (plan); uncertainty estimates pending | Intervals not yet computed; selection bias (first 100 cases) to be stated |
| 6.1 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 6.2 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 6.3 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 6.4 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |
| 6.5 | *To be transcribed* | *To be transcribed* | — | Pending | Obtain Appendix S1 |

**Row count check:** 32 rows (9 + 7 + 6 + 2 + 3 + 5).

## Summary of the provisional mapping (15 owner-described items only)

| Status | Items |
|---|---|
| Documented | 2.4, 3.5, 5.3 (each with planned follow-up) |
| Partially documented | 1.5, 1.6, 1.7, 1.8, 2.1, 2.5, 3.2, 3.3, 3.6, 4.2, 5.2 |
| Missing | 4.1 |
| Pending (wording unavailable) | 1.1–1.4, 1.9, 2.2, 2.3, 2.6, 2.7, 3.1, 3.4, 5.1, 6.1–6.5 (17 items) |

**Highest-priority gaps:**
- 1.5: possible prompt-development and evaluation overlap.
- 1.6 / 1.8: snapshot identifiers and drift.
- 3.6: Gold Standard process and evaluator expertise.
- 4.1: ethics.

These mappings must be re-checked against the exact Appendix S1 wording once it is available.


## Week 8 status

- Appendix S1 is **still not available** locally. No item titles were added.
- Mapping updates supported by new evidence:
  - **1.5:** the developer has confirmed that prompt-development cases overlap the evaluation sets; reference-label exposure in the CA analysis is unresolved. Status remains **partially documented** (disclosed as a limitation in the manuscript).
  - **3.2 / 3.3:** run-to-run consistency and κ were computed for CT (`04_…/07_…Results.md` §6). Status remains **partially documented** (CT only; no designed repeats).
  - **5.3:** uncertainty estimates are now computed (`07_…`); with that, the item is **documented** for the planned analyses.
- FLAIR compliance is **not** claimed. The crosswalk requires final verification against the publisher's supplementary material.
