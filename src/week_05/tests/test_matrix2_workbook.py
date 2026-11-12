"""Offline tests for the Matrix 2 workbook (A6 structure) using synthetic data."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from week_05.conditions import CONDITION_KEYS
from week_05.config import MATRIX1, MATRIX2
from week_05.evaluation.evaluate import compute_evaluation
from week_05.evaluation.matrix2_workbook import (
    FAILURE_COUNT_SOURCE,
    build_matrix2_workbook,
)
from week_05.evaluation.reconcile import reconcile
from week_05.tests.test_evaluation import (
    PARTIAL_LINE,
    as_reference,
    random_predictions,
    record_line,
    reference_for,
)

P, N = "Positive", "Negative"
SHEETS = ["Overall Summary", "Condition Summary", "Case Predictions", "Confusion Matrix",
          "Execution Log"]


class Matrix2TestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def build(self, reference, predictions, *, attempts=None, before=()):
        attempts = attempts or {}
        lines = list(before)
        for case_id, labels in predictions.items():
            record = json.loads(record_line(case_id, labels))
            record["attempts"] = attempts.get(case_id, 1)
            lines.append(json.dumps(record))
        path = self.dir / "predictions.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        labels = reconcile(MATRIX2, as_reference(reference, "gold.xlsx"), path)
        result = compute_evaluation(labels)
        out = build_matrix2_workbook(labels, result.per_condition, result.micro,
                                     self.dir / "m2.xlsx")
        return load_workbook(out), result

    def rows(self, sheet):
        return [[c.value for c in row] for row in sheet.iter_rows()]


class TestStructure(Matrix2TestCase):
    def setUp(self):
        super().setUp()
        self.ids = list(range(1, 101))
        self.wb, self.result = self.build(reference_for(self.ids),
                                          random_predictions(self.ids, seed=11))

    def test_sheets_and_no_metric_definitions(self):
        self.assertEqual(self.wb.sheetnames, SHEETS)

    def test_no_balanced_accuracy_or_macro_anywhere(self):
        for sheet in self.wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for value in row:
                    if isinstance(value, str):
                        self.assertNotIn("Balanced", value)
                        self.assertNotIn("Macro", value)

    def test_overall_summary_layout(self):
        sheet = self.wb["Overall Summary"]
        self.assertEqual(sheet["A1"].value, "VETOLOGY WEEK 4 - OVERALL EVALUATION SUMMARY")
        self.assertEqual([str(r) for r in sheet.merged_cells.ranges], ["A1:D1"])
        self.assertEqual([sheet.cell(r, 1).value for r in range(2, 9)], [
            "Metric", "Accuracy", "Sensitivity (Recall)", "Specificity",
            "Precision (Positive Predictive Value)", "F1 Score", None])
        self.assertEqual(sheet["A9"].value, "Evaluation Counts")
        self.assertEqual(sheet["A18"].value, "Dataset / Scope")
        micro = self.result.micro
        self.assertEqual([sheet.cell(r, 2).value for r in range(10, 17)],
                         [micro.tp, micro.fn, micro.tn, micro.fp, micro.total,
                          micro.positive_gt, micro.negative_gt])
        self.assertEqual([sheet.cell(r, 2).number_format for r in range(3, 8)], ["0.00%"] * 5)
        self.assertEqual(sheet.freeze_panes, "A3")

    def test_condition_summary(self):
        sheet = self.wb["Condition Summary"]
        self.assertEqual(sheet["M1"].value, "F1 Score")
        self.assertEqual([sheet.cell(r, 1).value for r in range(2, 23)],
                         [*CONDITION_KEYS, "MICRO TOTAL"])
        self.assertEqual(sheet["B22"].value, self.result.micro.tp)
        self.assertEqual(sheet["B22"].border.top.style, "medium")
        self.assertEqual(sheet["B2"].fill.fgColor.rgb, "00F7FAFC")      # banded rows
        self.assertEqual(sheet["B3"].fill.fill_type, None)
        self.assertEqual(sheet.auto_filter.ref, "A1:M22")

    def test_confusion_matrix_week2_template_columns(self):
        sheet = self.wb["Confusion Matrix"]
        self.assertEqual([c.value for c in sheet[1]][10:], [
            "Ground Truth Check", None, "Radiologist Agreement Rate", None])
        for r in range(2, 22):
            self.assertEqual(sheet.cell(r, 11).value, 100)
            self.assertEqual(sheet.cell(r, 13).value,
                             "N/A - no separate radiologist-agreement reference supplied")
        self.assertEqual(sheet["A22"].value, "TOTAL")
        self.assertEqual(sheet["M22"].value,
                         "Not calculated - separate radiologist-agreement reference not supplied")

    def test_case_predictions_sorted_with_agreement_fills(self):
        order = [*range(100, 0, -1)]
        reference = reference_for(order)
        predictions = random_predictions(order, seed=12)
        wb, _ = self.build(reference, predictions)
        sheet = wb["Case Predictions"]
        self.assertEqual([sheet.cell(r, 1).value for r in range(2, 102)], list(range(1, 101)))
        cell = sheet.cell(2, 4)
        expected = "Match" if reference[1][CONDITION_KEYS[0]] == predictions[1][
            CONDITION_KEYS[0]] else "Mismatch"
        self.assertEqual(cell.value, expected)
        self.assertEqual(cell.fill.fgColor.rgb,
                         "00E2F0D9" if expected == "Match" else "00FCE4D6")
        self.assertEqual(sheet["A1"].font.sz, 9)

    def test_execution_log(self):
        rows = self.rows(self.wb["Execution Log"])
        log = {r[0]: r for r in rows[:18]}
        self.assertEqual(log["Gold Standard file"][1], "gold.xlsx")
        self.assertEqual(log["Prediction file"][1], "predictions.jsonl")
        self.assertEqual(log["Failed records"][1:3], [0, FAILURE_COUNT_SOURCE])
        self.assertIn("No errors.jsonl was supplied", FAILURE_COUNT_SOURCE)
        self.assertEqual(log["Validation"][1],
                         "All 100 records successful; exact 20 condition keys; valid "
                         "Positive/Negative labels; CaseIDs 1–100 matched.")
        header = rows.index(["CaseID", "Status", "Attempts", "Completed At (UTC)"])
        self.assertEqual(rows[header - 1], [None, None, None, None])
        self.assertEqual([r[0] for r in rows[header + 1:]], list(range(1, 101)))
        self.assertTrue(all(r[1] == "success" for r in rows[header + 1:]))

    def test_refuses_non_matrix2_labels(self):
        path = self.dir / "p.jsonl"
        path.write_text(record_line(1, reference_for([1])[1]) + "\n", encoding="utf-8")
        labels = reconcile(MATRIX1, as_reference(reference_for([1])), path)
        result = compute_evaluation(labels)
        with self.assertRaisesRegex(ValueError, "matrix1"):
            build_matrix2_workbook(labels, result.per_condition, result.micro,
                                   self.dir / "x.xlsx")


class TestUndefinedMetrics(Matrix2TestCase):
    def test_f1_edge_case_and_undefined_values_are_blank(self):
        ids = list(range(1, 101))
        reference = {cid: {c: N for c in CONDITION_KEYS} for cid in ids}
        predictions = {cid: {c: N for c in CONDITION_KEYS} for cid in ids}
        reference[1]["perihilar_infiltrate"] = P      # TP 0, FN 1
        predictions[2]["perihilar_infiltrate"] = P    # FP 1 -> F1 edge case
        predictions[3]["esophagitis"] = P             # no reference positives
        wb, result = self.build(reference, predictions)
        cs = wb["Condition Summary"]
        row = 2 + CONDITION_KEYS.index("perihilar_infiltrate")
        self.assertEqual((cs.cell(row, 10).value, cs.cell(row, 12).value), (0, 0))
        self.assertIsNone(cs.cell(row, 13).value)
        esophagitis = 2 + CONDITION_KEYS.index("esophagitis")
        self.assertIsNone(cs.cell(esophagitis, 10).value)            # sensitivity undefined
        self.assertEqual(cs.cell(esophagitis, 12).value, 0)          # precision 0
        self.assertIsNone(cs.cell(esophagitis, 13).value)
        pneumonia = 2 + CONDITION_KEYS.index("pneumonia")
        self.assertIsNone(cs.cell(pneumonia, 12).value)              # no positive predictions
        self.assertIsNone(result.per_condition["perihilar_infiltrate"].f1)


class TestRunSpecificNarrative(Matrix2TestCase):
    """Decision D5: narrative text is generated from the actual results."""

    def scope(self, wb):
        sheet = wb["Overall Summary"]
        start = [c.value for c in sheet["A"]].index("Dataset / Scope") + 1
        rows = {}
        for r in range(start + 1, sheet.max_row + 1):
            if sheet.cell(r, 1).value is None:
                break
            rows[sheet.cell(r, 1).value] = (sheet.cell(r, 2).value, sheet.cell(r, 3).value)
        return rows

    def run_with(self, ids, attempts):
        return self.build(reference_for(ids), reference_for(ids), attempts=attempts)[0]

    def test_a6_wording_for_a6_numbers(self):
        scope = self.scope(self.run_with(range(1, 101), {3: 2}))
        self.assertEqual(scope["Cases evaluated"],
                         (100, "All 100 cases had successful validated predictions."))
        self.assertEqual(scope["First-attempt completions"],
                         (99, "One case required a second application-level attempt."))
        self.assertEqual(scope["Cases requiring 2 attempts"],
                         (1, "Transport-level retries may be additional."))
        self.assertEqual(scope["Failed prediction records"],
                         (0, "No final failed records in the completed batch."))

    def test_no_retries(self):
        scope = self.scope(self.run_with(range(1, 101), {}))
        self.assertEqual(scope["First-attempt completions"],
                         (100, "No case required a second application-level attempt."))
        self.assertEqual(scope["Cases requiring 2 attempts"][0], 0)

    def test_several_retries_and_three_attempts(self):
        wb = self.run_with(range(1, 61), {2: 2, 5: 2, 9: 3})
        scope = self.scope(wb)
        self.assertEqual(scope["Cases evaluated"][1],
                         "All 60 cases had successful validated predictions.")
        self.assertEqual(scope["First-attempt completions"],
                         (57, "3 cases required more than one application-level attempt."))
        self.assertEqual(scope["Cases requiring 2 attempts"][0], 2)
        self.assertEqual(scope["Cases requiring 3 attempts"][0], 1)
        log = {r[0].value: r[1].value for r in wb["Execution Log"].iter_rows(max_row=25)}
        self.assertEqual(log["Cases requiring 3 attempts"], 1)
        total = [c.value for c in wb["Overall Summary"]["C"]]
        self.assertIn("60 cases × 20 conditions", total)

    def test_single_retry_beyond_second_attempt(self):
        scope = self.scope(self.run_with(range(1, 11), {4: 3}))
        self.assertEqual(scope["First-attempt completions"][1],
                         "One case required more than one application-level attempt.")

    def test_non_contiguous_case_ids(self):
        wb = self.run_with([1, 2, 5, 9], {})
        log = {r[0].value: r[1].value for r in wb["Execution Log"].iter_rows(max_row=20)}
        self.assertTrue(log["Validation"].endswith("4 CaseIDs matched."))

    def test_skipped_lines_are_listed(self):
        ids = list(range(1, 11))
        wb, _ = self.build(reference_for(ids), reference_for(ids), before=[PARTIAL_LINE])
        names = [r[0].value for r in wb["Execution Log"].iter_rows()]
        self.assertIn("Skipped prediction lines", names)
        self.assertIn("Skipped prediction line", names)
        self.assertLess(names.index("Skipped prediction lines"), names.index("CaseID"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
