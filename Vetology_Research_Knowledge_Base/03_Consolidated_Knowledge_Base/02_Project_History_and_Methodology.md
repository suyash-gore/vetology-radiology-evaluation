# 02 — Project History and Methodology

Primary sources: KB_06 (Week 3), KB_05 (Week 4), KB_04 and KB_10 (Week 5), KB_03 (Week 6), KB_07, KB_08 and KB_09 (Week 7), KB_02 (Week 7 review).
Repository verification: branch `week-08/research-paper-development` at `ceb3f42` (Git log, tags, committed manifests and prompt files checked in Week 8).

## 1. Chronology

| When | Week | Event | Status | Source / repository anchor |
|---|---|---|---|---|
| Before Week 3 | 1 | Canine Thorax dataset selected; first 100 cases (CaseID 1–100) prepared; manual scoring; approved Gold Standard of 100 × 20 = 2,000 labels. The manual draft differed from the approved Gold Standard on 21 labels | Recorded | KB_06 §12 (from `weekly_progress(5).md`) |
| ≤ 2026-11-03 | 2 | CLI Excel scaffold, API demo scripts, project documentation | Verified (W8): commits `166f30e`, `60541e6`; tag `week-02-docs-baseline` → `60541e6` | KB_09 Table 5 |
| Week 3 | 3 | Master Prompts V1.0 and V1.1 for all three datasets; manual prompt review on five cases per dataset; no API execution | Recorded | KB_06 §5, §11 |
| 2026-11-03 | 3 | V1.3 advisor-informed update (RTM expansion, independent `diseased_lungs`, possible/suspected = Positive) | Recorded; Canine Thorax V1.3 file Verified (W8) by SHA-256 | KB_06 §10; `src/week_04/prompts/canine_thorax_master_prompt_v1_3.txt` |
| 2026-11-03 | 4 | Week 4 Matrix 2 batch (prediction file A4: 14:51–14:55 UTC) | Observed (prior) | KB_10 Table 12 |
| 2026-11-03 to 11-08 | 4 | Original Python application; Matrix 1 run on 7 Nov (A3: 05:29–05:32 UTC, i.e. 10:59–11:02 local time); Matrix 1 evaluation; optional JSON configuration | Verified (W8): commits `533c73c`, `bdb9952` | KB_05; KB_10 |
| 2026-11-10 | 5 | Claude Code rebuild in six gated phases (`d62470f` → `874aaea`); closeout `a938cde` (tag `week-05-closeout`) | Verified (W8): commits; tag object `f87a766` → `a938cde` | KB_04 Table 7; KB_10 Table 4 |
| 2026-11-12 | 5 | Developer's Windows fixes and two live 100-case OpenAI batches; commit `f20c240` | Verified (W8) commit; results Recorded | KB_04 §7.3; KB_10 |
| Week 6 | 6 | 17-slide HTML presentation draft and presenter scripts; presentation delivery and feedback **not evidenced** | Recorded (materials); delivery Unverified | KB_03 |
| 2026-11-20 | 7 | Week 7 Gemini pipeline (`a280f1b` → `a843a9a`); live Gemini batches for Canine Thorax Matrix 1 and Matrix 2 | Verified (W8): commits and manifests | KB_08; KB_09 |
| 2026-11-21 13:07 +05:30 | 7 | Gemini documentation closeout `67f133c` with two run manifests | Verified (W8) | KB_08 |
| 2026-11-21 15:34–16:00 UTC | 7 | Feline Thorax / Canine Abdomen extension and prompt registration (`92a2d3d`, `4044403`, `ec63636`, `65274d6`) | Verified (W8) commits | KB_07 Table 5 |
| 2026-11-21 16:22–16:44 UTC | 7 | Shared OpenAI prediction batches for Feline Thorax and Canine Abdomen | Verified (W8): manifests | KB_07 §8.2 |
| 2026-11-21 16:35–16:51 UTC | 7 | Feline / Abdomen Matrix 1 and Matrix 2 evaluations. The Abdomen Matrix 2 terminal log stamp 22:21:19 in KB_02 is unverified; a +05:30 offset is assumed | **Verified (W8)** against the actual workbooks (generated outputs are gitignored, not in the repository) | KB_02 §4; workbook Execution Logs |
| 2026-11-21 22:31 +05:30 | 7 | Feline / Abdomen manifests committed: `ceb3f42` | Verified (W8) | KB_02 §4; KB_07 |
| 2026-11-28 | 8 | Ten knowledge extractions produced; consolidation commit `ea92818` | — | All |
| 2026-11-28 | 8 | Evidence reconciliation against `files-bundle-01.zip` (42 files: source workbooks, evaluation workbooks, predictions, manifests, prompts, reports); all 10 reference evaluations and both agreement analyses verified | Verified (W8) | `../04_Evidence_and_Artifacts/` |

Week 8 timing evidence from the actual artifacts (prediction-record timestamps and workbook Execution Logs):
- Week 5 Matrix 1 live batch: an earlier attempt at 09:54–09:55 UTC on 12 Nov failed for all 100 cases with an authentication error (HTTP 401, expired API key; `outputs/week_05/matrix_1/errors.jsonl`). The successful batch ran 09:57–10:01 UTC; evaluation 10:04:10 UTC.
- Feline Matrix 1 evaluation 16:35:36 UTC and Canine Abdomen Matrix 1 evaluation 16:50:16 UTC on 21 Nov. The Matrix 2 workbooks carry no generation timestamp.

Branch lineage (Verified W8): `main` holds Weeks 2–4 only (`4031615`). The remote Week 5, Week 7 and Week 8 branches all descend from `bdb9952`. Week 5 and Week 7 work has **not** been merged into `main` (KB_07, KB_08 D-01, KB_10).

## 2. Research task definition

- The task is multi-condition binary classification of **radiology report text** (not images). For every case, each target condition receives exactly one label, `Positive` or `Negative` (KB_06 §2; KB_05 §11.1).
- The question is whether the original radiologist's report supports the label. The model does not diagnose the animal or infer findings the report does not state (KB_06 §2).
- The unit of evaluation is a case–condition label pair (KB_03 §5.1).

### 2.1 Datasets and conditions

| Dataset | Conditions | Pairs per matrix | Matrix 1 input (Vetology labels) | Matrix 2 input (Gold Standard) | Source |
|---|---|---|---|---|---|
| Canine Thorax | 20 | 2,000 | `Vetology_Matrix1_First100_Encoded.xlsx` | `1_canine_thorax_gold_standard_score_draft.xlsx` | KB_04 Table 11; manifests (Verified W8) |
| Feline Thorax | 21 | 2,100 | `2_feline_thorax_raw_data_encoded.xlsx` | `2_feline_thorax_gold_standard_score_draft.xlsx` | KB_07 Table 13; manifest (Verified W8) |
| Canine Abdomen | 10 | 1,000 | `3_canine_abdomen_raw_data_encoded.xlsx` | `3_canine_abdomen_gold_standard_score_draft.xlsx` | KB_07 Table 13; manifest (Verified W8) |

Week 3 workbook names (`1_canine_thorax_scoring_data.xlsx`, `2_feline_thorax_scoring_data.xlsx`, `3_canine_abdomen_scoring_data.xlsx`; KB_06 §2) differ from the Week 4–7 evaluation inputs. How these files relate is **not documented** (Unresolved).

**Canine Thorax keys (20, configured order):** perihilar_infiltrate, pneumonia, bronchitis, interstitial, diseased_lungs, hypo_plastic_trachea, cardiomegaly, pulmonary_nodules, pleural_effusion, rtm, focal_caudodorsal_lung, focal_perihilar, pulmonary_hypoinflation, right_sided_cardiomegaly, pericardial_effusion, bronchiectasis, pulmonary_vessel_enlargement, left_sided_cardiomegaly, thoracic_lymphadenopathy, esophagitis (KB_04 §3.1; KB_05 Table 4).

**Feline Thorax keys (21):** pulmonary_nodules, esophagitis, pneumonia, bronchitis, interstitial, diseased_lungs, hypo_plastic_trachea, cardiomegaly, pleural_effusion, perihilar_infiltrate, rtm, focal_caudodorsal_lung, right_sided_cardiomegaly, focal_perihilar, left_sided_cardiomegaly, bronchiectasis, pulmonary_vessel_enlargement, thoracic_lymphadenopathy, pulmonary_hypoinflation, pericardial_effusion, Fe_Alveolar (KB_02 Table 7; the manifest records 21 keys, Verified W8).

**Canine Abdomen keys (10):** gastritis, ascites, colitis, liver_mass, pancreatitis, microhepatia, small_intestinal_obstruction, splenic_mass, splenomegaly, hepatomegaly (KB_02 Table 8; the manifest records 10 keys, Verified W8).

**Terminology status** (KB_06 §9, §13):
- `rtm` = redundant tracheal membrane. Advisor-confirmed, as relayed by the user.
- `diseased_lungs` is a separate, independently assessed health condition. Advisor-confirmed concept; the clinical boundary remains broad.
- `Fe_Alveolar` = "Feline Alveolar Pattern". This is the **user's working interpretation, not advisor-confirmed**.

### 2.2 Reference-label tracks

| Track | Reference labels | Interpretation | Caveats |
|---|---|---|---|
| Matrix 1 | Original Vetology condition labels in the raw encoded workbook | Agreement with the original Vetology labels | Clinical provenance and encoding history are not fully established (KB_05 §7.1, KB_03 §5.4). The Matrix 1 workbook layout labels them "Gold Standard" for legacy reasons (D-041 / KB_09 TD13) |
| Matrix 2 | Peer-reviewed Gold Standard workbook (filenames end `_draft`) | Agreement with the peer-reviewed Gold Standard labels | **Owner clarification (Week 8 reconciliation, 2026-11-28): the Gold Standard dataset is peer-reviewed and agreed upon after discussion.** This is not formal, independent expert adjudication. The earlier KB_05 §8.1 wording ("assigned by a veterinary radiologist") is superseded and is kept only as a historical record. See 07 §3, C-03 |

**Matrix 1 terminology (verified in Week 8).** Matrix 1 evaluation workbooks label counts "GS Positive / GS Negative" and use "Gold Standard" wording. This is **legacy terminology only**, not a second reference source:
- The Matrix 1 reference is the Vetology encoded workbook. The Execution Log `Ground-truth workbook` field names `Vetology_Matrix1_First100_Encoded.xlsx` (SHA-256 `3f1a17b7…`), which is byte-identical to the supplied `Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx`; for Feline and Abdomen it names the `*_raw_data_encoded.xlsx` files.
- The reference prevalence (CT 1,049 / FT 534 / CA 280 positives) matches those workbooks and differs from the Gold Standard workbooks (158 / 117 / 81).
- The wording is deliberately preserved for parity with the delivered Week 4 workbook: decision D-041 (`docs/DECISION_LOG.md`) and the module docstring at `src/week_07/evaluation/matrix1_workbook.py` line 22.
- The Matrix 1 loader is `load_matrix1_reference` in `src/week_07/evaluation/reference_loader.py`, a reproduction of the Week 4 `load_matrix1_inputs`.

The definition of Matrix 1 is unchanged.

Feline Thorax Matrix 1 only: three columns (`pulmonary_nodules`, `esophagitis`, `pneumonia`) held `Normal`/`Abnormal` and were mapped Normal → Negative and Abnormal → Positive. No other column, workflow or application is normalised (KB_07 §5.4; manifest `source_label_normalization`, Verified W8). For Canine Thorax, legacy Abnormal/Normal values were *not* accepted as ground truth (KB_06 §12; KB_04 §3.1).

## 3. Prompt methodology

### 3.1 Knowledge building (KB_06 §3; KB_03 §5.2)

- Iterative workflow: exact condition keys → shared role/task/evidence policy → condition-specific definitions → review of representative reports → recording of ambiguous terms → Tech Advisor clarification → revision.
- Canine Thorax V1.3: the presenter credits guidance from Dr. Parin Candy, ten veterinary reference books queried with NotebookLM, and consolidation with ChatGPT (KB_03 §4.1, §5.2). These tools are described as *not* replacing veterinary expertise.
- Design choice: one master prompt per dataset (shared rules plus all condition definitions) rather than one prompt per condition (KB_06 §3; KB_03 slide 3).

### 3.2 Shared prompt rules (V1.0/V1.1 baseline; KB_06 §4)

- Evidence is limited to the original radiologist's Findings, Conclusions and Recommendations. The model must not use the CaseID, AI-generated report fields, existing labels, other cases or assumptions.
- Each condition is judged independently. Values are binary, with no Uncertain/Unknown output. Output is one JSON object with exact keys and no prose.
- Insufficient textual evidence → Negative (with the explicit note that "not mentioned" is not the same as "clinically absent").

### 3.3 Prompt version history

| Dataset | Version | What changed | Tested how | Source |
|---|---|---|---|---|
| All three | V1.0 | Baseline | Manual prompt review (baseline) | KB_06 §5 |
| All three | V1.1 | Sharper evidence thresholds, differential handling, pattern vs cause, anatomy/laterality, independence between labels | Manual review of five cases per dataset; no label changes recorded; **not** an API test or accuracy study | KB_06 §11 |
| Canine Thorax | V1.3 (3 Nov 2026) | Possible/suspected = Positive; not mentioned = Negative; recommendation alone ≠ Positive; RTM expansion; independent `diseased_lungs`; V1.3 takes precedence over older V1.1 examples | Live in Week 4 (gpt-4.1-mini), Week 5 (gpt-4.1-mini) and Week 7 (gemini-3.8-flash). File byte-identical across `src/week_04`, `src/week_05`, `src/week_07` (Verified W8, SHA-256 `31a7dab6…`) | KB_06 §10; KB_04 Table 10 |
| Feline / Abdomen | "V1.3" (Week 3) | Reported as created in Week 3; text not retrieved | **No file in the repository** | KB_06 §5, §10 |
| Feline Thorax | V1.1 (owner original) | Stored byte-for-byte; superseded | Registered `4044403` | KB_07 Table 20–21 |
| Feline Thorax | V1.2 (active) | 84 curly quotes in the JSON output example replaced with straight quotes. No clinical rule changed | Live batch 2026-11-21 | KB_07; manifest (Verified W8) |
| Canine Abdomen | V1.2 (owner original) | Stored; superseded. Uncertainty rules contradicted each other | Registered `4044403` | KB_07 |
| Canine Abdomen | V1.3 (intermediate) | Inclusive uncertainty policy applied consistently; rules renumbered | Registered `ec63636`; superseded | KB_07 |
| Canine Abdomen | V1.4 (active) | Section 4.1 item 3 only: differential-only mention → Negative unless independently established or explicitly elevated in Conclusions/Impression | Live batch 2026-11-21 | KB_07; manifest (Verified W8) |

**Version-lineage conflict (Unresolved):** KB_06 says V1.3 prompts were created for all three datasets in Week 3, yet the Week 7 registry starts Feline at V1.1 and Abdomen at V1.2 as "owner originals". No V1.2 rationale exists in the Week 3 record. See 07 §3, C-04.

**Supplied prompt files vs the prompts actually run (Week 8).**
- `files-bundle-01/Feline_Thorax_Master_Prompt_V1.1.txt` (SHA-256 `7696598e…`) and `Canine_Abdomen_Master_Prompt_V1.2.txt` (`f25b56fb…`) are byte-identical to the **superseded** owner originals in `src/week_07/prompts/`.
- The live runs used **Feline V1.2** (`9bbd36c4…`) and **Abdomen V1.4** (`9336be3f…`), per the manifest `identity.prompt` fields and the workbook Execution Logs (Matrix 1). Those exact files are in the repository (`src/week_07/prompts/feline_thorax_master_prompt_v1_2.txt`, `canine_abdomen_master_prompt_v1_4.txt`) and their hashes equal the manifest pins.
- So the run prompts are **not missing**. The supplied older files were **not** used in the runs.
- The supplied `Canine_Thorax_Master_Prompts_V1.3.docx` is the Word source and cannot be byte-compared with the pinned `.txt` (`31a7dab6…`). The `.txt` is the version recorded in the manifests.

See C-21.

### 3.4 Uncertainty policies differ across the active prompts (Observed (prior), KB_07 Table 22)

| Prompt | Treatment of possible / suspected findings |
|---|---|
| Canine Thorax V1.3 | Inclusive: explicitly possible or suspected → Positive |
| Feline Thorax V1.2 | Conservative: possible, suspected, cannot exclude, differential, rule out and similar → Negative unless confirmed |
| Canine Abdomen V1.4 | Inclusive but scoped: Positive only when named as a principal or meaningful interpretation in Conclusions/Impression *and* supported by findings |

This confounds any comparison across applications (KB_07 §7.2). The Week 3 project-wide rule (possible/suspected = Positive) was **not** carried into Feline V1.2 (see C-05).

## 4. Model inference methodology

| Run family | Provider / model | Settings | Source |
|---|---|---|---|
| Week 4 Canine Thorax | OpenAI `gpt-4.1-mini` via LangChain `ChatOpenAI` | temperature 0; timeout 90 s; LangChain `max_retries=2`; 2 application attempts; new client per case | KB_05 Table 3; KB_10 Table 11 |
| Week 5 Canine Thorax | OpenAI `gpt-4.1-mini` | Same as Week 4; one client per batch; configuration errors fail fast | KB_04 Table 10 |
| Week 7 Canine Thorax | Google `gemini-3.8-flash` via `langchain-google-genai` | temperature 0; JSON MIME type, no schema; 1 transport attempt; 2 application attempts; bounded backoff for transient errors | Manifests (Verified W8) |
| Week 7 Feline / Abdomen | OpenAI `gpt-4.1-mini` via `ChatOpenAI` | temperature 0.0; transport retries 0; no response format; timeout 90 s; 2 application attempts | Manifests (Verified W8) |

Common input boundary: the payload contains exactly the three original report fields; an empty field becomes `[Not provided]`. Labels, CaseID and AI-generated fields never reach the model (KB_07 §5.13; KB_04 §6.3; LEAK-marker tests).
Human instruction: "Classify the following {region} radiology report according to the system instructions." (Verified W8 in the Feline and Abdomen manifests.)

**Exact model snapshot identifiers** (beyond the alias strings above), API request IDs and cost were **not recorded** (KB_02 §6; KB_05 §11.2).

## 5. Evaluation methodology (KB_07 §5.14; KB_04 §7.1; KB_03 §5.5)

- Per condition: reference Positive + prediction Positive → TP; reference Positive + prediction Negative → FN; reference Negative + prediction Negative → TN; reference Negative + prediction Positive → FP.
- Accuracy = (TP+TN)/N; Sensitivity = TP/(TP+FN); Specificity = TN/(TN+FP); Precision = TP/(TP+FP); F1 = 2PS/(P+S).
- A zero denominator gives an **undefined** value, written as a blank cell and never as zero. F1 is undefined if P or S is undefined or P+S = 0.
- Micro averages sum counts across conditions. Macro averages (Matrix 1 only) are the unweighted mean of defined values. **Balanced accuracy is not computed** (it was excluded by developer decision; the delivered Week 4 Matrix 2 workbook did show 89.13%).
- Feline Thorax and Canine Abdomen: predictions are generated **once** from the Matrix 1 workbook and scored against both references. A Matrix 2 batch is refused. Before reuse, a cross-matrix check requires identical CaseIDs, order and report text (KB_07 §5.3).
- Canine Thorax: one batch **per matrix** in every week (Weeks 4, 5 and 7).

## 6. Development methodology

- **Week 4:** developer-built, script/block-based application; matrices built in separate code paths. The Matrix 2 evaluator source was never in the repository (KB_10 §5.1).
- **Week 5:** Claude Code rebuild, inspection first, with eight plan corrections and nine approval points (P1–P9). Six phases; parity via behaviour probes, side-by-side tests, real-artifact replay, cell-by-cell workbook comparison, mutation tests and network-blocked suites (KB_04 §5; KB_10 §5.4). Not autonomous: the developer corrected assumptions, ran the Windows tests and live batches, and reviewed outputs.
- **Week 7:** Claude Code sessions gated by explicit user approval; verbatim reuse of nine Week 5 modules with AST parity tests; extension by composition (KB_07 §5.1; KB_09).
- **Tooling split** (user preference, KB_02 §2): Claude Code for repository implementation; ChatGPT for review, explanation, interpretation and next-step instructions.
