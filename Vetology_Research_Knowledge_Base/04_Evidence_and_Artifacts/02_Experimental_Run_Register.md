# 02 — Experimental Run Register

A **run** is one live prediction batch, the only stage that calls a model. Evaluations of runs are in `03_Confusion_Matrix_and_Metrics_Register.md`. Run IDs are assigned by this knowledge base; the repository has no run IDs. Manifests exist only from Week 7 onward.

## Summary

| Run ID | Dataset | Workflow | Model (identifier as recorded) | Prompt | Date (UTC) | Cases | Outcome | Manifest | Status |
|---|---|---|---|---|---|---|---|---|---|
| RUN-00 | Canine Thorax | Matrix 1 single-case test | gpt-4.1-mini (record field) | V1.3 (record field) | Week 4 | 1 | status success (record); HTTP 200 (KB_05) | `outputs/week_04/matrix_1/single_case_test.json` (EV-R05) | Verified (W8) present; not a metric run |
| RUN-01 | Canine Thorax | Matrix 2 batch (Week 4) | gpt-4.1-mini | V1.3 | 2026-11-03 14:51–14:55 | 100 | 100 succeeded; 1 case needed a second attempt | None (predictions A4, sha `70fe9391…`) | Observed (prior) KB_10; Recorded KB_04 |
| RUN-02 | Canine Thorax | Matrix 1 batch (Week 4) | gpt-4.1-mini | V1.3 | 2026-11-07 05:29–05:32 (10:59–11:02 local) | 100 | 100 × HTTP 200; 0 retries / failures / skips | None (predictions A3, sha `78814024…`) | Observed (prior) KB_10; Recorded KB_05 |
| RUN-03 | Canine Thorax | Matrix 1 live (Week 5) | gpt-4.1-mini | V1.3 | 2026-11-12 | 100 | 100 succeeded, 0 failed; `errors.jsonl` holds 100 superseded attempt lines | None | Recorded (KB_04 T14; commit `f20c240`) |
| RUN-04 | Canine Thorax | Matrix 2 live (Week 5) | gpt-4.1-mini | V1.3 | 2026-11-12 | 100 | 100 succeeded, 0 failed | None | Recorded |
| RUN-05 | Canine Thorax | Matrix 1 (Week 7) | gemini-3.8-flash | V1.3 | 2026-11-20 16:41:45–17:02:06 | 100 | 100 succeeded, 0 failed, 0 backoffs | `outputs/week_07/matrix_1/run_manifest.json` (EV-R01) | **Verified (W8)** |
| RUN-06a–c | Canine Thorax | Matrix 2 (Week 7) trial runs | gemini-3.8-flash | V1.3 | 2026-11-20 15:00, 15:18, 15:27 | 1 each | Each: 0 succeeded, 1 failed, 1 transient backoff | `outputs/week_07/matrix_2/run_manifest.json` runs[0–2] (EV-R02) | **Verified (W8)**; error text Inaccessible |
| RUN-06d | Canine Thorax | Matrix 2 (Week 7) trial | gemini-3.8-flash | V1.3 | 2026-11-20 16:12:36–16:12:52 | 1 | 1 succeeded | runs[3] | **Verified (W8)** |
| RUN-06 | Canine Thorax | Matrix 2 (Week 7) main run | gemini-3.8-flash | V1.3 | 2026-11-20 16:16:36–16:35:50 | 100 selected | 99 succeeded, 1 skipped (already checkpointed by RUN-06d), 0 failed, 1 backoff → 100 final predictions | runs[4] | **Verified (W8)** |
| RUN-07 | Feline Thorax | Shared batch from Matrix 1 (reused by Matrix 2) | gpt-4.1-mini | V1.2 | 2026-11-21 16:22:06–16:26:24 | 100 | 100 succeeded, 0 failed / skipped / backoffs | `outputs/week_07/feline_thorax/predictions/run_manifest.json` (EV-R03) | **Verified (W8)** |
| RUN-08 | Canine Abdomen | Shared batch from Matrix 1 (reused by Matrix 2) | gpt-4.1-mini | V1.4 | 2026-11-21 16:42:21–16:44:40 | 100 | 100 succeeded, 0 failed / skipped / backoffs | `outputs/week_07/canine_abdomen/predictions/run_manifest.json` (EV-R04) | **Verified (W8)** |

Counts: **8 identifiable 100-case prediction batches** (RUN-01 to RUN-08). Also recorded: one Week 4 single-case test (RUN-00) and four 1-case Gemini Matrix 2 trial runs (RUN-06a–d) inside the RUN-06 manifest.

Not runs:
- Week 3 V1.0/V1.1 manual prompt reviews: no API calls (KB_06 §11.4).
- Week 5 parity replays: no model call; Week 4 predictions were re-evaluated (EVAL-03/04).
- The offline fake-classifier end-to-end run on real FT/CA workbooks (KB_07 §8.6).

## Manifest details (Verified W8)

| Field | RUN-05 | RUN-06 | RUN-07 | RUN-08 |
|---|---|---|---|---|
| Manifest SHA-256 | `9ca8f2ad6ad5a20175dc2dc3ac926a6ce6aa345d2812be6eba73942637841d57` | `706a42be49b4a1505b794a76ce62b6ed3576419f847f9d1dd22fbb080df9abde` | `d56ce43d4965ce98b156c253c0fca27366dbddac1109274c88e779d389fd6175` | `05e4fa5ceabf11ef3c215f6c1ef6e5810a4be5071be70dd65d6ea47fef8ebc3d` |
| Commit | `67f133c` | `67f133c` | `ceb3f42` | `ceb3f42` |
| Provider | Google Gemini via langchain-google-genai ChatGoogleGenerativeAI | same | OpenAI via langchain-openai ChatOpenAI | same |
| Model | gemini-3.8-flash | gemini-3.8-flash | gpt-4.1-mini | gpt-4.1-mini |
| Temperature | 0.0 | 0.0 | 0.0 | 0.0 |
| Response mode | application/json, schema none | same | response_format none | none |
| Transport / application attempts | 1 / 2 | 1 / 2 | 1 (max_retries 0) / 2 | 1 / 2 |
| Timeout | 90 s | 90 s | 90 s | 90 s |
| Prompt | Canine Thorax V1.3; file `31a7dab6…7ab7b1`; text `97ad5b74…3d44d29` | same | Feline Thorax V1.2; file `9bbd36c4…1c418f25`; text `a7adb707…6f9c81c3` | Canine Abdomen V1.4; file `9336be3f…7b2a254c`; text `d6c50d5d…497dee91` |
| Input workbook | Vetology_Matrix1_First100_Encoded.xlsx, `3f1a17b7046b2e1ff7e7d857e24b2f421f56392040a624b90836818b1176ef25` | 1_canine_thorax_gold_standard_score_draft.xlsx, `d1fab50ee938f0608d7487f87e6650a28846cc5253dd6f170dce3fa990896fa4` | 2_feline_thorax_raw_data_encoded.xlsx, `ef8fcc979132b59d26f37ecae04c2331ad97b37247d123e72556a655a3815516` | 3_canine_abdomen_raw_data_encoded.xlsx, `583e7523abb30794cdabe745820a27c896ff0d8ddab5803c54511b8b747a5efe` |
| Condition keys | (20, per KB) | (20) | 21 | 10 |
| Label normalisation | — | — | pulmonary_nodules, esophagitis, pneumonia (Normal→Negative, Abnormal→Positive) | none |
| LLM input fields | 3 | 3 | 3 | 3 |
| Python / key packages | 3.14.6; langchain-google-genai 4.4.2; google-genai 2.31.0; langchain-core 1.7.7; httpx 0.28.1; openpyxl 3.1.5 | same | 3.14.6; langchain-openai 1.7.2; openai 3.49.0; langchain-core 1.7.7; httpx 0.28.1; openpyxl 3.1.5 | same |
| Metrics in manifest | None | None | None | None |

**Manifests record batch provenance and outcomes only. None contains evaluation metrics.** That FT/CA prediction batches completed (RUN-07, RUN-08) is verified. That their evaluations completed is **not** verified (see EVAL-11 to EVAL-14).
