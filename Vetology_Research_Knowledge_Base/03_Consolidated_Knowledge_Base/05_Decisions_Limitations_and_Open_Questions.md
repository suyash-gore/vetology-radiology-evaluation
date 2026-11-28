# 05 — Decisions, Limitations and Open Questions

"By" records who made each decision, as reported in the sources: **User** (explicit choice), **Approved** (proposal approved by the user), **Claude** (implementation choice within an approved plan), **Advisor** (Tech Advisor, as relayed by the user).

## 1. Decisions

### 1.1 Research and paper process

| ID | Decision | By | Status | Source |
|---|---|---|---|---|
| R-1 | Build the knowledge base first; draft no blueprint or paper until explicitly requested | User | Adopted | KB_01 §9 |
| R-2 | Finish the paper before presentation work | User | Adopted | KB_01 §2 |
| R-3 | Updated Vetology section lengths supersede the webpage values | User | Adopted | KB_01 §3.3 |
| R-4 | Follow the Springer format; identify the exact template before final layout | User | Adopted; template **unresolved** | KB_01 §3.4 |
| R-5 | Use the sample white paper only for style; copy nothing | User | Adopted | KB_01 §9 |
| R-6 | Keep individual source extractions first, consolidate later | User | Adopted (this KB) | KB_01 §10 |
| R-7 | Conserve Claude Code usage; work in consolidated cycles | User | Adopted | KB_02 T15 |

### 1.2 Methodology

| ID | Decision | By | Status | Source |
|---|---|---|---|---|
| M-1 | One master prompt per dataset | Project | Adopted | KB_06 §14 |
| M-2 | Only the original Findings/Conclusions/Recommendations go to the model; CaseID, labels and AI-generated fields are excluded | Project | Implemented (all weeks) | KB_06; KB_04; KB_07 |
| M-3 | Binary Positive/Negative output; no Uncertain state | Project | Adopted | KB_06 §14 |
| M-4 | Possible/suspected target → Positive (V1.3, Canine Thorax) | Advisor-informed (user-reported) | Implemented for CT; **not** applied uniformly to FT/CA (C-05) | KB_06 §9–10 |
| M-5 | Treating every differential as Positive | — | **Rejected** | KB_06 §14 |
| M-6 | Treating recommendations alone as evidence of disease | — | **Rejected** | KB_06 §14 |
| M-7 | Legacy Abnormal/Normal as ground truth (Canine Thorax) | — | **Rejected** | KB_06 §12 |
| M-8 | Approved Gold Standard (not the manual draft) as the evaluation reference; described by the owner as peer-reviewed and agreed upon after discussion | Project / owner clarification (W8) | Adopted; participants and procedure **not documented** | KB_06 §12; owner clarification 2026-11-28 |
| M-9 | Keep Matrix 1 and Matrix 2 separate; never pool | Project | Implemented | all |
| M-10 | Pause prompt iteration after Week 4 until mismatch/error analysis is done | User | Adopted (no CT V1.4) | KB_05 §5.1 |
| M-11 | No balanced accuracy | Developer | Implemented (not computed) | KB_04 T19 |
| M-12 | No prediction-level error analysis in Week 5 | User | Not performed | KB_04 T19 |
| M-13 | FT/CA: one shared prediction run from Matrix 1, reused for Matrix 2 (D-058) | User | Implemented | KB_07 T31 |
| M-14 | Feline Matrix 1 normalisation of three columns only (D-059) | User | Implemented | KB_07 |
| M-15 | Per-application pinned prompts; prompts are never invented (D-060) | User | Implemented | KB_07 |
| M-16 | Region-specific human instruction (D-061) | User | Implemented | KB_07 |
| M-17 | Feline V1.2 quote correction; Abdomen V1.3 inclusive policy; Abdomen V1.4 item-3 tightening (D-065–D-067) | User | Implemented | KB_07 |
| M-18 | Conservative reading of the Abdomen uncertainty rules | — | **Rejected** (inclusive policy adopted instead) | KB_07 T35 |
| M-19 | Gemini kept for CT; gpt-4.1-mini for FT/CA (D-056) | User | Implemented | KB_07 |
| M-20 | Week 7 comparison: same prompt, input boundary, validator and metrics, so only the model varies; agreement kept separate from accuracy (D-053) | Approved | Implemented | KB_08 §7.4 |

### 1.3 Engineering

Recorded in `docs/DECISION_LOG.md` (67 distinct IDs D-001–D-067 counted in Week 8; ranges D-020–D-043 for Week 5, D-044–D-054 for Week 7 Gemini, D-055–D-067 for the extension) and in the source tables:

- KB_04 T19 and KB_10 T17 (Week 5: P1–P9, D1–D8).
- KB_08 T13–T14 (closeout DD-1–DD-12, D-044–D-054).
- KB_09 T15 (O1–O3).
- KB_07 T31 (D-055–D-067).

Notable rejected or deferred engineering options:
- Runtime import of Week 5 instead of verbatim copies (Rejected, O1).
- Provider response schema (Rejected, O2).
- SDK-owned retries (Rejected, O3).
- Retry-After handling (Rejected for this stage).
- JSONL provenance fields (Rejected, P2; replaced by manifests in Week 7).
- Stricter CaseID validation (Rejected).
- Matrix 1 `--limit` (Removed).
- Tightening `spec=None` writes (Deferred).
- OpenAI JSON mode (Not used).
- Per-application engine copies (Rejected, D-055).
- Application-aware comparison (Not implemented).

## 2. Limitations

### 2.1 Required by Vetology (KB_01 §3.3)
- The Gold Standard covers 100 reports per file.
- The ground truth is not expert ground truth. **Owner clarification (2026-11-28): the Gold Standard dataset is peer-reviewed and agreed upon after discussion.** This is not formal, independent expert adjudication. The earlier KB_05 wording ("assigned by a veterinary radiologist") is superseded (C-03).
- Model outputs vary between runs.

### 2.2 Evidenced by the project
| Limitation | Source |
|---|---|
| One 100-case sample per application; one live run per model/application | KB_07 §16 |
| Run-to-run variation (8/2,000 pairs) even at temperature 0 | KB_10; testing_log |
| No veterinary adjudication of any mismatch in any dataset; Week 4 screening was text-only | KB_05; KB_07 |
| Matrix 1 label provenance and encoding history unestablished | KB_05 §7.1 |
| Gold Standard workbooks are named "draft"; FT/CA approval status undocumented | KB_07 §16 |
| Reference prevalence differs sharply between tracks; accuracy is inflated by negative-dominant references | KB_03; KB_07 |
| Sparse positives: 10 of 21 Feline Gold Standard conditions have zero positives; several Abdomen conditions have 2–3 | KB_07; KB_02 |
| Uncertainty policies are not harmonised across the three prompts | KB_07 §7.2 |
| Matrix 2 loader rules were inferred from artifacts; ambiguous workbooks are rejected rather than resolved | KB_04; KB_07 |
| Delivered Week 4 workbooks' provenance is partly unknown (unrecorded Matrix 1 evaluator variant; Matrix 2 produced outside the repository) | KB_04 §13 |
| Text-only classification; no images | KB_05 §11.1 |
| No confidence intervals, significance tests or inter-rater statistics | KB_02 §18 |
| No timing, cost or token measurements; no development-time comparison | KB_03 §13; KB_04 §13 |
| ~~FT/CA evaluation workbooks and all prediction files are inaccessible~~. **Resolved in the Week 8 reconciliation:** the workbooks and predictions were supplied and verified. They remain outside version control (gitignored) | KB_07; Week 8 |
| Run-to-run variation is present in every model family: 8, 11 and 13 of 2,000 pairs differ between separate CT batches on identical report text | Week 8 cross-check |
| Sparse or absent positives: Feline Matrix 2 has 10 of 21 conditions with zero positives; Feline predictions contain no positives for 10 conditions | Week 8 workbooks |
| Comparison package is CT-only; no second model for FT/CA | KB_09 TD7; KB_02 §11.3 |
| Documentation drift: the repository still says FT/CA live runs were not executed | KB_07 §17.2 #1; `README.md` L9, L16–17 (Verified W8) |

## 3. Open questions (unresolved)

| # | Question | Owner (per source) |
|---|---|---|
| ~~OQ-1~~ | **Resolved (W8):** the FT/CA evaluations were run (Matrix 1 workbooks generated 16:35:36 and 16:50:16 UTC on 21 Nov) and contain exactly the KB_02 values (C-01) | — |
| OQ-2 | Gold Standard nature: **resolved by owner clarification** (peer-reviewed, agreed after discussion). Still open: who took part in the review, the procedure, and how the 21 draft-vs-approved Canine Thorax differences were settled (C-03) | User / Vetology |
| OQ-3 | Are the FT/CA "draft" Gold Standards final? | Vetology |
| OQ-4 | What is the lineage between the Week 3 "V1.3" Feline/Abdomen prompts and the registry's V1.1/V1.2 originals? (C-04) | User |
| OQ-5 | Should the uncertainty policies be harmonised before any cross-application analysis? | User / Vetology |
| ~~OQ-6~~ | **Resolved (W8):** the workbook stores 0.78395 and displays 78.40%; the 78.39% in the Week 4 report is a truncated derived value (C-02). Recommended convention: round half-up to 2 d.p., matching the workbooks | — |
| OQ-7 | What exact Springer template applies? | User |
| OQ-8 | What does `Fe_Alveolar` mean in the dataset? | Advisor |
| OQ-9 | What feedback did Vetology and the Tech Advisors give in Week 6, and was it implemented? | User |
| OQ-10 | Do the Week 6 one-page outline and its team review exist? | User |
| OQ-11 | Was Week 5 peer review completed? | User |
| OQ-12 | What is the merge/tag strategy for `main` (divergent `.gitkeep` commits; no Week 7 tag)? | User |
| OQ-13 | Should repeat runs be done for a variance estimate (≥2 per model/application)? | User |
| OQ-14 | Which two Week 7 local-artifact tests were skipped, and why? | User |
| OQ-15 | What are the exact model snapshot identifiers? | User |
| OQ-16 | Should the paper's scope be Canine Thorax only (KB_03 outline) or all three datasets (programme requirement)? | User |


## 4. Week 8 additions: provenance, overlap, analyses

| ID | Item | Status | Source |
|---|---|---|---|
| L-W8-1 | **Prompt-development / evaluation overlap.** Selected cases from the evaluation datasets were reviewed during prompt development (CT/FT cases 3, 4, 5, 7, 8; CA 13–17), using report text and model predictions. The developer reports that reference labels were not inspected in the manual review | Developer clarification (2026-11-28). The evaluation is **not held out** | KB_06 §11; owner |
| L-W8-2 | **CA hedged-language analysis.** The developer recalls using report wording and model predictions, and does not remember whether any script inspected the reference-label columns. KB_07 §8.5 records a keyword heuristic that tabulated reference labels; its provenance could not be independently established | **Unresolved**: possible reference-label exposure | KB_07 §8.5; owner |
| L-W8-3 | **Prompt domain provenance.** For CT V1.3: ten textbooks queried with NotebookLM, consolidated with ChatGPT, guidance from Dr. Parin Candy. Editions, source-to-rule mapping, intermediate notes and the scope of expert input are undocumented. **No evidence that this process informed FT or CA** | Partially documented | KB_03 §5.2; `09_…` §8 |
| L-W8-4 | **D-A.** CT common-batch compatibility verified. Exploratory rescoring of both Week 5 batches done; batch selection open | Open (owner) | `04_…/07_…Results.md` §7 |
| L-W8-5 | **Statistical settings** (B, seed, interval rule) executed without prior owner approval | Disclosed; approval pending | `08_…` §13 |
| L-W8-6 | **Reference-label agreement** between Matrix 1 and Matrix 2 is low (κ CT 0.069, FT 0.031, CA 0.129); reason unresolved | New finding; interpretation open | `07_…Results.md` §4 |
| L-W8-7 | **FLAIR Appendix S1** not retrieved (publisher access challenge) | Open | `11_…` |
