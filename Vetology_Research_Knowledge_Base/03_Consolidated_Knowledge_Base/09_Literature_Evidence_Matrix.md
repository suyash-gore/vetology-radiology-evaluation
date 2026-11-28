# 09 — Literature Evidence Matrix

**Status:** structured **preliminary** literature review to prepare the research paper. **This is not a completed systematic review**, and no novelty is established by it. See `10_Research_Gap_Assessment.md` for the critical gap analysis and `11_FLAIR_Checklist_Crosswalk.md` for reporting-guideline mapping.
**Prepared:** 2026-11-28 on `week-08/research-paper-development` (approved baseline `fb30842`).
**Study framing:** general-purpose LLMs performing structured binary multi-condition classification from veterinary radiology **report text** (no radiographic images). Three equally important datasets:
- Canine Thorax: 100 cases, 20 conditions.
- Feline Thorax: 100 cases, 21 conditions.
- Canine Abdomen: 100 cases, 10 conditions.

There are two reference workflows:
- Matrix 1: original Vetology labels.
- Matrix 2: Gold Standard labels, peer-reviewed and agreed upon after discussion. Independent veterinary-radiologist adjudication is **not** established.

The design and analysis plan is in `08_Research_Design_and_Analysis_Plan.md`.

---

## 1. Review scope, cut-off and search record

| Item | Record |
|---|---|
| Evidence cut-off | 2026-11-28, the date the metadata was checked in this session |
| Review type | Structured preliminary review of an **owner-supplied seed set**, plus targeted metadata lookups. No protocol registration, no dual screening, no PRISMA flow, no risk-of-bias assessment |
| Seed set | 11 publications supplied by the project owner (items L01–L11). The previously mentioned "Lee et al." review is **excluded**: its full citation and claims were not independently verified |
| Verification method | DOI metadata via the Crossref REST API (`api.crossref.org`) for all 11 DOIs. Abstracts where Crossref provides them. Open-access full text where the publisher host was reachable: aclanthology.org, psb.stanford.edu, www.frontiersin.org |
| Hosts not accessible | `pubs.rsna.org` returned a bot-protection challenge (HTTP 403), so the FLAIR Appendix S1 and the Radiology full text were not retrieved. `www.nature.com` returned 429/403 in this session |
| Additional search concepts used so far | Crossref keyword queries only, used to identify image-based veterinary radiology AI context studies: "deep learning thoracic radiographs dogs"; "convolutional neural network canine thoracic radiographs classification"; "artificial intelligence feline thoracic radiographs"; "deep learning canine abdominal radiographs". Crossref title lookups for the ten veterinary textbooks (§7) |
| Databases not yet searched | PubMed/MEDLINE, CAB Abstracts, Web of Science, Scopus, Embase, ACL Anthology search, arXiv/medRxiv, Google Scholar |
| Concepts still required for a defensible search | (veterinary OR canine OR feline OR small animal) AND (radiology report OR radiograph report OR imaging report OR free text) AND (large language model OR GPT OR Gemini OR LLaMA OR natural language processing) AND (classification OR extraction OR labelling). Plus agreement/reference-standard and repeatability/reproducibility terms. See `10_Research_Gap_Assessment.md` §6 |

### 1.1 Verification-status vocabulary

| Status | Meaning |
|---|---|
| **Publisher/original full text checked** | The full text (or its relevant sections) was read in this session |
| **Abstract/metadata checked** | The Crossref record and, where shown, the abstract were read. The full text was not read |
| **Metadata only** | The Crossref bibliographic record only, with no abstract |
| **Secondary citation only** | Known only through another source |
| **Details still to verify** | Owner-supplied details that the checked material did not confirm. They are listed per item and **not** used as facts |

### 1.2 Evidence-classification vocabulary

| Class | Meaning for this study |
|---|---|
| **Direct** | LLM classification of veterinary radiology report text. *No item in the current set qualifies* |
| **Adjacent** | Shares a key feature (veterinary clinical text and LLMs, or radiology report text and LLMs/NLP, or binary multi-label classification and repeatability) but not all of them |
| **Background** | Broader context (benchmarks, reviews, image-based AI) |
| **Reporting guidance** | Reporting checklists or guidelines |

---

## 2. Master reference list

| ID | Reference (as verified in Crossref) | DOI / stable link | Verification status |
|---|---|---|---|
| L01 | Chang Y, Chu CP. Applying artificial intelligence to automate clinical data extraction from veterinary electronic health records: A practical guidance and comparative scoping review. *Veterinary Pathology*. Published online 2026-07-16; article 03009858261461761 (no volume or issue assigned in Crossref) | https://doi.org/10.1177/03009858261461761 | Abstract/metadata checked |
| L02 | Fins IS, Davies H, Farrell S, Torres JR, Pinchbeck G, Radford AD, Noble P. Evaluating ChatGPT text mining of clinical records for companion animal obesity monitoring. *Veterinary Record*. 2024;194(3):e3669. Published online 2023-12-06 | https://doi.org/10.1002/vetr.3669 | Abstract/metadata checked |
| L03 | Jiang Y, Irvin JA, Ng AY, Zou J. VetLLM: Large Language Model for Predicting Diagnosis from Veterinary Notes. In: *Biocomputing 2024* (Pacific Symposium on Biocomputing 2024). pp. 120–133 | https://doi.org/10.1142/9789811286421_0010 ; PDF https://psb.stanford.edu/psb-online/proceedings/psb24/jiang.pdf | Publisher/original full text checked (key sections) |
| L04 | Hur B, Wang LL, Hardefeldt L, Yetisgen M. Is That the Right Dose? Investigating Generative Language Model Performance on Veterinary Prescription Text Analysis. In: *Proceedings of the 23rd Workshop on Biomedical Natural Language Processing* (BioNLP 2024). pp. 390–397 | https://doi.org/10.18653/v1/2024.bionlp-1.30 | Publisher/original full text checked (key sections) |
| L05 | Wulcan JM, Jacques KL, Lee MA, Kovacs SL, Dausend N, Prince LE, Wulcan J, Marsilio S, Keller SM. Classification performance and reproducibility of GPT-4 omni for information extraction from veterinary electronic health records. *Frontiers in Veterinary Science*. 2025;11:1490030. Published 2025-01-16 | https://doi.org/10.3389/fvets.2024.1490030 | Publisher/original full text checked (methods and abstract) |
| L06 | Farrell S, Radford A, Al Moubayed N, Noble PJ. PetEVAL: A veterinary free text electronic health records benchmark. In: *Proceedings of the 24th Workshop on Biomedical Language Processing* (BioNLP 2025). pp. 341–353 | https://doi.org/10.18653/v1/2025.bionlp-1.29 | Publisher/original full text checked (abstract and results tables) |
| L07 | Reichenpfader D, Müller H, Denecke K. A scoping review of large language model based approaches for information extraction from radiology reports. *npj Digital Medicine*. 2024;7:222. Published 2024-08-24 | https://doi.org/10.1038/s41746-024-01219-0 | Metadata only |
| L08 | Yang Q, Jiang J, Dong X, Yang H, Wang Q, Yang Z, Yang D, Liu P. Performance of Natural Language Processing Model in Extracting Information from Free-Text Radiology Reports: A Systematic Review and Meta-Analysis. *Journal of Imaging Informatics in Medicine*. 2026;39(4):3639–3653. Published online 2025-10-28 | https://doi.org/10.1007/s10278-025-01728-8 | Abstract/metadata checked |
| L09 | Kottlors J, Iuga AI, Bluethgen C, Bressem K, Kather JN, et al. (28 authors). Guidelines for Reporting Studies on Large Language Models in Radiology: An International Delphi Expert Survey. *Radiology*. 2026;318(2):e250913 | https://doi.org/10.1148/radiol.250913 ; Appendix S1: https://pubs.rsna.org/doi/suppl/10.1148/radiol.250913/suppl_file/ry250913suppa1.pdf | Abstract/metadata checked. **Appendix S1 not retrieved** (blocked) |
| L10 | Sorin V, Collins JD, Bratt AK, Kusmirek JE, Mugu VK, Kline TL, Butler CL, Wood NG, Cook CJ, Korfiatis P. Evaluating prompt and data perturbation sensitivity in large language models for radiology reports classification. *JAMIA Open*. 2025;8(4):ooaf073 | https://doi.org/10.1093/jamiaopen/ooaf073 | Abstract/metadata checked |
| L11 | Khosravi B, Dapamede T, Li F, Chisango Z, Bikmal A, Garg S, Owosela B, Khosravi A, Chavoshi M, Trivedi HM, Wyles CC, Purkayastha S, Erickson BJ, Gichoya JW. Role of Model Size and Prompting Strategies in Extracting Labels from Free-Text Radiology Reports with Open-Source Large Language Models. *Journal of Imaging Informatics in Medicine*. 2026;39(1):995–1004. Published online 2025-05-05 | https://doi.org/10.1007/s10278-025-01505-7 | Metadata only |
| C01 | Burti S, Longhin Osti V, Zotti A, et al. Use of deep learning to detect cardiomegaly on thoracic radiographs in dogs. *The Veterinary Journal*. 2020 | https://doi.org/10.1016/j.tvjl.2020.105505 | Metadata only (context) |
| C02 | Banzato T, Wodzinski M, Burti S, et al. Automatic classification of canine thoracic radiographs using deep learning. *Scientific Reports*. 2021 | https://doi.org/10.1038/s41598-021-83515-3 | Metadata only (context) |
| C03 | Valente C, Wodzinski M, Guglielmini C, et al. Development of an artificial intelligence-based algorithm for the detection of left atrial enlargement from feline thoracic radiographs (title truncated in the metadata lookup). *Veterinary Quarterly*. 2026 | https://doi.org/10.1080/01652176.2025.2611847 | Metadata only (context); full title to verify |
| C04 | Mekonnen et al. Deep learning framework for vertebral heart size and cardiothoracic ratio estimation in dogs and cats using thoracic radiographs (title truncated in the metadata lookup). *Frontiers in Veterinary Science*. 2025 | https://doi.org/10.3389/fvets.2025.1612338 | Metadata only (context); full author list and title to verify |

Metadata differences relative to the owner-supplied list (not errors in the list, but details to record correctly):
- **L02:** online publication 2023-12-06; issue 2024 (194(3), e3669).
- **L03:** the DOI `10.1142/9789811286421_0010` is confirmed.
- **L05:** volume 11 with a 2025-01-16 publication date.
- **L08:** issue 39(4).
- **L11:** now has volume/issue/pages 39(1):995–1004.
- **L01:** no volume yet (online first).

---

## 3. Veterinary LLM text studies

### L02 — Fins et al. (Veterinary Record 2024)

| Field | Content |
|---|---|
| Objective | Compare an LLM (ChatGPT) with a previously developed regular-expression method (RegexT) for identifying overweight body condition scores (BCS) in veterinary narratives (abstract) |
| Species / domain | Companion animals; first-opinion clinical narratives; obesity monitoring |
| Input type | Other clinical text (clinical narratives); not radiology, no images |
| Dataset | 4,415 anonymised clinical narratives (abstract). Source practices/network: **to verify** |
| Task / labels | BCS value extraction; overweight identification |
| Model / version | "ChatGPT" per the abstract. The owner-supplied "GPT-3.5 Turbo" is **to verify** against the full text |
| Method | Narrative appended to a prompt asking the model to return BCS information (prompt-based, no fine-tuning) |
| Reference standard | Manual review of the data (abstract). Reviewer number and expertise **to verify** |
| Metrics / findings | Precision: RegexT 100% (95% CI 94.81–100%) vs ChatGPT 89.3% (82.75–93.64%). Recall: ChatGPT 100% (96.18–100%) vs RegexT 72.6% (63.92–79.94%) (abstract) |
| Repeatability | Not stated in the abstract (**to verify**) |
| Limitations (source) | Prior anonymisation and subtle prompt engineering are needed to improve ChatGPT output |
| Relevance | Prompt-based veterinary text extraction with CIs; a different input type and task from ours |
| Class / status | **Adjacent** / Abstract/metadata checked |

### L03 — Jiang et al., VetLLM (PSB 2024)

| Field | Content |
|---|---|
| Objective | Predict diagnoses from veterinary notes with an LLM; compare zero-shot and fine-tuned models |
| Species / domain | Veterinary clinical notes (multi-species; species detail **to verify**) |
| Input type | Other clinical text (veterinary notes and discharge summaries) |
| Dataset | CSU portion: 112,557 notes (Colorado State University). PP portion: 586 discharge summaries from a commercial practice (full text). Fine-tuning used 5,000 notes |
| Task / labels | Diagnosis prediction (multi-label diagnosis codes; exact code set **to verify**) |
| Model / version | Alpaca-7B (zero-shot); VetLLM = Alpaca-7B fine-tuned |
| Method | Zero-shot prompting and **supervised fine-tuning**. Not comparable to general-purpose API prompting |
| Reference standard | Existing diagnosis annotations from prior VetTag datasets (full text); annotation process **to verify** |
| Metrics / findings | Zero-shot Alpaca-7B F1: 0.538 (CSU), 0.389 (PP). VetLLM F1: 0.747 (CSU), 0.637 (PP) (full text) |
| Repeatability | Not identified (**to verify**) |
| Relevance | Veterinary diagnosis prediction from text by an LLM. It differs in fine-tuning, input type and label structure |
| Class / status | **Adjacent** / full text checked (key sections) |

### L04 — Hur et al. (BioNLP 2024)

| Field | Content |
|---|---|
| Objective | Assess LLMs for extracting prescription attributes (dose, duration, active ingredient, indication) for antimicrobial stewardship |
| Species / domain | Veterinary (companion animal examples); prescription and clinical notes |
| Input type | Other clinical text (consultation notes and prescription labels) |
| Dataset | Size and source **to verify** (not extracted in this session) |
| Task / labels | Structured attribute extraction with numeric transformation |
| Model / version | GPT-3.5, GPT-4, LLaMA2-70B vs a BERT-based ensemble baseline (RxVetBERT) (full text). Exact API snapshots **to verify** |
| Method | Prompt engineering, including prompts iteratively generated with GPT-4 and "functional prompting" combining probabilistic predictions with deterministic calculations (full text) |
| Reference standard | Inferred labels; exact-match evaluation. Inter-annotator agreement reported per attribute, e.g. F1 0.8 for indication (full text). Full annotation protocol **to verify** |
| Metrics / findings | Exact-match accuracy/F1 per attribute; GPT-4 highest in the reported table (full text). Exact per-attribute values to be transcribed before use |
| Repeatability | Not identified (**to verify**) |
| Relevance | Prompt strategy and structured output from veterinary text; not radiology |
| Class / status | **Adjacent** / full text checked (key sections) |

### L05 — Wulcan et al. (Frontiers in Veterinary Science 2025) — **closest methodological analogue**

| Field | Content |
|---|---|
| Objective | Assess the classification performance and reproducibility of GPT-4o for identifying six clinical signs associated with feline chronic enteropathy (FCE) from EHRs; compare with GPT-3.5 Turbo and with human reproducibility; relate LLM errors to human disagreement (abstract/full text) |
| Species / domain | Feline; veterinary referral hospital EHRs; gastrointestinal clinical signs |
| Input type | Other clinical text (EHR text, history-type content); **not radiology reports**, no images |
| Dataset | 250 EHRs in the test set. Separate pilot sets and a **tuning set used to refine prompts and model parameters, distinct from the test set** (full text) |
| Task / labels | Binary presence/absence of six clinical signs (decreased appetite, vomiting, weight loss, diarrhoea, constipation, polyphagia) plus a citation task (full text) |
| Model / version | GPT-4o and GPT-3.5 Turbo via the Azure OpenAI chat-completion endpoint, API version 2024-02-01 (full text). Exact model snapshot **to verify** |
| Method | Prompt engineering through iterative evaluation on the tuning set; JSON output; no fine-tuning |
| Reference standard | Majority opinion (mode) of five human respondents, blinded to each other and to the LLMs (full text) |
| Metrics / findings | GPT-4o vs human majority: sensitivity 96.9%, specificity 97.6%, PPV 80.7%, NPV 99.5%, F1 84.4%, balanced accuracy 96.3% (medians across signs with IQR). GPT-3.5 Turbo sensitivity 81.7%. McNemar's test for model and temperature comparisons. 35/43 GPT-4o errors (81.4%) occurred where humans disagreed |
| Repeatability | **Designed**: five repeated runs at each temperature (0, 0.5, 1). Cohen's κ averaged over run pairs: 0.98 for GPT-4o vs 0.80 for human pairs (full text/abstract) |
| Limitations (source) | Requires validation for the intended setting. Web-based ChatGPT cannot set temperature, so reproduction requires API access (full text) |
| Relevance | Binary multi-label classification, sensitivity/specificity/F1, McNemar, κ and repeat-run design. **Directly informs our analysis plan**, but on a different text type, task scale and reference design (`10_…` §3.1) |
| Class / status | **Adjacent (high methodological relevance)** / full text checked (methods and abstract) |

### L01 — Chang & Chu (Veterinary Pathology 2026) — review

| Field | Content |
|---|---|
| Objective | PRISMA-ScR scoping review of information extraction from veterinary EHRs, extended to prompt-based LLM approaches in human medicine; practical framework (abstract) |
| Scope | 4 databases (PubMed, CAB Abstracts, Web of Science, ACL Anthology). 5,796 records screened; **23 veterinary and 31 human studies** included. The human component is limited to prompt-based studies (abstract) |
| Findings (source) | Veterinary studies more often trained supervised models on larger data sets, while human studies increasingly used prompt-based LLMs (LLaMA, GPT) with smaller annotated sets. The review provides a workflow and prompt example (abstract) |
| Details to verify | Veterinary search end date (owner: 3 June 2025); the count of four veterinary generative-LLM studies; the treatment of ground truth, inter-annotator agreement and reproducibility; whether any included study used radiology reports |
| Relevance | The most important review for positioning our work; **its included-study list must be screened for veterinary radiology-report studies** before any gap claim |
| Class / status | **Background (review)** / Abstract/metadata checked |

## 4. Veterinary conventional NLP and benchmark studies

### L06 — Farrell et al., PetEVAL (BioNLP 2025)

| Field | Content |
|---|---|
| Objective | Introduce a benchmark from real-world, free-text veterinary EHRs (full text) |
| Domain | First-opinion UK veterinary practices; companion-animal EHRs |
| Input type | Other clinical text (EHR free text) |
| Dataset | 17,600 professionally annotated EHRs. Training 11,000; evaluation 1,600; test 5,000, with distinct clinic distributions (full text) |
| Tasks / labels | ICD-11 syndromic chapter multi-label classification (20,408 labels); disease NER (429 labels); anonymisation NER (8,244 labels) (full text) |
| Models | BERT-base, PetBERT, LLaMA 3.1 8B baselines (full text) |
| Reference standard | Professional annotation with a multistage protocol; pre-annotation with the PetBERT-ICD model is mentioned. Full protocol **to verify** |
| Metrics | Precision, recall, macro and weighted F1; SeqEval for NER (full text). Values to be transcribed before use |
| Relevance | Shows that a veterinary text benchmark **exists** (multi-label classification included). It does not cover radiology reports. Our study must not claim that veterinary NLP lacks benchmarks |
| Note | Published after the L01 veterinary search cut-off (per the owner; L01 cut-off to verify) |
| Class / status | **Background (benchmark)** / full text checked (abstract, task tables) |

*No further conventional veterinary NLP studies were verified in this session.* PetBERT, VetTag and others cited inside L03 and L06 are **secondary citations only** and need their own verification.

## 5. Human radiology-report text studies

### L07 — Reichenpfader et al. (npj Digital Medicine 2024) — review

| Field | Content |
|---|---|
| Scope | Scoping review of LLM-based information extraction from radiology reports (title) |
| Details to verify | Search period and end date; number of included studies; models covered; findings. The owner notes that the search predates much recent generative-LLM work, and this is **to verify** |
| Distinction | Human radiology **report text**, not image interpretation |
| Class / status | **Background (review)** / Metadata only |

### L08 — Yang et al. (J Imaging Inform Med 2026) — systematic review and meta-analysis

| Field | Content |
|---|---|
| Scope | NLP systems broadly (not only generative LLMs) for extracting information from free-text radiology reports. Search 21–23 November 2024 in 6 databases; QUADAS-2; bivariate random-effects model (abstract) |
| Dataset | 28 studies; 51,187 reports; 421,692 extracted entities (abstract) |
| Findings | Pooled sensitivity 91% (95% CI 87–93); specificity 96% (93–97); DOR 220; AUC 0.98. Single-site extraction outperformed multiple-site extraction (AUC 0.99 vs 0.95). Anatomical site was the only significant source of heterogeneity in meta-regression. No significant differences across NLP model types, data sources, languages or modalities (abstract) |
| Relevance | Human-domain benchmark for report-text extraction performance. **Not veterinary evidence**, and pooled values are not comparable to our pilot |
| Class / status | **Background (meta-analysis)** / Abstract/metadata checked |

### L10 — Sorin et al. (JAMIA Open 2025)

| Field | Content |
|---|---|
| Objective | Evaluate LLM classification of radiology reports for pulmonary embolism (PE) under different prompt designs and data perturbations (abstract) |
| Domain / input | Human; CT pulmonary angiography **report text** |
| Dataset | 11,999 reports; 1,296 (10.8%) PE-positive (abstract) |
| Models | Gemini-1.5-Pro, Gemini-1.5-Flash-001, Gemini-1.5-Flash-002 (abstract) |
| Reference standard | Concordance between a computer-vision PE detection algorithm and multiple LLM runs, with discrepancies manually reviewed (abstract). *Our interpretation:* the reference is partly LLM-derived, which needs consideration when comparing |
| Findings | Accuracy 0.953–0.996 across LLMs. Performance varied with prompt design and data quality. Flash-002 was most robust to perturbations. Variability across geographic cloud regions was minimal for Pro, and Flash was stable (abstract) |
| Repeatability | Repeated analyses across cloud regions (abstract); run counts **to verify** |
| Relevance | Single-condition human report classification. **Informs prompt sensitivity and repeat-run considerations (RQ5/RQ6)** |
| Class / status | **Adjacent** / Abstract/metadata checked; full details to verify (as instructed) |

### L11 — Khosravi et al. (J Imaging Inform Med 2026)

| Field | Content |
|---|---|
| Objective (title) | Role of model size and prompting strategies in extracting labels from free-text radiology reports with open-source LLMs |
| Details to verify | Dataset, label schema, models and sizes, prompting strategies, reference standard, results. The owner noted a reference-label-schema aspect, which is **to verify** |
| Relevance | Potentially relevant to label schema and prompt effects (RQ6) |
| Class / status | **Adjacent (provisional)** / Metadata only; **use only after full-text confirmation** |

## 6. Image-based veterinary radiology AI (context only — NOT direct evidence)

These studies interpret **radiographic images** and are listed only to show that veterinary radiology AI exists in an image modality distinct from our report-text task. They were identified by Crossref keyword queries. Only titles, venues and dates were seen; **content was not reviewed**, and no findings are recorded.

| ID | Topic (from title) | Species / region | Status |
|---|---|---|---|
| C01 | Deep learning detection of cardiomegaly on thoracic radiographs | Canine thorax | Metadata only |
| C02 | Automatic classification of canine thoracic radiographs with deep learning | Canine thorax | Metadata only |
| C03 | AI detection of left atrial enlargement from feline thoracic radiographs | Feline thorax | Metadata only; title to verify |
| C04 | Deep learning estimation of vertebral heart size / cardiothoracic ratio | Canine and feline thorax | Metadata only; authors/title to verify |

No image-based **canine abdominal** radiography study was found by the single query run. This is **not** evidence that none exist.

## 7. Reporting guidelines and methodological reviews

| ID | Item | Role | Status |
|---|---|---|---|
| L09 | Kottlors et al., FLAIR guideline (Radiology 2026; 28 authors). The abstract states that the guidelines are based on multidisciplinary expert consensus to enhance reporting standards, reproducibility, comparability and clinical translation | **Reporting guidance**. Voluntary checklist for this study; **not** a mandatory journal requirement. The owner states 32 items in six categories; the item list is **not verified** because Appendix S1 could not be retrieved (see `11_…`) | Abstract/metadata checked |
| L01, L07, L08 | Reviews above | Methodological context | As above |

---

## 8. Veterinary domain references used in prompt development (NOT primary research studies)

These ten textbooks were supplied by the owner as the veterinary diagnostic-imaging reference set used during prompt development. They are **domain knowledge references**. They are not experimental studies, they provide **no validation evidence** for the LLM results, and they do not substitute for veterinary expert review.

### 8.1 Inventory

Titles are as supplied by the owner. Edition, editors and year are recorded only where the owner stated them or a Crossref record was seen; the edition actually consulted must be confirmed.

| ID | Title (owner-supplied) | Edition actually consulted | Candidate bibliographic record seen in Crossref (to confirm) |
|---|---|---|---|
| T01 | Thrall's Textbook of Veterinary Diagnostic Radiology | 8th edition (owner) | Elsevier records exist, e.g. chapters with ISBN prefix 978-0-323-48247-9 (2018) and 978-0-323-93235-6 (2026). Which corresponds to the 8th edition is **to verify** |
| T02 | BSAVA Manual of Canine and Feline Radiography and Radiology | To confirm | BSAVA record, 2013 (DOI prefix 10.22233/9781910443187) — to confirm |
| T03 | Practical Veterinary Diagnostic Imaging | To confirm | No matching record found — **to verify** |
| T04 | BSAVA Manual of Canine and Feline Thoracic Imaging | To confirm | BSAVA record, 2024 (10.22233/9781910443941) — edition to confirm |
| T05 | BSAVA Manual of Canine and Feline Abdominal Imaging | To confirm | BSAVA record, 2009 (10.22233/9781905319718) — to confirm |
| T06 | Small Animal Diagnostic Ultrasound | To confirm | Elsevier edited-book records for 2002, 2015 and 2021 — edition to confirm |
| T07 | Lavin's Radiography for Veterinary Technicians | To confirm | No clear matching record — **to verify** |
| T08 | Veterinary Radiology: Basic Principles and Radiographic Positioning | To confirm | No matching record found — **to verify** |
| T09 | Kealy, McAllister and Graham — Diagnostic Radiology and Ultrasonography of the Dog and Cat | To confirm | Elsevier edited book, 2011 (10.1016/c2009-0-46814-4) — edition to confirm |
| T10 | Thrall and Robertson — Atlas of Normal Radiographic Anatomy and Anatomic Variants (in the Dog and Cat) | To confirm | Elsevier edited-book records for 2016 and 2023 — edition to confirm |

### 8.2 Prompt-development provenance (what the evidence shows)

| Source type | Documented role | Evidence | Datasets / prompt versions | Traceability |
|---|---|---|---|---|
| **Veterinary textbooks (T01–T10)** | For Canine Thorax Master Prompt V1.3, the presenter described consulting **ten veterinary reference books**, querying them with NotebookLM using targeted questions, and consolidating the extracted material with ChatGPT into the master prompt | KB_03 §5.2 and §4.1 (Week 6 presentation narrative; `02_Project_History_and_Methodology.md` §3.1). The book list itself was in `Presenter_Script_and_Notes(1).docx`, which is **not in the repository** | **Canine Thorax only** in the evidence. **No record links the textbooks to the Feline Thorax or Canine Abdomen prompts**, although use is plausible and must be confirmed by the owner | **No source-to-rule traceability.** The prompt files contain no citations to any textbook, and no record maps a specific book or page to a specific condition definition or rule |
| **AI tools (NotebookLM, ChatGPT)** | Extraction from the books (NotebookLM) and consolidation into the prompt (ChatGPT) | KB_03 §5.2 | CT V1.3 (documented) | Intermediate outputs not preserved |
| **Veterinary expert guidance** | Dr. Parin Candy credited for veterinary guidance | KB_03 §4.1, §5.2 | CT (documented) | Nature and scope of the guidance undocumented |
| **Tech Advisor feedback (Atharva)** | RTM = redundant tracheal membrane; `diseased_lungs` as an independent condition; possible/suspected → Positive (project-wide V1.3 rule, 3 Nov 2026) | KB_06 §9–10; CT V1.3 Word change log (`files-bundle-01/Canine_Thorax_Master_Prompts_V1.3.docx`) | Reported as applied to CT and FT (RTM) and to all three V1.3 prompts; only the CT V1.3 text is retrievable | Original advisor message not preserved (user-reported) |
| **Owner working interpretation** | `Fe_Alveolar` = Feline Alveolar Pattern | KB_06 §9 | FT | Not advisor-confirmed |
| **Project data used during prompt refinement** | V1.0 vs V1.1 manual review on selected cases (CT/FT cases 3, 4, 5, 7, 8; CA cases 13–17). A keyword heuristic over **reference labels** of the evaluation workbooks informed the CA V1.3/V1.4 uncertainty policy | KB_06 §11; KB_07 §8.5; `03_Results_and_Experimental_Findings.md` §3 | All three (review); CA (heuristic) | Relevant to FLAIR item 1.5 (see `11_…`): whether these cases overlap the 100-case evaluation sets must be confirmed |
| **Internet research** | **Not documented** in any knowledge-base source | — | — | Owner to state whether and how used |
| **Peer-reviewed literature** | **Not documented** as an input to prompt development | — | — | Owner to state |

**Constraint inside the prompts themselves.** The V1.0 baseline prompts instruct the model **not** to rely on external medical knowledge to fill gaps or expand undefined abbreviations (KB_06 Appendix A). Textbook knowledge therefore shaped the **wording of definitions and rules written by the authors**. It was not supplied to the model as external context at inference time.

**Required owner confirmations (provenance):**
- **P-1:** which books informed which dataset prompt (CT, FT, CA) and which version (V1.0, V1.1, V1.3, FT V1.1/V1.2, CA V1.2–V1.4).
- **P-2:** the editions consulted.
- **P-3:** whether NotebookLM/ChatGPT intermediate notes exist.
- **P-4:** whether internet sources or journal articles were used.
- **P-5:** the scope of Dr. Parin Candy's input.
- **P-6:** whether the prompt-review cases and the hedged-language analysis used cases from the evaluation sets.


## 9. Week 8 update (manuscript use)

- Sources cited in `paper/Research_Paper_Draft_v0.1.md`: L01–L11. L07 (Reichenpfader et al.) and L11 (Khosravi et al.) are cited **for their stated topic only** and are flagged `[SOURCE VERIFICATION REQUIRED]`. L01 lacks volume and pages.
- **Not done:** screening of the 23 veterinary studies included in L01; the database searches in `10_…` §6; full-text review of L01, L07, L09, L10 and L11.
- **Correction to §8.2 wording:** the "keyword heuristic over reference labels" is as recorded in KB_07 §8.5. The developer does not recall reference labels being inspected, and the provenance of that heuristic is **unresolved** (`05_…` §4 L-W8-2).
- C01–C04 (image-based AI) are not cited in the manuscript.
