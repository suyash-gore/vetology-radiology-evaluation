# Structured Multi-Condition Classification of Veterinary Radiology Report Text with General-Purpose Large Language Models: A Retrospective Comparison Across Three Datasets and Two Reference-Label Workflows

**Manuscript draft v0.5 — consolidated academic submission draft.** Prepared 2026-11-29 on branch `week-08/research-paper-development`. Drafts v0.1–v0.4 are retained unchanged.

*Revision note (v0.4 → v0.5):*
- Incorporated author confirmations on Matrix 1 provenance, Matrix 2 review procedure, blinding, written guidance, final status of the Feline Thorax and Canine Abdomen reference files, dataset selection, keyword-analysis inputs, ethics approval, data-use permission and authorship.
- Clarified that the Canine Abdomen keyword analysis used report-text fields and CaseID, not reference-label columns.
- Reframed the primary conclusion and removed author-confirmation drafting placeholders where the supplied facts resolve them.

No statistical results or confusion counts changed.

**Author:** Suyash Kishor Gore

**Affiliation:** The author's institutional affiliation was not supplied in the project record.
**Context:** Vetology Free Training Program.

**Scope statement.** This study evaluates **classification of written radiology reports**. The models received report text only. No radiographic images were analysed, and the work does not evaluate image interpretation, clinical diagnosis or clinical readiness.

---

## Abstract

**Background.** Large language models (LLMs) are increasingly used to structure clinical text, but their behaviour on veterinary radiology reports is poorly characterised.

**Objective.** To evaluate general-purpose LLMs for binary multi-condition classification of veterinary radiology report text, and how performance depends on the reference labels.

**Methods.** In this retrospective pilot study, GPT-4.1 mini classified report text from three datasets:
- canine thorax (20 conditions);
- feline thorax (21 conditions);
- canine abdomen (10 conditions).

Each dataset contained 100 reports, and no images were used. Predictions were scored against two reference sets:
- the original Vetology labels (Matrix 1);
- a three-reviewer, independent manual, majority-vote reference set (Matrix 2; the project's "Gold Standard").

A Gemini model was compared on canine thorax only.

**Results.** Specificity was ≥96.0% in all ten evaluations.

With shared predictions, sensitivity was:
- feline thorax: 5.43% (Matrix 1) vs 49.57% (Matrix 2);
- canine abdomen: 12.14% vs 65.43%.

Canine thorax: 12.01% vs 79.75% with separate batches, and 12.01% vs 79.11% in exploratory common-batch rescoring.

The reference sets disagreed substantially (positive agreement 12–24%; κ 0.03–0.13). On canine thorax, two models agreed on 97.00–97.20% of predictions, and repeated temperature-0 executions differed on 8–13 of 2,000 pairs.

**Conclusion.** Measured performance was strongly dependent on the reference-label workflow. No clinical validity is implied.

*(Abstract ≈ 198 words.)*

**Keywords:** large language models; veterinary radiology reports; text classification; reference standard; inter-reference agreement; reproducibility

---

## 1. Introduction

Free-text clinical records hold much of the information generated in veterinary practice, but their unstructured form limits secondary use for research, surveillance and quality assurance (Chang and Chu, 2026). Radiology reports are a particularly information-dense part of these records. They state findings, interpretations and recommendations in specialist language and often hedge, for example with "possible" or "cannot be excluded".

Converting such reports into structured condition labels could support case retrieval, audit and dataset construction. It requires methods that cope with multiple co-occurring conditions, negation and diagnostic uncertainty.

General-purpose LLMs can be instructed to perform this conversion without task-specific training. Their measured performance, however, depends on what they are compared with. A classifier evaluated against one set of reference labels may appear poor, and against another set apparently competent, without any change in its predictions.

This study uses a pilot dataset drawn from three veterinary radiology domains. It examines both the classification behaviour of general-purpose LLMs on report text and the extent to which reported performance depends on the reference-label workflow.

---

## 2. Background and related literature

The literature summarised here was identified through a **targeted, preliminary review** of a seed set of publications, with metadata verified against DOI records. It is **not a systematic review**. The 23 veterinary studies included in the scoping review by Chang and Chu (2026) have not yet been screened individually, so absence of evidence below is not evidence of absence.

### 2.1 Veterinary clinical-text processing

A recent PRISMA-ScR scoping review screened 5,796 records and included 23 veterinary and 31 human studies of information extraction from electronic health records (Chang and Chu, 2026). It reported that veterinary studies more often trained supervised models on larger datasets, whereas human studies increasingly used prompt-based LLMs.

Prompt-based LLM applications to veterinary narratives include:
- **Body-condition-score extraction.** ChatGPT reached recall of 100% and precision of 89.3%, compared with 72.6% and 100% for a regular-expression method (Fins et al., 2024).
- **Diagnosis prediction from veterinary notes.** A fine-tuned Alpaca-7B model (VetLLM) reached F1 0.747 and 0.637 on two test sets, compared with 0.538 and 0.389 for the zero-shot base model (Jiang et al., 2024). Fine-tuning distinguishes this work from the general-purpose prompting studied here.
- **Prescription-attribute extraction.** GPT-3.5, GPT-4 and LLaMA2-70B were compared with a BERT-based ensemble (Hur et al., 2024).

The study methodologically closest to the present one is Wulcan et al. (2025):
- GPT-4o classified six clinical signs of feline chronic enteropathy in 250 electronic health records.
- The reference was the majority opinion of five blinded human respondents.
- Prompts were refined on a separate tuning set.
- Each analysis was repeated five times at each of three temperatures.
- GPT-4o achieved a median sensitivity of 96.9% and specificity of 97.6%, with inter-run Cohen's κ of 0.98.

A public benchmark of 17,600 annotated veterinary free-text records now also exists (PetEVAL; Farrell et al., 2025). It covers syndromic classification and named-entity recognition, but not radiology reports.

### 2.2 Human radiology-report processing

In human radiology, NLP extraction of information from free-text reports has been studied extensively. A systematic review and meta-analysis of 28 studies (51,187 reports) reported:
- pooled sensitivity of 91% and specificity of 96%;
- anatomical site as the main source of heterogeneity (Yang et al., 2026).

For LLMs specifically:
- **Prompt and data-perturbation sensitivity.** Classification of 11,999 CT pulmonary angiography reports for pulmonary embolism with three Gemini models was sensitive to prompt design and data perturbations (Sorin et al., 2025).
- **Scoping review.** LLM-based information extraction from radiology reports has been reviewed (Reichenpfader et al., 2024).
- **Model size and prompting.** The effects of model size and prompting strategy on label extraction have been studied (Khosravi et al., 2026).

Reichenpfader et al. and Khosravi et al. were verified at metadata level only and are cited here solely for their stated topic.

### 2.3 Image-based veterinary AI

A separate body of work applies deep learning to **radiographic images** of dogs and cats. That work concerns image interpretation, which is a different task and modality from the report-text classification studied here. It is not used as comparative evidence in this paper.

### 2.4 Reporting guidance

A Delphi-based reporting guideline for LLM studies in radiology (FLAIR) has been published (Kottlors et al., 2026). It was used here as voluntary guidance. The item-level check is incomplete because the checklist appendix could not be retrieved, and compliance is not claimed.

### 2.5 Research gap (provisional)

Existing research has examined:
- LLM-based information extraction and classification from veterinary clinical narratives;
- extensive work on human radiology-report extraction.

The specific application of general-purpose LLMs to multi-condition binary classification of veterinary radiology report text has not been established by the literature reviewed so far. This applies in particular to evaluation across canine and feline thoracic and canine abdominal datasets, and under distinct reference-label workflows. That application warrants investigation.

**This is a provisional statement from a non-systematic review, not a claim of novelty.**

---

## 3. Research objectives and questions

The objective was to describe the behaviour of general-purpose LLMs performing structured binary classification of veterinary radiology report text, and the dependence of measured performance on the reference-label workflow.

**Research questions.**
- **RQ1.** How does classification performance vary across the Canine Thorax, Feline Thorax and Canine Abdomen datasets? (Descriptive; not a controlled species or region comparison.)
- **RQ2.** How do results differ between the original Vetology labels (Matrix 1) and the three-reviewer majority-vote reference set (Matrix 2), and how far do the two reference sets agree?
- **RQ3.** Which conditions show consistently strong or weak classification performance?
- **RQ4.** On Canine Thorax only, how do an OpenAI and a Gemini model differ in performance and in prediction agreement?
- **RQ5.** On Canine Thorax only, how consistent are separate executions under nominally identical settings?

The role of prompt uncertainty rules is treated as an **exploratory discussion topic**, not a research question. No experiment varied the prompt within a dataset.

---

## 4. Materials and methods

### 4.1 Study design

This was a retrospective, multi-dataset pilot evaluation of LLM-based text classification, conducted in November 2026 within the Vetology Free Training Program. The three datasets were given equal analytical standing. They are **not** a controlled comparison of species or anatomical regions, because the condition sets, label prevalence, prompts and batch designs all differ (Section 4.6).

### 4.2 Datasets

Each dataset comprised the **first 100 populated records** selected from the raw dataset supplied for the programme. The first 100 were selected for operational simplicity and to facilitate coordination, record matching and comparison while constructing the Matrix 2 reference set. This was a convenience-based selection, not random sampling; the resulting samples should not be considered representative of the source population. The source period and clinic mix were not available for this analysis.

For every record, the model input consisted of the original radiologist's report split into three fields: *Findings*, *Conclusions* and *Recommendations*. An empty field was sent as `[Not provided]`.

The following were excluded from the model input by code:
- case identifiers;
- reference labels;
- AI-generated report fields present in the workbooks.

Within each dataset, the Matrix 1 and Matrix 2 workbooks contain identical case identifiers, case order and report text. This was documented for Feline Thorax and Canine Abdomen during implementation and verified for Canine Thorax in this work.

**Table 1. Dataset characteristics.** Positive-label prevalence is the share of report–condition pairs labelled Positive.

| | Canine Thorax (CT) | Feline Thorax (FT) | Canine Abdomen (CA) |
|---|---|---|---|
| Reports | 100 | 100 | 100 |
| Binary conditions | 20 | 21 | 10 |
| Report–condition pairs | 2,000 | 2,100 | 1,000 |
| Matrix 1 Positive / Negative pairs | 1,049 / 951 | 534 / 1,566 | 280 / 720 |
| Matrix 1 positive prevalence | 52.45% | 25.43% | 28.00% |
| Matrix 2 Positive / Negative pairs | 158 / 1,842 | 117 / 1,983 | 81 / 919 |
| Matrix 2 positive prevalence | 7.90% | 5.57% | 8.10% |
| Matrix 2 conditions with 0 positives | 4 | 10 | 0 |
| Matrix 2 conditions with 1–4 positives | 8 | 6 | 4 |
| Active prompt | Canine Thorax Master Prompt V1.3 | Feline Thorax Master Prompt V1.2 | Canine Abdomen Master Prompt V1.4 |

The condition keys are listed in Appendix B:
- The 20 Canine Thorax names all recur in Feline Thorax, which adds `Fe_Alveolar`. A shared name does not imply an identical clinical definition, because the prompts define and threshold conditions differently.
- The Canine Abdomen conditions do not overlap with either thoracic set.

### 4.3 Classification task

For each report, the model returned one JSON object containing every configured condition key exactly once, each with the value `Positive` or `Negative`. There was no "uncertain" category.

Responses were validated strictly:
- exactly one JSON object;
- the exact key set, with no duplicate keys;
- only the two permitted values.

Invalid responses were retried and never repaired.

### 4.4 Reference-label generation and comparison

Two reference-label workflows were used. They are evaluated separately throughout.

**Matrix 1 — original Vetology labels.** These are the condition labels supplied in the encoded source workbooks and were created by Vetology's radiologist. In Feline Thorax, three columns recorded Normal/Abnormal; these were mapped to Negative/Positive, and no other column was transformed. Matrix 1 evaluation workbooks label the counts "GS Positive/Negative", but this is legacy terminology only; the reference is the original Vetology labels. Further details of the radiologist's labelling protocol and the encoding history were not available.

**Matrix 2 — three-reviewer majority-vote reference set (project name: "Gold Standard").** The term "Gold Standard" is retained only as the project's historical name for this label set. It does not denote clinical ground truth. For each dataset, the labels were produced as follows:
1. Three members of the research team (the first author, Suyash Kishor Gore; Zach Tungate; and Akshay Rathod) received the same original raw dataset.
2. Each reviewer independently examined the same selected source-data columns. AI-generated report fields were excluded from the annotation.
3. Each reviewer assigned a binary Positive or Negative label for every relevant condition in the first 100 records, and kept a separate annotation file.
4. The three files were consolidated, and majority voting was applied at each record–condition combination. A label supported by at least two of the three reviewers became the final Matrix 2 label.

Matrix 2 is therefore a **three-reviewer, independently generated, majority-vote research-team reference**. The reviewers had access to the original Vetology label columns, were blinded to model outputs, and followed written annotation guidance. The Feline Thorax and Canine Abdomen files whose filenames end in "draft" were confirmed by the project owner as the final versions used for evaluation. The reviewers' professional qualifications were not supplied for this manuscript. Matrix 2 is **not** veterinary-radiologist adjudication, a formal expert consensus or clinically validated ground truth. The relationship between an earlier record of 21 differences between a Canine Thorax manual-scoring draft and the approved reference remains undocumented.

The three individual annotation files were later deleted, and only the consolidated files remain. **Inter-reviewer agreement (for example pairwise κ or Fleiss' κ) cannot therefore be calculated retrospectively**, and it was not reconstructed from the majority-vote files. One reviewer also developed the prompts (Section 4.5).

**Comparison of the two reference sets.** On the same report–condition pairs, the following were computed:
- the 2×2 counts: both Positive (n₁₁), both Negative (n₀₀) and each direction of disagreement (n₁₀ = Matrix 1 Positive/Matrix 2 Negative; n₀₁ = the reverse);
- raw agreement (n₁₁ + n₀₀)/N;
- positive agreement PA = 2n₁₁/(2n₁₁ + n₁₀ + n₀₁);
- negative agreement NA = 2n₀₀/(2n₀₀ + n₁₀ + n₀₁);
- Cohen's κ.

Because κ depends on prevalence, which differs markedly between the two sets, it is interpreted together with PA, NA and the directional counts. These statistics describe **disagreement between two labelling workflows**. They do not show which, if either, is clinically correct.

### 4.5 Prompt development and model configuration

**Prompt development.** Prompts were written as one master prompt per dataset. Each master prompt specifies the model's role, the permitted evidence (the three report fields only), shared rules, condition-specific definitions and the output contract. They were developed in stages:
- **Week 3:** a V1.0 baseline, then V1.1.
- **Canine Thorax V1.3** (3 November 2026), after clarifications relayed by the programme's Tech Advisor:
  - `rtm` denotes redundant tracheal membrane;
  - `diseased_lungs` is an independent condition;
  - explicitly possible or suspected conditions are classified as Positive.

The developer's working interpretation of `Fe_Alveolar` as *Feline Alveolar Pattern* was not advisor-confirmed.

For Canine Thorax V1.3, the developer:
- consulted ten veterinary diagnostic-imaging texts (Appendix A.3);
- queried them with NotebookLM;
- consolidated the material with ChatGPT;
- received guidance from Dr. Parin Candy.

The editions consulted, the mapping from sources to individual rules, the intermediate notes and the scope of the expert input are not documented. There is no record that this process informed the Feline Thorax or Canine Abdomen prompts. The prompts instruct the model not to rely on external medical knowledge, so domain knowledge shaped the authors' wording of the rules; it was not supplied to the model at inference.

The Week 7 prompts were registered byte for byte with SHA-256 digests:
- **Feline Thorax V1.2** corrected only the quotation marks in the JSON example of V1.1.
- **Canine Abdomen V1.3** made contradictory uncertainty rules consistent.
- **Canine Abdomen V1.4** narrowed one differential-diagnosis clause.

The three active prompts therefore encode different uncertainty policies:
- **Canine Thorax:** possible or suspected → Positive.
- **Feline Thorax:** possible or suspected → Negative unless confirmed.
- **Canine Abdomen:** Positive only when named in the primary impression and supported by findings.

**Overlap between prompt development and evaluation.** Selected cases from the evaluation datasets were reviewed during prompt development:
- Canine and Feline Thorax: cases 3, 4, 5, 7 and 8;
- Canine Abdomen: cases 13–17.

The project owner confirms that this manual review used report text and model predictions, and did not involve inspecting the Positive/Negative reference labels. The project owner clarified that the Canine Abdomen keyword analysis used only CaseID and the original radiologist's Findings, Conclusions and Recommendations fields. Reference-label columns were not used in that analysis. Nevertheless, selected evaluation cases were reviewed during prompt development, so the evaluation sets are **not held out**, and adaptive refinement on evaluation cases may have influenced the results.

**Models and settings.** Table 2 summarises the runs. All runs used:
- temperature 0;
- the same input boundary, validator and metric engine;
- a 90-second timeout and up to two application-level attempts per case.

Provider-specific settings were:
- **OpenAI** runs used `gpt-4.1-mini` through LangChain `ChatOpenAI`.
- The **Gemini** run used `gemini-3.8-flash` through `ChatGoogleGenerativeAI`, with JSON MIME output and no schema.

Transport-retry settings differed between application versions (Appendix C). Model aliases were recorded, but **exact provider snapshot identifiers were not**. The provider snapshot identifiers could not be recovered for this manuscript.

Failed attempts never contributed predictions:
- an aborted Week 5 attempt failed for all cases with an authentication error (expired key) before the successful batch;
- one Gemini case failed three times (HTTP 503, 503, 504) before succeeding.

**Table 2. Evaluation runs.** Dates are 2026, UTC.

| Run(s) | Dataset | Model (alias) | Prompt | Date | Batch design | Evaluations |
|---|---|---|---|---|---|---|
| RUN-02 / RUN-01 | CT | gpt-4.1-mini (Week 4 application) | V1.3 | 7 Nov / 3 Nov | Separate batch per matrix | EVAL-01 (M1) / EVAL-02 (M2) |
| RUN-03 / RUN-04 | CT | gpt-4.1-mini (Week 5 rebuild) | V1.3 | 12 Nov | Separate batch per matrix | EVAL-05 (M1) / EVAL-06 (M2) |
| RUN-05 / RUN-06 | CT | gemini-3.8-flash | V1.3 | 20 Nov | Separate batch per matrix | EVAL-07 (M1) / EVAL-08 (M2) |
| RUN-07 | FT | gpt-4.1-mini | V1.2 | 21 Nov | One batch, scored against both | EVAL-11 (M1), EVAL-12 (M2) |
| RUN-08 | CA | gpt-4.1-mini | V1.4 | 21 Nov | One batch, scored against both | EVAL-13 (M1), EVAL-14 (M2) |

### 4.6 Experimental design

The ten reference-based evaluations (Table 2) comprise:
- three Canine Thorax experiments (Week 4 and Week 5 GPT-4.1 mini, Week 7 Gemini), each scored against both matrices;
- one Feline Thorax experiment, scored against both matrices;
- one Canine Abdomen experiment, scored against both matrices.

The designs differ between datasets:
- **Feline Thorax and Canine Abdomen** used **one** prediction batch scored against both references. This is a paired design that isolates the effect of the reference.
- **Canine Thorax** used a **separate** batch per reference in each week.

To approximate the paired design for Canine Thorax, each Week 5 batch was additionally scored offline against the other reference. This **exploratory common-batch rescoring** does not replace the original evaluations (EVAL-05/06), and no batch has been designated primary (decision D-A, open).

The model comparison (RQ4) uses the Week 5 GPT-4.1 mini and Week 7 Gemini runs on the same Canine Thorax reports and references. Run-to-run consistency (RQ5) uses pairs of separate Canine Thorax batches run over identical report text.

Predictions were saved as JSON Lines with run manifests (Week 7) that recorded the model, settings, prompt digests, input digest and package versions. Evaluation was offline and deterministic.

### 4.7 Performance metrics

For each condition, predictions were cross-tabulated with the reference (TP, FN, TN, FP). The metrics were:
- Accuracy = (TP + TN)/N;
- Sensitivity = TP/(TP + FN);
- Specificity = TN/(TN + FP);
- Precision = TP/(TP + FP);
- F1 = 2TP/(2TP + FP + FN).

A ratio with a zero denominator is undefined; it is never reported as 0% or 100%. For a condition with no reference positives:
- sensitivity is undefined;
- if the model predicted any positives, precision and F1 are 0;
- if it predicted none, precision and F1 are undefined.

Micro averages pool counts over conditions. Macro averages are unweighted means over the conditions where the metric is defined, and the number of contributing conditions is reported because it varies by metric and reference.

The original evaluation workbooks left F1 blank when precision or sensitivity was undefined. They remain the historical record, and micro F1 is identical under both conventions in all ten evaluations.

### 4.8 Statistical analysis

**What the plan fixed in advance.** The written analysis plan specified:
- the metrics;
- report-level resampling as the unit of uncertainty;
- Wilson intervals for condition-level proportions;
- paired comparisons only where predictions were genuinely shared.

It also proposed, as candidate settings to be confirmed: 10,000 resamples, a fixed seed, percentile or BCa intervals, and Holm adjustment.

**What was finalized during analysis.** The following were finalized during analysis and subsequently approved by the study owner, so they are **not all pre-specified**:
- the seed value (20261128);
- the choice of percentile intervals;
- the rule of recording undefined replicates and summarising over defined replicates;
- the 2,000-resample subset for agreement intervals;
- confirmation of B = 10,000 and Holm adjustment.

The methods were:
- **Micro and macro metrics.** A report-level cluster bootstrap resampled the 100 reports with replacement, keeping all their condition labels together.
- **Per-condition sensitivity, specificity and precision.** 95% Wilson score intervals.
- **Paired contrasts.** These were computed only where predictions were genuinely shared:
  - Matrix 2 minus Matrix 1 on one prediction set: Feline Thorax (RUN-07) and Canine Abdomen (RUN-08), plus, as an exploratory analysis only, the Canine Thorax RUN-03 batch rescored against Matrix 2.
  - Gemini minus GPT-4.1 mini, for which the two models' predictions on the same Canine Thorax cases are compared against the same references.

  Both use the same bootstrap resamples of reports. The original Canine Thorax Matrix 1 and Matrix 2 evaluations used separate batches and are not treated as a paired reference contrast.
- **Agreement.** Reference-set agreement as in Section 4.4. Cohen's κ between models and between repeated runs.
- **Exploratory model test.** Exact McNemar tests of discordant correctness per condition, Holm-adjusted within each matrix.

Pooled pairs were never treated as independent. All intervals are conditional on these non-randomly selected cases, labels, prompts and runs. They do not capture reference-label uncertainty, run-to-run variation or model drift. All tests are exploratory.

### 4.9 Reproducibility, data confidentiality and declarations

The code, prompts (with digests), run manifests and analysis script (`analysis/week08_statistics.py`, with unit tests) are version-controlled. The script reproduces every confusion count from the retained case-level files and stops on any discrepancy; repeated executions give identical output.

Source workbooks, predictions and report text are confidential and are not public. Ethics approval was obtained, and Vetology granted permission for the data to be used in this research. The approving committee, approval identifier and date were not supplied in the project record and should be added if required by the receiving institution or venue.

**Data and code availability.** The analysis code, prompts and run manifests are maintained in the project repository. The underlying source workbooks, report text, prediction-level outputs and evaluation workbooks are confidential and are not publicly available. Access to those materials is subject to Vetology's permission.

**Funding.** No separate funding information was supplied for this manuscript; confirm whether the programme or institution requires a formal funding statement.

**Conflicts of interest.** The author must confirm the applicable conflict-of-interest declaration before external publication; no declaration was available in the project record at the time this draft was prepared.

**Use of AI tools.** General-purpose AI tools, including ChatGPT and NotebookLM, were used during prompt-development work as described in Section 4.5. ChatGPT was also used to assist with manuscript drafting and editing. The author reviewed and takes responsibility for the final content. The LLMs evaluated in the experiments were used for the report-text classification task described in this paper.

---

## 5. Results

### 5.1 Overview

All ten evaluations used 100 successfully validated predictions per run (Table 3). Specificity was at least 96.00% throughout. Across the evaluations, sensitivity was low against Matrix 1 (5.43–12.20%) and higher against Matrix 2 (49.57–80.38%). Only the Feline Thorax and Canine Abdomen pairs (and the exploratory Canine Thorax rescoring, Section 5.7) share predictions between the two references.

**Table 3. Confusion counts and micro metrics for the ten evaluations (percentages; 95% report-level bootstrap intervals).**

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

The Week 4 Matrix 2 F1 is 0.78395, which displays as 78.40%. A truncated value of 78.39% appears in an earlier technical report.

### 5.2 Results by dataset (RQ1)

- **Canine Thorax.** Against Matrix 1, all three runs combined specificity of 96.00–97.16% with sensitivity of 9.15–12.20%, and accuracy was about 51–52%. Against Matrix 2, sensitivity was 64.56–80.38%, specificity 97.88–98.91% and accuracy 96.20–96.60%.
- **Feline Thorax.** Specificity was 97.64% (Matrix 1) and 99.60% (Matrix 2), and sensitivity was 5.43% and 49.57%. The model made positive predictions for 11 of the 21 conditions, 66 positive labels in total.
- **Canine Abdomen.** Specificity was 96.81% and 99.56%, and sensitivity was 12.14% and 65.43%. Precision against Matrix 2 was 92.98%.

These differences are descriptive. The datasets differ in condition sets, prevalence, prompts and batch design.

### 5.3 Effect of the reference-label workflow and reference-set agreement (RQ2)

**Table 4. Matrix 2 minus Matrix 1 on identical predictions (percentage points; paired report-level bootstrap 95% intervals).**

| Dataset (prediction set) | Sensitivity | Specificity | Precision | F1 | Accuracy |
|---|---|---|---|---|---|
| FT (RUN-07) | +44.14 (+33.45 to +54.38) | +1.96 (+1.15 to +2.86) | +43.94 (+26.15 to +63.16) | +53.72 (+44.41 to +61.59) | +22.62 (+18.95 to +26.38) |
| CA (RUN-08) | +53.29 (+43.82 to +62.76) | +2.76 (+1.43 to +4.27) | +33.33 (+17.74 to +49.02) | +56.63 (+48.57 to +64.80) | +23.70 (+20.20 to +27.30) |
| CT (RUN-03; exploratory rescoring) | +67.10 (+60.62 to +73.30) | +1.73 (+0.14 to +3.48) | −0.62 (−12.24 to +11.52) | +57.54 (+51.84 to +63.07) | +44.45 (+39.45 to +49.35) |

**Table 5. Agreement between the two reference-label sets on the same report–condition pairs.**

| Dataset | Pairs | M1 Positive / Negative prevalence | M2 Positive / Negative prevalence | Both Positive | Both Negative | M1 Pos / M2 Neg | M1 Neg / M2 Pos | Raw agreement | Positive agreement (95% CI) | Negative agreement (95% CI) | Cohen's κ (95% CI) |
|---|---:|---|---|---:|---:|---:|---:|---|---|---|---|
| CT | 2,000 | 52.45% / 47.55% | 7.90% / 92.10% | 119 | 912 | 930 | 39 | 51.55% | 19.72% (15.80–23.55) | 65.31% (59.98–70.24) | 0.069 (0.041 to 0.097) |
| FT | 2,100 | 25.43% / 74.57% | 5.57% / 94.43% | 39 | 1,488 | 495 | 78 | 72.71% | 11.98% (7.82–15.91) | 83.85% (81.09–86.29) | 0.031 (−0.008 to 0.067) |
| CA | 1,000 | 28.00% / 72.00% | 8.10% / 91.90% | 43 | 682 | 237 | 38 | 72.50% | 23.82% (17.98–29.47) | 83.22% (80.75–85.50) | 0.129 (0.077 to 0.183) |

Matrix 1 marked 3.5–6.6 times as many pairs positive as Matrix 2. In every dataset, most disagreements were labels positive in Matrix 1 but negative in Matrix 2:
- Canine Thorax: 930 of 969 disagreements;
- Feline Thorax: 495 of 573;
- Canine Abdomen: 237 of 275.

Positive agreement was low (12–24%). Negative agreement was higher (65–84%), but it partly reflects the large number of pairs labelled negative in both sets. Raw agreement was higher in Feline Thorax and Canine Abdomen than in Canine Thorax, mainly because Matrix 1 prevalence was lower there. Cohen's κ was low in all datasets, but given the prevalence imbalance it is reported only alongside these measures.

### 5.4 Condition-level performance (RQ3)

Full per-condition results are in Supplementary Table S1 and in the evidence files. Table 6 summarises conditions with at least 10 reference positives.

**Table 6. Selected condition-level sensitivity (conditions with ≥ 10 reference positives; 95% Wilson intervals).**

| Dataset / reference | Lowest sensitivity | Highest sensitivity |
|---|---|---|
| CT M1 (EVAL-05) | bronchiectasis 0/67 (0.0–5.4); focal_perihilar 0/58 (0.0–6.2); hypo_plastic_trachea 0/35 (0.0–9.9) | diseased_lungs 28/63, 44.4% (32.8–56.7); cardiomegaly 12/29, 41.4% (25.5–59.3) |
| CT M2 (EVAL-06; 5 eligible) | bronchitis 9/15, 60.0% (35.7–80.2); diseased_lungs 33/48, 68.8% (54.7–80.1) | interstitial 28/28, 100% (87.9–100); left_sided_cardiomegaly 13/15, 86.7% (62.1–96.3) |
| FT M1 (EVAL-11) | esophagitis 0/59 (0.0–6.1); pneumonia 0/51 (0.0–7.0); 11 of 21 conditions with TP = 0 | diseased_lungs 10/33, 30.3% (17.4–47.3); bronchitis 4/14, 28.6% (11.7–54.6) |
| FT M2 (EVAL-12; 3 eligible) | bronchitis 11/38, 28.9% (17.0–44.8); diseased_lungs 18/46, 39.1% (26.4–53.5) | cardiomegaly 9/10, 90.0% (59.6–98.2) |
| CA M1 (EVAL-13) | pancreatitis 2/75, 2.7% (0.7–9.2); splenomegaly 1/19, 5.3% (0.9–24.6) | hepatomegaly 11/47, 23.4% (13.6–37.2); gastritis 6/29, 20.7% (9.8–38.4) |
| CA M2 (EVAL-14; 3 eligible) | colitis 8/24, 33.3% (18.0–53.3) | hepatomegaly 10/10, 100% (72.2–100) |

Many Matrix 2 conditions had very few positives:
- Canine Thorax: 12 of 20 had 0–4 positives;
- Feline Thorax: 16 of 21;
- Canine Abdomen: 4 of 10.

For these conditions, sensitivity was undefined or highly uncertain. The four Canine Abdomen Matrix 2 conditions with 2–4 positives had point sensitivities of 50–100%, with wide intervals.

Macro averages rest on different condition subsets. For example, Canine Thorax Matrix 2 macro sensitivity includes 16 of 20 conditions, and Feline Thorax Matrix 2 includes 11 of 21. They are therefore not directly comparable across references.

### 5.5 Model comparison on Canine Thorax only (RQ4)

**Table 7. Week 5 GPT-4.1 mini compared with Week 7 gemini-3.8-flash on the same 100 Canine Thorax reports.**

| | Matrix 1 | Matrix 2 |
|---|---|---|
| Prediction agreement (not accuracy) | 1,940/2,000 (97.00%) | 1,944/2,000 (97.20%) |
| Cohen's κ between models (95% CI) | 0.773 (0.716–0.822) | 0.788 (0.735–0.839) |
| Δ Sensitivity, Gemini − OpenAI (pp) | −2.86 (−4.22 to −1.55) | −15.19 (−23.17 to −7.14) |
| Δ Specificity (pp) | +0.84 (−0.13 to +1.96) | +0.87 (+0.38 to +1.41) |
| Δ Precision (pp) | −0.21 (−5.95 to +5.87) | +5.83 (+0.85 to +10.52) |
| Δ F1 (pp) | −4.44 (−6.53 to −2.38) | −5.89 (−11.79 to −0.20) |
| Conditions testable by McNemar / significant after Holm | 13 / 0 | 14 / 0 |

The two models agreed on about 97% of predictions:
- Gemini had lower sensitivity and F1 against both references.
- Against Matrix 2, Gemini had higher specificity and precision.
- Discordance concentrated in `bronchitis`, `diseased_lungs` and `cardiomegaly`.
- No per-condition test was significant after Holm adjustment; the smallest unadjusted p values were about 0.013.

### 5.6 Run-to-run consistency on Canine Thorax only (RQ5)

**Table 8. Differences between separate executions at temperature 0 over identical report text.**

| Comparison | Differing pairs | Reports affected | κ |
|---|---|---|---|
| Week 4 GPT-4.1 mini: Matrix 1 batch vs Matrix 2 batch | 8/2,000 | 6 | 0.974 |
| Week 5 GPT-4.1 mini: Matrix 1 batch vs Matrix 2 batch | 11/2,000 | 8 | 0.963 |
| Week 7 Gemini: Matrix 1 batch vs Matrix 2 batch | 13/2,000 | 11 | 0.943 |
| Week 4 vs Week 5 application, Matrix 1 inputs | 13/2,000 | 10 | 0.957 |
| Week 4 vs Week 5 application, Matrix 2 inputs | 8/2,000 | 6 | 0.973 |

These repeats are incidental rather than designed. Feline Thorax and Canine Abdomen were each run once.

### 5.7 Exploratory common-batch rescoring (Canine Thorax)

The Canine Thorax Matrix 1 and Matrix 2 workbooks contain identical case identifiers and order, identical text in all three report fields and identical condition keys. Both Week 5 batches contain 100 valid 20-key records.

Each batch was rescored against the other reference:
- RUN-03 against Matrix 2: sensitivity 79.11%, specificity 98.05%, F1 78.37%.
- RUN-04 against Matrix 1: sensitivity 11.82%, specificity 96.00%, F1 20.48%.

Both are close to the original evaluations. These analyses are exploratory. EVAL-05 and EVAL-06 remain the recorded Week 5 results, and decision D-A (which batch, if any, becomes primary) is open.

---

## 6. Discussion

### 6.1 Principal finding: dependence on the reference-label workflow

The most consistent result across the three datasets is that measured performance was strongly dependent on the reference-label workflow. With identical predictions, switching from Matrix 1 to Matrix 2 raised sensitivity by:
- 44.1 percentage points in Feline Thorax;
- 53.3 in Canine Abdomen;
- 67.1 in the exploratory Canine Thorax rescoring.

The two reference sets labelled the same reports very differently. Matrix 1 contained many more positives, positive agreement was low, and almost all disagreements ran in one direction.

The reason is not established. Possible explanations include:
- different labelling conventions, thresholds or scope;
- information available to one workflow but not present in the report text;
- error in either set.

Higher model sensitivity against Matrix 2 does **not** show that Matrix 2 is more accurate. It shows that the model's labelling behaviour is closer to that of the three-reviewer majority vote than to the original labels. One of the three reviewers also wrote the prompts, which may contribute to that alignment. Without inter-reviewer reliability data, independent adjudication or documentation of the Matrix 1 labelling process, neither reference can be regarded as clinical truth.

### 6.2 Sensitivity, specificity and the limits of accuracy

High specificity was observed everywhere, but in this setting it is not evidence of useful performance. Most condition labels are negative, especially in Matrix 2, where 5.6–8.1% of pairs are positive. A classifier that rarely predicts Positive will therefore achieve high specificity and, against Matrix 2, high accuracy (about 96–97%), while still missing reference positives.

Against Matrix 1, accuracy of 51–74% coexisted with sensitivity of 5–12%. Sensitivity, precision, F1 and support counts are needed to interpret performance; aggregate accuracy alone is misleading.

### 6.3 Prompt uncertainty rules (exploratory)

The Feline Thorax prompt's conservative rule, which treats possible or suspected findings as Negative, coincided with the lowest sensitivity under both references and the lowest Matrix 1 precision. Uncertainty policy, dataset, condition set and prevalence are fully confounded, however, so this association cannot be interpreted causally. A controlled prompt ablation would be required.

### 6.4 Relation to previous work

**Veterinary clinical text.** Wulcan et al. (2025) reported much higher sensitivity (median 96.9%) for six clinical signs in feline health records. Their study differs from this one in:
- text type (general records rather than radiology reports);
- task size (6 labels rather than 10–21);
- reference design (the majority of five blinded respondents);
- a separate tuning set;
- designed repeat runs.

The two sets of results are therefore not directly comparable. Their design choices, especially separating prompt tuning from evaluation and designing repeats, are strengths the present study lacks.

Other veterinary applications addressed different targets: body-condition scores (Fins et al., 2024), diagnosis coding with a fine-tuned model (Jiang et al., 2024) and prescriptions (Hur et al., 2024). Benchmarks for veterinary free text exist, though not for radiology reports (Farrell et al., 2025). The emphasis of Chang and Chu (2026) on ground-truth definition and annotation protocols is consistent with the present observation that the reference standard can dominate the measured result.

**Human radiology reports.** The pooled sensitivity and specificity reported for NLP extraction from human radiology reports (91% and 96%; Yang et al., 2026) come from heterogeneous systems and references and are not a benchmark for this pilot. Sensitivity of LLM report classification to prompt design and perturbations (Sorin et al., 2025) is consistent with the observation that outputs varied between executions at temperature 0. The size of that variation here, 0.4–0.65% of pairs, applies only to these runs.

### 6.5 Model comparison

On Canine Thorax, GPT-4.1 mini and gemini-3.8-flash agreed on about 97% of predictions (κ about 0.77–0.79) but had different sensitivity–specificity balances. Because the comparison involves one dataset, one run per model, different execution dates and different client configurations, it cannot be generalised to other datasets or to the model families.

---

## 7. Limitations

- **Sample.** Only the first 100 populated records per dataset were evaluated, from one source. The samples are not necessarily representative, and intervals do not imply population representativeness.
- **Text only.** The models received report text only; no radiographic images were supplied. Reference labels may encode information that is absent from the text.
- **Reference standards.** The two workflows differ substantially. The origin of Matrix 1 is undocumented. Matrix 2 is a three-reviewer majority-vote research-team reference, not clinically validated ground truth or veterinary-radiologist adjudication. Reviewer qualifications and annotation guidance are undocumented.
- **No inter-reviewer reliability.** The individual Matrix 2 annotation files were deleted, so inter-reviewer reliability cannot be assessed retrospectively.
- **Evaluation independence.** Prompt-development cases overlapped with evaluation cases, and one Matrix 2 reviewer developed the prompts. The manual prompt review used report text and predictions, not reference labels. However, a recorded Canine Abdomen keyword analysis involving reference-label columns has unresolved provenance, so reference-label exposure during development cannot be excluded.
- **Confounding.** Condition sets, prevalence, prompt versions and uncertainty policies, and batch designs differ between datasets. Cross-dataset comparisons are descriptive, and no species, anatomical or prompt effect can be inferred.
- **Model coverage and versioning.** The model comparison covers Canine Thorax only, with one run per model. Model snapshot identifiers were not recorded.
- **Repeatability.** Temperature 0 did not guarantee identical outputs. Repeatability evidence is incidental and limited to Canine Thorax.
- **Sparse conditions.** Condition-level estimates are imprecise or undefined for sparse conditions. Per-condition tests are exploratory, and multiplicity applies.
- **Statistical settings.** Some settings were finalized during analysis rather than pre-specified.
- **Unresolved decision.** The Canine Thorax common-batch decision (D-A) is unresolved.
- **No clinical validation** was conducted.

---

## 8. Implications for veterinary radiology report processing

These pilot results do not support clinical or autonomous use. They suggest the following practices for evaluating LLM-based labelling of veterinary reports:

1. **Define and document the reference standard.** Record who produced the labels, from which inputs, under what guidance and with what agreement. Retain the individual annotations so that reliability can be measured.
2. **Report more than κ or accuracy.** Report prevalence, directional disagreement, and positive and negative agreement between reference sets, and do not rely on κ or accuracy alone.
3. **Hold out evaluation cases.** Keep evaluation cases out of prompt development, and record whether any reference labels were consulted during development.
4. **Report condition-level results.** Report condition-level sensitivity and precision with support counts, and flag undefined metrics.
5. **Report model versions and repeats.** Record model snapshot identifiers and run designed repeat executions.

In practice, the choice between models with different sensitivity–specificity balances would depend on the relative cost of missed and false findings. That requires clinical input, which this study did not provide.

---

## 9. Conclusion

General-purpose LLMs classified veterinary radiology report text, not images, with high specificity across three pilot datasets. Sensitivity depended strongly on which reference-label workflow was used, and the original Vetology labels and the three-reviewer majority-vote reference set (Matrix 2) disagreed substantially.

The principal conclusion is methodological: reference-label provenance and reliability must be established before LLM report-labelling performance can be interpreted. The study provides no evidence of clinical validity or readiness.

Future work should:
- document and preserve independent annotations, and measure inter-reviewer reliability;
- evaluate on held-out cases;
- test uncertainty rules experimentally;
- include repeated runs and further models across all datasets;
- use larger, representative samples.

---

## Acknowledgements

The author thanks Zach Tungate and Akshay Rathod for their participation in the independent Matrix 2 annotation process, Dr. Parin Candy and the programme's Tech Advisor for their guidance during prompt development, and Vetology for providing the source data and permitting its use for this research.

## References

Chang Y, Chu CP. 2026. Applying artificial intelligence to automate clinical data extraction from veterinary electronic health records: A practical guidance and comparative scoping review. *Veterinary Pathology*. Advance online publication 16 July 2026. https://doi.org/10.1177/03009858261461761. Abstract-level content was checked; final volume and page details were not available in the source record used.

Farrell S, Radford A, Al Moubayed N, Noble PJ. 2025. PetEVAL: A veterinary free text electronic health records benchmark. In: *Proceedings of the 24th Workshop on Biomedical Language Processing*, pp. 341–353. https://doi.org/10.18653/v1/2025.bionlp-1.29

Fins IS, Davies H, Farrell S, Torres JR, Pinchbeck G, Radford AD, Noble P. 2024. Evaluating ChatGPT text mining of clinical records for companion animal obesity monitoring. *Veterinary Record* 194(3): e3669 (published online 6 December 2023). https://doi.org/10.1002/vetr.3669

Hur B, Wang LL, Hardefeldt L, Yetisgen M. 2024. Is That the Right Dose? Investigating Generative Language Model Performance on Veterinary Prescription Text Analysis. In: *Proceedings of the 23rd Workshop on Biomedical Natural Language Processing*, pp. 390–397. https://doi.org/10.18653/v1/2024.bionlp-1.30

Jiang Y, Irvin JA, Ng AY, Zou J. 2024. VetLLM: Large Language Model for Predicting Diagnosis from Veterinary Notes. In: *Biocomputing 2024: Proceedings of the Pacific Symposium*, pp. 120–133 (published online December 2023). https://doi.org/10.1142/9789811286421_0010

Khosravi B, Dapamede T, Li F, Chisango Z, Bikmal A, Garg S, Owosela B, Khosravi A, Chavoshi M, Trivedi HM, Wyles CC, Purkayastha S, Erickson BJ, Gichoya JW. 2026. Role of Model Size and Prompting Strategies in Extracting Labels from Free-Text Radiology Reports with Open-Source Large Language Models. *Journal of Imaging Informatics in Medicine* 39(1): 995–1004 (published online 5 May 2025). https://doi.org/10.1007/s10278-025-01505-7 (metadata-level verification only)

Kottlors J, Iuga AI, Bluethgen C, Bressem K, Kather JN, et al. 2026. Guidelines for Reporting Studies on Large Language Models in Radiology: An International Delphi Expert Survey. *Radiology* 318(2): e250913. https://doi.org/10.1148/radiol.250913

Reichenpfader D, Müller H, Denecke K. 2024. A scoping review of large language model based approaches for information extraction from radiology reports. *npj Digital Medicine* 7: 222. https://doi.org/10.1038/s41746-024-01219-0 (metadata-level verification only)

Sorin V, Collins JD, Bratt AK, Kusmirek JE, Mugu VK, Kline TL, Butler CL, Wood NG, Cook CJ, Korfiatis P. 2025. Evaluating prompt and data perturbation sensitivity in large language models for radiology reports classification. *JAMIA Open* 8(4): ooaf073. https://doi.org/10.1093/jamiaopen/ooaf073

Wulcan JM, Jacques KL, Lee MA, Kovacs SL, Dausend N, Prince LE, Wulcan J, Marsilio S, Keller SM. 2025. Classification performance and reproducibility of GPT-4 omni for information extraction from veterinary electronic health records. *Frontiers in Veterinary Science* 11: 1490030. https://doi.org/10.3389/fvets.2024.1490030

Yang Q, Jiang J, Dong X, Yang H, Wang Q, Yang Z, Yang D, Liu P. 2026. Performance of Natural Language Processing Model in Extracting Information from Free-Text Radiology Reports: A Systematic Review and Meta-Analysis. *Journal of Imaging Informatics in Medicine* 39(4): 3639–3653 (published online 28 October 2025). https://doi.org/10.1007/s10278-025-01728-8

---

**Source-verification level** (preliminary review; see `Vetology_Research_Knowledge_Base/03_Consolidated_Knowledge_Base/09_Literature_Evidence_Matrix.md`). Bibliographic metadata for all eleven sources was checked against DOI (Crossref) records.

| Level | Sources | Note |
|---|---|---|
| Full text (relevant sections) | Farrell et al. 2025; Hur et al. 2024; Jiang et al. 2024; Wulcan et al. 2025 | |
| Abstract | Chang and Chu 2026; Fins et al. 2024; Sorin et al. 2025; Yang et al. 2026 | |
| Abstract (one sentence) and metadata | Kottlors et al. 2026 | FLAIR Appendix S1 not retrieved |
| Metadata only | Khosravi et al. 2026; Reichenpfader et al. 2024 | |

Claims attributed to abstract-level and metadata-level sources are limited to what those records state.

## Appendix A. Prompts, repository and outputs

**A.1 Active prompts** (full texts version-controlled in the project repository; publication or redistribution remains subject to Vetology's data and confidentiality permissions).

| Dataset | Prompt | Path | File SHA-256 |
|---|---|---|---|
| CT | Canine Thorax Master Prompt V1.3 | `src/week_07/prompts/canine_thorax_master_prompt_v1_3.txt` | `31a7dab6e535e6f0af6a54106cf449ecadfe3644c7b3c805710309f0e85ab7b1` |
| FT | Feline Thorax Master Prompt V1.2 | `src/week_07/prompts/feline_thorax_master_prompt_v1_2.txt` | `9bbd36c4a1d9ac15cb24c39b3e9d0ad5af9106a9bddb3adf3401098e1c418f25` |
| CA | Canine Abdomen Master Prompt V1.4 | `src/week_07/prompts/canine_abdomen_master_prompt_v1_4.txt` | `9336be3fa463be14bdfd71d93e2709b4bad70c626d0533d8e4f887809b2a254c` |

User message: "Classify the following {canine thorax | feline thorax | canine abdomen} radiology report according to the system instructions.", followed by the three labelled report sections.

**A.2 Repository and outputs.**
- Repository: https://github.com/suyash-gore/vetology-radiology-evaluation. The code and prompt files are maintained in the repository; the evaluated data and prediction outputs are not public.
- Weeks 5–8 are on feature branches and have not been merged into `main`.
- Output files are confidential and are not in the repository: per-run `predictions.jsonl`, the Matrix 1/Matrix 2 evaluation workbooks, and the comparison workbooks. The Week 7 run manifests are committed.

**A.3 Domain texts consulted for the Canine Thorax V1.3 prompt.** The edition details were not recorded for most titles; the one recorded edition is shown where available. These are domain references for prompt writing, not evidence for the results:
1. Thrall's Textbook of Veterinary Diagnostic Radiology (8th ed.).
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

## Appendix C. Run configuration details

| Setting | Week 4 (CT) | Week 5 (CT) | Week 7 Gemini (CT) | Week 7 (FT, CA) |
|---|---|---|---|---|
| Temperature | 0 | 0 | 0.0 | 0.0 |
| Timeout | 90 s | 90 s | 90 s | 90 s |
| Transport retries | LangChain `max_retries=2` | 2 | 1 attempt | 0 |
| Application attempts | 2 | 2 | 2, with bounded backoff | 2, with bounded backoff |
| Response format | none | none | JSON MIME, no schema | none |
| Run manifest | no | no | yes | yes |
| Runtime (from manifests) | — | — | Python 3.14.6; langchain-google-genai 4.4.2; google-genai 2.31.0 | Python 3.14.6; langchain-openai 1.7.2; openai 3.49.0 |

## Supplementary Table S1. Per-condition results (95% Wilson intervals)

Generated from `Vetology_Research_Knowledge_Base/04_Evidence_and_Artifacts/07_statistical_results.json`. The table shows the GPT-4.1 mini core evaluations for each dataset: CT Week 5 (EVAL-05/06, separate batches), FT (EVAL-11/12) and CA (EVAL-13/14). The other Canine Thorax evaluations are in `07_Statistical_Analysis_Results.md` §8.
- F1 uses the manuscript definition 2TP/(2TP + FP + FN) (Section 4.7). Where the original workbooks left F1 blank (`06_Per_Condition_Results.md`), this table may show 0.0%.
- "undef." = zero denominator.
- Ref + = reference positives; Pred + = model positive predictions.

**EVAL-05 — CT Week 5 OpenAI M1**

| Condition | Ref + / Ref − | Pred + | TP | FN | TN | FP | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| perihilar_infiltrate | 57 / 43 | 2 | 1 | 56 | 42 | 1 | 1.8% (0.3–9.3) | 97.7% (87.9–99.6) | 50.0% (9.5–90.5) | 3.4% |
| pneumonia | 47 / 53 | 8 | 7 | 40 | 52 | 1 | 14.9% (7.4–27.7) | 98.1% (90.1–99.7) | 87.5% (52.9–97.8) | 25.5% |
| bronchitis | 63 / 37 | 19 | 15 | 48 | 33 | 4 | 23.8% (15.0–35.6) | 89.2% (75.3–95.7) | 78.9% (56.7–91.5) | 36.6% |
| interstitial | 59 / 41 | 28 | 19 | 40 | 32 | 9 | 32.2% (21.7–44.9) | 78.0% (63.3–88.0) | 67.9% (49.3–82.1) | 43.7% |
| diseased_lungs | 63 / 37 | 34 | 28 | 35 | 31 | 6 | 44.4% (32.8–56.7) | 83.8% (68.9–92.3) | 82.4% (66.5–91.7) | 57.7% |
| hypo_plastic_trachea | 35 / 65 | 0 | 0 | 35 | 65 | 0 | 0.0% (0.0–9.9) | 100.0% (94.4–100.0) | undef. | 0.0% |
| cardiomegaly | 29 / 71 | 16 | 12 | 17 | 67 | 4 | 41.4% (25.5–59.3) | 94.4% (86.4–97.8) | 75.0% (50.5–89.8) | 53.3% |
| pulmonary_nodules | 62 / 38 | 8 | 7 | 55 | 37 | 1 | 11.3% (5.6–21.5) | 97.4% (86.5–99.5) | 87.5% (52.9–97.8) | 20.0% |
| pleural_effusion | 60 / 40 | 1 | 1 | 59 | 40 | 0 | 1.7% (0.3–8.9) | 100.0% (91.2–100.0) | 100.0% (20.7–100.0) | 3.3% |
| rtm | 55 / 45 | 6 | 4 | 51 | 43 | 2 | 7.3% (2.9–17.3) | 95.6% (85.2–98.8) | 66.7% (30.0–90.3) | 13.1% |
| focal_caudodorsal_lung | 47 / 53 | 3 | 3 | 44 | 53 | 0 | 6.4% (2.2–17.2) | 100.0% (93.2–100.0) | 100.0% (43.9–100.0) | 12.0% |
| focal_perihilar | 58 / 42 | 0 | 0 | 58 | 42 | 0 | 0.0% (0.0–6.2) | 100.0% (91.6–100.0) | undef. | 0.0% |
| pulmonary_hypoinflation | 72 / 28 | 11 | 10 | 62 | 27 | 1 | 13.9% (7.7–23.7) | 96.4% (82.3–99.4) | 90.9% (62.3–98.4) | 24.1% |
| right_sided_cardiomegaly | 32 / 68 | 3 | 2 | 30 | 67 | 1 | 6.2% (1.7–20.1) | 98.5% (92.1–99.7) | 66.7% (20.8–93.9) | 11.4% |
| pericardial_effusion | 24 / 76 | 1 | 1 | 23 | 76 | 0 | 4.2% (0.7–20.2) | 100.0% (95.2–100.0) | 100.0% (20.7–100.0) | 8.0% |
| bronchiectasis | 67 / 33 | 0 | 0 | 67 | 33 | 0 | 0.0% (0.0–5.4) | 100.0% (89.6–100.0) | undef. | 0.0% |
| pulmonary_vessel_enlargement | 52 / 48 | 2 | 2 | 50 | 48 | 0 | 3.8% (1.1–13.0) | 100.0% (92.6–100.0) | 100.0% (34.2–100.0) | 7.4% |
| left_sided_cardiomegaly | 28 / 72 | 14 | 10 | 18 | 68 | 4 | 35.7% (20.7–54.2) | 94.4% (86.6–97.8) | 71.4% (45.4–88.3) | 47.6% |
| thoracic_lymphadenopathy | 82 / 18 | 3 | 3 | 79 | 18 | 0 | 3.7% (1.3–10.2) | 100.0% (82.4–100.0) | 100.0% (43.9–100.0) | 7.1% |
| esophagitis | 57 / 43 | 2 | 1 | 56 | 42 | 1 | 1.8% (0.3–9.3) | 97.7% (87.9–99.6) | 50.0% (9.5–90.5) | 3.4% |

**EVAL-06 — CT Week 5 OpenAI M2**

| Condition | Ref + / Ref − | Pred + | TP | FN | TN | FP | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| perihilar_infiltrate | 2 / 98 | 3 | 1 | 1 | 96 | 2 | 50.0% (9.5–90.5) | 98.0% (92.9–99.4) | 33.3% (6.1–79.2) | 40.0% |
| pneumonia | 6 / 94 | 8 | 6 | 0 | 92 | 2 | 100.0% (61.0–100.0) | 97.9% (92.6–99.4) | 75.0% (40.9–92.9) | 85.7% |
| bronchitis | 15 / 85 | 18 | 9 | 6 | 76 | 9 | 60.0% (35.7–80.2) | 89.4% (81.1–94.3) | 50.0% (29.0–71.0) | 54.5% |
| interstitial | 28 / 72 | 30 | 28 | 0 | 70 | 2 | 100.0% (87.9–100.0) | 97.2% (90.4–99.2) | 93.3% (78.7–98.2) | 96.6% |
| diseased_lungs | 48 / 52 | 33 | 33 | 15 | 52 | 0 | 68.8% (54.7–80.1) | 100.0% (93.1–100.0) | 100.0% (89.6–100.0) | 81.5% |
| hypo_plastic_trachea | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| cardiomegaly | 19 / 81 | 15 | 14 | 5 | 80 | 1 | 73.7% (51.2–88.2) | 98.8% (93.3–99.8) | 93.3% (70.2–98.8) | 82.4% |
| pulmonary_nodules | 6 / 94 | 8 | 5 | 1 | 91 | 3 | 83.3% (43.6–97.0) | 96.8% (91.0–98.9) | 62.5% (30.6–86.3) | 71.4% |
| pleural_effusion | 1 / 99 | 1 | 1 | 0 | 99 | 0 | 100.0% (20.7–100.0) | 100.0% (96.3–100.0) | 100.0% (20.7–100.0) | 100.0% |
| rtm | 2 / 98 | 6 | 2 | 0 | 94 | 4 | 100.0% (34.2–100.0) | 95.9% (90.0–98.4) | 33.3% (9.7–70.0) | 50.0% |
| focal_caudodorsal_lung | 1 / 99 | 3 | 1 | 0 | 97 | 2 | 100.0% (20.7–100.0) | 98.0% (92.9–99.4) | 33.3% (6.1–79.2) | 50.0% |
| focal_perihilar | 2 / 98 | 0 | 0 | 2 | 98 | 0 | 0.0% (0.0–65.8) | 100.0% (96.2–100.0) | undef. | 0.0% |
| pulmonary_hypoinflation | 9 / 91 | 11 | 9 | 0 | 89 | 2 | 100.0% (70.1–100.0) | 97.8% (92.3–99.4) | 81.8% (52.3–94.9) | 90.0% |
| right_sided_cardiomegaly | 1 / 99 | 3 | 1 | 0 | 97 | 2 | 100.0% (20.7–100.0) | 98.0% (92.9–99.4) | 33.3% (6.1–79.2) | 50.0% |
| pericardial_effusion | 0 / 100 | 1 | 0 | 0 | 99 | 1 | undef. | 99.0% (94.6–99.8) | 0.0% (0.0–79.3) | 0.0% |
| bronchiectasis | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| pulmonary_vessel_enlargement | 1 / 99 | 2 | 1 | 0 | 98 | 1 | 100.0% (20.7–100.0) | 99.0% (94.5–99.8) | 50.0% (9.5–90.5) | 66.7% |
| left_sided_cardiomegaly | 15 / 85 | 15 | 13 | 2 | 83 | 2 | 86.7% (62.1–96.3) | 97.6% (91.8–99.4) | 86.7% (62.1–96.3) | 86.7% |
| thoracic_lymphadenopathy | 2 / 98 | 3 | 2 | 0 | 97 | 1 | 100.0% (34.2–100.0) | 99.0% (94.4–99.8) | 66.7% (20.8–93.9) | 80.0% |
| esophagitis | 0 / 100 | 2 | 0 | 0 | 98 | 2 | undef. | 98.0% (93.0–99.4) | 0.0% (0.0–65.8) | 0.0% |

**EVAL-11 — FT Week 7 OpenAI M1**

| Condition | Ref + / Ref − | Pred + | TP | FN | TN | FP | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| pulmonary_nodules | 6 / 94 | 5 | 1 | 5 | 90 | 4 | 16.7% (3.0–56.4) | 95.7% (89.6–98.3) | 20.0% (3.6–62.4) | 18.2% |
| esophagitis | 59 / 41 | 0 | 0 | 59 | 41 | 0 | 0.0% (0.0–6.1) | 100.0% (91.4–100.0) | undef. | 0.0% |
| pneumonia | 51 / 49 | 0 | 0 | 51 | 49 | 0 | 0.0% (0.0–7.0) | 100.0% (92.7–100.0) | undef. | 0.0% |
| bronchitis | 14 / 86 | 11 | 4 | 10 | 79 | 7 | 28.6% (11.7–54.6) | 91.9% (84.1–96.0) | 36.4% (15.2–64.6) | 32.0% |
| interstitial | 19 / 81 | 9 | 3 | 16 | 75 | 6 | 15.8% (5.5–37.6) | 92.6% (84.8–96.6) | 33.3% (12.1–64.6) | 21.4% |
| diseased_lungs | 33 / 67 | 19 | 10 | 23 | 58 | 9 | 30.3% (17.4–47.3) | 86.6% (76.4–92.8) | 52.6% (31.7–72.7) | 38.5% |
| hypo_plastic_trachea | 12 / 88 | 0 | 0 | 12 | 88 | 0 | 0.0% (0.0–24.2) | 100.0% (95.8–100.0) | undef. | 0.0% |
| cardiomegaly | 4 / 96 | 11 | 3 | 1 | 88 | 8 | 75.0% (30.1–95.4) | 91.7% (84.4–95.7) | 27.3% (9.7–56.6) | 40.0% |
| pleural_effusion | 28 / 72 | 3 | 3 | 25 | 72 | 0 | 10.7% (3.7–27.2) | 100.0% (94.9–100.0) | 100.0% (43.9–100.0) | 19.4% |
| perihilar_infiltrate | 54 / 46 | 0 | 0 | 54 | 46 | 0 | 0.0% (0.0–6.6) | 100.0% (92.3–100.0) | undef. | 0.0% |
| rtm | 21 / 79 | 0 | 0 | 21 | 79 | 0 | 0.0% (0.0–15.5) | 100.0% (95.4–100.0) | undef. | 0.0% |
| focal_caudodorsal_lung | 38 / 62 | 1 | 0 | 38 | 61 | 1 | 0.0% (0.0–9.2) | 98.4% (91.4–99.7) | 0.0% (0.0–79.3) | 0.0% |
| right_sided_cardiomegaly | 5 / 95 | 0 | 0 | 5 | 95 | 0 | 0.0% (0.0–43.4) | 100.0% (96.1–100.0) | undef. | 0.0% |
| focal_perihilar | 52 / 48 | 0 | 0 | 52 | 48 | 0 | 0.0% (0.0–6.9) | 100.0% (92.6–100.0) | undef. | 0.0% |
| left_sided_cardiomegaly | 5 / 95 | 0 | 0 | 5 | 95 | 0 | 0.0% (0.0–43.4) | 100.0% (96.1–100.0) | undef. | 0.0% |
| bronchiectasis | 26 / 74 | 0 | 0 | 26 | 74 | 0 | 0.0% (0.0–12.9) | 100.0% (95.1–100.0) | undef. | 0.0% |
| pulmonary_vessel_enlargement | 5 / 95 | 3 | 2 | 3 | 94 | 1 | 40.0% (11.8–76.9) | 98.9% (94.3–99.8) | 66.7% (20.8–93.9) | 50.0% |
| thoracic_lymphadenopathy | 46 / 54 | 1 | 1 | 45 | 54 | 0 | 2.2% (0.4–11.3) | 100.0% (93.4–100.0) | 100.0% (20.7–100.0) | 4.3% |
| pulmonary_hypoinflation | 32 / 68 | 1 | 1 | 31 | 68 | 0 | 3.1% (0.6–15.7) | 100.0% (94.7–100.0) | 100.0% (20.7–100.0) | 6.1% |
| pericardial_effusion | 2 / 98 | 0 | 0 | 2 | 98 | 0 | 0.0% (0.0–65.8) | 100.0% (96.2–100.0) | undef. | 0.0% |
| Fe_Alveolar | 22 / 78 | 2 | 1 | 21 | 77 | 1 | 4.5% (0.8–21.8) | 98.7% (93.1–99.8) | 50.0% (9.5–90.5) | 8.3% |

**EVAL-12 — FT Week 7 OpenAI M2**

| Condition | Ref + / Ref − | Pred + | TP | FN | TN | FP | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| pulmonary_nodules | 5 / 95 | 5 | 4 | 1 | 94 | 1 | 80.0% (37.6–96.4) | 98.9% (94.3–99.8) | 80.0% (37.6–96.4) | 80.0% |
| esophagitis | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| pneumonia | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| bronchitis | 38 / 62 | 11 | 11 | 27 | 62 | 0 | 28.9% (17.0–44.8) | 100.0% (94.2–100.0) | 100.0% (74.1–100.0) | 44.9% |
| interstitial | 6 / 94 | 9 | 6 | 0 | 91 | 3 | 100.0% (61.0–100.0) | 96.8% (91.0–98.9) | 66.7% (35.4–87.9) | 80.0% |
| diseased_lungs | 46 / 54 | 19 | 18 | 28 | 53 | 1 | 39.1% (26.4–53.5) | 98.1% (90.2–99.7) | 94.7% (75.4–99.1) | 55.4% |
| hypo_plastic_trachea | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| cardiomegaly | 10 / 90 | 11 | 9 | 1 | 88 | 2 | 90.0% (59.6–98.2) | 97.8% (92.3–99.4) | 81.8% (52.3–94.9) | 85.7% |
| pleural_effusion | 3 / 97 | 3 | 3 | 0 | 97 | 0 | 100.0% (43.9–100.0) | 100.0% (96.2–100.0) | 100.0% (43.9–100.0) | 100.0% |
| perihilar_infiltrate | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| rtm | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| focal_caudodorsal_lung | 1 / 99 | 1 | 0 | 1 | 98 | 1 | 0.0% (0.0–79.3) | 99.0% (94.5–99.8) | 0.0% (0.0–79.3) | 0.0% |
| right_sided_cardiomegaly | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| focal_perihilar | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| left_sided_cardiomegaly | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| bronchiectasis | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| pulmonary_vessel_enlargement | 3 / 97 | 3 | 3 | 0 | 97 | 0 | 100.0% (43.9–100.0) | 100.0% (96.2–100.0) | 100.0% (43.9–100.0) | 100.0% |
| thoracic_lymphadenopathy | 1 / 99 | 1 | 1 | 0 | 99 | 0 | 100.0% (20.7–100.0) | 100.0% (96.3–100.0) | 100.0% (20.7–100.0) | 100.0% |
| pulmonary_hypoinflation | 1 / 99 | 1 | 1 | 0 | 99 | 0 | 100.0% (20.7–100.0) | 100.0% (96.3–100.0) | 100.0% (20.7–100.0) | 100.0% |
| pericardial_effusion | 0 / 100 | 0 | 0 | 0 | 100 | 0 | undef. | 100.0% (96.3–100.0) | undef. | undef. |
| Fe_Alveolar | 3 / 97 | 2 | 2 | 1 | 97 | 0 | 66.7% (20.8–93.9) | 100.0% (96.2–100.0) | 100.0% (34.2–100.0) | 80.0% |

**EVAL-13 — CA Week 7 OpenAI M1**

| Condition | Ref + / Ref − | Pred + | TP | FN | TN | FP | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| gastritis | 29 / 71 | 9 | 6 | 23 | 68 | 3 | 20.7% (9.8–38.4) | 95.8% (88.3–98.6) | 66.7% (35.4–87.9) | 31.6% |
| ascites | 19 / 81 | 4 | 3 | 16 | 80 | 1 | 15.8% (5.5–37.6) | 98.8% (93.3–99.8) | 75.0% (30.1–95.4) | 26.1% |
| colitis | 25 / 75 | 8 | 3 | 22 | 70 | 5 | 12.0% (4.2–30.0) | 93.3% (85.3–97.1) | 37.5% (13.7–69.4) | 18.2% |
| liver_mass | 13 / 87 | 2 | 2 | 11 | 87 | 0 | 15.4% (4.3–42.2) | 100.0% (95.8–100.0) | 100.0% (34.2–100.0) | 26.7% |
| pancreatitis | 75 / 25 | 3 | 2 | 73 | 24 | 1 | 2.7% (0.7–9.2) | 96.0% (80.5–99.3) | 66.7% (20.8–93.9) | 5.1% |
| microhepatia | 14 / 86 | 6 | 1 | 13 | 81 | 5 | 7.1% (1.3–31.5) | 94.2% (87.1–97.5) | 16.7% (3.0–56.4) | 10.0% |
| small_intestinal_obstruction | 21 / 79 | 8 | 4 | 17 | 75 | 4 | 19.0% (7.7–40.0) | 94.9% (87.7–98.0) | 50.0% (21.5–78.5) | 27.6% |
| splenic_mass | 18 / 82 | 3 | 1 | 17 | 80 | 2 | 5.6% (1.0–25.8) | 97.6% (91.5–99.3) | 33.3% (6.1–79.2) | 9.5% |
| splenomegaly | 19 / 81 | 3 | 1 | 18 | 79 | 2 | 5.3% (0.9–24.6) | 97.5% (91.4–99.3) | 33.3% (6.1–79.2) | 9.1% |
| hepatomegaly | 47 / 53 | 11 | 11 | 36 | 53 | 0 | 23.4% (13.6–37.2) | 100.0% (93.2–100.0) | 100.0% (74.1–100.0) | 37.9% |

**EVAL-14 — CA Week 7 OpenAI M2**

| Condition | Ref + / Ref − | Pred + | TP | FN | TN | FP | Sensitivity (Wilson) | Specificity (Wilson) | Precision (Wilson) | F1 |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| gastritis | 16 / 84 | 9 | 9 | 7 | 84 | 0 | 56.2% (33.2–76.9) | 100.0% (95.6–100.0) | 100.0% (70.1–100.0) | 72.0% |
| ascites | 5 / 95 | 4 | 4 | 1 | 95 | 0 | 80.0% (37.6–96.4) | 100.0% (96.1–100.0) | 100.0% (51.0–100.0) | 88.9% |
| colitis | 24 / 76 | 8 | 8 | 16 | 76 | 0 | 33.3% (18.0–53.3) | 100.0% (95.2–100.0) | 100.0% (67.6–100.0) | 50.0% |
| liver_mass | 2 / 98 | 2 | 2 | 0 | 98 | 0 | 100.0% (34.2–100.0) | 100.0% (96.2–100.0) | 100.0% (34.2–100.0) | 100.0% |
| pancreatitis | 4 / 96 | 3 | 2 | 2 | 95 | 1 | 50.0% (15.0–85.0) | 99.0% (94.3–99.8) | 66.7% (20.8–93.9) | 57.1% |
| microhepatia | 6 / 94 | 6 | 6 | 0 | 94 | 0 | 100.0% (61.0–100.0) | 100.0% (96.1–100.0) | 100.0% (61.0–100.0) | 100.0% |
| small_intestinal_obstruction | 8 / 92 | 8 | 6 | 2 | 90 | 2 | 75.0% (40.9–92.9) | 97.8% (92.4–99.4) | 75.0% (40.9–92.9) | 75.0% |
| splenic_mass | 3 / 97 | 3 | 3 | 0 | 97 | 0 | 100.0% (43.9–100.0) | 100.0% (96.2–100.0) | 100.0% (43.9–100.0) | 100.0% |
| splenomegaly | 3 / 97 | 3 | 3 | 0 | 97 | 0 | 100.0% (43.9–100.0) | 100.0% (96.2–100.0) | 100.0% (43.9–100.0) | 100.0% |
| hepatomegaly | 10 / 90 | 11 | 10 | 0 | 89 | 1 | 100.0% (72.2–100.0) | 98.9% (94.0–99.8) | 90.9% (62.3–98.4) | 95.2% |

