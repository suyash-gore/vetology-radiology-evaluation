# 08 — Research Design and Statistical Analysis Plan

**Status:** proposed design for owner review. This is **not** the research paper. It sets out the scientific design, analysis plan and reporting structure the paper would follow.
**Prepared:** 2026-11-28, branch `week-08/research-paper-development`, knowledge-base baseline `ea92818` + `6843bab`.
**Evidence basis:** the consolidated knowledge base and the evidence registers only. The evidence was not re-extracted or re-verified for this document.

Conventions used throughout:
- **Established** = supported by a verified entry in the registers.
- **Proposed** = an analysis or design choice not yet carried out.
- **Unresolved** = requires an author decision or evidence that does not yet exist.

Paths are relative to `Vetology_Research_Knowledge_Base/`.

| Source used | Path |
|---|---|
| Paper requirements | `03_Consolidated_Knowledge_Base/01_Research_Paper_Requirements.md` |
| History and methodology | `03_Consolidated_Knowledge_Base/02_Project_History_and_Methodology.md` |
| Verified results | `03_Consolidated_Knowledge_Base/03_Results_and_Experimental_Findings.md` |
| Architecture and reproducibility | `03_Consolidated_Knowledge_Base/04_Technical_Architecture_and_Reproducibility.md` |
| Decisions, limitations, open questions | `03_Consolidated_Knowledge_Base/05_Decisions_Limitations_and_Open_Questions.md` |
| Candidate contributions | `03_Consolidated_Knowledge_Base/06_Research_Contributions_and_Application_Potential.md` |
| Crosswalk and contradiction register | `03_Consolidated_Knowledge_Base/07_Source_Crosswalk_and_Verification_Register.md` |
| Run register | `04_Evidence_and_Artifacts/02_Experimental_Run_Register.md` |
| Aggregate metrics register | `04_Evidence_and_Artifacts/03_Confusion_Matrix_and_Metrics_Register.md` |
| Gaps and provenance | `04_Evidence_and_Artifacts/05_Evidence_Gaps_and_Provenance.md` |
| Per-condition results | `04_Evidence_and_Artifacts/06_Per_Condition_Results.md` |

---

## 1. Research identity

**Provisional title.** *Evaluating Large Language Models for Structured Condition Classification from Veterinary Radiology Reports: A Comparative Study Across Three Datasets*

**Study type.** A retrospective, multi-dataset comparative evaluation of LLM-based **text classification**.

**Scope statements (to appear explicitly in the paper).**

1. The evaluated models received **original radiologist report text only**: the *Findings*, *Conclusions* and *Recommendations* fields of the original radiologist's report. An empty field was sent as `[Not provided]`. CaseIDs, reference labels and AI-generated report fields were excluded (Established; `02_…Methodology.md` §4; manifest field `llm_input_fields` = 3 entries, `04_Evidence_and_Artifacts/02_Experimental_Run_Register.md`).
2. The models **did not receive radiographic images** in any documented experiment.
3. The task is to decide whether a written report supports each condition label (Positive/Negative). It is **not** independent image interpretation and **not** clinical diagnosis.
4. All experiments are 100-case pilots. **No clinical validation is claimed or implied.**

**Equal-importance principle.** Canine Thorax (CT), Feline Thorax (FT) and Canine Abdomen (CA) are co-equal objects of study:
- None is the primary dataset.
- Every results and discussion element is reported for all three in parallel.
- Wherever coverage is unequal (§3), the asymmetry is stated, not hidden.

---

## 2. Research questions

Answerability scale:
- **Answerable** = verified evidence is enough for a descriptive answer.
- **Partially answerable** = a descriptive answer exists, but confounding or missing evidence limits interpretation.
- **Requires additional evidence** = a new experiment or record is needed.

### RQ1 — How does LLM-based condition classification performance vary across Canine Thorax, Feline Thorax and Canine Abdomen?

| Element | Assessment |
|---|---|
| Purpose | Characterise performance in three species/region domains with distinct condition sets |
| Evidence available | Verified aggregate and per-condition confusion counts for gpt-4.1-mini on all three datasets, both matrices (EVAL-01/02, 05/06, 11/12, 13/14; `04_…/03_…Register.md`; `04_…/06_Per_Condition_Results.md`) |
| Datasets | CT, FT, CA (equal) |
| Experiments | GPT-4.1 mini: CT Week 4 and Week 5; FT and CA Week 7 shared batches |
| Analysis required | Per-dataset, per-matrix confusion counts, rates and Wilson / cluster-bootstrap intervals (§6); descriptive side-by-side comparison; no pooled headline |
| Critical assessment | Datasets differ simultaneously in condition sets (20/21/10), prevalence, **prompt version and uncertainty policy** (CT V1.3 inclusive; FT V1.2 conservative; CA V1.4 scoped-inclusive), execution date and batch design (CT one batch per matrix; FT/CA one shared batch). Differences between datasets therefore **cannot be attributed to the domain alone** |
| Status | **Partially answerable** (descriptive yes; causal attribution no) |

### RQ2 — How do results differ between original Vetology reference labels (Matrix 1) and the peer-reviewed, discussion-agreed Gold Standard labels (Matrix 2)?

| Element | Assessment |
|---|---|
| Purpose | Quantify how much the choice of reference set changes measured performance |
| Evidence available | Matrix 1 and Matrix 2 evaluations for every dataset. Reference prevalence: CT 1,049 vs 158 positives /2,000; FT 534 vs 117 /2,100; CA 280 vs 81 /1,000 (Established) |
| Datasets | CT, FT, CA |
| Experiments | FT and CA: **the same prediction set** scored against both references (a clean paired design). CT: **separate batches** per matrix in every week (prediction sets differ by 8–13 of 2,000 pairs) |
| Analysis required | Per-dataset Matrix 1 vs Matrix 2 contrasts of each rate; **direct agreement between the two reference label sets** (raw agreement, Cohen's κ, per condition) computed from the reference workbooks (Proposed; not yet computed); offline rescoring of a single CT batch against both references to match the FT/CA design (Proposed; preferred D-A option; needs owner approval, no API call; §3.3) |
| Critical assessment | A Matrix 1 vs Matrix 2 difference reflects the **reference standard**, not model improvement. Neither reference is established as clinical truth. The Gold Standard review procedure is undocumented (§4.2) |
| Status | **Answerable** for FT and CA; **partially answerable** for CT until a single-batch rescoring is done |

### RQ3 — Which diagnostic conditions demonstrate consistently strong or weak classification performance across the three datasets?

| Element | Assessment |
|---|---|
| Purpose | Identify condition-level failure patterns and robust conditions |
| Evidence available | Verified per-condition tables for all 10 evaluations (`04_…/06_Per_Condition_Results.md`). The 20 CT condition keys all recur by name in FT (FT adds `Fe_Alveolar`). CA's 10 abdominal keys have **no overlap** with the thoracic sets |
| Datasets | CT and FT (shared keys); CA (within-dataset only) |
| Analysis required | Per-condition rates with intervals; flags for small denominators, zero-positive and undefined metrics (§6.3); shared-key comparison between CT and FT, stated as same **key name** only (definitions and prompt rules differ); CA analysed internally |
| Critical assessment | "Across the three datasets" is only partly meaningful: cross-dataset consistency can be judged for thoracic keys (CT vs FT), not for abdominal conditions. **A shared condition name does not establish an identical clinical definition.** The CT and FT prompts define and threshold conditions differently (e.g. opposite possible/suspected rules), and the species differ, so a CT–FT comparison is a comparison of same-named labels, not of a verified common construct. Many Matrix 2 conditions have 0–4 reference positives (CT 12 of 20; FT 16 of 21; CA 4 of 10), so condition-level sensitivity is often undefined or highly uncertain |
| Status | **Partially answerable** |

### RQ4 — Where comparable experiments exist, how do OpenAI and Gemini differ in classification performance and prediction agreement?

| Element | Assessment |
|---|---|
| Purpose | Compare two model families under a shared prompt, input boundary, validator and metric engine |
| Evidence available | **Canine Thorax only**: Week 5 gpt-4.1-mini vs Week 7 gemini-3.8-flash; Matrix 1 and Matrix 2; agreement 1,940/2,000 and 1,944/2,000; joint-correctness tables (AGR-01/02; EVAL-05–08) |
| Datasets | CT only. **No Gemini experiment exists for FT or CA** |
| Analysis required | Per-matrix rate differences with paired case-cluster bootstrap intervals; raw agreement and Cohen's κ (overall and per condition); per-condition McNemar's test, where discordant counts allow (§6.5) |
| Critical assessment | The comparison is controlled for prompt (V1.3, identical hash), input fields, validator and metrics. It is **not** controlled for execution date (12 Nov vs 20 Nov), client/retry configuration (transport retries 2 vs 1 attempt; JSON MIME mode for Gemini only) or model snapshot (unrecorded). It is a single run per model. **It must not be presented as a three-dataset comparison** |
| Status | **Answerable for CT (descriptive and paired inference feasible); not answerable for FT and CA** |

### RQ5 — How consistent are repeated executions under nominally identical model and prompt settings?

| Element | Assessment |
|---|---|
| Purpose | Characterise output instability at temperature 0 |
| Evidence available | CT only. Pairs of separate batches over identical report text: Week 4 Matrix 1 vs Matrix 2 batch 8/2,000 differing pairs (6 cases); Week 5 11/2,000 (8 cases); Week 7 Gemini 13/2,000 (11 cases) (Established, cross-checked; `03_…Findings.md` §1.3). Week 4 vs Week 5 predictions on the same workflow also exist case-level but **have not been compared** |
| Datasets | CT only; FT and CA have one batch each |
| Analysis required | Per-pair disagreement counts, affected cases, per-condition breakdown, κ between runs. The asymmetry must be stated |
| Critical assessment | These are incidental repeats, not a designed repeatability experiment. The Week 4 and Week 5 runs differ in client lifetime and other engineering details. Results describe **observed** variability in this project. They do not establish a general property of LLMs |
| Status | **Partially answerable for CT; requires additional evidence** (designed repeat runs) for FT, CA and any general claim |

### RQ6 — How do prompt design and uncertainty-handling rules relate to classification outcomes?

| Element | Assessment |
|---|---|
| Purpose | Relate prompt rules, especially the treatment of possible/suspected findings, to error patterns |
| Evidence available | Three active prompts with different uncertainty policies (`02_…Methodology.md` §3.4). Abdomen hedged-language heuristic, indicative only (Observed (prior)). FT V1.1→V1.2 was a syntax-only change; CA V1.2→V1.3→V1.4 were clinical-rule changes, **but only V1.4 was executed** |
| Datasets | All three (qualitative); no controlled within-dataset contrast |
| Analysis required | Qualitative mapping of policy to FN/FP patterns. A **controlled prompt ablation** (same dataset, same model, prompt varied) would be required for any causal statement |
| Critical assessment | Prompt policy is perfectly confounded with dataset. No experiment varies the prompt within a dataset |
| Status | **Requires additional evidence** (only exploratory discussion is possible now) |
| Recommendation | **Treat RQ6 as an exploratory Discussion topic, not a primary research question**, unless a controlled prompt-ablation experiment is performed before submission (D-H, D-J). Any statement about prompt effects must be labelled as hypothesis-generating |

**Coverage summary:** RQ2 (FT/CA) is the best-supported question. RQ1 and RQ3 are descriptive. RQ4 and RQ5 are CT-only. RQ1–RQ5 are retained as research questions with the limitations stated above. RQ6 is recommended as an exploratory discussion topic. The paper should say so rather than give the questions equal evidential weight.

---

## 3. Dataset and experimental design

### 3.1 Datasets (equal treatment)

| Attribute | Canine Thorax (CT) | Feline Thorax (FT) | Canine Abdomen (CA) |
|---|---|---|---|
| Species / region | Canine / thorax | Feline / thorax | Canine / abdomen |
| Cases | 100 | 100 | 100 |
| Configured conditions | 20 | 21 | 10 |
| Case–condition pairs per matrix | 2,000 | 2,100 | 1,000 |
| Matrix 1 reference positives / negatives | 1,049 / 951 | 534 / 1,566 | 280 / 720 |
| Matrix 2 reference positives / negatives | 158 / 1,842 | 117 / 1,983 | 81 / 919 |
| Matrix 2 zero-positive conditions | 4 | 10 | 0 |
| Matrix 2 conditions with 1–4 positives | 8 | 6 | 4 |
| Reference-label notes | Labels already Positive/Negative | Matrix 1: three columns (`pulmonary_nodules`, `esophagitis`, `pneumonia`) normalised Normal→Negative, Abnormal→Positive | Labels already Positive/Negative |
| Active prompt | Canine Thorax Master Prompt V1.3 (`31a7dab6…`) | Feline Thorax Master Prompt V1.2 (`9bbd36c4…`) | Canine Abdomen Master Prompt V1.4 (`9336be3f…`) |
| Uncertainty policy | Inclusive (possible/suspected → Positive) | Conservative (→ Negative unless confirmed) | Scoped-inclusive (Positive only in the primary impression, with support) |
| Ambiguous terms | `rtm`, `diseased_lungs` (advisor-clarified) | `Fe_Alveolar` (user working interpretation, unconfirmed) | — |

Sources: `04_…/03_…Register.md`, `04_…/06_Per_Condition_Results.md`, `04_…/04_Prompts_and_Configurations_Index.md`, `02_…Methodology.md` §2–3.

### 3.2 Experiment coverage matrix

| Dataset | Model | Run(s) | Prompt | Matrix 1 | Matrix 2 | Batch design | Repeat evidence | Model comparison |
|---|---|---|---|---|---|---|---|---|
| CT | gpt-4.1-mini | Week 4: RUN-02 (M1), RUN-01 (M2) | V1.3 | EVAL-01 | EVAL-02 | Separate batch per matrix | Yes (8/2,000) | — |
| CT | gpt-4.1-mini | Week 5: RUN-03 (M1), RUN-04 (M2) | V1.3 | EVAL-05 | EVAL-06 | Separate batch per matrix | Yes (11/2,000) | Comparator in AGR-01/02 |
| CT | gemini-3.8-flash | Week 7: RUN-05 (M1), RUN-06 (M2) | V1.3 | EVAL-07 | EVAL-08 | Separate batch per matrix | Yes (13/2,000) | AGR-01/02 |
| FT | gpt-4.1-mini | Week 7: RUN-07 | V1.2 | EVAL-11 | EVAL-12 | **One shared batch** | None | None |
| FT | gemini | — | — | — | — | — | — | **Not performed** |
| CA | gpt-4.1-mini | Week 7: RUN-08 | V1.4 | EVAL-13 | EVAL-14 | **One shared batch** | None | None |
| CA | gemini | — | — | — | — | — | — | **Not performed** |

Additional CT evaluations: the parity replays EVAL-03/04 (software verification, not model results) and EVAL-01b (a duplicate workbook of EVAL-01).

### 3.3 Design implications

1. **Common core design (Proposed primary analysis; conditional).** The intended primary, equally weighted analysis is: **one gpt-4.1-mini prediction set per dataset, scored against both Matrix 1 and Matrix 2**.
   - FT (RUN-07) and CA (RUN-08) already satisfy this design.
   - **For CT the design is not yet in place.** Every existing CT run used a separate batch per matrix. The common design becomes available only after **one CT gpt-4.1-mini batch has been selected and scored offline against both reference matrices** (D-A).
   - Until then, the primary analysis is conditional, and the CT Matrix 1 / Matrix 2 contrast carries the small batch confound in §5.2.
2. **CT asymmetry and decision D-A.** CT has three model runs and separate batches per matrix; FT and CA have one shared batch each.
   - **Preferred proposed option: offline rescoring.** Score one existing CT gpt-4.1-mini prediction batch against the reference matrix it was not originally evaluated against, so CT mirrors the FT/CA shared-prediction design. No API call and no new model output are involved.
   - **Prerequisites to confirm before rescoring:**
     - (a) The CT Matrix 1 and Matrix 2 workbooks contain identical CaseIDs, case order and report text. This is documented (`02_…Methodology.md` §6, from KB_04) but must be re-checked.
     - (b) Both reference workbooks use the same 20 condition keys and mapping.
     - (c) The chosen prediction file is compatible with the other matrix's evaluator (100 success records, exact 20 keys, Positive/Negative labels).
   - **Initial candidate: Week 5** (RUN-03 or RUN-04). It used the rebuilt application lineage that the Week 7 FT and CA evaluations also used (verbatim Week 5 engine; `04_…Reproducibility.md` §1). This is a **lineage-consistency** reason only. It does **not** imply that Week 5 is more accurate or scientifically superior to Week 4. Which Week 5 batch to use (Matrix 1 or Matrix 2 batch) is also part of D-A. **The exact selected batch (RUN-03 or RUN-04) and the reason for selecting it must be recorded** when the owner makes the decision. No batch has been selected in this document.
   - *Alternatives retained:* Week 4 (the original application) as the core run; or no rescoring, reporting CT with separate batches and an explicit caveat.
   - **Status of evidence:**
     - The existing verified results (EVAL-01, 02, 05, 06, 07, 08 in `04_…/03_…Register.md`) are **historical records and remain unchanged**.
     - A rescored CT result would be a **new, additional, proposed offline analysis**, reported with its own identifier and provenance. It would not replace or overwrite any existing evaluation, run ID or workbook.
     - Nothing has been rescored yet.
   - The other CT runs serve RQ4 and RQ5 **as secondary analyses**, so that CT does not dominate the paper through volume.
3. **No pooled headline.** The three datasets are not pooled into a single accuracy or F1 figure (justification in §6.8).

---

## 4. Reference-label methodology

### 4.1 The two evaluation workflows

| | Matrix 1 | Matrix 2 |
|---|---|---|
| Reference | **Original Vetology reference labels** from the encoded raw workbooks (`Vetology_Matrix1_First100_Encoded.xlsx` (CT), `2_feline_thorax_raw_data_encoded.xlsx`, `3_canine_abdomen_raw_data_encoded.xlsx`) | **Gold Standard labels, peer-reviewed and agreed upon after discussion** (owner clarification, 2026-11-28; `07_…Register.md` C-03), in the `*_gold_standard_score_draft.xlsx` workbooks |
| What agreement means | Agreement with the labels originally attached to the records | Agreement with the project's peer-reviewed, discussion-agreed labels |
| Terminology note | Matrix 1 workbooks say "GS Positive/Negative". This is **legacy wording only** (D-041); the reference is the Vetology labels (`07_…Register.md` C-23) | — |
| Prevalence | Substantially higher positive-label prevalence in every dataset | Substantially lower positive-label prevalence in every dataset |

**Interpretation rule.** Agreement with the original Vetology labels (Matrix 1) and agreement with the peer-reviewed, discussion-agreed Gold Standard (Matrix 2) are **different quantities**. Neither is accuracy against clinical truth.
- The Gold Standard must **not** be described as independently adjudicated by a veterinary radiologist, or as formal independent expert adjudication.
- The two reference sets show **substantially different positive-label prevalence and labelling patterns** in all three datasets. **The reason for this difference is unresolved.** The evidence does not establish whether it reflects different labelling conventions, thresholds, information sources, scope, error, or a combination (see GS-5, GS-8).

### 4.2 Missing methodological information on the Gold Standard (Unresolved)

| # | Missing item | Why it matters |
|---|---|---|
| GS-1 | Who took part in the peer review (number, roles, qualifications) | Construct validity of the reference |
| GS-2 | Review procedure: independent scoring before discussion? blinded to Vetology labels or model output? per case or per condition? | Possible anchoring or bias |
| GS-3 | How disagreements were resolved: consensus, majority, or escalation | Reliability of the final labels |
| GS-4 | Whether any inter-rater agreement was measured before discussion | Ability to report reference reliability |
| GS-5 | Scoring rules and their relation to each dataset's prompt rules (e.g. hedged language) | Whether prompt and reference use the same construct |
| GS-6 | How the 21 CT manual-draft-vs-approved differences were settled (`05_…Open_Questions.md` OQ-2) | Traceability |
| GS-7 | Whether FT and CA followed the same process as CT; final status of the "draft" workbooks (OQ-3) | Comparability across datasets |
| GS-8 | Origin and encoding history of the Matrix 1 Vetology labels | Interpretation of Matrix 1 results |

---

## 5. Model, prompt and execution design

### 5.1 Model and prompt configurations (Established)

| Run family | Datasets | Provider / model | Settings | Prompt |
|---|---|---|---|---|
| Week 4 | CT | OpenAI `gpt-4.1-mini` via LangChain | temp 0; timeout 90 s; LangChain `max_retries=2`; 2 application attempts; new client per case | CT V1.3 |
| Week 5 | CT | OpenAI `gpt-4.1-mini` | As Week 4; one client per batch | CT V1.3 |
| Week 7 | CT | Google `gemini-3.8-flash` | temp 0; JSON MIME mode, no schema; 1 transport attempt; 2 application attempts; bounded backoff | CT V1.3 |
| Week 7 | FT, CA | OpenAI `gpt-4.1-mini` | temp 0.0; transport retries 0; no response format; 2 application attempts | FT V1.2; CA V1.4 |

Exact model snapshot identifiers are **not recorded** in any artifact (`04_…/05_…Provenance.md` G-8).

### 5.2 Controlled vs confounded comparisons

| Comparison | Held constant | Varies (confounders) | Classification |
|---|---|---|---|
| FT Matrix 1 vs FT Matrix 2 | Predictions, model, prompt, cases, report text | Reference set only | **Controlled (reference effect)** |
| CA Matrix 1 vs CA Matrix 2 | Same | Reference set only | **Controlled (reference effect)** |
| CT Matrix 1 vs CT Matrix 2 (any week) | Model, prompt, cases, report text | Reference set **and** prediction batch (8–13/2,000 differ) | Nearly controlled; small batch confound |
| CT Week 5 OpenAI vs Week 7 Gemini | Prompt (hash), inputs, validator, metrics, cases, references | Model family, date, transport/retry/response-format configuration, unknown snapshots | **Partially controlled** model comparison |
| CT Week 4 vs Week 5 (gpt-4.1-mini) | Model alias, prompt, inputs, references | Date, application code (client lifetime, fail-fast), possibly the snapshot | Quasi-repeat; not a pure replicate |
| CT Matrix 1 batch vs Matrix 2 batch, same week | Model, prompt, report text, settings | Execution only (different workbook inputs with identical report text) | Best available repeatability evidence |
| CT vs FT vs CA | Model alias (gpt-4.1-mini), engine lineage | Domain, condition set, prevalence, prompt version and uncertainty policy, date, batch design, Matrix 1 normalisation (FT) | **Confounded**; descriptive only |
| Prompt policy effects | — | Policy perfectly aliased with dataset | **Not identifiable** |

---

## 6. Statistical analysis plan

All analyses below are **Proposed** unless marked Established. No inferential test has been run. The case-level data needed for them exist as owner-supplied, uncommitted artifacts (`04_…/05_…Provenance.md` §1). They must be analysed offline without committing case-level data.

### 6.1 Unit of analysis and notation

- For dataset *d*, matrix *m*, experiment *e*: cases *i* = 1…100 and conditions *j* = 1…*K_d* (*K* = 20, 21, 10).
- For each pair (*i*, *j*): reference label *y_ij* ∈ {0, 1} and prediction *ŷ_ij* ∈ {0, 1}.
- Per condition *j*:
  - TP_j = Σᵢ 1[y_ij = 1, ŷ_ij = 1]
  - FN_j = Σᵢ 1[y_ij = 1, ŷ_ij = 0]
  - TN_j = Σᵢ 1[y_ij = 0, ŷ_ij = 0]
  - FP_j = Σᵢ 1[y_ij = 0, ŷ_ij = 1]
- Micro totals sum the counts over *j*.

### 6.2 Primary descriptive metrics (per dataset × matrix × experiment)

| Metric | Definition | Undefined when |
|---|---|---|
| Accuracy | (TP + TN) / (TP + FN + TN + FP) | N = 0 |
| Sensitivity (recall) | TP / (TP + FN) | No reference positives |
| Specificity | TN / (TN + FP) | No reference negatives |
| Precision (PPV) | TP / (TP + FP) | No positive predictions |
| F1-score | **F1 = 2TP / (2TP + FP + FN)** | **Only** when 2TP + FP + FN = 0 (no reference positives and no positive predictions) |
| Micro average | Formulas applied to summed counts | As above |
| Macro average | Unweighted mean of the **defined** condition-level values of a metric; undefined values excluded, never replaced by zero | No condition has a defined value |

**F1 cases.**
- F1 is defined whenever there is at least one reference positive or at least one positive prediction. It is **not** automatically undefined because sensitivity or precision is undefined.
- **Zero reference positives, FP > 0:** sensitivity is undefined, but F1 = 2·0 / (0 + FP + 0) = **0**. All positive predictions are false.
- **Zero reference positives, FP = 0:** the denominator is 0, so F1 is **undefined**. No positives exist on either side; only specificity (100%) is informative.
- **TP = 0, FP = 0, FN > 0** (no positive predictions; reference positives exist): precision is undefined, but F1 = **0**.
- **TP = 0, FP > 0, FN > 0:** F1 = **0**.

**Relationship to the verified workbooks (no value changed here).**
- The project's evaluation engine and the verified workbooks follow a different convention: F1 is left blank when precision or sensitivity is undefined, or P + S = 0 (`02_…Methodology.md` §5; `04_…/06_Per_Condition_Results.md` header).
- Under the definition above, some condition-level F1 values shown as "undef." in the workbooks would be 0. Examples:
  - conditions with reference positives but no positive predictions (FT Matrix 1 esophagitis);
  - zero-positive conditions with FP > 0 (CT Matrix 2 esophagitis).
- Macro F1 would also change. Micro F1 values are unaffected, because TP > 0 in every evaluation.
- The verified workbook values remain the **historical record**. Any F1 recomputed under this definition would be a **proposed derived value**, labelled as such and reported with the convention stated.
- No such recomputation has been performed in this document.

**Macro-average reporting rules.**
- The set of conditions contributing to a macro average **can differ by metric and by reference matrix**. For example, macro sensitivity excludes zero-positive conditions, which are numerous in Matrix 2; macro precision excludes conditions without positive predictions. Macro values within one evaluation can therefore rest on different condition subsets.
- For **every** macro metric, report the number of conditions included and the number excluded as undefined, with the reason (e.g. "macro sensitivity: 11 of 21 conditions; 10 excluded, no reference positives").
- Macro averages computed over different condition sets (between metrics, matrices, datasets or experiments) are **not directly equivalent** and must not be compared as if they were.
- Undefined condition values are never silently replaced by zero (or by one).

- **Reporting:** report all four counts and all five rates. Accuracy must never appear alone. High specificity with low sensitivity must be described as such, not as strong performance.
- **Rounding:** round half-up to 2 d.p., matching the workbooks (`03_…Findings.md` §1.2).
- **Prevalence:** also report the positive rate (TP + FN)/N, because it drives accuracy and precision.

### 6.3 Condition-level analysis

Source: `04_…/06_Per_Condition_Results.md` (verified).

1. Report for every condition: reference positives and negatives, TP/FN/TN/FP, sensitivity, specificity, precision and F1.
2. **Undefined metrics** are shown as "undefined" with the reason: no reference positives (sensitivity), no positive predictions (precision), or 2TP + FP + FN = 0 (F1, §6.2). They are never 0% or 100%. They are excluded from macro averages, with included and excluded counts stated per macro metric (§6.2).
3. **Zero-positive conditions** (CT Matrix 2: 4; FT Matrix 2: 10; CA: 0) are listed separately. For these conditions (TP = FN = 0):
   - Sensitivity is **undefined**, because there are no reference positives.
   - Specificity and false-positive counts and rates **remain informative**.
   - If positive predictions occur (FP > 0), precision (= 0) and F1 (= 2·0 / (0 + FP + 0) = 0) are **mathematically defined**. They must be interpreted cautiously because the condition has no reference-positive cases, so they reflect only false positives.
   - If there are no positive predictions (FP = 0), precision and F1 are **undefined** (denominators TP + FP = 0 and 2TP + FP + FN = 0; consistent with §6.2).
4. **Small denominators.** Flag sensitivity when reference positives < 10, and precision when positive predictions < 10.
   - Proposed tiers: < 5 = "very small"; 5–9 = "small".
   - A 100% value from 2–4 positives (e.g. CA Matrix 2 liver_mass, splenic_mass, splenomegaly) must be shown with its interval and support count.
5. **Class imbalance.** Report prevalence per condition. Prefer sensitivity, specificity, precision and F1 with intervals over accuracy. Optionally add balanced accuracy, (S + Sp)/2, as a **secondary**, clearly labelled metric. It was not part of the project methodology (decision M-11), so including it is **Unresolved decision D-B**.
6. **Consistently poor performance** (Proposed operational definition; **Unresolved decision D-C**): sensitivity < 20% with ≥ 10 reference positives, in both matrices where defined (and, for CT/FT shared keys, in both datasets).
   - Example evidence: FT Matrix 1 has 11 conditions with TP = 0 despite reference positives; CA Matrix 1 pancreatitis has 2/75.
   - Thresholds must be fixed **before** the final analysis to avoid post-hoc selection.
7. **Cross-dataset condition view:**
   - CT vs FT on the 20 shared key names, with the caveat that definitions and prompt rules differ.
   - CA conditions are reported within-dataset only.

### 6.4 Uncertainty estimates

| Method | Use | Assumptions | Limitations here |
|---|---|---|---|
| 95% **Wilson score interval** for a single proportion (sensitivity, specificity, precision, accuracy) | **Recommended for condition-level rates**, where each condition contributes one label per case (100 approximately independent cases) | Independent Bernoulli trials; fixed denominator | Valid per condition. **Not valid for micro rates** pooling conditions within a report (§6.7). Precision's denominator is random (number of positive predictions); report it as conditional |
| Wald (normal-approximation) interval | Not recommended | Large *n*, *p* away from 0/1 | Fails for small denominators and extreme proportions, which are common here |
| Clopper–Pearson exact interval | Alternative for very small denominators | Independent trials | Conservative |
| **Report-level cluster (nonparametric) bootstrap**: resample the 100 reports with replacement, keeping all of a report's condition labels together; recompute micro and macro metrics. Candidate settings: B = 10,000, a fixed seed, percentile or BCa interval (D-I) | **Recommended for micro and macro rates and F1** | Reports are exchangeable, independent units | 100 clusters is modest; intervals are approximate. Rare-positive conditions create undefined replicates (see below) |
| **Paired bootstrap** (same cases, resampled jointly) | Differences between two predictions or references on the same cases: FT/CA Matrix 1 vs Matrix 2; CT Gemini vs OpenAI; CT repeat runs | The two arms are measured on the same cases | Does not remove confounders listed in §5.2 |

Wilson interval for a proportion p̂ = x/n with z = 1.96:

  centre = (p̂ + z²/(2n)) / (1 + z²/n)
  half-width = [z / (1 + z²/n)] · √( p̂(1 − p̂)/n + z²/(4n²) )

**Undefined bootstrap replicates.**
- Conditions with few reference positives (e.g. 1–4 in many Matrix 2 conditions) or few positive predictions will, in some bootstrap replicates, have **zero positive cases or zero positive predictions**. The condition-level sensitivity, precision or F1 is then undefined in that replicate, and the macro averages change their contributing condition set.
- **Required reporting:** for every affected metric, report the **frequency of undefined replicates** (count and percentage of B), and for macro metrics, the distribution of the number of contributing conditions across replicates.
- Undefined replicates must **not** be silently discarded, with the remaining interval then presented as unbiased or fully reliable. Discarding conditions on the resample is itself a choice that biases the interval toward replicates where the condition happened to be observed.
- Options include:
  - reporting the interval conditional on definedness, with the undefined frequency stated;
  - reporting no interval (descriptive only) where undefined replicates are frequent;
  - using a per-condition Wilson or Clopper–Pearson interval instead.
- The threshold for "frequent" is part of D-I.
- **The final bootstrap method, interval type, replicate count, seed and undefined-replicate rule must be fixed only after testing the procedure against the actual case-level data**, and before any final result is computed (§6.9).
- No bootstrap or other statistic is computed in this document.

**Interpreting confidence intervals.**
- The 100 cases per dataset are the **first 100 populated cases**, not a random sample from a defined population (§8.2).
- Wilson, Clopper–Pearson and bootstrap intervals here quantify **sampling-like variability under the stated model, conditional on these cases, labels, prompts and runs**.
- They must be interpreted cautiously. They do **not** establish that the estimates represent any wider population of reports, clinics or species. They do **not** establish general or clinical validity.
- They also do not capture reference-label uncertainty, run-to-run model variability (§6.6) or model-version drift.

### 6.5 Model comparison (CT only; RQ4)

| Method | Planned use | Conditions for validity |
|---|---|---|
| Raw prediction agreement | Report overall (Established: 97.00% Matrix 1; 97.20% Matrix 2) and per condition | Descriptive only; inflated by prevalence of Negative |
| **Cohen's κ** | Chance-corrected model–model agreement, overall and per condition; also Matrix 1–Matrix 2 **reference** agreement (RQ2) | Both raters label the same items. κ is prevalence-sensitive and unstable or undefined when a condition is almost always Negative. Report alongside raw agreement and positive/negative counts. A pooled κ over pairs inherits within-report dependence; use a cluster bootstrap interval |
| **McNemar's test** (exact binomial on discordant pairs) | Paired correctness of OpenAI vs Gemini against the same reference, **per condition** across 100 cases | Each case contributes one pair per condition (independent cases). Needs adequate discordant counts (use the exact version; say "not testable" when discordants are ~0). **Do not** apply to the 2,000 pooled pairs: within-report dependence violates independence. Multiple conditions → correct for multiplicity (Holm) or treat as exploratory |
| **Paired case-cluster bootstrap** of metric differences (Δ sensitivity, Δ specificity, Δ F1, Gemini − OpenAI) | Primary inferential summary of the model difference at aggregate level | Same 100 cases in both arms (holds). Single run per model, so run-to-run noise (8–13/2,000) is part of the observed difference and cannot be separated |

Interpretation guardrails:
- The comparison covers Canine Thorax only.
- Agreement is not accuracy.
- A statistically detectable difference is limited to these runs, settings and dates. It is not a general claim about model families.
- **Unresolved decision D-D:** whether to run any inferential test at all, or keep RQ4 descriptive with intervals.

### 6.6 Run-to-run consistency (RQ5)

- **Report:** for each CT repeat pair, the differing pairs (8, 11, 13 of 2,000), the affected cases (6, 8, 11), the direction (Positive→Negative vs Negative→Positive), the conditions involved, between-run κ and the effect on each metric.
- **Proposed additional comparison** using existing data: Week 4 vs Week 5 predictions on the same workflow.
- **Interpretation:** temperature 0 did not give byte-identical outputs across separate executions in this project. This is an **observation for these models, dates and settings**. It does not establish a general LLM property, a rate that applies to FT/CA, or a cause (provider-side non-determinism, snapshot change and client differences are not separable).
- Designed repeat runs (≥ 2 per model and dataset) would be needed for any broader statement (`05_…Open_Questions.md` OQ-13).

### 6.7 Clustering and dependence

- Each report contributes *K_d* labels (20, 21 or 10) that share the same text, the same model call and correlated reference-labelling decisions. The 2,000 / 2,100 / 1,000 pairs are **not independent observations**. The effective sample size for micro metrics lies between 100 (reports) and *N* (pairs).
- **Consequences for the plan:**
  - Never compute binomial intervals or tests on pooled pairs as if independent.
  - Use the case-level cluster bootstrap for micro and macro metrics and pooled κ.
  - Use per-condition analyses, where independence across cases is plausible, for Wilson intervals and McNemar.
- **Optional (Proposed, exploratory):** a mixed-effects logistic model of correctness with random intercepts for case (and fixed effects for condition, matrix, model) could quantify dependence. With 100 cases per dataset and sparse positives, it may fail to converge. This is **Unresolved decision D-E**.
- Cases are also assumed independent of each other. Their sampling frame ("first 100 populated cases") is **not a random sample** (§8.2). Intervals are therefore interpreted as described in §6.4 ("Interpreting confidence intervals").

### 6.8 Cross-dataset analysis

- **Equal importance ≠ pooling.** Each dataset gets the same set of tables, figures and analyses, reported in parallel. Pooling is inappropriate because:
  - condition sets differ (20 / 21 / 10; CA shares no condition with the thoracic sets);
  - prevalence differs (e.g. Matrix 1 positive rate 52% CT, 25% FT, 28% CA);
  - prompts and uncertainty policies differ;
  - batch designs differ;
  - reference-labelling processes may differ (GS-7).
- A pooled micro metric would be dominated by CT and FT pair counts and by the most prevalent conditions. This would contradict the equal-importance principle.
- **Recommended:** side-by-side per-dataset estimates with cluster-bootstrap intervals; macro averages within dataset; and a dataset-weighted summary (mean of the three per-dataset values), only if a summary is required, labelled descriptive.
- Formal tests of between-dataset differences are **not recommended**: confounding (§5.2) makes them uninterpretable as domain effects.

### 6.9 Pre-specification and transparency

- Fix all thresholds, interval methods, bootstrap settings (including the undefined-replicate rule, after testing on the case-level data), the F1 reporting convention (§6.2), multiplicity handling and decisions D-A to D-J before computing final numbers.
- Report every pre-specified analysis, including null or undefined results.
- Keep case-level analysis outputs out of the repository; commit only aggregate outputs and scripts if approved.

---

## 7. Potential contributions and novelty assessment

> All items are **provisional**. **None is claimed as novel** until a systematic literature review has been done (`06_…Potential.md`; `01_…Requirements.md` §2).

### 7.1 Demonstrated (evidence exists in this project; not a novelty claim)

| Contribution | Evidence |
|---|---|
| Three-dataset veterinary report-classification evaluation with verified confusion counts for all datasets and both reference sets | `04_…/03_…Register.md`, `06_Per_Condition_Results.md` |
| Paired comparison of original annotations vs a peer-reviewed, discussion-agreed reference on identical predictions (FT, CA) | EVAL-11/12, 13/14 |
| Condition-level sensitivity/specificity profiles, including zero-positive and small-denominator handling | `06_Per_Condition_Results.md` |
| Reproducible evaluation architecture with prompt/input hashing, run manifests and offline re-evaluation that reproduced every workbook count | `04_…Reproducibility.md` §3 |

### 7.2 Potential (requires the proposed analyses)

- Quantified reference-standard effect with uncertainty (RQ2), including Matrix 1–Matrix 2 label agreement.
- Cross-domain performance differences, stated as descriptive and confounded (RQ1).
- Condition-level failure taxonomy for thoracic keys shared between CT and FT (RQ3).
- CT-only paired OpenAI vs Gemini comparison with κ and McNemar or bootstrap (RQ4).
- Observed run-to-run inconsistency at temperature 0 in CT (RQ5).

### 7.3 Future research

- Controlled prompt-ablation experiments on uncertainty rules (RQ6).
- Gemini (or other models) on FT and CA.
- Designed repeat runs for all datasets.
- Documented, blinded expert adjudication with inter-rater statistics.
- Larger and prospective samples.
- Image-plus-text studies.

---

## 8. Limitations and threats to validity

### 8.1 Internal validity

- Prompt version and uncertainty policy are confounded with dataset.
- The model comparison is confounded by date, client/retry configuration and unknown snapshots.
- CT uses separate batches per matrix while FT/CA use a shared batch.
- Single runs per model and dataset (except the CT incidental repeats).
- API execution variability: 8–13/2,000 pairs differ between CT batches.
- Model snapshot identifiers are unavailable.

### 8.2 External validity

- 100 cases per dataset, selected as the first 100 populated records (not a random or representative sample). Confidence intervals therefore do not imply population representativeness or general clinical validity (§6.4).
- One organisation's reports.
- Retrospective design.
- No prospective or clinical-workflow validation.
- Three species/region combinations only.
- Results may not transfer to other models, versions, dates or report styles.

### 8.3 Construct validity

- Text-only input: the reference labels may reflect information not stated in the report text.
- Matrix 1 label provenance is unestablished (GS-8).
- The Gold Standard process is incompletely documented (GS-1 to GS-7), and the workbooks are still named "draft".
- `Fe_Alveolar` definition is unconfirmed; `diseased_lungs` boundary is broad.
- Binary Positive/Negative output removes uncertainty.
- Class imbalance and sparse positives: many Matrix 2 conditions have 0–4 positives.
- Condition-level sample sizes are too small for precise estimates.

### 8.4 Statistical conclusion validity

- Within-report dependence.
- Small denominators.
- Undefined metrics.
- Multiplicity across many conditions.
- No pre-registered analysis until §6.9 is completed.

### 8.5 Reproducibility

- Case-level artifacts are retained outside version control.
- Model snapshots and API request IDs are not recorded.
- Repository documentation is stale for FT/CA runs (`07_…Register.md` C-14).
- Week 5 replay workbooks are not supplied.

---

## 9. Proposed manuscript structure

Confirmed requirements (section lengths, figure/table numbering, Table of Contents and Lists of Figures and Tables, final prompts in the appendix, every number traceable, no identifiers) are in `01_Research_Paper_Requirements.md`. **The exact Springer template is unresolved (RQ-1 there).** No additional formatting rule or word limit is introduced here.

| # | Section | Content (equal treatment of CT, FT, CA) |
|---|---|---|
| 1 | Abstract | Question, design, per-dataset headline metrics for both matrices (not pooled), one conclusion |
| 2 | Introduction | Motivation for LLM classification of veterinary report text; research questions RQ1–RQ5 with their coverage stated (RQ6 framed as an exploratory topic, subject to D-H) |
| 3 | Materials and Methods | Data (three datasets, parallel description); reference workflows; prompts; models and settings; pipeline and provenance; metrics and statistical plan (§6) |
| 4 | Results | 4.1 Dataset characteristics; 4.2 aggregate results, **one parallel subsection each for CT, FT and CA** with Matrix 1 and Matrix 2; 4.3 reference-set effect; 4.4 condition-level results per dataset; 4.5 CT model comparison (labelled CT-only); 4.6 CT repeatability (labelled CT-only) |
| 5 | Discussion | Cross-dataset patterns; reference-standard dependence; condition-level failure patterns; prompt and uncertainty considerations (exploratory); engineering and reproducibility; manual build vs Claude Code (required by `01_…Requirements.md`) |
| 6 | Limitations | §8 |
| 7 | Conclusion | Next steps and key takeaway |
| 8 | References | Requires the literature review |
| — | Appendix | Required by `01_…Requirements.md`: final prompts, repository link, output filenames |

**Structural note (Unresolved D-F):** the requested structure adds References and the "Materials and Methods" label. The confirmed requirements list Method and Appendix. The final order must follow the chosen Springer template.

### 9.1 Table and figure plan

| ID | Type | Content | Source |
|---|---|---|---|
| T1 | Table | Dataset characteristics (§3.1) for CT, FT, CA | `06_…Results.md`; `03_…Register.md` |
| T2 | Table | Experiment coverage matrix (§3.2) | `02_…Run_Register.md` |
| T3 | Table | Model and prompt configurations (§5.1) | `04_…Prompts_and_Configurations_Index.md` |
| T4a–c | Tables | Aggregate confusion counts and rates with 95% cluster-bootstrap CIs, Matrix 1 and Matrix 2, **one table per dataset, identical layout** | `03_…Register.md` + proposed analysis |
| T5a–c | Tables (or appendix) | Per-condition results with Wilson CIs and support flags, per dataset | `06_…Results.md` |
| T6 | Table | Matrix 1 vs Matrix 2 reference agreement (κ) per dataset | Proposed |
| T7 | Table | CT OpenAI vs Gemini: metrics, Δ with paired CIs, agreement, κ, McNemar where testable | AGR-01/02; proposed |
| T8 | Table | CT repeatability: differing pairs, cases, κ | `03_…Findings.md` §1.3; proposed |
| F1 | Figure | Experimental workflow / system diagram (report text → prompt → LLM → validation → two reference evaluations) | `04_…Reproducibility.md` §2 |
| F2 | Figure | Reference prevalence by dataset and matrix | T1 |
| F3a–c | Figure | Confusion-matrix heatmaps, per dataset and matrix | T4 |
| F4a–c | Figure | Per-condition sensitivity vs specificity with CIs, per dataset | T5 |
| F5 | Figure | Matrix 1 vs Matrix 2 paired differences (FT, CA; CT after D-A) | Proposed |
| F6 | Figure | CT model-comparison forest plot (labelled CT-only) | T7 |

---

## 10. Reporting checklist (FLAIR)

The FLAIR reporting framework was identified in the research-planning discussion as a completeness check. **It is not documented anywhere in the knowledge base**, and its official item list, version and citation are not recorded. It is used here **only as a voluntary checklist, not as a journal requirement**.

The topics below are this project's reporting domains. **Mapping them to the exact FLAIR items requires author confirmation (decision D-G).**

| Reporting domain | Status | Evidence / note |
|---|---|---|
| Study purpose and research questions | Partially documented | RQ1–RQ5 here, with RQ6 recommended as exploratory; final wording not approved (`01_…Requirements.md` RQ-2) |
| Study design (retrospective, comparative) | Already documented | §1 |
| Data sources, selection and sample size | Partially documented | 100 cases per dataset, first populated rows; the selection rationale is not documented |
| Inclusion/exclusion and data preprocessing | Already documented | Three input fields; Feline normalisation; blank-row skipping |
| Reference standard definition and process | Partially documented | Owner clarification on the Gold Standard; GS-1 to GS-8 missing |
| Label definitions and ambiguous terms | Partially documented | `rtm`, `diseased_lungs`, `Fe_Alveolar` status (`02_…Methodology.md` §2.1) |
| Model identity, version and access | Partially documented | Aliases recorded; snapshots missing |
| Prompts (full text, versions) | Already documented | Pinned files and hashes; appendix required |
| Inference settings (temperature, retries, format) | Already documented | Manifests |
| Output parsing and validation | Already documented | Strict JSON validator |
| Metrics and definitions | Partially documented | §6.2. The F1 definition proposed for the paper differs from the convention in the verified workbooks for some conditions; the convention must be stated |
| Uncertainty quantification | Missing | §6.4 proposed |
| Handling of dependence, imbalance and undefined metrics | Partially documented | Undefined handling documented; dependence plan proposed |
| Model comparison methodology | Partially documented | CT-only; tests proposed |
| Repeatability / variability | Partially documented | Incidental CT repeats only |
| Error analysis | Partially documented | Week 4 text screening; no adjudication |
| Reproducibility (code, provenance, data availability) | Already documented | Commits, hashes, manifests; data withheld (confidential) |
| Data privacy and ethics | Partially documented | No identifiers committed; ethics/approval statement **requires author confirmation** |
| Limitations and generalisability | Already documented | §8 |
| Intended use and clinical claims | Already documented | Text classification only; no clinical claim |
| Conflicts of interest / funding / author contributions | Requires author confirmation | Not in the knowledge base |
| Use of AI tools in research and writing (Claude Code, ChatGPT, NotebookLM) | Requires author confirmation | Usage documented in `02_…Methodology.md` §3.1, §6; disclosure wording undecided |

---

## 11. Open decisions

| ID | Decision | Options / note |
|---|---|---|
| D-A | Which CT gpt-4.1-mini batch forms the core analysis, and confirmation of the offline rescoring against both reference matrices. The common primary design is **conditional on this decision** | **Preferred:** offline rescoring of one Week 5 batch (initial candidate on lineage grounds only, not accuracy), subject to the identical case/condition mapping and prediction-compatibility checks in §3.3. The exact selected batch (RUN-03 or RUN-04) and the reason for selecting it must be recorded; not yet selected. Alternatives: Week 4 batch; no rescoring with explicit caveat. Existing verified results are not altered |
| D-B | Whether to report balanced accuracy as a secondary metric | Excluded in the original methodology (M-11) |
| D-C | Thresholds for "consistently poor" and "small denominator" | Proposed: sensitivity < 20% with ≥ 10 positives; < 5 and 5–9 tiers |
| D-D | Whether to perform inferential tests (McNemar, paired bootstrap) or remain descriptive with CIs | Requires offline case-level analysis |
| D-E | Whether to fit an exploratory mixed-effects model | Convergence risk |
| D-F | Final section order and template | Springer template unresolved |
| D-G | FLAIR version, citation and item mapping | Not documented in the knowledge base |
| D-H | Final research-question wording; confirmation that RQ6 is treated as an exploratory Discussion topic | **Recommended:** RQ6 exploratory unless a controlled prompt ablation is performed (D-J) |
| D-I | Bootstrap settings (B, seed, percentile vs BCa), undefined-replicate rule and threshold, and multiplicity method | Proposed B = 10,000, a fixed seed, Holm. To be fixed only after testing on the actual case-level data |
| D-J | Whether any new experiments (Gemini on FT/CA, repeat runs, prompt ablation) will run before submission | Changes the answerability of RQ4–RQ6 |

---

## 12. Evidence boundaries (deliberately left unresolved)

These items are not supported by the knowledge base and are **not** filled in here:
- Gold Standard participants, procedure and disagreement resolution (GS-1 to GS-7).
- Matrix 1 label origin (GS-8).
- The rationale for case selection.
- Model snapshot identifiers.
- The FLAIR item list.
- The Springer template.
- Ethics, approval, funding and conflict-of-interest statements.
- Literature-based novelty.
- Any inferential statistic: no κ, CI or p-value has been computed yet.

---

## 13. Execution record and deviations (added after approval; the plan above is unchanged)

Analyses executed 2026-11-28 with `analysis/week08_statistics.py`. Outputs: `04_Evidence_and_Artifacts/07_Statistical_Analysis_Results.md` and `07_statistical_results.json` (aggregate only).

| Plan element | Executed as | Deviation or note |
|---|---|---|
| §6.2 metrics | All ten evaluations recomputed from case-level files; counts equal the registered values | F1 uses the plan definition. Macro F1 therefore differs from the workbook values, which remain the historical record |
| §6.3 condition-level | Wilson 95% intervals for sensitivity, specificity and precision; support counts; undefined flagged | D-C thresholds not applied as formal flags. The manuscript uses ≥ 10 reference positives as a descriptive cut-off only |
| §6.4 bootstrap (D-I) | Report-level cluster bootstrap; B = 10,000; seed 20261128; percentile intervals over defined replicates; undefined-replicate counts and contributing-condition ranges reported | Settings chosen by the analyst after testing on the case-level data; **owner approval pending**. κ intervals use the first 2,000 replicates (deviation, for speed) |
| §6.5 model comparison (D-D) | CT only: agreement, κ (overall and per condition), exact McNemar per condition with Holm, paired bootstrap Δ | Exploratory. No condition significant after Holm |
| §6.6 run-to-run | Five CT comparisons, including the Week 4 vs Week 5 quasi-repeat | — |
| §6.7 dependence | Pooled pairs never treated as independent; per-condition tests only | Mixed-effects model (D-E) **not** fitted |
| RQ2 reference agreement | Raw agreement and κ between Matrix 1 and Matrix 2 labels per dataset | — |
| D-A | Compatibility verified (CaseIDs, order, report text, keys, prediction format). Both Week 5 batches rescored against the other reference (exploratory) | **No batch selected.** The owner must record the selected batch (RUN-03 or RUN-04) and the reason |
| D-B balanced accuracy | Not reported | Unresolved |
| §6.9 pre-specification | Settings fixed in the script before final results were written | Settings were not owner-approved before execution; disclosed |
