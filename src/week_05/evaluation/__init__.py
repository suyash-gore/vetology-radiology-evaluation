"""Evaluation of LLM predictions against a workflow's reference labels.

* ``metrics``         — pure confusion-matrix and metric calculations (shared).
* ``reconcile``       — loads predictions JSONL and aligns it with reference labels.
* ``matrix1_workbook``— Matrix 1 workbook (replicates the Week 4 Matrix 1 evaluator).
* ``evaluate``        — workflow-level entry point.

The Matrix 2 workbook layout is intentionally not implemented until
``Evaluation Workbook v2.xlsx`` has been inspected.
"""
