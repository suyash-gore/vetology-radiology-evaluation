# 07 — Source Crosswalk and Verification Register

Trace chain for each important claim:
**(1) source extraction → (2) repository file or commit → (3) evaluation artifact or run manifest.**
"—" means no such link exists. EV-IDs refer to `../04_Evidence_and_Artifacts/01_Evidence_Inventory.csv`.

**Week 8 reconciliation note.** Columns (1)–(3) keep the evidence picture as recorded at `ea92818`; for example, "Inaccessible" there means unavailable at that time. The **last column is the current status** after verification against `files-bundle-01.zip` (bundle rows EV-B01–EV-B42).

## 1. Topic-to-source crosswalk

| Topic | ChatGPT sources | Claude sources | Repository anchor |
|---|---|---|---|
| Paper requirements | KB_01 (primary), KB_03 §12 | — | — (webpage not in repository) |
| Week 3 prompt engineering | KB_06 | — | `src/week_04/prompts/canine_thorax_master_prompt_v1_3.txt` (V1.3 only) |
| Week 4 application and results | KB_05, KB_04 §3–4, KB_03 §6.1 | KB_10 §5.1, §8.1 | `src/week_04/`; commits `533c73c`, `bdb9952`; `docs/testing_log.md` |
| Week 5 rebuild and parity | KB_04, KB_03 §7 | KB_10, KB_09 §11 | `src/week_05/`; commits `d62470f`–`f20c240`; tag `week-05-closeout` |
| Week 6 presentation | KB_03 | — | — (presentation files not in repository) |
| Week 7 Gemini | KB_02 §11.2 (brief) | KB_08, KB_09, KB_07 §8.1 | `src/week_07/`; `67f133c`; `outputs/week_07/matrix_1|2/run_manifest.json` |
| Week 7 FT/CA extension | KB_02 (primary for results) | KB_07 (primary for implementation), KB_09 §5.8 | `92a2d3d`–`ceb3f42`; FT/CA manifests; prompt files |
| Architecture | — | KB_09 (primary), KB_07 §5 | `src/week_07/` |
| Documentation accuracy | — | KB_08 (primary), KB_07 §17.2, KB_10 §17.2 | `README.md`, `docs/*.md` |

## 2. Claim verification register (key quantitative and methodological claims)

| # | Claim | (1) Sources | (2) Repository | (3) Artifact / manifest | Week 8 status |
|---|---|---|---|---|---|
| V-01 | CT Week 4 M1 counts 128/921/913/38 | KB_05, KB_04, KB_03, KB_07, KB_10 | `docs/testing_log.md`, `docs/project_documentation.md` L257 | Delivered workbook A5 (Inaccessible; replay Observed (prior) by KB_10) | **Verified against workbook + cross-checked against predictions (W8 reconciliation)**; `Week 4 … Confusion Matrix 1.xlsx` Overall Summary B6:B14 |
| V-02 | CT Week 4 M2 counts 127/31/1,803/39 | same | `docs/testing_log.md` L110 | A6 (Inaccessible) | **Verified against workbook + cross-checked against predictions (W8 reconciliation)**; F1 = 78.40% displayed (B7 = 0.78395); C-02 resolved |
| V-03 | Week 5 reproduced both Week 4 matrices exactly | KB_04, KB_03, KB_10 | `docs/testing_log.md` (Week 5 section); tests `src/week_05/tests/test_baseline_artifacts.py` | Week 4 baseline artifacts A1–A6 (gitignored `data/`; Inaccessible) | Observed (prior); consistent with the verified EVAL-01/02 counts |
| V-04 | CT Week 5 live M1 126/923/916/35; M2 126/32/1,806/36 | KB_04, KB_03, KB_07, KB_08, KB_10 | `docs/project_documentation.md` §11.6 | `outputs/week_05/…` (Inaccessible) | **Verified against workbook + cross-checked against predictions (W8 reconciliation)**; `outputs/week_05/matrix_1|2/…` |
| V-05 | CT Week 7 Gemini M1 96/953/924/27; M2 102/56/1,822/20 | KB_07, KB_08, KB_09, KB_10 | `README.md`, `docs/CHANGELOG.md` L185–186, `docs/testing_log.md` | Batches: EV-R01, EV-R02 manifests (**Verified W8**); workbooks Inaccessible | **Verified against workbook + cross-checked against predictions (W8 reconciliation)**; batches supported by manifest |
| V-06 | Gemini–OpenAI agreement 1,940 and 1,944 of 2,000 | KB_07, KB_08, KB_09 | `docs/testing_log.md` L208–209 | Comparison workbooks (Inaccessible) | **Verified against comparison workbooks + recomputed from prediction files (W8)** |
| V-07 | FT M1 29/505/1,529/37; M2 58/59/1,975/8 | **KB_02 only** | **None** (repository docs say not executed) | Workbooks Inaccessible; batch EV-R03 **Verified W8** | **Verified against workbook + cross-checked against predictions (W8 reconciliation)**; supported by manifest; **C-01 resolved** |
| V-08 | CA M1 34/246/697/23; M2 53/28/915/4 | **KB_02 only** | **None** | Workbooks Inaccessible; batch EV-R04 **Verified W8** | **Verified against workbook + cross-checked against predictions (W8 reconciliation)**; supported by manifest; **C-01 resolved** |
| V-09 | FT/CA batches 100/100, 0 failures, gpt-4.1-mini, temp 0, V1.2/V1.4 | KB_07, KB_02 (FT), KB_09, KB_10 | commit `ceb3f42` | EV-R03, EV-R04 | **Verified W8** |
| V-10 | FT/CA manifest SHA-256 values (`d56ce43d…6175`, `05e4fa5c…bc3d`) | KB_02 T14 | — | EV-R03, EV-R04 | **Verified W8** (KB_02 T18 has a typo in the FT value; see C-13) |
| V-11 | FT/CA input workbook SHA-256 (`ef8fcc97…`, `583e7523…`) and Gold Standard SHA-256 (`c01a6e4b…`, `95e053a4…`) | KB_02 T14, KB_07 T28 | — | Input digests are in the manifests (**Verified W8**); Gold Standard digests only in sources (Recorded) | **Verified (W8)**: all four workbook hashes equal the supplied bundle files |
| V-12 | FT/CA prediction file SHA-256 (`c1038853…`, `61e151c4…`) | KB_02 T14 | — | Files Inaccessible | **Verified (W8)**: bundle prediction files hash to `c1038853…` and `61e151c4…` |
| V-13 | Prompt digests for all six registered prompts | KB_07 T20, KB_02 T17 | `src/week_07/prompts/*.txt` | Manifest prompt identity | **Verified W8** (file SHA-256) |
| V-14 | CT V1.3 prompt byte-identical across Weeks 4/5/7 | KB_04, KB_08, KB_10 | Three prompt files | Manifests | **Verified W8** |
| V-15 | Reference prevalence FT 534/117, CA 280/81 | KB_07 T26–27 (Observed (prior)); KB_02 §9.1 | — | Uploaded workbooks (Inaccessible) | **Verified (W8)** from the workbook Ground Truth columns and source workbooks |
| V-16 | 8 of 2,000 run-to-run differences (Week 4) | KB_07, KB_04, KB_03, KB_10 | `docs/testing_log.md` L120 | A3 vs A4 (Inaccessible) | **Cross-checked against prediction records (W8)**: 8 pairs / 6 cases |
| V-17 | Gemini M2: three failed 1-case trials before success | KB_07, KB_08, KB_09 | — | EV-R02 (5 runs) | **Verified W8** |
| V-18 | Only three report fields reach the model | KB_02, KB_04, KB_05, KB_07, KB_09 | `dataset_loader.ReportCase.to_llm_payload`, `llm_client.validate_payload` | Manifest `llm_input_fields` (3 entries) | Manifest **Verified W8**; code Observed (prior) |
| V-19 | Test-suite counts | KB_03, KB_04, KB_07, KB_08, KB_09, KB_10 | `docs/testing_log.md` | — | Recorded / Observed (prior); not re-run in Week 8 |
| V-20 | Tag `week-05-closeout` → `a938cde` | KB_04, KB_08, KB_10 (KB_07 names tag object `f87a766`) | Git | — | **Verified W8**: tag object `f87a766` → commit `a938cde` |
| V-21 | `main` lacks Weeks 5/7 | KB_07, KB_08, KB_09, KB_10 | `origin/main` = `4031615` | — | Verified W8 (ref present; content per sources) |
| V-22 | Gold Standard is peer-reviewed and agreed upon after discussion | Owner clarification in the Week 8 reconciliation instruction (2026-11-28) | — | — | **Owner clarification**; supersedes KB_05 §8.1 |
| V-23 | Per-condition counts and metrics for all 10 reference evaluations | KB_02 T12 (CA partial) | — | `../04_Evidence_and_Artifacts/06_Per_Condition_Results.md` (from bundle workbooks, Condition Summary sheets) | **Verified + cross-checked (W8)**; the KB_02 T12 values all match |
| V-24 | Run-to-run variation: Week 5 11/2,000, Week 7 Gemini 13/2,000 | — | — | Bundle prediction files | **Cross-checked against prediction records (W8)**; new |
| V-25 | Matrix 1 "GS" wording is legacy terminology; the reference is the Vetology encoded workbook | KB_09 TD13 | D-041; `src/week_07/evaluation/matrix1_workbook.py` L22; `reference_loader.py` `load_matrix1_reference` | Workbook Execution Log B3 (`Ground-truth workbook`); prevalence 1,049/534/280 | **Verified (W8)**; C-23 |
| V-26 | Run prompts were FT V1.2 and CA V1.4, not the supplied V1.1 / V1.2 files | KB_07 T20 | `src/week_07/prompts/*` | Manifest `identity.prompt`; Matrix 1 workbook Execution Log B13 | **Verified (W8)**; C-21 |

## 3. Contradiction and discrepancy register

Nothing here was silently resolved. "Week 8 note" gives evidence gathered in this session, not a ruling.

| ID | Topic | Position A (source) | Position B (source) | Week 8 note | Severity |
|---|---|---|---|---|---|
| C-01 | Existence of FT/CA evaluation results | Evaluations completed; full aggregate metrics and workbook paths given (KB_02 §4, §9, T19) | No FT/CA metrics anywhere in the repository; whether `evaluate` was run is unknown (KB_07 §8.2, §17.2 #2; KB_08 §16.2; KB_09 §8.2; KB_10 T29) | Repository docs still say live runs were not executed (`README.md` L9, L16–17; `docs/testing_log.md` L358, L384) while the manifests show completed batches. KB_02 counts are internally consistent and match KB_07's observed prevalence. Workbooks remain inaccessible | **Resolved (W8 reconciliation)**: the actual workbooks contain exactly the KB_02 values, and those values are reproduced from the predictions. Repository docs remain stale (C-14) |
| C-02 | CT Week 4 M2 F1 | 78.39% (KB_05, KB_04, KB_03, quoting the Week 4 report) | 78.40% (KB_07, KB_10; delivered workbook; `docs/testing_log.md`, `README.md`) | Derived 254/324 = 78.3951% → 78.40% at 2 d.p. | **Resolved (W8)**: workbook stores 0.7839506 (displayed 78.40%); 78.39% is the Week 4 report's truncated derived value |
| C-03 | Nature of the Gold Standard | Peer-agreed, not expert ground truth (KB_01 Vetology requirement; KB_03 §5.4; KB_02 §10.1) | Assigned by a veterinary radiologist (user statement, KB_05 §8.1) | **Resolved by owner clarification (Week 8 reconciliation instruction, 2026-11-28): "The Gold Standard dataset is peer-reviewed and agreed upon after discussion."** Use this wording consistently. It is distinct from formal independent expert adjudication. No direct evidence supports the KB_05 claim, which is retained as historical only. Participants, procedure and the 21-difference resolution remain undocumented | Resolved (wording); procedure detail Missing |
| C-04 | Feline/Abdomen prompt version lineage | V1.3 created for all three datasets in Week 3 (KB_06 §5, §10) | Registry starts FT at V1.1 and CA at V1.2 as "owner originals" (KB_07 T20–21) | Repository contains no FT/CA "V1.3 (Week 3)" file; CA V1.3 in the registry is a Week 7 intermediate | Medium (W8: the supplied bundle has no FT/CA V1.3 file either; the supplied FT V1.1 and CA V1.2 files equal the registry originals) |
| C-05 | Uncertainty rule | Project-wide V1.3: possible/suspected → Positive (KB_06 §8, §10) | FT V1.2 conservative (→ Negative); CA V1.4 positive only in the primary impression (KB_07 T22; KB_02 §7.1) | Active prompts were not inspected for clinical content in Week 8 | Medium (confounds comparison) |
| C-06 | CA batch success evidence | Batch log missing; do not infer 100 successes (KB_02 §8.2) | Manifest shows 100/100 (KB_07 T25) | **Manifest Verified W8**; gap closed for the batch summary | Resolved |
| C-07 | Week 7 Gemini test counts | 288: 282 passed, 6 skipped (Windows; KB_08, testing_log) | 288 OK, 5 skipped (Linux; KB_07, KB_09) | Environmental (Windows-only symlink skip) | Low |
| C-08 | Week 5 test counts | 338/338, 0 skipped (KB_03, KB_04; Linux with artifacts) | 338 OK, 9 skipped (KB_07; export without artifacts) | KB_10 T15 shows both conditions | Low |
| C-09 | Extension test counts | 504 (499 passed, 5 skipped) claimed (commit `65274d6`) | 504 OK, 6 skipped (KB_07 export); 455 run + 2 import errors without `openai` (KB_09) | Environmental | Low |
| C-10 | `week-05-closeout` tag identity | `f87a766` "tag object; points into this lineage" (KB_07) | → `a938cde` (KB_04, KB_08, KB_10); local unpushed tag object `8ee459a` (KB_10) | Verified W8: `f87a766` → `a938cde` | Resolved |
| C-11 | Code size | ~2,100 / ~7,600 (KB_03) | ~7,560 (KB_04); 2,096 / 7,556 (KB_10, KB_09) | Rounding | Low |
| C-12 | Description of the "two Week 4 runs" | "Two Week 4 runs differed on 8/2,000" (KB_04, KB_03) | These are the Matrix 1 (A3) and Matrix 2 (A4) prediction files, separate runs over identical report text (KB_10; `docs/testing_log.md` L120) | Clarify wording in the paper | Low |
| C-13 | FT manifest SHA-256 | `d56ce43d…0fca27366…6175` (KB_02 T14) | `d56ce43d…0fa27366…6175` (KB_02 T18) | Verified W8: `d56ce43d4965ce98b156c253c0fca27366dbddac1109274c88e779d389fd6175` (T14 correct) | Resolved (typo) |
| C-14 | Repository documentation vs manifests (FT/CA) | Live runs "to be executed locally" (`README.md`, CHANGELOG, testing_log, project_documentation §18) | Completed 100/100 (manifests `ceb3f42`) | Verified W8 | High (stale docs) |
| C-15 | Gemini M2 run history completeness | Docs: "zero unresolved final failures" (KB_08) | Manifest: three failed 1-case trials, then 1-case success, then 100-case run (99 succeeded, 1 skipped) | Verified W8 | Low |
| C-16 | Week 5 Matrix 1 "0 failed" | Week 5 records: 0 failed | `errors.jsonl` has 100 superseded attempt records (KB_08 D-05; KB_04 §7.4) | Not a contradiction in final outcomes; a wording issue | Low |
| C-17 | `google-genai` version | 2.31.0 pinned and executed (requirements, manifests) | Code docstrings cite verification against 2.34.0 | Manifests Verified W8 at 2.31.0 | Low |
| C-18 | CHANGELOG / D-043 "forced LF override removed" | Claimed in docs | No committed version ever forced LF (KB_04 §9.3; KB_10 T25 #1) | Not re-inspected in Week 8 | Low |
| C-19 | Number of Claude source documents | Six planned (task instruction) | Four supplied (KB_07–KB_10) | Missing two not fabricated; companion documents referenced but absent | Medium |
| C-20 | Week 3 vs Week 4–7 dataset filenames | `*_scoring_data.xlsx` (KB_06) | `*_raw_data_encoded.xlsx`, `*_gold_standard_score_draft.xlsx`, `Vetology_Matrix1_First100_Encoded.xlsx` (manifests) | Relationship undocumented | Low |
| C-21 | Prompt files supplied vs run prompts | Bundle supplies `Feline_Thorax_Master_Prompt_V1.1.txt` and `Canine_Abdomen_Master_Prompt_V1.2.txt` (and CT V1.3 `.docx`) | Manifests pin FT V1.2 (`9bbd36c4…`) and CA V1.4 (`9336be3f…`); CT V1.3 `.txt` (`31a7dab6…`) | Supplied FT/CA files equal the **superseded** registry files and were **not** used in the runs. The exact run prompts are present in `src/week_07/prompts/` with matching hashes, so they are not missing. The CT `.docx` cannot be byte-compared | Resolved (documented) |
| C-22 | Week 5 Matrix 1 error log | "100 superseded failures" (KB_08; comparison workbook Execution Log C18) | Actual records: 100 × HTTP 401 (expired API key) at 09:54–09:55 UTC, before the successful batch at 09:57 UTC | Consistent: superseded, 0 final failures. The cause is now documented. Error text contains no key value | Resolved (W8) |
| C-23 | Matrix 1 "GS Positive / GS Negative" terminology | Matrix 1 workbooks call the Vetology labels "Gold Standard" / "GS" | Matrix 1 is defined as the original Vetology reference labels | Terminology only: the Execution Log names the Vetology encoded workbook; prevalence equals that workbook; D-041 preserves the wording. No reference-source ambiguity. Matrix 1 definition unchanged | Resolved (W8) |
| C-24 | CT Matrix 1 input filename | Manifest / Execution Log: `Vetology_Matrix1_First100_Encoded.xlsx` (A5 log: `…(1).xlsx`) | Bundle: `Vetology_Matrix1_First100Raw_EncodedPositveNegative_Canine_Thorax_Records.xlsx` | Same SHA-256 `3f1a17b7…`, so it is the same file renamed | Resolved (W8) |
| C-25 | Two Week 4 Matrix 1 workbooks | Delivered A5 (`Week 4 … Confusion Matrix 1.xlsx`, generated 05:46:24 UTC) | `outputs/week_04/matrix_1/matrix1_evaluation_workbook.xlsx` (06:02:57 UTC) | Identical counts, micro and macro metrics; presentation text differs (cf. KB_10 "A5 differs from committed evaluator") | Low; not separate experiments |

## 4. Coverage check

| Requested consolidation element | Location |
|---|---|
| Confirmed requirements vs recommendations | 01 §1–§2 |
| Observed / recorded / derived / proposed / planned / rejected / unresolved | Vocabulary in 00 §3; applied throughout |
| Source disagreements and their provenance | §3 above |
| Demonstrated capability vs product potential | 06 §2–§3 |
| Provisional novelty | 06 §1 |


## 5. Manuscript evidence map (draft v0.1)

| Manuscript element | Evidence | Status |
|---|---|---|
| Table 1 (datasets, prevalence) | `04_Evidence_and_Artifacts/03_…Register.md`; `06_Per_Condition_Results.md` | Verified against workbooks |
| Table 2 (runs, configurations) | `02_Experimental_Run_Register.md`; `04_Prompts_and_Configurations_Index.md` | Verified (manifests for Week 7) |
| Table 3 (counts, micro metrics, CIs) | `03_…Register.md`; `07_Statistical_Analysis_Results.md` §1 | Counts verified; CIs computed by `analysis/week08_statistics.py` |
| Table 4 (paired M2 − M1; reference κ) | `07_…Results.md` §3, §4, §7 | Computed (FT, CA paired; CT exploratory rescoring) |
| Table 5 (condition-level) | `07_…Results.md` §8 | Computed |
| Table 6 (CT model comparison) | `07_…Results.md` §5; AGR-01/02 | Computed; exploratory tests |
| Table 7 (run-to-run) | `07_…Results.md` §6 | Computed |
| Prompt-development overlap and CA heuristic | `05_…` §4 L-W8-1, L-W8-2 | Developer clarification; heuristic provenance unresolved |
| Literature citations | `09_Literature_Evidence_Matrix.md` §2 (L01–L11) | Verification level per item; L07 and L11 metadata only |
| C-26 *(new)* | KB_07 §8.5 records a reference-label keyword heuristic; the developer does not recall reference-label use | **Conflicting / unresolved** |
