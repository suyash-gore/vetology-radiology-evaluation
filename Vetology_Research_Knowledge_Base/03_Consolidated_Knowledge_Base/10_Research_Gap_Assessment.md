# 10 — Research Gap Assessment (provisional)

**Status:** a critical, **provisional** assessment of where this study may add to the literature identified in `09_Literature_Evidence_Matrix.md`. It is based on an owner-supplied seed set of 11 publications and targeted metadata lookups, **not** a systematic search. No statement here establishes novelty. Words such as "first", "novel" or "unprecedented" are not used as claims.
**Prepared:** 2026-11-28; baseline `fb30842`.
**Study facts used:** from `08_Research_Design_and_Analysis_Plan.md` and the evidence registers. The three datasets are treated with equal importance:
- Canine Thorax (CT): 100 cases, 20 conditions.
- Feline Thorax (FT): 100 cases, 21 conditions.
- Canine Abdomen (CA): 100 cases, 10 conditions.

They are **not** a controlled species or anatomical comparison: prompt policy, condition sets, prevalence and batch design all differ (`08_…` §5.2).
**Reference workflows:**
- Matrix 1 = original Vetology labels.
- Matrix 2 = Gold Standard labels, peer-reviewed and agreed upon after discussion. The detailed process is unresolved, and the labels are **not** independent veterinary-radiologist adjudication (`08_…` §4.2).

Status scale per candidate: **established** (the literature already covers it), **partially supported** (our evidence adds something, with material caveats), **candidate gap** (no covering study found so far, pending systematic search), **unsupported** (should not be claimed).

---

## 1. Central candidate gap (PROVISIONAL)

> "Although LLMs have been applied to veterinary clinical-text extraction, diagnosis coding and binary clinical-sign classification, and NLP has been extensively investigated for human radiology-report extraction, the literature identified so far has not established whether general-purpose LLMs can reliably perform structured, multi-condition classification from veterinary radiology report text across multiple species and anatomical regions, with performance evaluated against distinct reference-label workflows."

**Assessment.** Each clause is supported by the seed set:
- Veterinary clinical-text extraction: L02, L04, L05, L06.
- Diagnosis prediction: L03.
- Binary clinical-sign classification: L05.
- Human radiology-report extraction: L07, L08, L10, L11.

The negative clause ("has not established…") rests **only** on the 11-item seed set. That set contains no veterinary radiology-report study. **It does not demonstrate absence.**

Before the gap can be stated in a manuscript:
- The L01 scoping review's 23 included veterinary studies must be screened.
- A structured multi-database search must be completed (§6).

Even if the gap survives, our evidence supports only a **pilot-scale, descriptive** answer to "can… reliably perform": 100 cases per dataset, single runs for FT/CA, confounded cross-dataset differences, and incompletely documented references. "Reliably" should therefore not appear in any claim of what this study *shows*.

**Status: candidate gap (provisional).**

---

## 2. Candidate contribution areas

### 2.1 Veterinary report-text classification

| Element | Assessment |
|---|---|
| Existing coverage | LLMs on veterinary **clinical narratives/EHRs**: L02 (BCS extraction), L05 (six clinical signs), L04 (prescriptions), L03 (diagnosis prediction, fine-tuned), L06 (benchmark incl. multi-label ICD-11 chapters). None in the seed set uses **radiology reports** |
| What we add | Classification of **veterinary radiology report text** (original radiologist Findings, Conclusions and Recommendations) by general-purpose API models (gpt-4.1-mini; gemini-3.8-flash for CT) |
| Confounders / limits | Report-text classification ≠ image interpretation. The reference labels may encode image information absent from the text (`08_…` §8.3). The prompt-development process used project cases (`09_…` §8.2, P-6) |
| Status | **Candidate gap** (domain-specific), pending search |
| Cautious statement | "Within the literature reviewed so far, we did not identify a study evaluating general-purpose LLMs for classifying veterinary radiology report text." |
| Needed | Screen L01's included studies. Search veterinary radiology report NLP (including pre-LLM rule-based and ML work), conference proceedings (ACVR/ECVDI/EVDI abstracts, BioNLP) and preprints |

### 2.2 Multi-condition classification from radiology report text

| Element | Assessment |
|---|---|
| Existing coverage | Human radiology report extraction across many studies and entities (L08: 28 studies, 421,692 entities). Multi-label settings exist (L08 single vs multiple anatomical sites; L11 label extraction, to verify). L10 is single-condition (PE). Veterinary multi-label text classification exists outside radiology (L05: 6 signs; L06: ICD-11 chapters) |
| What we add | 51 condition keys in total (20 + 21 + 10), with per-condition confusion counts and verified per-condition results for every evaluation (`04_…/06_Per_Condition_Results.md`) |
| Confounders / limits | Many conditions have sparse positives (Matrix 2 has 0–4 positives in 12/20 CT, 16/21 FT and 4/10 CA conditions). Undefined metrics. Within-report dependence |
| Status | **Partially supported.** Multi-condition report classification is **established** in human radiology; the veterinary application is part of 2.1 |
| Cautious statement | "The study extends multi-condition report classification, studied extensively in human radiology, to veterinary radiology reports, at pilot scale." |
| Needed | Verify L07 and L11 details. Identify human studies with comparable label counts and prompt-based LLMs for methodological comparison |

### 2.3 Multiple veterinary species and anatomical domains

| Element | Assessment |
|---|---|
| Existing coverage | L05 is feline only. L02/L06 are companion animals in general. Image-based work (C01–C04) covers canine and feline thorax in the **image** modality only |
| What we add | Three datasets of equal standing (canine thorax, feline thorax, canine abdomen) evaluated in one pipeline |
| Confounders / limits | **Not a controlled species or region comparison.** The datasets differ in condition sets (CA shares no condition with the thoracic sets), prevalence, prompt version and uncertainty policy (CT inclusive, FT conservative, CA scoped-inclusive) and batch design (CT separate batches; FT/CA shared). Shared CT/FT key names are not identical clinical definitions. There is no feline abdomen or canine–feline paired region |
| Status | **Partially supported** (descriptive breadth only); a causal domain effect is **unsupported** |
| Cautious statement | "Results are reported for three veterinary report datasets spanning two species and two anatomical regions; differences between datasets are descriptive and confounded." |
| Needed | A controlled design would need a common prompt policy across datasets, or a prompt ablation (D-J). Search multi-species veterinary text studies |

### 2.4 Evaluation against two distinct reference-label workflows

| Element | Assessment |
|---|---|
| Existing coverage | Reference standards in the seed set include manual review (L02), the majority of five humans (L05), professional annotation (L06), existing annotations (L03) and CV-algorithm/LLM concordance with manual discrepancy review (L10). L05 relates LLM errors to human disagreement. No seed study scores one prediction set against **two different label sources** for the same cases |
| What we add | For FT and CA, the **same predictions** are scored against original Vetology labels (Matrix 1) and peer-reviewed, discussion-agreed Gold Standard labels (Matrix 2). There are large, verified prevalence differences (FT 534 vs 117; CA 280 vs 81; CT 1,049 vs 158) and correspondingly different sensitivity. CT does the same with separate batches, pending the D-A rescoring |
| Confounders / limits | The origin of the Matrix 1 labels and the Matrix 2 review process are undocumented (GS-1–GS-8). The reason the reference sets differ is unresolved. Neither reference is clinical truth. The Matrix 2 labels are **not** independent radiologist adjudication |
| Status | **Candidate gap** (the most distinctive feature identified so far), pending search on reference-standard dependence in report labelling |
| Cautious statement | "The study illustrates, at pilot scale, how strongly measured LLM performance on veterinary report classification depends on the choice of reference-label workflow." |
| Needed | Search label-noise and reference-standard-dependence literature in human radiology NLP. Document the Gold Standard process. Compute Matrix 1–Matrix 2 label agreement (κ) as planned |

### 2.5 Condition-level performance and class imbalance

| Element | Assessment |
|---|---|
| Existing coverage | L05 reports per-sign metrics with medians/IQR. L08 shows anatomical-site heterogeneity. Per-label reporting and imbalance handling are standard practice |
| What we add | Verified per-condition counts for all 10 evaluations. Explicit handling of zero-positive conditions, undefined metrics and small denominators (`08_…` §6.2–6.3) |
| Confounders / limits | Small samples per condition; undefined or unstable metrics; multiplicity |
| Status | **Established** as a methodology. Our condition-level findings are **partially supported** (descriptive) |
| Cautious statement | "Condition-level results show heterogeneous performance, including conditions with no correct positive predictions." Not a methodological novelty |
| Needed | Wilson/bootstrap intervals per the plan; per-condition comparison only where denominators allow |

### 2.6 Model comparison

| Element | Assessment |
|---|---|
| Existing coverage | GPT-4o vs GPT-3.5 Turbo (L05). GPT-3.5/GPT-4/LLaMA2-70B vs a BERT ensemble (L04). Three Gemini variants (L10). Open-source model sizes (L11, to verify). Zero-shot vs fine-tuned (L03) |
| What we add | gpt-4.1-mini vs gemini-3.8-flash under the same prompt hash, input boundary, validator and metrics: **Canine Thorax only**, Matrix 1 and Matrix 2; agreement 97.00%/97.20% |
| Confounders / limits | CT only. Single run per model. Different dates, client/retry configuration and response format; unknown snapshots. **Not a three-dataset comparison** |
| Status | **Established** in general (model comparisons are common). Ours is **partially supported**, limited to CT |
| Cautious statement | "In Canine Thorax, two general-purpose models showed high prediction agreement but different sensitivity/specificity profiles against both references." |
| Needed | Gemini (or other) runs on FT and CA would be required before any multi-dataset model comparison (D-J) |

### 2.7 Repeatability and prompt uncertainty

| Element | Assessment |
|---|---|
| Existing coverage | **L05 already studies repeatability in veterinary text**: five repeated GPT-4o runs at temperatures 0, 0.5 and 1, with κ 0.98 between runs vs 0.80 between humans. L10 studies prompt design, data perturbation and repeated analyses across cloud regions. Prompt strategy effects: L04, L11 (to verify) |
| What we add | Observed (not designed) run-to-run differences at temperature 0 in CT: 8, 11 and 13 of 2,000 pairs between separate batches on identical report text. Three different uncertainty policies across datasets |
| Confounders / limits | Repeats are incidental and CT-only. Prompt policy is perfectly confounded with dataset. No prompt ablation. RQ6 is exploratory (`08_…` §2) |
| Status | Repeatability as a research topic is **established** (L05, L10). Our repeatability evidence is **partially supported** (CT, descriptive). Prompt-policy effects are **unsupported** as a finding |
| Cautious statement | "Consistent with prior reports of LLM output variability, separate executions at temperature 0 were not identical in this project." |
| Needed | Designed repeat runs (≥ 2 per dataset), a prompt ablation, and full-text review of L10/L11 |

### 2.8 Reproducibility and transparent evaluation architecture

| Element | Assessment |
|---|---|
| Existing coverage | L05 publishes its scripts (GitHub) and reports its API version. L09 (FLAIR) sets reporting expectations. L01 discusses reproducibility (to verify) |
| What we add | Prompt and input SHA-256 pinning, run manifests, isolation, and offline re-evaluation that reproduced every workbook count exactly (`04_Technical_Architecture_and_Reproducibility.md` §3) |
| Confounders / limits | Engineering provenance is not scientific validity. Model snapshots and request IDs are unrecorded. Data cannot be shared (confidential) |
| Status | **Partially supported** as a practical contribution. **Not** a methodological novelty (provenance practices exist broadly) |
| Cautious statement | "The evaluation was implemented with versioned prompts, hashed inputs and run manifests, allowing all reported counts to be reproduced from retained artifacts." |
| Needed | A FLAIR item-level check (`11_…`); a data/code availability statement; a search of reproducibility frameworks for LLM evaluation |

---

## 3. Explicit comparison with Wulcan et al. (2025) — L05

### 3.1 How our task differs

L05 is the closest methodological analogue in the seed set. It must be cited as such.

| Dimension | Wulcan et al. (L05) | This study |
|---|---|---|
| Text type | Veterinary referral-hospital EHR text (clinical history) | Veterinary **radiology report** text (original radiologist Findings, Conclusions, Recommendations) |
| Species / domain | Feline; gastrointestinal clinical signs (FCE) | Canine thorax, feline thorax, canine abdomen; radiographic diagnostic conditions |
| Labels | 6 clinical signs per record | 20 / 21 / 10 conditions per report (51 keys in total) |
| Sample | 250 test EHRs (plus separate pilot and tuning sets) | 100 reports per dataset |
| Prompt development vs evaluation data | **Separate tuning set**, distinct from the test set | Prompt review and a hedged-language analysis used project cases and reference labels. Overlap with the evaluation sets is **to be confirmed** (P-6; FLAIR 1.5) |
| Reference standard | Majority of 5 blinded human respondents | Two label workflows: original Vetology labels; peer-reviewed, discussion-agreed Gold Standard (process undocumented) |
| Models | GPT-4o, GPT-3.5 Turbo (Azure, API version 2024-02-01) | gpt-4.1-mini (all datasets); gemini-3.8-flash (CT only) |
| Repeatability | **Designed**: 5 runs × 3 temperatures; κ between runs | **Incidental**, CT-only, temperature 0; differing pairs between separate batches |
| Metrics | Sens, spec, PPV, NPV, F1, balanced accuracy (median/IQR); McNemar; κ | Sens, spec, precision, F1, accuracy; micro/macro; per-condition; planned Wilson/bootstrap, κ, McNemar (`08_…` §6) |
| Additional analyses | Citation task; error attribution to human disagreement; cost and time | Matrix 1 vs Matrix 2 reference dependence; condition-level sparsity analysis |

### 3.2 Implications

- Our study **does not** introduce LLM binary classification of veterinary clinical text, or the study of LLM repeatability in veterinary text. L05 covers both.
- Distinguishing features to examine (still provisional):
  - radiology report text;
  - larger condition sets across three datasets;
  - dependence on two reference workflows.
- L05's separate tuning set and designed repeat runs are **methodological strengths our study lacks**. They should be acknowledged as limitations.

---

## 4. What our three datasets can and cannot support

- **Can:** a parallel, equally weighted description of performance per dataset and per reference workflow, and per-condition profiles within each dataset.
- **Cannot:** attribute differences to species or anatomy, because prompt policy, condition sets, prevalence, reference process and batch design differ. Nor can we generalise beyond 100 non-randomly selected cases per dataset.

---

## 5. Conclusions

### 5.1 Best-supported potential contribution (provisional)

A pilot-scale, equally weighted evaluation of general-purpose LLMs classifying **veterinary radiology report text** across three datasets (canine thorax, feline thorax, canine abdomen). Measured performance is shown to depend strongly on the **reference-label workflow**: the same predictions were scored against original labels and against a peer-reviewed, discussion-agreed Gold Standard (FT, CA; CT pending D-A). The evaluation is backed by verified condition-level results and a reproducible evaluation pipeline.

### 5.2 What should NOT be claimed

- "First", "novel", "unprecedented" or "no prior study", unless a systematic search and screening of L01's included studies support it.
- That LLMs can **reliably** classify veterinary radiology reports, or any clinical validity, diagnostic accuracy or readiness.
- Any image-interpretation capability. The models received text only.
- A controlled species or anatomical comparison, or causal effects of prompt or uncertainty policy.
- That Matrix 2 is independent veterinary-radiologist adjudication or clinical truth.
- A three-dataset OpenAI-vs-Gemini comparison. That comparison is CT only.
- That our repeatability evidence is new in kind (L05 and L10 precede it), or that it characterises LLMs generally.
- That veterinary NLP lacks benchmarks (L06 exists).
- That prompts were derived from textbooks rule by rule (there is no traceability; `09_…` §8.2).

### 5.3 Additional evidence required before novelty language is approved

1. A documented multi-database search (§6) with dates, strings, screening counts and inclusion criteria.
2. Screening of L01's 23 veterinary included studies for radiology-report text.
3. Full-text verification of L01, L07, L09, L10 and L11. The details marked "to verify" in `09_…` must be resolved.
4. Documentation of the Gold Standard process (GS-1–GS-8) and the Matrix 1 label origin.
5. Confirmation of prompt-development data separation (P-6; FLAIR 1.5).
6. The completed statistical analyses in `08_…` §6 (intervals, reference agreement κ, the D-A rescoring).
7. Author approval of the final contribution wording.

---

## 6. Additional searches required (proposed, not run)

| # | Concept block | Example terms | Sources |
|---|---|---|---|
| S1 | Veterinary radiology report NLP/LLM | (veterinary OR canine OR feline OR "small animal") AND ("radiology report*" OR "radiograph* report*" OR "imaging report*" OR "diagnostic imaging report*") AND (NLP OR "natural language processing" OR "large language model*" OR GPT OR Gemini OR LLaMA OR "text classification" OR "information extraction") | PubMed, CAB Abstracts, Web of Science, Scopus, ACL Anthology, arXiv |
| S2 | Veterinary LLM clinical text (update L01 beyond its cut-off) | veterinary AND ("large language model*" OR ChatGPT OR GPT-4* OR Gemini) AND (EHR OR "clinical record*" OR narrative*) | Same |
| S3 | Reference-standard dependence in report labelling | ("reference standard" OR "ground truth" OR "label noise" OR "annotation disagreement") AND ("radiology report*") AND (NLP OR LLM) | PubMed, ACL Anthology |
| S4 | LLM repeatability / non-determinism in clinical text classification | (reproducib* OR repeatab* OR "non-determinism" OR temperature) AND LLM AND (clinical OR radiology) | PubMed, arXiv |
| S5 | Image-based veterinary radiology AI (context only) | (deep learning OR CNN OR AI) AND (canine OR feline) AND (radiograph*) AND (thorax OR abdomen) | PubMed, Scopus |
| S6 | Reporting guidance | FLAIR, TRIPOD-LLM, CLAIM, STARD-AI and related LLM reporting guidance (to verify existence and versions before citing) | Publisher sites |


## 7. Final cautious gap statement used in the manuscript (Week 8)

> "Existing research has examined LLM-based information extraction and classification from veterinary clinical narratives, alongside extensive work on human radiology-report extraction. The specific application of general-purpose LLMs to multi-condition binary classification of veterinary radiology report text, evaluated across canine and feline thoracic and canine abdominal datasets under distinct reference-label workflows, warrants further investigation."

The manuscript introduces this as a provisional observation from a targeted, non-systematic review. Supporting evidence added in Week 8 (§2.4):
- With identical predictions, sensitivity differed by +44.1 pp (FT) and +53.3 pp (CA) between the reference workflows, and by +67.1 pp in the CT exploratory rescoring.
- The two label sets agreed only slightly beyond chance (κ 0.03–0.13).

This strengthens 2.4 as the best-supported potential contribution. It does **not** establish novelty: §5.3 still applies.


**Week 8 v0.2 correction to the wording above.** The disagreement between workflows is described with positive agreement (CT 19.7%, FT 12.0%, CA 23.8%), negative agreement (65.3%, 83.9%, 83.2%), the directional counts and prevalence, together with κ. κ alone is not used, because it is prevalence-dependent. The finding supports the reference-dependence observation (2.4). It does not show that either reference is clinically correct or incorrect.


**v0.3 note (2.4).** Matrix 2 is now confirmed as a three-reviewer, independently generated, majority-vote research-team reference. Its individual annotation files were deleted, so inter-reviewer reliability is unavailable. The reference-dependence observation stands, but it remains a contrast between two non-validated labelling workflows.
