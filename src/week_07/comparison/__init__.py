"""Offline comparison of Week 5 OpenAI and Week 7 Gemini predictions (Phase 4).

* ``sources``   — read-only prediction sources with provenance (SHA-256, run
  manifest) and transparent error-log reconciliation (superseded vs unresolved).
* ``agreement`` — pure calculations: model-vs-model agreement and, separately,
  correctness against the reference labels; metric differences.

Rules: Matrix 1 is only ever compared with Matrix 1, and Matrix 2 with Matrix 2;
no API request is made and no model client is imported; every source file is
read-only and SHA-256-checked; nothing is silently excluded.
"""
