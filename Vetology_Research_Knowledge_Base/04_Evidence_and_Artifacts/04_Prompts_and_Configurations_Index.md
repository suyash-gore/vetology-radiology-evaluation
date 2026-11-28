# 04 — Prompts and Configurations Index

Prompt *text* is not copied here; the files are referenced by path and hash. File SHA-256 values were **computed in Week 8** and match the registry pins recorded in KB_07 Table 20. Stripped-text hashes and character counts come from KB_07 and the manifests.

## 1. Prompt files in the repository

| Prompt | Status | Path | Bytes | File SHA-256 (Verified W8) | Stripped-text SHA-256 (manifest / KB_07) | Used by run(s) | Commit registered |
|---|---|---|---|---|---|---|---|
| Canine Thorax Master Prompt V1.3 | Active (canine_thorax) | `src/week_07/prompts/canine_thorax_master_prompt_v1_3.txt` | 8,715 | `31a7dab6e535e6f0af6a54106cf449ecadfe3644c7b3c805710309f0e85ab7b1` | `97ad5b74be0ebaa8655227e50e6fcc9cee1a96e7ba072c45ee6f822673d44d29` (8,710 chars) | RUN-00–RUN-06 | Weeks 4/5/7 |
| — Week 4 copy | Historical | `src/week_04/prompts/canine_thorax_master_prompt_v1_3.txt` | 8,715 | identical | — | RUN-00–02 | `533c73c` era |
| — Week 5 copy | Historical | `src/week_05/prompts/canine_thorax_master_prompt_v1_3.txt` | 8,715 | identical | — | RUN-03–04 | `d62470f` |
| Feline Thorax Master Prompt V1.1 | Superseded (owner original) | `src/week_07/prompts/feline_thorax_master_prompt_v1_1.txt` | 26,060 | `7696598eda2faa39ef44df3e9c260ca7870d487094df40ae6e05c4b0c2665d27` | `bf9142f7…eb103` (25,833) | none | `4044403` |
| Feline Thorax Master Prompt V1.2 | **Active** (feline_thorax) | `src/week_07/prompts/feline_thorax_master_prompt_v1_2.txt` | 25,892 | `9bbd36c4a1d9ac15cb24c39b3e9d0ad5af9106a9bddb3adf3401098e1c418f25` | `a7adb7078bc50df891f23110d6c4de9046db779b118e39201b4923f96f9c81c3` (25,833) | RUN-07 | `ec63636` |
| Canine Abdomen Master Prompt V1.2 | Superseded (owner original) | `src/week_07/prompts/canine_abdomen_master_prompt_v1_2.txt` | 17,216 | `f25b56fb0fbd2a7e697be287ef51357a8e911243523464d860eff7726a5e17aa` | `1156c72a…05402` (17,081) | none | `4044403` |
| Canine Abdomen Master Prompt V1.3 | Superseded (intermediate) | `src/week_07/prompts/canine_abdomen_master_prompt_v1_3.txt` | 17,913 | `142d8e532fcd851dda98c3982e4ece1f4561c1f844c0232dc2ef1b312e654e93` | `4a0ee63a…dd9549` (17,776) | none | `ec63636` |
| Canine Abdomen Master Prompt V1.4 | **Active** (canine_abdomen) | `src/week_07/prompts/canine_abdomen_master_prompt_v1_4.txt` | 18,133 | `9336be3fa463be14bdfd71d93e2709b4bad70c626d0533d8e4f887809b2a254c` | `d6c50d5d2e9e8dde080e7c77879cfd9c4c2ccc7fbcad96753a090803497dee91` (17,996) | RUN-08 | `65274d6` |
| Week 4 optional JSON prompt config (V1.3) | Optional; not an inference path | `src/week_04/optional_json_config/config/canine_thorax_v1_3.json` | 9,701 | `0686095c9a8df2b4750acbb1ed6ee2cf305a33ca3e5910def1af2cda782ec58b` | — | none | `bdb9952` |

Byte and character counts for the FT/CA prompts are from KB_07 Table 20. Week 8 confirmed the byte sizes with `wc -c`.

## 2. Prompt versions not in the repository

| Prompt | Where it is recorded | Status |
|---|---|---|
| Canine/Feline/Abdomen V1.0 and V1.1 (Week 3) | Full text reproduced in the KB_06 appendices, from the Week 3 Word documents | Not in repository; Word source files Inaccessible |
| Canine Thorax V1.3 Word document | KB_06 Appendix D (advisor update wording) | Text equivalent believed to be the `.txt` above; not verified |
| Feline / Abdomen "V1.3" (Week 3, 3 Nov 2026) | KB_06 §5, §10 says they were created | **Missing**; relation to the registry V1.1/V1.2 is unresolved (C-04) |
| Canine Thorax V1.4 | — | Never created (iteration paused; KB_05 §5.1) |

## 3. Change rationale (active lineage)

| Change | Nature | Approved | Commit | Source |
|---|---|---|---|---|
| CT V1.1 → V1.3 | Clinical: global possible/suspected = Positive; RTM; independent diseased_lungs | Advisor-informed (user-reported) | pre-Week 4 | KB_06 §10 |
| FT V1.1 → V1.2 | **Syntax only:** 84 curly quotes in the JSON example → straight quotes; header label | User | `ec63636` | KB_07 T21 |
| CA V1.2 → V1.3 | Clinical: inclusive uncertainty policy applied consistently; renumbering | User | `ec63636` | KB_07 T21 |
| CA V1.3 → V1.4 | Clinical: Section 4.1 item 3 (a differential-only mention → Negative unless independently established or elevated) | User | `65274d6` | KB_07 T21 |

KB_02 §16.1 and KB_07 §13 both stress keeping syntax fixes separate from changes to clinical rules.

## 4. Model and runtime configurations

| Configuration | Week 4 | Week 5 | Week 7 CT (Gemini) | Week 7 FT / CA (OpenAI) |
|---|---|---|---|---|
| Model string | gpt-4.1-mini | gpt-4.1-mini | gemini-3.8-flash | gpt-4.1-mini |
| Exact snapshot ID | not recorded | not recorded | not recorded | not recorded |
| Temperature | 0 | 0 | 0.0 | 0.0 |
| Timeout | 90 s | 90 s | 90 s | 90 s |
| Transport retries | LangChain max_retries 2 | 2 | 1 attempt (max_retries=1 passed) | max_retries 0 |
| Application attempts | 2, no backoff | 2, no backoff | 2; backoff 2 s × 2ⁿ ≤ 30 s for 408/429/500/502/503/504 and network errors; fatal 400/401/403/404 | same |
| Response format | none | none | JSON MIME, no schema | none |
| Environment variables | OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_TIMEOUT_SECONDS, OPENAI_MAX_RETRIES | same | GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_TIMEOUT_SECONDS (GEMINI_MAX_RETRIES refused) | OPENAI_* (OPENAI_MAX_RETRIES ignored) |
| Evidence | KB_05 T3 | KB_04 T10 | Manifests (Verified W8); KB_08 | Manifests (Verified W8); KB_07 |

The names of the variables come from the sources and `.env.example`. **No values were read or copied.** `.env.example` is hashed in the inventory (EV-D08); `.env` is gitignored and was not accessed.

## 5. Dependency record

`requirements.txt` (EV-D07, sha `24f9b5b6…1dea`) per KB_07 T19, KB_08, KB_10 T10:
- openpyxl 3.1.5
- langchain-openai 1.7.2
- openai 3.49.0
- langchain-core 1.7.7
- httpx 0.28.1
- langchain-google-genai 4.4.2
- google-genai 2.31.0
- python-dotenv 1.2.4
- flake8 7.4.1

Known issues:
- certifi 2026.10.18 is below langchain-core's requirement (KB_07; not changed).
- httpx2 is imported by tests but not pinned (KB_08 D-08).
- Code docstrings cite google-genai 2.34.0 (C-17).
