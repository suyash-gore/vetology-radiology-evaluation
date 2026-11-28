# Evaluating Large Language Models for Structured Condition Classification from Veterinary Radiology Reports: A Comparative Study Across Three Datasets

**Draft v0.2. Not for submission.** Prepared 2026-11-28 on branch `week-08/research-paper-development`.

*Revision note (v0.1 → v0.2):*
- The statistical settings were finalized and approved by the owner.
- Reference-label agreement is now reported with positive and negative agreement and prevalence, not κ alone.
- The interpretation of reference disagreement was revised.
- The status of the exploratory Canine Thorax rescoring was clarified.

All confusion counts are unchanged; v0.1 is retained unchanged.
**Author:** Suyash Kishor Gore `[AUTHOR CONFIRMATION REQUIRED: final author list, affiliations, ORCID, corresponding author]`
**Programme:** Vetology Free Training Program.
**Evidence map:** every number in this draft is traceable through `paper/README.md`.

---

## Abstract

**Background.** Large language models (LLMs) are increasingly used to extract information from clinical text, but their behaviour on veterinary radiology reports is not well characterised.
**Objective.** To evaluate general-purpose LLMs for structured, binary, multi-condition classification of veterinary radiology report text.
**Methods.** In this retrospective pilot, report text (no images) from canine thoracic, feline thoracic and canine abdominal datasets (100 reports each; 20, 21 and 10 conditions) was classified with GPT-4.1 mini. Predictions were scored against original Vetology labels (Matrix 1) and peer-reviewed, discussion-agreed Gold Standard labels (Matrix 2). A Gemini model was compared on the canine thoracic data only.
**Results.** Specificity exceeded 96% in all ten evaluations. Sensitivity depended strongly on the reference set:
- Canine thorax: 12.01% (Matrix 1) vs 79.75% (Matrix 2).
- Feline thorax: 5.43% vs 49.57%.
- Canine abdomen: 12.14% vs 65.43%.

The two reference-label workflows disagreed substantially (positive agreement 12–24%; κ 0.03–0.13). The OpenAI and Gemini predictions agreed on 97.00% and 97.20% of pairs. Repeated executions at temperature 0 differed on 8–13 of 2,000 pairs.
**Conclusion.** Measured performance depended primarily on which reference-label workflow was used. Reference provenance must be established before LLM-based report labelling can be interpreted. No clinical validity is implied.

*(Word count ≈ 190.)*

**Keywords:** large language models; veterinary radiology; radiology reports; text classification; reference standard; reproducibility

---

## 1. Introduction

Free-text clinical records are a large but under-used resource in veterinary medicine. Converting them into structured data has been approached with rule-based methods, supervised machine learning and, more recently, prompt-based LLMs (Chang and Chu, 2026). In veterinary clinical narratives, LLMs have been used:
- to identify body-condition-score information (Fins et al., 2024);
- to predict diagnoses from clinical notes, with a fine-tuned model (Jiang et al., 2024);
- to extract prescription attributes (Hur et al., 2024);
- to classify six clinical signs of feline chronic enteropathy, with an explicit evaluation of repeatability (Wulcan et al., 2025).

A veterinary free-text benchmark has also been published (Farrell et al., 2025). In human medicine, information extraction from radiology reports has been studied extensively. A recent meta-analysis pooled 28 NLP studies (Yang et al., 2026), and LLM-specific work has examined prompt and data-perturbation sensitivity (Sorin et al., 2025). A scoping review (Reichenpfader et al., 2024) and a study of model size and prompting in report label extraction (Khosravi et al., 2026) are also relevant. `[SOURCE VERIFICATION REQUIRED: the full texts of Reichenpfader et al. and Khosravi et al. have not been reviewed; they are cited for their stated topic only.]`

Veterinary radiology reports differ from general clinical notes in vocabulary, structure and diagnostic hedging. In the targeted, non-systematic review conducted for this work, we did not identify a study that applied general-purpose LLMs to multi-condition binary classification of veterinary radiology report text, evaluated across canine and feline thoracic and canine abdominal datasets under distinct reference-label workflows. This application therefore warrants investigation. **This is a provisional observation, not a claim of novelty.** The review was not systematic, and the studies included in Chang and Chu (2026) have not yet been screened.

This study asks how such classification performs across three veterinary datasets, and how strongly measured performance depends on the reference-label workflow. Secondary, Canine-Thorax-only questions concern the agreement between two model families and run-to-run consistency. The study evaluates **text classification only**. The models received no radiographic images, and the work is not an assessment of image interpretation, diagnosis or clinical readiness.

---

## 2. Materials and Methods

### 2.1 Study design and scope

A retrospective, multi-dataset comparative evaluation of LLM-based text classification, conducted within the Vetology Free Training Program (Weeks 3–8, November 2026). The three datasets have equal standing. They are not a controlled comparison of species or anatomical regions, because their condition sets, prevalence, prompts and batch designs differ (Section 2.6).

### 2.2 Datasets and case selection

Each dataset comprised the first 100 populated records of an encoded workbook supplied for the programme (Table 1). Case selection was therefore **not random** `[AUTHOR CONFIRMATION REQUIRED: rationale and origin of the first-100 selection; source period and clinic mix]`.

For each case, the model input was the original radiologist's report split into three fields: *Findings*, *Conclusions* and *Recommendations*. Empty fields were sent as `[Not provided]`. Case identifiers, reference labels and AI-generated report fields were excluded from the model input, and this was enforced in code. Within each dataset, the Matrix 1 and Matrix 2 workbooks contain identical CaseIDs, order and report text. This was documented for Feline Thorax and Canine Abdomen during implementation and verified for Canine Thorax in this work (Section 3.6). No patient or clinic identifiers, report text or case-level data are reproduced here.

**Table 1. Datasets and reference-label characteristics.** Sources: `04_Evidence_and_Artifacts/03_Confusion_Matrix_and_Metrics_Register.md`; `06_Per_Condition_Results.md`.

| | Canine Thorax (CT) | Feline Thorax (FT) | Canine Abdomen (CA) |
|---|---|---|---|
| Reports | 100 | 100 | 100 |
| Conditions (binary) | 20 | 21 | 10 |
| Report–condition pairs per reference | 2,000 | 2,100 | 1,000 |
| Matrix 1 positives (prevalence) | 1,049 (52.5%) | 534 (25.4%) | 280 (28.0%) |
| Matrix 2 positives (prevalence) | 158 (7.9%) | 117 (5.6%) | 81 (8.1%) |
| Matrix 2 conditions with 0 positives | 4 | 10 | 0 |
| Matrix 2 conditions with 1–4 positives | 8 | 6 | 4 |
| Active prompt | Canine Thorax Master Prompt V1.3 | Feline Thorax Master Prompt V1.2 | Canine Abdomen Master Prompt V1.4 |

The condition keys are listed in Appendix B. The Feline Thorax condition names include all 20 Canine Thorax names plus `Fe_Alveolar`. Shared names do not imply identical clinical definitions, because the prompts define and threshold conditions differently. The Canine Abdomen conditions do not overlap with the thoracic sets.

### 2.3 Classification task and condition definitions

For each report, the model returned one JSON object containing every configured condition key exactly once, each with the value `Positive` or `Negative`. There was no "uncertain" category. Responses were validated strictly: exactly one JSON object, the exact key set, no duplicate keys and only the two permitted values. Invalid responses were retried and never repaired.

Definitions were written in one "master prompt" per dataset. Each master prompt sets out the role, the permitted evidence (the three report fields only), shared rules, condition-specific definitions and the output contract.

Three definitional clarifications were relayed by the programme's Tech Advisor:
- `rtm` denotes redundant tracheal membrane;
- `diseased_lungs` is an independent condition;
- explicitly possible or suspected conditions are classified as Positive.

The last rule is implemented in the Canine Thorax V1.3 prompt. The developer's working interpretation of `Fe_Alveolar` as *Feline Alveolar Pattern* was not confirmed by the advisor.

### 2.4 Reference-label workflows

- **Matrix 1** uses the original Vetology condition labels in the encoded source workbooks. In Feline Thorax, three Matrix 1 columns recorded Normal/Abnormal and were mapped to Negative/Positive; no other column was transformed. Matrix 1 evaluation workbooks label these counts "GS Positive/Negative". This is legacy terminology preserved for compatibility; the reference source remains the Vetology labels. `[AUTHOR CONFIRMATION REQUIRED: origin and encoding history of the Matrix 1 labels.]`
- **Matrix 2** uses Gold Standard labels that were **peer-reviewed and agreed upon after discussion** within the programme. They are not described here as independent veterinary-radiologist adjudication or as clinical truth. `[AUTHOR CONFIRMATION REQUIRED: number, roles and qualifications of reviewers; whether initial scoring was independent and blinded; how disagreements were resolved; whether agreement was measured; whether the Feline Thorax and Canine Abdomen workbooks, whose filenames end in "draft", are final.]`

### 2.5 Prompt development

Prompts were developed iteratively in Week 3 (V1.0 baseline, then V1.1). They were then revised following Tech Advisor clarifications (Canine Thorax V1.3, 3 November 2026).

For Canine Thorax V1.3, the developer:
- consulted ten veterinary diagnostic-imaging reference texts (Appendix A.3);
- queried them with NotebookLM using targeted questions;
- consolidated the extracted material with ChatGPT;
- received guidance from Dr. Parin Candy.

The precise editions, the mapping from sources to individual rules, the intermediate notes and the scope of the expert input are not documented. There is no record that the same process informed the Feline Thorax or Canine Abdomen prompts. The prompts instruct the model not to rely on external medical knowledge, so domain knowledge shaped the authors' wording of the rules rather than being supplied to the model at inference.

The Week 7 prompts were registered byte-for-byte with SHA-256 digests:
- **Feline Thorax V1.2** corrected only the quotation marks in the JSON output example of V1.1.
- **Canine Abdomen V1.3** resolved contradictory uncertainty rules in V1.2.
- **Canine Abdomen V1.4** narrowed a differential-diagnosis clause.

As a result, the three active prompts encode different policies for hedged language:
- Canine Thorax: possible or suspected → Positive.
- Feline Thorax: conservative; possible or suspected → Negative unless confirmed.
- Canine Abdomen: Positive only when named in the primary impression and supported by findings.

**Overlap between prompt development and evaluation.** Selected cases from the eventual evaluation datasets were reviewed during prompt development, using report text and model predictions:
- Canine and Feline Thorax: cases 3, 4, 5, 7 and 8;
- Canine Abdomen: cases 13–17.

The developer reports that reference labels were not inspected during this manual review. The developer also does not recall inspecting reference labels during the Canine Abdomen hedged-language analysis. However, the provenance of a previously documented keyword-based analysis, recorded as tabulating reference labels, could not be independently established. Possible reference-label exposure therefore remains unresolved. The evaluation sets are **not held out**: adaptive prompt refinement on evaluation cases may have influenced results, particularly for Canine Abdomen.

### 2.6 Models, configurations and executions

All runs used temperature 0 and the same input boundary, validator and metric engine (Table 2). Model aliases were recorded; exact provider snapshot identifiers were not.

**Table 2. Evaluation runs and configurations.** Sources: `04_Evidence_and_Artifacts/02_Experimental_Run_Register.md`; `04_Prompts_and_Configurations_Index.md`.

| Run | Dataset | Model (alias) | Prompt | Date (UTC) | Batch design | Evaluated against |
|---|---|---|---|---|---|---|
| RUN-02 / RUN-01 | CT | gpt-4.1-mini (Week 4 application) | V1.3 | 7 Nov / 3 Nov | Separate batch per matrix | M1 (EVAL-01) / M2 (EVAL-02) |
| RUN-03 / RUN-04 | CT | gpt-4.1-mini (Week 5 rebuild) | V1.3 | 12 Nov | Separate batch per matrix | M1 (EVAL-05) / M2 (EVAL-06) |
| RUN-05 / RUN-06 | CT | gemini-3.8-flash | V1.3 | 20 Nov | Separate batch per matrix | M1 (EVAL-07) / M2 (EVAL-08) |
| RUN-07 | FT | gpt-4.1-mini | V1.2 | 21 Nov | One batch, scored against both | M1 (EVAL-11), M2 (EVAL-12) |
| RUN-08 | CA | gpt-4.1-mini | V1.4 | 21 Nov | One batch, scored against both | M1 (EVAL-13), M2 (EVAL-14) |

- The OpenAI runs used LangChain `ChatOpenAI` with a 90 s timeout.
- The Gemini runs used `ChatGoogleGenerativeAI` with JSON MIME output and no schema.
- Each case was allowed up to two application-level attempts. Transport retries and backoff differed between application versions (Appendix C).

Failed attempts never contributed predictions:
- Before the successful Week 5 Matrix 1 batch, an earlier attempt failed on all 100 cases with an authentication error (expired API key).
- One Gemini Matrix 2 case failed three times (two HTTP 503 errors, one 504) before succeeding.

### 2.7 Prediction and evaluation workflow

Predictions were checkpointed as JSON Lines. A run manifest recorded the model, settings, prompt digests, input digest and package versions; manifests exist for the Week 7 runs only. Evaluation was offline and deterministic: it reconciled predictions with references by CaseID and produced confusion matrices and evaluation workbooks. All counts in this paper were re-derived independently from the prediction files and the source workbooks and matched the workbooks exactly (Section 2.10).

### 2.8 Confusion matrices and performance metrics

For each condition, reference and prediction were cross-tabulated (TP, FN, TN, FP). The metrics were:
- Accuracy = (TP+TN)/N;
- Sensitivity = TP/(TP+FN);
- Specificity = TN/(TN+FP);
- Precision = TP/(TP+FP);
- F1 = 2TP/(2TP+FP+FN).

A ratio with a zero denominator is undefined and is never reported as 0 or 100%. In particular, for a condition with no reference positives:
- F1 is 0 if the model made false-positive predictions;
- F1 is undefined if it made none.

Micro averages pool the counts over conditions. Macro averages are unweighted means over conditions with defined values, and the number of included conditions is reported because it varies by metric and reference. The evaluation workbooks used a slightly different F1 convention: F1 was blank when precision or sensitivity was undefined. The workbook values are retained as the historical record. Micro F1 is identical under both conventions in all ten evaluations.

### 2.9 Statistical analysis

The analysis followed a written plan (`03_Consolidated_Knowledge_Base/08_Research_Design_and_Analysis_Plan.md`). The plan fixed the metrics, the report-level resampling unit, the use of Wilson intervals and the restriction of paired comparisons to shared predictions. Several **execution settings were finalized during the analysis**: the number of resamples, the seed, the percentile interval rule, the rule for undefined replicates and Holm adjustment for the per-condition tests. These were then approved by the study owner. They are therefore not all pre-specified (plan §13).

Because each report contributes 10–21 correlated labels, pairs were **not** treated as independent:
- **Micro and macro metrics:** a report-level cluster bootstrap. The 100 reports were resampled with replacement, keeping all their labels together (B = 10,000; seed 20261128; percentile 95% intervals over defined replicates). The frequency of undefined replicates was recorded.
- **Per-condition sensitivity, specificity and precision:** 95% Wilson intervals.
- **Paired contrasts** were computed only where predictions were genuinely shared:
  - Matrix 2 versus Matrix 1 on the same prediction set (Feline Thorax, Canine Abdomen; for Canine Thorax only as an exploratory rescoring, Section 3.6);
  - Gemini versus GPT-4.1 mini on the same Canine Thorax cases and references.
- **Agreement:**
  - Between the two reference label sets: raw agreement, positive agreement PA = 2n₁₁/(2n₁₁+n₁₀+n₀₁), negative agreement NA = 2n₀₀/(2n₀₀+n₁₀+n₀₁), Cohen's κ, the directional disagreement counts and each matrix's positive prevalence. Intervals use 2,000 report-level resamples. Because κ depends on prevalence, which differs greatly between the matrices, it is not interpreted alone.
  - Between models, and between repeated runs: Cohen's κ.
- **Exploratory per-condition test:** an exact McNemar test of discordant correctness between models, across 100 cases, with Holm adjustment within each matrix.

All intervals are conditional on these non-randomly selected cases, labels, prompts and runs. They do not capture reference-label uncertainty, model drift or variability between runs. Statistical tests are exploratory.

### 2.10 Reproducibility and data confidentiality

The code, prompts (with SHA-256 digests), run manifests and analysis script (`analysis/week08_statistics.py`) are version-controlled. The script reproduces every confusion count from the retained case-level files and aborts on any discrepancy; two executions produced identical output. Source workbooks, prediction files and report text are confidential and are not in the public repository. Reporting was checked against the FLAIR guideline for LLM studies in radiology (Kottlors et al., 2026) as voluntary guidance. The item-level check is incomplete because the guideline's checklist appendix could not be retrieved, and compliance is not claimed. `[AUTHOR CONFIRMATION REQUIRED: ethics/approval status and data-use permission; data-availability statement.]`

---

## 3. Results

### 3.1 Overview

All ten reference-based evaluations completed with 100 successfully validated predictions per run. Table 3 reports the counts and the micro metrics; the counts reconcile exactly to the evaluation workbooks.

**Table 3. Confusion counts and micro metrics for all ten evaluations, with 95% report-level bootstrap intervals.** Sources: `04_Evidence_and_Artifacts/03_Confusion_Matrix_and_Metrics_Register.md`; `07_Statistical_Analysis_Results.md` §1.

| Evaluation | Ref. | TP | FN | TN | FP | Accuracy | Sensitivity | Specificity | Precision | F1 |
|---|---|---:|---:|---:|---:|---|---|---|---|---|
| CT, Week 4, GPT-4.1 mini (EVAL-01) | M1 | 128 | 921 | 913 | 38 | 52.05 (47.15–57.05) | 12.20 (9.50–14.88) | 96.00 (94.10–97.66) | 77.11 (67.11–86.06) | 21.07 (16.75–25.13) |
| CT, Week 4, GPT-4.1 mini (EVAL-02) | M2 | 127 | 31 | 1,803 | 39 | 96.50 (95.55–97.40) | 80.38 (73.24–86.67) | 97.88 (97.12–98.57) | 76.51 (70.15–82.39) | 78.40 (72.84–82.97) |
| CT, Week 5, GPT-4.1 mini (EVAL-05) | M1 | 126 | 923 | 916 | 35 | 52.10 (47.20–57.15) | 12.01 (9.28–14.67) | 96.32 (94.48–97.88) | 78.26 (68.45–87.15) | 20.83 (16.46–24.88) |
| CT, Week 5, GPT-4.1 mini (EVAL-06) | M2 | 126 | 32 | 1,806 | 36 | 96.60 (95.65–97.50) | 79.75 (72.53–86.14) | 98.05 (97.29–98.73) | 77.78 (71.34–83.89) | 78.75 (73.15–83.47) |
| CT, Week 7, Gemini (EVAL-07) | M1 | 96 | 953 | 924 | 27 | 51.00 (45.90–56.30) | 9.15 (7.06–11.30) | 97.16 (95.61–98.47) | 78.05 (67.29–87.62) | 16.38 (12.86–19.85) |
| CT, Week 7, Gemini (EVAL-08) | M2 | 102 | 56 | 1,822 | 20 | 96.20 (95.15–97.20) | 64.56 (56.73–72.44) | 98.91 (98.43–99.35) | 83.61 (76.86–89.57) | 72.86 (66.19–78.91) |
| FT, Week 7, GPT-4.1 mini (EVAL-11) | M1 | 29 | 505 | 1,529 | 37 | 74.19 (70.48–77.71) | 5.43 (2.85–7.99) | 97.64 (96.69–98.49) | 43.94 (25.40–60.87) | 9.67 (5.15–13.96) |
| FT, Week 7, GPT-4.1 mini (EVAL-12) | M2 | 58 | 59 | 1,975 | 8 | 96.81 (95.95–97.62) | 49.57 (37.27–61.16) | 99.60 (99.29–99.85) | 87.88 (78.66–95.59) | 63.39 (51.66–72.63) |
| CA, Week 7, GPT-4.1 mini (EVAL-13) | M1 | 34 | 246 | 697 | 23 | 73.10 (69.60–76.40) | 12.14 (8.41–16.05) | 96.81 (95.28–98.15) | 59.65 (45.76–73.33) | 20.18 (14.46–25.77) |
| CA, Week 7, GPT-4.1 mini (EVAL-14) | M2 | 53 | 28 | 915 | 4 | 96.80 (95.70–97.90) | 65.43 (54.55–75.61) | 99.56 (99.12–99.89) | 92.98 (86.49–98.31) | 76.81 (68.42–83.93) |

All values are percentages with 95% intervals in parentheses. The Week 4 Matrix 2 F1 is 0.78395 (displayed as 78.40%). A truncated value of 78.39% appears in an earlier technical report.

### 3.2 Results by dataset and reference workflow

The datasets are reported in parallel.

- **Canine Thorax.** Against Matrix 1, all three runs combined high specificity (96.00–97.16%) with low sensitivity (9.15–12.20%). Against Matrix 2, sensitivity was 64.56–80.38% and specificity 97.88–98.91%. Accuracy was about 51–52% against Matrix 1 and about 96–97% against Matrix 2.
- **Feline Thorax.** Specificity was 97.64% (Matrix 1) and 99.60% (Matrix 2), while sensitivity was 5.43% and 49.57%. The model made positive predictions for 11 of the 21 conditions (66 positive labels in total).
- **Canine Abdomen.** Specificity was 96.81% and 99.56%; sensitivity was 12.14% and 65.43%. Precision against Matrix 2 was 92.98%.

**Table 4. Matrix 2 minus Matrix 1 on identical predictions (paired report-level bootstrap, percentage points, 95% interval).** Source: `07_Statistical_Analysis_Results.md` §3 and §7.

| Dataset (prediction set) | Sensitivity | Specificity | Precision | F1 | Accuracy |
|---|---|---|---|---|---|
| FT (RUN-07) | +44.14 (+33.45 to +54.38) | +1.96 (+1.15 to +2.86) | +43.94 (+26.15 to +63.16) | +53.72 (+44.41 to +61.59) | +22.62 (+18.95 to +26.38) |
| CA (RUN-08) | +53.29 (+43.82 to +62.76) | +2.76 (+1.43 to +4.27) | +33.33 (+17.74 to +49.02) | +56.63 (+48.57 to +64.80) | +23.70 (+20.20 to +27.30) |
| CT (RUN-03; exploratory rescoring) | +67.10 (+60.62 to +73.30) | +1.73 (+0.14 to +3.48) | −0.62 (−12.24 to +11.52) | +57.54 (+51.84 to +63.07) | +44.45 (+39.45 to +49.35) |

**Table 4b. Agreement between the two reference-label workflows on the same report–condition pairs.** These statistics describe disagreement between two labelling workflows; they do not show which, if either, is clinically correct. Source: `07_Statistical_Analysis_Results.md` §4.

| Dataset | Pairs | M1 positive prevalence | M2 positive prevalence | Both positive | Both negative | M1 Pos / M2 Neg | M1 Neg / M2 Pos | Raw agreement | Positive agreement (95% CI) | Negative agreement (95% CI) | Cohen's κ (95% CI) |
|---|---:|---|---|---:|---:|---:|---:|---|---|---|---|
| CT | 2,000 | 52.45% | 7.90% | 119 | 912 | 930 | 39 | 51.55% | 19.72% (15.80–23.55) | 65.31% (59.98–70.24) | 0.069 (0.041 to 0.097) |
| FT | 2,100 | 25.43% | 5.57% | 39 | 1,488 | 495 | 78 | 72.71% | 11.98% (7.82–15.91) | 83.85% (81.09–86.29) | 0.031 (−0.008 to 0.067) |
| CA | 1,000 | 28.00% | 8.10% | 43 | 682 | 237 | 38 | 72.50% | 23.82% (17.98–29.47) | 83.22% (80.75–85.50) | 0.129 (0.077 to 0.183) |

In every dataset, most disagreements were labels positive in Matrix 1 but negative in Matrix 2: 930 of 969 in CT, 495 of 573 in FT and 237 of 275 in CA. Positive agreement was low (12–24%). Negative agreement was higher (65–84%), but it is partly driven by the many labels negative in both matrices. Raw agreement is higher in FT and CA than in CT mainly because Matrix 1 prevalence is lower there. The κ values are low in all three datasets, but they are not interpreted as a measure of reference quality.

### 3.3 Condition-level performance

Per-condition counts, Wilson intervals and support are given in `07_Statistical_Analysis_Results.md` §8 and `06_Per_Condition_Results.md`. Table 5 summarises conditions with at least 10 reference positives.

**Table 5. Condition-level sensitivity for selected conditions (≥ 10 reference positives), with 95% Wilson intervals.** Source: `07_Statistical_Analysis_Results.md` §8.

| Dataset / reference | Lowest sensitivity | Highest sensitivity |
|---|---|---|
| CT M1 (EVAL-05) | bronchiectasis 0/67 (0.0–5.4); focal_perihilar 0/58 (0.0–6.2); hypo_plastic_trachea 0/35 (0.0–9.9) | diseased_lungs 28/63, 44.4% (32.8–56.7); cardiomegaly 12/29, 41.4% (25.5–59.3) |
| CT M2 (EVAL-06; 5 conditions eligible) | bronchitis 9/15, 60.0% (35.7–80.2); diseased_lungs 33/48, 68.8% (54.7–80.1) | interstitial 28/28, 100% (87.9–100); left_sided_cardiomegaly 13/15, 86.7% (62.1–96.3) |
| FT M1 (EVAL-11) | esophagitis 0/59 (0.0–6.1); pneumonia 0/51 (0.0–7.0); 11 of 21 conditions with TP = 0 | diseased_lungs 10/33, 30.3% (17.4–47.3); bronchitis 4/14, 28.6% (11.7–54.6) |
| FT M2 (EVAL-12; 3 eligible) | bronchitis 11/38, 28.9% (17.0–44.8); diseased_lungs 18/46, 39.1% (26.4–53.5) | cardiomegaly 9/10, 90.0% (59.6–98.2) |
| CA M1 (EVAL-13) | pancreatitis 2/75, 2.7% (0.7–9.2); splenomegaly 1/19, 5.3% (0.9–24.6) | hepatomegaly 11/47, 23.4% (13.6–37.2); gastritis 6/29, 20.7% (9.8–38.4) |
| CA M2 (EVAL-14; 3 eligible) | colitis 8/24, 33.3% (18.0–53.3) | hepatomegaly 10/10, 100% (72.2–100) |

Many Matrix 2 conditions had very few positives:
- Canine Thorax: 12 of 20 had 0–4 positives.
- Feline Thorax: 16 of 21 had 0–4 positives.
- Canine Abdomen: 4 of 10 had 0–4 positives.

Condition-level sensitivity was therefore undefined or highly uncertain for many conditions. For example, the four Canine Abdomen Matrix 2 conditions with 2–4 positives showed point sensitivities of 50–100% with wide intervals.

Macro averages rest on different condition subsets. For example, Canine Thorax Matrix 2 macro sensitivity includes 16 of 20 conditions, and Feline Thorax Matrix 2 macro sensitivity includes 11 of 21. Macro averages are therefore not directly comparable across matrices (`07_…` §2).

`[FIGURE 1 PLACEHOLDER: per-condition sensitivity vs specificity with Wilson intervals, one panel per dataset and matrix (six panels), marking conditions with < 10 positives. Data: 07_statistical_results.json → evaluations.*.conditions (EVAL-05/06, 11/12, 13/14).]`

### 3.4 Model comparison on Canine Thorax (only)

**Table 6. Week 5 GPT-4.1 mini vs Week 7 gemini-3.8-flash on the same 100 Canine Thorax reports.** Source: `07_Statistical_Analysis_Results.md` §5.

| | Matrix 1 | Matrix 2 |
|---|---|---|
| Prediction agreement (not accuracy) | 1,940/2,000 (97.00%) | 1,944/2,000 (97.20%) |
| Cohen's κ between models (95% CI) | 0.773 (0.716–0.822) | 0.788 (0.735–0.839) |
| Δ Sensitivity, Gemini − OpenAI (pp) | −2.86 (−4.22 to −1.55) | −15.19 (−23.17 to −7.14) |
| Δ Specificity (pp) | +0.84 (−0.13 to +1.96) | +0.87 (+0.38 to +1.41) |
| Δ Precision (pp) | −0.21 (−5.95 to +5.87) | +5.83 (+0.85 to +10.52) |
| Δ F1 (pp) | −4.44 (−6.53 to −2.38) | −5.89 (−11.79 to −0.20) |
| Conditions testable by McNemar / significant after Holm | 13 / 0 | 14 / 0 |

Against both references, Gemini had lower sensitivity and F1. Against Matrix 2 it had higher specificity and precision. Most discordance between the models occurred in `bronchitis`, `diseased_lungs` and `cardiomegaly`. No single-condition McNemar test remained significant after Holm adjustment; the smallest unadjusted p values were about 0.013. This comparison is limited to one dataset and one run per model, and it differs in execution date and client configuration as well as model family.

### 3.5 Observed run-to-run differences

Canine Thorax was classified in separate batches for each matrix over identical report text (Table 7).

**Table 7. Differences between separate executions at temperature 0 (Canine Thorax).** Source: `07_Statistical_Analysis_Results.md` §6.

| Comparison | Differing pairs | Reports affected | κ |
|---|---|---|---|
| Week 4 GPT-4.1 mini, M1 batch vs M2 batch | 8/2,000 | 6 | 0.974 |
| Week 5 GPT-4.1 mini, M1 batch vs M2 batch | 11/2,000 | 8 | 0.963 |
| Week 7 Gemini, M1 batch vs M2 batch | 13/2,000 | 11 | 0.943 |
| Week 4 vs Week 5 application, M1 inputs | 13/2,000 | 10 | 0.957 |
| Week 4 vs Week 5 application, M2 inputs | 8/2,000 | 6 | 0.973 |

These are incidental, not designed, repeats. Feline Thorax and Canine Abdomen were each run once.

### 3.6 Exploratory common-batch rescoring (Canine Thorax)

To approximate the paired Feline Thorax/Canine Abdomen design, the compatibility of the Week 5 batches was checked. The Matrix 1 and Matrix 2 workbooks contain identical CaseIDs and order, identical text in all three report fields, and identical condition keys. Both batches contain 100 valid 20-key records.

Each Week 5 batch was then scored offline against the other reference:
- RUN-03 against Matrix 2: sensitivity 79.11%, specificity 98.05%, F1 78.37%.
- RUN-04 against Matrix 1: sensitivity 11.82%, specificity 96.00%, F1 20.48%.

Both are close to the original evaluations. These are additional, **exploratory** analyses. The original evaluations EVAL-05 and EVAL-06, which used separate batches per matrix, remain the recorded Canine Thorax Week 5 results. The rescoring does not replace them, and no batch has been designated primary (decision D-A remains open).

---

## 4. Discussion

### 4.1 Main findings

The dominant pattern, consistent across all three datasets, is that measured performance depended on the reference workflow far more than on any other factor examined. With identical predictions, sensitivity rose when scoring switched from the original Vetology labels to the peer-reviewed Gold Standard: by 44.1 percentage points in Feline Thorax and 53.3 in Canine Abdomen, and by 67.1 in the exploratory Canine Thorax rescoring. The two workflows labelled the same reports very differently. Matrix 1 marked 3.5–6.6 times as many pairs positive as Matrix 2. Positive agreement between them was 12–24%, and most disagreements were Matrix 1 positives that Matrix 2 scored negative. Cohen's κ was low (0.03–0.13), but κ is sensitive to the large prevalence difference and is not read here as a verdict on either reference.

The reason for this discrepancy is not established. It could reflect:
- different labelling conventions or thresholds;
- information unavailable in the report text;
- different scope;
- errors in either set.

Because the Matrix 2 adjudication process is incompletely documented, neither set can be treated as clinical truth. The practical implication is that a single headline accuracy for an LLM report classifier is uninterpretable without a clear account of how the reference labels were produced.

### 4.2 Sensitivity, specificity and the limits of accuracy

Specificity was high everywhere (≥ 96%), but this does not by itself indicate useful performance. Most condition labels are negative, especially in Matrix 2 (5.6–8.1% positive), so a model that rarely predicts positives achieves high specificity and accuracy while missing many positive labels. Against Matrix 1, low sensitivity (5–12%) meant that most reference positives were missed. Against Matrix 2, sensitivity was moderate (50–80%) and precision varied (76.51–92.98%).

The Feline Thorax prompt's conservative uncertainty policy, which treats possible or suspected findings as Negative, coincided with the lowest sensitivity under both references and the lowest Matrix 1 precision. However, prompt policy is confounded with dataset, so this association cannot be attributed causally. Reporting sensitivity, precision and F1 alongside accuracy, with support counts, is essential.

### 4.3 Comparison with veterinary NLP literature

The closest methodological analogue is Wulcan et al. (2025). They classified six clinical signs in 250 feline EHRs with GPT-4o against the majority of five blinded human respondents, using a tuning set separate from the test set and five repeated runs at each of three temperatures. GPT-4o reached a median sensitivity of 96.9% and specificity of 97.6%, with high inter-run agreement (κ 0.98).

Our task differs in several ways:
- radiology report text rather than general EHR text;
- 10–21 conditions per report across three datasets;
- two reference workflows rather than one;
- no held-out tuning set and only incidental repeats.

The lower sensitivities observed here should therefore not be read as a direct contrast with that study. Other veterinary work addressed:
- body-condition-score extraction with high recall but lower precision than a rule-based method (Fins et al., 2024);
- diagnosis prediction with a fine-tuned model (Jiang et al., 2024), which is not comparable to general-purpose prompting;
- prescription attribute extraction (Hur et al., 2024).

A veterinary EHR benchmark now exists (Farrell et al., 2025), but it does not cover radiology reports. The scoping review by Chang and Chu (2026) emphasises ground-truth definition and annotation protocols, which aligns with our observation about reference dependence.

### 4.4 Comparison with human radiology-report research

In human radiology, NLP extraction from reports shows high pooled sensitivity and specificity (91% and 96%), with anatomical site as the main source of heterogeneity (Yang et al., 2026). These pooled figures come from diverse systems, tasks and references and are not a benchmark for this pilot. LLM report classification for a single condition (pulmonary embolism) has been shown to be sensitive to prompt design and data perturbations (Sorin et al., 2025). This is consistent with our observation that outputs were not identical across executions at temperature 0. The observed run-to-run differences (0.4–0.65% of pairs) are specific to these runs and are not evidence of a general property of LLMs.

### 4.5 Practical implications

The results do not support clinical or autonomous use. They suggest three priorities for any future application of LLM-based labelling of veterinary reports:
1. Define and document the reference standard, including reviewers, procedure and agreement.
2. Separate prompt-development cases from evaluation cases.
3. Report condition-level sensitivity with support counts, rather than aggregate accuracy.

The single-model comparison on Canine Thorax showed high agreement between models (κ ≈ 0.78), with different sensitivity–specificity balances. Model choice would therefore depend on the relative cost of missed versus false findings, which requires clinical input.

`[FIGURE 2 PLACEHOLDER: experimental workflow — report text (three fields) → master prompt → LLM → strict JSON validation → predictions → evaluation against Matrix 1 and Matrix 2 → confusion matrices. Source: 03_Consolidated_Knowledge_Base/04_Technical_Architecture_and_Reproducibility.md §2.]`

---

## 5. Limitations

- **Sample.** 100 non-randomly selected reports per dataset from one organisation. Results cannot be generalised, and the intervals do not imply representativeness.
- **Input.** The models received report text only. The reference labels may reflect information that is not in the text.
- **Reference standards.** The Matrix 1 label origin and the Matrix 2 peer-review procedure (reviewers, qualifications, blinding, disagreement resolution) are incompletely documented. Matrix 2 is not independent expert adjudication, and the Feline Thorax and Canine Abdomen Gold Standard files are labelled "draft".
- **Evaluation independence.** Prompt-development cases overlapped with evaluation cases. Possible reference-label exposure during the Canine Abdomen hedged-language analysis is unresolved, so the evaluation is not held out.
- **Confounding.** Datasets differ in condition sets, prevalence, prompt versions and uncertainty policies, and batch design. No species, anatomical or prompt effect can be inferred.
- **Model coverage.** The model comparison covers Canine Thorax only, with one run per model, different dates and client configurations, and unknown model snapshots.
- **Repeatability.** Repeatability evidence is incidental and limited to Canine Thorax.
- **Sparse labels.** Condition-level estimates are imprecise or undefined for many sparse conditions, and multiplicity limits per-condition testing.
- **Prompt provenance.** The source-to-rule provenance of prompt content is not documented.

---

## 6. Conclusion and future work

In this pilot, general-purpose LLMs classified veterinary radiology report text with high specificity across three datasets. Sensitivity depended strongly on which reference labels were used, and the two available reference sets disagreed substantially. The principal take-away is methodological: reference-label provenance must be established before LLM-based report labelling can be interpreted, let alone used clinically.

Future work should:
- document and, where possible, independently adjudicate the reference labels and measure their reliability;
- evaluate on held-out cases;
- harmonise or experimentally vary uncertainty rules;
- repeat runs and add further models across all three datasets;
- extend to larger, representative samples.

---

## References

Chang Y, Chu CP. 2026. Applying artificial intelligence to automate clinical data extraction from veterinary electronic health records: A practical guidance and comparative scoping review. *Veterinary Pathology*. Advance online publication 16 July 2026. https://doi.org/10.1177/03009858261461761 `[SOURCE VERIFICATION REQUIRED: volume/pages not yet assigned; full text not reviewed]`

Farrell S, Radford A, Al Moubayed N, Noble PJ. 2025. PetEVAL: A veterinary free text electronic health records benchmark. In: *Proceedings of the 24th Workshop on Biomedical Language Processing*, pp. 341–353. https://doi.org/10.18653/v1/2025.bionlp-1.29

Fins IS, Davies H, Farrell S, Torres JR, Pinchbeck G, Radford AD, Noble P. 2024. Evaluating ChatGPT text mining of clinical records for companion animal obesity monitoring. *Veterinary Record* 194(3): e3669. https://doi.org/10.1002/vetr.3669

Hur B, Wang LL, Hardefeldt L, Yetisgen M. 2024. Is That the Right Dose? Investigating Generative Language Model Performance on Veterinary Prescription Text Analysis. In: *Proceedings of the 23rd Workshop on Biomedical Natural Language Processing*, pp. 390–397. https://doi.org/10.18653/v1/2024.bionlp-1.30

Jiang Y, Irvin JA, Ng AY, Zou J. 2024. VetLLM: Large Language Model for Predicting Diagnosis from Veterinary Notes. In: *Biocomputing 2024: Proceedings of the Pacific Symposium*, pp. 120–133. https://doi.org/10.1142/9789811286421_0010

Khosravi B, Dapamede T, Li F, Chisango Z, Bikmal A, Garg S, Owosela B, Khosravi A, Chavoshi M, Trivedi HM, Wyles CC, Purkayastha S, Erickson BJ, Gichoya JW. 2026. Role of Model Size and Prompting Strategies in Extracting Labels from Free-Text Radiology Reports with Open-Source Large Language Models. *Journal of Imaging Informatics in Medicine* 39(1): 995–1004. https://doi.org/10.1007/s10278-025-01505-7 `[SOURCE VERIFICATION REQUIRED: metadata only; content not reviewed]`

Kottlors J, Iuga AI, Bluethgen C, Bressem K, Kather JN, et al. 2026. Guidelines for Reporting Studies on Large Language Models in Radiology: An International Delphi Expert Survey. *Radiology* 318(2): e250913. https://doi.org/10.1148/radiol.250913

Reichenpfader D, Müller H, Denecke K. 2024. A scoping review of large language model based approaches for information extraction from radiology reports. *npj Digital Medicine* 7: 222. https://doi.org/10.1038/s41746-024-01219-0 `[SOURCE VERIFICATION REQUIRED: metadata only; content not reviewed]`

Sorin V, Collins JD, Bratt AK, Kusmirek JE, Mugu VK, Kline TL, Butler CL, Wood NG, Cook CJ, Korfiatis P. 2025. Evaluating prompt and data perturbation sensitivity in large language models for radiology reports classification. *JAMIA Open* 8(4): ooaf073. https://doi.org/10.1093/jamiaopen/ooaf073

Wulcan JM, Jacques KL, Lee MA, Kovacs SL, Dausend N, Prince LE, Wulcan J, Marsilio S, Keller SM. 2025. Classification performance and reproducibility of GPT-4 omni for information extraction from veterinary electronic health records. *Frontiers in Veterinary Science* 11: 1490030. https://doi.org/10.3389/fvets.2024.1490030

Yang Q, Jiang J, Dong X, Yang H, Wang Q, Yang Z, Yang D, Liu P. 2026. Performance of Natural Language Processing Model in Extracting Information from Free-Text Radiology Reports: A Systematic Review and Meta-Analysis. *Journal of Imaging Informatics in Medicine* 39(4): 3639–3653. https://doi.org/10.1007/s10278-025-01728-8

*Kottlors et al. (2026) is used as reporting guidance (FLAIR); compliance is not claimed (see `11_FLAIR_Checklist_Crosswalk.md`). The Vetology Free Training Program webpage is a programme instruction source and is not cited as scientific evidence.*

---

## Appendix A. Prompts, repository and outputs

**A.1 Final prompt versions.** Full prompt texts are version-controlled and should be reproduced in the final submission if permitted `[AUTHOR CONFIRMATION REQUIRED: whether full prompts may be published]`.

| Dataset | Prompt | Path | File SHA-256 |
|---|---|---|---|
| CT | Canine Thorax Master Prompt V1.3 | `src/week_07/prompts/canine_thorax_master_prompt_v1_3.txt` | `31a7dab6e535e6f0af6a54106cf449ecadfe3644c7b3c805710309f0e85ab7b1` |
| FT | Feline Thorax Master Prompt V1.2 | `src/week_07/prompts/feline_thorax_master_prompt_v1_2.txt` | `9bbd36c4a1d9ac15cb24c39b3e9d0ad5af9106a9bddb3adf3401098e1c418f25` |
| CA | Canine Abdomen Master Prompt V1.4 | `src/week_07/prompts/canine_abdomen_master_prompt_v1_4.txt` | `9336be3fa463be14bdfd71d93e2709b4bad70c626d0533d8e4f887809b2a254c` |

User message template: "Classify the following {canine thorax | feline thorax | canine abdomen} radiology report according to the system instructions.", followed by the three labelled report sections.

**A.2 Repository and outputs.**
- Repository: https://github.com/suyash-gore/vetology-radiology-evaluation `[AUTHOR CONFIRMATION REQUIRED: public visibility; final branch or release tag]`.
- Code for Weeks 5–7 is on feature branches and has not been merged to `main`.
- Output files (confidential; not in the repository): per-run `predictions.jsonl`, `run_manifest.json` (the Week 7 manifests are committed), and the Matrix 1/Matrix 2 evaluation workbooks listed in `04_Evidence_and_Artifacts/01_Evidence_Inventory.csv` (rows EV-B10–EV-B42).

**A.3 Domain reference texts consulted for the Canine Thorax V1.3 prompt** (titles as recorded by the developer; editions `[AUTHOR CONFIRMATION REQUIRED]`). These were domain references used to write the prompt, not sources of evidence for the results:
1. Thrall's Textbook of Veterinary Diagnostic Radiology, 8th ed.
2. BSAVA Manual of Canine and Feline Radiography and Radiology.
3. Practical Veterinary Diagnostic Imaging.
4. BSAVA Manual of Canine and Feline Thoracic Imaging.
5. BSAVA Manual of Canine and Feline Abdominal Imaging.
6. Small Animal Diagnostic Ultrasound.
7. Lavin's Radiography for Veterinary Technicians.
8. Veterinary Radiology: Basic Principles and Radiographic Positioning.
9. Kealy, McAllister and Graham, Diagnostic Radiology and Ultrasonography of the Dog and Cat.
10. Thrall and Robertson, Atlas of Normal Radiographic Anatomy and Anatomic Variants in the Dog and Cat.

## Appendix B. Condition keys

- **CT (20):** perihilar_infiltrate, pneumonia, bronchitis, interstitial, diseased_lungs, hypo_plastic_trachea, cardiomegaly, pulmonary_nodules, pleural_effusion, rtm, focal_caudodorsal_lung, focal_perihilar, pulmonary_hypoinflation, right_sided_cardiomegaly, pericardial_effusion, bronchiectasis, pulmonary_vessel_enlargement, left_sided_cardiomegaly, thoracic_lymphadenopathy, esophagitis.
- **FT (21):** pulmonary_nodules, esophagitis, pneumonia, bronchitis, interstitial, diseased_lungs, hypo_plastic_trachea, cardiomegaly, pleural_effusion, perihilar_infiltrate, rtm, focal_caudodorsal_lung, right_sided_cardiomegaly, focal_perihilar, left_sided_cardiomegaly, bronchiectasis, pulmonary_vessel_enlargement, thoracic_lymphadenopathy, pulmonary_hypoinflation, pericardial_effusion, Fe_Alveolar.
- **CA (10):** gastritis, ascites, colitis, liver_mass, pancreatitis, microhepatia, small_intestinal_obstruction, splenic_mass, splenomegaly, hepatomegaly.

Full per-condition tables are in `Vetology_Research_Knowledge_Base/04_Evidence_and_Artifacts/06_Per_Condition_Results.md` (workbook values) and `07_Statistical_Analysis_Results.md` §8 (with Wilson intervals).

## Appendix C. Evaluation configuration details

| Setting | Week 4 (CT) | Week 5 (CT) | Week 7 Gemini (CT) | Week 7 (FT, CA) |
|---|---|---|---|---|
| Temperature | 0 | 0 | 0.0 | 0.0 |
| Timeout | 90 s | 90 s | 90 s | 90 s |
| Transport retries | LangChain `max_retries=2` | 2 | 1 attempt | 0 |
| Application attempts | 2 | 2 | 2, with bounded backoff for transient errors | 2, with bounded backoff |
| Response format | none | none | JSON MIME, no schema | none |
| Run manifest | no | no | yes | yes |
| Runtime (manifests) | — | — | Python 3.14.6; langchain-google-genai 4.4.2; google-genai 2.31.0 | Python 3.14.6; langchain-openai 1.7.2; openai 3.49.0 |

Source: `04_Evidence_and_Artifacts/04_Prompts_and_Configurations_Index.md` §4.
