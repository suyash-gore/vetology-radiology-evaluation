"""Evaluation of Week 7 Gemini predictions against a workflow's reference labels.

* ``metrics``          — confusion-matrix metrics (verbatim Week 5 copy).
* ``reconcile``        — strict predictions loader and CaseID alignment (verbatim copy).
* ``reference_loader`` — per-workflow evaluation reference loaders (verbatim copy).
* ``workbook_compare`` — cell-by-cell workbook comparison (verbatim copy).
* ``matrix1_workbook`` — Matrix 1 workbook; Week 5 layout, model record parameterised.
* ``matrix2_workbook`` — Matrix 2 workbook; Week 5 layout, Week 7 title and model note.
* ``evaluate``         — workflow-level entry point with Week 7 isolation guards.

Matrix 1 (Vetology reference labels) and Matrix 2 (Gold Standard reference
labels) are always evaluated separately. The OpenAI vs Gemini comparison is a
separate component (not part of this package).
"""
