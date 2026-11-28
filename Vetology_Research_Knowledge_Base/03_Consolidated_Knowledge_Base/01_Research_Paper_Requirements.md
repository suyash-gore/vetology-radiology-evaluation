# 01 — Research Paper Requirements

Primary sources: KB_01 (requirements conversation), KB_03 §2 and §12, KB_04 §2, KB_02 §3 and §20.
Status labels follow `00_README.md` §3.

> This document records requirements only. It does not draft the paper, and it does not introduce journal rules, citations or section lengths that the sources do not contain.

## 1. Confirmed requirements

### 1.1 Programme-level (Vetology Free Training Program webpage `vetology-free-training-program.html`, as reviewed in KB_01, KB_03 and KB_04)

| Requirement | Source |
|---|---|
| Ten-week programme. Build Python applications that use LLMs to evaluate veterinary radiology reports, compare them with radiologist reports and manual scoring, present findings and write a short research paper | KB_01 §3.1 |
| Three input datasets: Canine Thorax, Feline Thorax, Canine Abdomen | KB_01 §3.1 |
| Original paper sections: Abstract, Introduction, Method, Results, Discussion, Limitations, Conclusion, Appendix | KB_01 §3.2 |
| Single-column PDF; numbered figures and tables referenced in the text; no patient or clinic identifiers; no Vetology data files in the repository | KB_01 §3.2 |
| Every number in the paper traces to a generated output file. Describe model failures and common patterns. State limitations plainly. Obtain peer reviews from two others | KB_01 Table 2 (Week 8); KB_03 §12 |
| Week 10: final PDF with repository link, output files and confusion matrices for **all three** input files | KB_01 Table 2 |

### 1.2 Week 6–10 paper milestones (webpage)

| Week | Requirement | Status (from sources) |
|---|---|---|
| 6 | One-page outline (research question, method, measurements, expected tables/figures); team review | **Unverified.** No standalone outline artifact or review record exists (KB_03 §11.3). A candidate outline was reconstructed in KB_03 §11.2 |
| 7 | Method draft (data, prompts, models, scoring, matrix construction); results tables with sensitivity, specificity and error counts by condition across all three files | **Pending / not evidenced** (KB_02 Table 19) |
| 8 | Full draft; trace every number; failure analysis; limitations; two peer reviews and revision | **Planned.** This knowledge base is preparatory work, not the draft |
| 9 | Slides built from the paper | **Deferred** by user decision until the paper is complete (KB_01 §2) |
| 10 | Apply feedback; revise; clean repository; submit final PDF, repository link, outputs and confusion matrices | **Planned** |

### 1.3 Updated section lengths (supplied by the user as a later Vetology update; **supersede** the webpage values)

| Section | Updated length | Required content | Earlier webpage value |
|---|---|---|---|
| Abstract | 150–200 words | Question, method, headline numbers, one conclusion | 150–200 words |
| Introduction | 0.5–1 page | Why comparing radiology reports with an LLM is worth testing; the specific research question | 0.5 page |
| Method | 1–3 pages | Input files, conditions, manual scoring rules, final prompts (in appendix), models and versions, confusion-matrix calculations | 1–2 pages |
| Results | 1–2 pages | Confusion matrices per input file; sensitivity and specificity per condition; agreement with manual scoring | 1–2 pages |
| Discussion | 1–2 pages | Where and why the model failed; prompt changes that mattered; manual build vs Claude Code | 1 page |
| Limitations | 1 page | 100-report Gold Standard per file; peer-agreed rather than expert ground truth; model variability between runs | 0.25 page |
| Conclusion | 0.5 page | What should happen next; key reader takeaway | 0.25 page |
| Appendix | No limit | Final prompts, repository link, output filenames | No limit |

Note: the Limitations wording "peer-agreed rather than expert ground truth" is quoted from the Vetology requirement. The owner later clarified that the Gold Standard is *peer-reviewed and agreed upon after discussion* (see `00_README.md` §4 and 07 C-03).

Source: KB_01 Tables 3 and 7; repeated in KB_03 §12. KB_03 adds that the update is dated 28 November 2026 and should not be presented as the original Week 6 wording.

### 1.4 Formatting and visual requirements (user instruction, KB_01 §3.4)

- Follow the applicable **Springer** research-paper format strictly. **The exact Springer journal or proceedings template has not been identified** (Unresolved; KB_01 §16).
- Include figures, tables, visual charts, a system diagram and flow diagrams.
- Give every figure and table a descriptive caption, consistent numbering and a reference in the text.
- Include a Table of Contents, List of Figures and List of Tables. An abbreviations list and appendix contents are to be *considered* (recommendation, not a fixed requirement).

### 1.5 Writing and integrity requirements (user decisions, KB_01 §9 and §13)

- The paper must be original, plagiarism-free and a truthful account of the user's own work. Nothing may be fabricated.
- Use clear, sophisticated academic English that sounds natural, not ornate or artificial.
- Use the APA verb-tense guidance (supplied by Ben) as a writing reference.
- The user must be able to explain and defend every substantive paragraph.
- Keep demonstrated findings, proposed improvements and future research separate.
- Use the Vetology sample white paper ("Leveraging Machine Learning to Automatically Analyze Multi-Site Veterinary Radiographic Reports", Vetology Innovations LLC) only as a style and communication reference. Its methods, data and findings must not be copied or presented as the user's work (KB_01 §17.1).
- The paper is completed before presentation work begins (KB_01 §2).
- No blueprint or draft is written until the user explicitly says to proceed (KB_01 §9, KB_02 §3.3).

### 1.6 Assignment items that bear on paper scope

| Item | Status | Source |
|---|---|---|
| Week 5 peer review of original and rebuilt applications | **Not evidenced.** The user confirmed peer review is their own responsibility | KB_04 §11 |
| Week 6 presentation feedback incorporated into code | **Unverified.** No feedback transcript or change mapping exists | KB_03 §9 |
| Week 7 optional second-model comparison on one input file | **Completed for Canine Thorax** (Gemini vs GPT-4.1 mini); results recorded in repository documentation | KB_08, KB_09, KB_02 §11.2 |

## 2. Recommendations (not confirmed requirements)

These come from source analyses, not from Vetology instructions. Treat them as proposals.

| Recommendation | Source |
|---|---|
| Aim for a distinctive, evidence-based paper, not a routine internship report; include product/deployment thinking grounded in findings | KB_01 §2 (user intent) |
| Write for an audience that includes Corey (a Vetology director): technical understanding plus practical implications, without a sales pitch | KB_01 §2 (user intent) |
| Candidate working title and research question for the Canine Thorax scope | KB_03 §11.2 (proposed; not approved) |
| Expected tables: dataset/condition overview, confusion matrices per matrix, per-condition metrics, Week 4/5 live comparison, parity comparison, QA summary | KB_03 §11.2 |
| Expected figures: end-to-end flow diagram, architecture comparison, confusion-matrix heatmaps, sensitivity/specificity by condition, error distribution | KB_03 §11.2 |
| Statistical analysis (confidence intervals, support counts, class imbalance) before publication | KB_07 §19 #10; KB_02 §18 |
| Conduct a literature review before any novelty or commercial-opportunity claim | KB_01 §19 #8 |

## 3. Open requirement questions

| # | Question | Status |
|---|---|---|
| RQ-1 | Which exact Springer template (journal, proceedings, LNCS or other)? | Unresolved |
| RQ-2 | Final research question wording and scope: Canine Thorax only (KB_03 outline) or all three datasets (programme Week 7/10 requirement)? | Unresolved. The programme requires all three files; the Week 6 outline covered Canine Thorax only |
| RQ-3 | Do page lengths in §1.3 assume the Springer template's page size? | Unresolved |
| RQ-4 | Who are the two peer reviewers for the Week 8 draft? | Unresolved |
| RQ-5 | Will the Feline/Abdomen "draft" Gold Standard workbooks be confirmed as final by Vetology? | Unresolved (KB_07 §19 #5) |
