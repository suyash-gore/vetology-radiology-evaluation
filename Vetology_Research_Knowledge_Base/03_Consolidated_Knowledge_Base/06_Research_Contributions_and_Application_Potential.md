# 06 — Research Contributions and Application Potential

> **All contributions here are provisional candidates.** None has been checked against the research literature. "Novel" must not be claimed until a literature review is done (KB_01 §14). The classification states what the *project evidence* shows, not what is new to the field. Nothing here is a clinical claim.

## 1. Candidate contributions

| # | Candidate contribution | Evidence basis | Evidence status | Sources |
|---|---|---|---|---|
| CC-1 | **Dual-reference evaluation design**: one fixed prediction set scored separately against two independent reference sets (Vetology labels vs Gold Standard) | Shared-prediction architecture, cross-matrix identity check; FT/CA manifests | Method Demonstrated (software); FT/CA results **Verified against workbooks** (Week 8 reconciliation) | KB_07 T36; KB_02 §16.2 |
| CC-2 | **Reference-set choice dominates apparent performance** (e.g. CT accuracy ~52% vs ~96%; sensitivity far higher against Matrix 2 in all three datasets) | Recorded counts; prevalence asymmetry observed in all three datasets | **Verified** counts (all three datasets); needs statistical analysis and adjudication | KB_07 T36; 03 §4 |
| CC-3 | **Provenance-pinned, reproducible evaluation framework** for report-based LLM classification across species and body regions (prompt and input SHA-256, run identity, refusal on mismatch, read-only guards) | Code; manifests (Verified W8) | Demonstrated (engineering) | KB_07; KB_09 T19 |
| CC-4 | **Prompt-as-artifact quality control**: integrity pinning, exact-diff tests, contradiction detection, version retention | FT V1.1→V1.2; CA V1.2→V1.3→V1.4 | Demonstrated | KB_07 T36 |
| CC-5 | **Artifact-anchored parity protocol** for an AI-assisted rebuild (request-body parity, JSONL byte parity, cell-level workbook comparison, mutation checks), including reconstruction of a missing evaluator from its delivered output | Week 5 replay reproduced both Week 4 matrices exactly | Demonstrated on one pipeline (Observed (prior)) | KB_10 T22; KB_04 §7.2 |
| CC-6 | **Case study of human-gated AI-assisted re-engineering**: eight plan corrections, nine approvals, a corrected AI assumption (Matrix 2 loader); the rebuild was not autonomous | Conversation records and commits | Demonstrated (single case) | KB_04; KB_03 slide 14 |
| CC-7 | **Separating model agreement from reference accuracy at the architecture level** (the agreement functions cannot receive reference labels) | `comparison/agreement.py` | Demonstrated (software) | KB_09 T19 |
| CC-8 | **Controlled cross-provider comparison**: identical prompt, input, validator and metrics; only the model changes (Gemini vs GPT-4.1 mini, CT) | Week 7 results | Recorded; single run per model; no significance test | KB_08; KB_07 |
| CC-9 | **Quantifying the effect of hedged language on reference labels** and its link to prompt uncertainty policy | Heuristic analysis of Abdomen hedged-only mentions | Observed (prior), indicative only; needs validated NLP or manual adjudication | KB_07 §8.5 |
| CC-10 | **Condition-specific prompt design** effects on binary classification | Prompt versions exist, but no controlled prompt A/B evaluation was run | **Not evidenced**; proposed research direction only | KB_01 §14; KB_06 §16 |
| CC-11 | **Documentation-integrity pattern** for LLM evaluation studies (implemented / tested / user-reported / pending labels; append-only logs; code as authority) | Closeout audit | Demonstrated in this repository | KB_08 T19 |
| CC-12 | **Deployment-oriented validation framework** (QA, human review, monitoring) | Proposals only | **Proposed** | KB_01 §14–15 |

Candidates that must **not** be claimed:
- That Claude Code improved diagnostic accuracy.
- That the system is clinically valid or ready for production.
- That development time was saved.
- That Vetology/advisor feedback was incorporated.
- That any approach is novel in the literature.

(KB_03 §13; KB_04 §14.)

## 2. Demonstrated capabilities (within this pilot)

| Capability | Status |
|---|---|
| Batch classification of 100 report texts per dataset into 20/21/10 binary condition labels with strict JSON validation | Demonstrated: 100/100 batches (manifests Verified W8 for Weeks 7 FT/CA/CT) |
| Checkpoint/resume, typed error handling and bounded retries | Demonstrated (tests; manifests) |
| Evaluation workbooks per dataset and matrix with confusion counts and rates | Demonstrated: workbooks for all three datasets and both matrices verified, and reproduced from predictions (Week 8) |
| Provider abstraction (OpenAI, Gemini) | Demonstrated (offline tests; live manifests) |
| Isolation of applications/workflows and read-only source guards | Demonstrated (tests) |
| Leakage control: labels and IDs never reach the model | Demonstrated (tests; code inspection by earlier sessions) |

## 3. Potential product / commercial applications (Proposed; no evidence of readiness)

Source: KB_01 §15; KB_07 T37; KB_09 §15; KB_02 §17; KB_08 T20.

| Area | Proposed application or requirement | Basis in the project | Status |
|---|---|---|---|
| Report QA / coding assist | Post-report triage, quality assurance or label coding across species and regions; **not** diagnosis | Text-only classification pipeline | Proposed; needs validation |
| Human-in-the-loop review | Route Matrix 1/2 disagreements and hedged-language cases to veterinary review | Disagreement sheets; adjudication registers (Week 4) | Proposed |
| Model selection | Choose by the clinical cost of FN vs FP (Gemini more specific, GPT-4.1 mini more sensitive on CT) | Single-run CT results | Recorded; requires validation |
| Prompt governance | Registry with active/superseded versions and digests per run; automated contradiction and schema checks before release | Implemented registry; checks done manually | Mechanism Demonstrated; automation Proposed |
| Monitoring and audit | Manifests feed run monitoring and drift tracking; audit trail | Manifests | Proposed |
| Deployment architecture | Provider abstraction, isolation and fatal/transient policy as reusable service components; concurrency, a database, packaging, CI and containers would be needed | Code; technical-debt register | Proposed |
| Data governance | Privacy, vendor data-processing terms, clinic workflow integration | Not assessed | Proposed |
| Staged path | Offline evaluation → controlled pilot → wider deployment only after validation | — | Proposed |

Prerequisites the sources name before any deployment claim:
- Expert adjudication.
- Larger, representative cohorts.
- External validation.
- Repeat-run variance estimates.
- Workflow safety and governance.
- Literature review.

(KB_02 §17; KB_01 §19.)
