"""Offline tests for reconciliation, the Matrix 1 workbook and the evaluate pipeline."""
from __future__ import annotations

import contextlib
import io
import json
import random
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from unittest.mock import patch

from openpyxl import load_workbook

from week_05 import cli, config
from week_05.batch_runner import run_workflow_batch
from week_05.conditions import CONDITION_KEYS
from week_05.config import MATRIX1, MATRIX2, ConfigurationError
from week_05.evaluation.evaluate import (
    compute_evaluation,
    evaluate_workflow,
    resolve_workbook_path,
    write_evaluation_workbook,
)
from week_05.evaluation.matrix1_workbook import build_matrix1_workbook
from week_05.evaluation.reconcile import (
    EvaluationInputError,
    load_prediction_records,
    reconcile,
    sorted_case_ids,
)
from week_05.evaluation.reference_loader import (
    EvaluationReference,
    ReferenceLoadError,
    ReferenceLoadingPending,
)
from week_05.evaluation.workbook_compare import compare_workbooks
from week_05.tests.support import FrozenDatetime, ScriptedClassifier, StepClock, quiet
from week_05.tests.workbook_factory import (
    MATRIX1_HEADERS,
    MATRIX2_HEADERS,
    label_for,
    make_workbook,
)

LOGGERS = ("week_05.batch_runner", "week_05.jsonl_store", "week_05.dataset_loader")
P, N = "Positive", "Negative"
PARTIAL_LINE = '{"case_id": 100, "status": "success", "attem'


def reference_for(case_ids):
    return {cid: {c: label_for(cid, i) for i, c in enumerate(CONDITION_KEYS)} for cid in case_ids}


def as_reference(labels: dict,
                 name: str = "Vetology_Matrix1_First100_Encoded.xlsx") -> EvaluationReference:
    return EvaluationReference(
        source_path=Path("/synthetic") / name,
        worksheet_name="Sheet1",
        case_ids=tuple(labels),
        labels=MappingProxyType({k: MappingProxyType(dict(v)) for k, v in labels.items()}),
    )


def random_predictions(case_ids, seed=0, rate=0.25):
    rng = random.Random(seed)
    return {cid: {c: P if rng.random() < rate else N for c in CONDITION_KEYS} for cid in case_ids}


def rounded(values, places=12):
    """Excel stores ~15 significant digits; compare floats read back at 12 places."""
    return [round(v, places) if isinstance(v, float) else v for v in values]


def record_line(case_id, labels, status="success") -> str:
    return json.dumps({"case_id": case_id, "status": status, "attempts": 1,
                       "completed_at_utc": "2026-11-10T00:00:00+00:00", "predictions": labels},
                      ensure_ascii=False)


def write_predictions(path: Path, predictions: dict, *, extra_lines=(), before=()) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [*before, *(record_line(cid, labels) for cid, labels in predictions.items()),
             *extra_lines]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


class EvalTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        quiet(self, *LOGGERS)


# ---------------------------------------------------------------------------
# Reconciliation (strict rules)
# ---------------------------------------------------------------------------

class TestReconcile(EvalTestCase):
    def setUp(self):
        super().setUp()
        self.ids = list(range(1, 101))
        self.reference = as_reference(reference_for(self.ids))
        self.predictions = random_predictions(self.ids)

    def test_valid_inputs_align_in_reference_order(self):
        path = write_predictions(self.dir / "p.jsonl", dict(reversed(self.predictions.items())))
        labels = reconcile(MATRIX1, self.reference, path, expected_cases=100)
        self.assertEqual(labels.case_ids, tuple(self.ids))
        self.assertEqual({k: dict(v) for k, v in labels.predictions.items()}, self.predictions)
        self.assertEqual(labels.skipped_lines, ())
        self.assertEqual(labels.workflow, "matrix1")

    def test_reference_and_predictions_stay_separate_and_read_only(self):
        labels = reconcile(MATRIX1, self.reference,
                           write_predictions(self.dir / "p.jsonl", self.predictions))
        self.assertIsNot(labels.reference, labels.predictions)
        with self.assertRaises(TypeError):
            labels.predictions[1]["rtm"] = P
        with self.assertRaises(TypeError):
            labels.reference[1]["rtm"] = P
        self.assertNotIn("Positive", repr(labels))

    def test_prediction_key_order_normalised_and_blank_lines_ignored(self):
        shuffled = {cid: dict(reversed(list(v.items()))) for cid, v in self.predictions.items()}
        path = write_predictions(self.dir / "p.jsonl", shuffled, extra_lines=["", "   "])
        labels = reconcile(MATRIX1, self.reference, path)
        self.assertEqual(tuple(labels.predictions[1]), CONDITION_KEYS)
        self.assertEqual(labels.skipped_lines, ())

    def test_case_ids_converted_with_int_like_week4(self):
        mixed = {(str(k) if k % 3 == 0 else float(k) if k % 3 == 1 else k): v
                 for k, v in self.predictions.items()}
        labels = reconcile(MATRIX1, self.reference, write_predictions(self.dir / "p.jsonl", mixed))
        self.assertEqual(set(labels.predictions), set(self.ids))

    def test_strict_rejections(self):
        good = {k: v for k, v in self.predictions.items() if k != 100}
        last = self.predictions[100]
        cases = {
            "non-object JSON": (["[1, 2]"], "not a JSON object"),
            "no case_id": ([json.dumps({"status": "success", "predictions": last})],
                           "has no case_id"),
            "unconvertible case_id": ([record_line("A-100", last)], "cannot be converted"),
            "duplicate valid record": ([record_line(100, last), record_line(100, last)],
                                       "Duplicate prediction CaseID: 100"),
            "failed record": ([record_line(100, last, status="failed")], "not successful"),
            "missing status": ([json.dumps({"case_id": 100, "predictions": last})],
                               "not successful"),
            "missing key": ([record_line(100, {k: v for k, v in last.items() if k != "rtm"})],
                            "keys mismatch"),
            "extra key": ([record_line(100, {**last, "extra": N})], "keys mismatch"),
            "predictions not an object": ([record_line(100, ["Positive"])], "keys mismatch"),
            "invalid label": ([record_line(100, {**last, "rtm": "positive"})],
                              "Invalid prediction label"),
        }
        for name, (extra, message) in cases.items():
            with self.subTest(case=name):
                path = write_predictions(self.dir / f"{len(name)}x.jsonl", good, extra_lines=extra)
                with self.assertRaisesRegex(EvaluationInputError, message):
                    reconcile(MATRIX1, self.reference, path)

    def test_case_id_set_mismatches(self):
        missing = {k: v for k, v in self.predictions.items() if k != 50}
        with self.assertRaisesRegex(EvaluationInputError, r"reference-only=\[50\]"):
            reconcile(MATRIX1, self.reference, write_predictions(self.dir / "a.jsonl", missing))
        extra = {**self.predictions, 999: self.predictions[1]}
        with self.assertRaisesRegex(EvaluationInputError, r"prediction-only=\[999\]"):
            reconcile(MATRIX1, self.reference, write_predictions(self.dir / "b.jsonl", extra))

    def test_matrix1_requires_100_cases_matrix2_only_exact_set(self):
        ids = list(range(1, 61))
        path = write_predictions(self.dir / "p.jsonl", random_predictions(ids))
        ref = as_reference(reference_for(ids))
        with self.assertRaisesRegex(EvaluationInputError, "exactly 100 cases; found 60"):
            reconcile(MATRIX1, ref, path, expected_cases=100)
        self.assertEqual(len(reconcile(MATRIX2, ref, path).case_ids), 60)
        big = list(range(1, 126))
        big_path = write_predictions(self.dir / "big.jsonl", random_predictions(big))
        self.assertEqual(len(reconcile(MATRIX2, as_reference(reference_for(big)),
                                       big_path).case_ids), 125)

    def test_missing_and_empty_files(self):
        with self.assertRaises(FileNotFoundError):
            load_prediction_records(self.dir / "absent.jsonl")
        empty = self.dir / "empty.jsonl"
        empty.write_text("\n", encoding="utf-8")
        with self.assertRaisesRegex(EvaluationInputError, "No valid prediction records"):
            load_prediction_records(empty)

    def test_predictions_from_the_other_workflow_directory_are_refused(self):
        for spec, other in ((MATRIX1, MATRIX2), (MATRIX2, MATRIX1)):
            with self.subTest(workflow=spec.name):
                with self.assertRaisesRegex(EvaluationInputError, other.name):
                    reconcile(spec, self.reference, other.predictions_path)

    def test_sorted_case_ids(self):
        self.assertEqual(sorted_case_ids([3, 1, 2]), [1, 2, 3])


# ---------------------------------------------------------------------------
# Option B: skipping unreadable (interrupted-write) lines, with safeguards
# ---------------------------------------------------------------------------

class TestSkippedLines(EvalTestCase):
    def setUp(self):
        super().setUp()
        self.ids = list(range(1, 101))
        self.reference = as_reference(reference_for(self.ids))
        self.predictions = random_predictions(self.ids, seed=3)

    def test_partial_line_is_skipped_and_recorded_when_predictions_are_complete(self):
        first = {k: v for k, v in self.predictions.items() if k < 100}
        path = self.dir / "p.jsonl"
        lines = [*(record_line(k, v) for k, v in first.items()), PARTIAL_LINE,
                 record_line(100, self.predictions[100])]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        labels = reconcile(MATRIX1, self.reference, path, expected_cases=100)
        self.assertEqual(len(labels.skipped_lines), 1)
        self.assertEqual(labels.skipped_lines[0].line_number, 100)
        self.assertIn("not valid JSON", labels.skipped_lines[0].reason)
        self.assertIn("interrupted", labels.skipped_lines[0].reason)
        self.assertEqual(len(labels.predictions), 100)

    def test_several_unreadable_lines_each_recorded(self):
        lines = ["garbage", *(record_line(k, v) for k, v in self.predictions.items()),
                 '{"case_id": 5, "sta', "{"]
        path = self.dir / "p.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        labels = reconcile(MATRIX1, self.reference, path)
        self.assertEqual([s.line_number for s in labels.skipped_lines], [1, 102, 103])

    def test_skipping_never_hides_a_missing_prediction(self):
        complete_except_last = {k: v for k, v in self.predictions.items() if k != 100}
        path = write_predictions(self.dir / "p.jsonl", complete_except_last,
                                 extra_lines=[PARTIAL_LINE])
        with self.assertRaisesRegex(EvaluationInputError,
                                    r"reference-only=\[100\].*1 unreadable prediction line"):
            reconcile(MATRIX1, self.reference, path)

    def test_only_unparseable_lines_are_skipped(self):
        """Readable-but-invalid records are rejected even next to a skipped line."""
        good = {k: v for k, v in self.predictions.items() if k != 100}
        path = write_predictions(self.dir / "p.jsonl", good, extra_lines=[
            PARTIAL_LINE, record_line(100, {**self.predictions[100], "rtm": "Maybe"})])
        with self.assertRaisesRegex(EvaluationInputError, "Invalid prediction label"):
            reconcile(MATRIX1, self.reference, path)

    def test_file_of_only_unreadable_lines(self):
        path = self.dir / "p.jsonl"
        path.write_text(PARTIAL_LINE + "\n", encoding="utf-8")
        with self.assertRaisesRegex(EvaluationInputError, "No valid prediction records"):
            load_prediction_records(path)

    def test_execution_log_lists_skipped_lines(self):
        path = self.dir / "p.jsonl"
        path.write_text("\n".join([PARTIAL_LINE, *(record_line(k, v) for k, v in
                                                   self.predictions.items())]) + "\n",
                        encoding="utf-8")
        labels = reconcile(MATRIX1, self.reference, path)
        result = compute_evaluation(labels)
        out = build_matrix1_workbook(labels, result.per_condition, result.micro, result.macro,
                                     self.dir / "w.xlsx", clock=StepClock())
        rows = [(r[0].value, r[1].value) for r in load_workbook(out)["Execution Log"]
                .iter_rows(min_row=2)]
        names = [name for name, _ in rows]
        start = names.index("Prediction validation") + 1
        self.assertEqual(rows[start][0], "Skipped prediction lines")
        self.assertIn("1 unreadable line(s)", rows[start][1])
        self.assertIn("all 100 CaseIDs still have exactly one", rows[start][1])
        self.assertEqual(rows[start + 1][0], "Skipped prediction line")
        self.assertTrue(rows[start + 1][1].startswith("line 1: not valid JSON"))
        self.assertEqual(rows[start + 2][0], "Model")

    def test_crash_recovered_batch_output_evaluates_and_reports(self):
        """Phase 5 crash recovery + Phase 6 Option B, end to end."""
        gt = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        out = self.dir / "matrix_1"
        run_workflow_batch(MATRIX1, gt, output_dir=out, classifier=ScriptedClassifier(),
                           clock=StepClock())
        predictions = out / "predictions.jsonl"
        lines = predictions.read_text(encoding="utf-8").splitlines()
        # simulate: case 100's line was cut off mid-write, then the batch was re-run
        predictions.write_text("\n".join(lines[:-1]) + "\n" + lines[-1][:40], encoding="utf-8")
        run_workflow_batch(MATRIX1, gt, output_dir=out, classifier=ScriptedClassifier(),
                           clock=StepClock())
        result = evaluate_workflow(MATRIX1, gt, predictions)
        self.assertEqual(len(result.labels.skipped_lines), 1)
        self.assertEqual(result.labels.skipped_lines[0].line_number, 100)
        self.assertEqual(result.micro.total, 2000)


# ---------------------------------------------------------------------------
# Matrix 1 workbook
# ---------------------------------------------------------------------------

class TestMatrix1Workbook(EvalTestCase):
    def build(self, reference, predictions, name="w5.xlsx", clock=None):
        pred_path = write_predictions(self.dir / "predictions.jsonl", predictions)
        labels = reconcile(MATRIX1, as_reference(reference), pred_path)
        result = compute_evaluation(labels)
        path = build_matrix1_workbook(labels, result.per_condition, result.micro, result.macro,
                                      self.dir / name, clock=clock or StepClock())
        return load_workbook(path), result

    def setUp(self):
        super().setUp()
        self.ids = list(range(1, 101))
        self.reference = reference_for(self.ids)

    def test_sheet_order(self):
        wb, _ = self.build(self.reference, random_predictions(self.ids))
        self.assertEqual(wb.sheetnames, ["Overall Summary", "Condition Summary",
                                         "Case Predictions", "Confusion Matrix",
                                         "Execution Log", "Metric Definitions"])

    def test_overall_summary_rows_values_and_formats(self):
        wb, result = self.build(self.reference, random_predictions(self.ids, seed=4))
        sheet = wb["Overall Summary"]
        self.assertEqual(sheet["A1"].value, "VETOLOGY MATRIX 1 - EVALUATION SUMMARY")
        self.assertEqual([c.value for c in sheet[2]],
                         ["Metric", "Result", "Calculation / Definition", "Interpretation"])
        self.assertEqual([sheet.cell(r, 1).value for r in range(3, 20)], [
            "Cases evaluated", "Conditions evaluated", "Total paired labels",
            "True Positive (TP)", "False Negative (FN)", "True Negative (TN)",
            "False Positive (FP)", "Micro Accuracy", "Micro Sensitivity (Recall)",
            "Micro Specificity", "Micro Precision", "Micro F1-score", "Macro Accuracy",
            "Macro Sensitivity", "Macro Specificity", "Macro Precision", "Macro F1-score"])
        micro, macro = result.micro, result.macro
        self.assertEqual(rounded([sheet.cell(r, 2).value for r in range(3, 20)]), rounded([
            100, 20, 2000, micro.tp, micro.fn, micro.tn, micro.fp, micro.accuracy,
            micro.sensitivity, micro.specificity, micro.precision, micro.f1, macro.accuracy,
            macro.sensitivity, macro.specificity, macro.precision, macro.f1]))
        self.assertEqual([sheet.cell(r, 2).number_format for r in range(10, 20)],
                         ["0.00%"] * 10)
        self.assertEqual(sheet.cell(9, 2).number_format, "General")
        self.assertEqual(sheet.freeze_panes, "B3")

    def test_condition_summary_and_confusion_matrix(self):
        wb, result = self.build(self.reference, random_predictions(self.ids, seed=5))
        cs, cm = wb["Condition Summary"], wb["Confusion Matrix"]
        self.assertEqual([cs.cell(r, 1).value for r in range(2, 23)], [*CONDITION_KEYS, "TOTAL"])
        self.assertEqual([cm.cell(r, 1).value for r in range(2, 23)], [*CONDITION_KEYS, "TOTAL"])
        rtm = result.per_condition["rtm"]
        row = 2 + CONDITION_KEYS.index("rtm")
        self.assertEqual(rounded([c.value for c in cs[row]]),
                         rounded(["rtm", rtm.tp, rtm.fn, rtm.tn, rtm.fp, rtm.total,
                                  rtm.positive_gt, rtm.negative_gt, rtm.accuracy,
                                  rtm.sensitivity, rtm.specificity, rtm.precision, rtm.f1]))
        self.assertEqual(rounded([c.value for c in cm[row]]),
                         rounded(["rtm", rtm.tp, rtm.fn, rtm.tn, rtm.fp, rtm.sensitivity,
                                  rtm.specificity, rtm.total, rtm.positive_gt, rtm.negative_gt,
                                  rtm.accuracy, rtm.precision, rtm.f1, rtm.total]))
        self.assertEqual(cs.cell(22, 2).value, result.micro.tp)
        self.assertTrue(cs.cell(22, 1).font.bold)
        self.assertEqual(cs.cell(22, 1).fill.fgColor.rgb, "00E2F0D9")
        self.assertEqual(cs.auto_filter.ref, "A1:M22")
        self.assertEqual(cm.auto_filter.ref, "A1:N22")

    def test_undefined_metrics_are_blank_cells(self):
        predictions = {cid: {c: N for c in CONDITION_KEYS} for cid in self.ids}
        reference = {cid: {c: N for c in CONDITION_KEYS} for cid in self.ids}
        reference[1]["rtm"] = P
        predictions[2]["rtm"] = P                   # rtm: TP0 FN1 FP1 -> F1 edge case
        wb, result = self.build(reference, predictions)
        cs = wb["Condition Summary"]
        pneumonia_row = 2 + CONDITION_KEYS.index("pneumonia")
        self.assertIsNone(cs.cell(pneumonia_row, 10).value)   # sensitivity undefined
        self.assertIsNone(cs.cell(pneumonia_row, 12).value)   # precision undefined
        self.assertIsNone(cs.cell(pneumonia_row, 13).value)   # F1 undefined
        self.assertEqual(cs.cell(pneumonia_row, 11).value, 1.0)
        rtm_row = 2 + CONDITION_KEYS.index("rtm")
        self.assertEqual(cs.cell(rtm_row, 10).value, 0.0)
        self.assertEqual(cs.cell(rtm_row, 12).value, 0.0)
        self.assertIsNone(cs.cell(rtm_row, 13).value)         # preserved F1 edge case
        self.assertIsNone(wb["Overall Summary"].cell(19, 2).value)  # Macro F1: none defined
        self.assertIsNone(result.macro.f1)

    def test_case_predictions_sheet(self):
        order = [*range(100, 50, -1), *range(1, 51)]
        reference = reference_for(order)
        predictions = random_predictions(order, seed=6)
        wb, _ = self.build(reference, predictions)
        sheet = wb["Case Predictions"]
        self.assertEqual(sheet.max_column, 61)
        self.assertEqual([sheet.cell(1, c).value for c in (2, 3, 4)],
                         ["perihilar_infiltrate - Gold Standard",
                          "perihilar_infiltrate - Model Prediction",
                          "perihilar_infiltrate - Agreement"])
        self.assertEqual([sheet.cell(r, 1).value for r in range(2, 102)], list(range(1, 101)))
        for r in (2, 50, 101):
            case_id = sheet.cell(r, 1).value
            for i, condition in enumerate(CONDITION_KEYS):
                actual, predicted, agreement = (sheet.cell(r, 2 + 3 * i + k).value
                                                for k in range(3))
                self.assertEqual(actual, reference[case_id][condition])
                self.assertEqual(predicted, predictions[case_id][condition])
                self.assertEqual(agreement, "Match" if actual == predicted else "Mismatch")
                fill = sheet.cell(r, 4 + 3 * i).fill.fgColor.rgb
                self.assertEqual(fill, "00E2F0D9" if agreement == "Match" else "00FCE4D6")

    def test_execution_log_without_skipped_lines_is_week4_layout(self):
        clock = StepClock(datetime(2026, 11, 10, 14, 5, 9, tzinfo=timezone.utc))
        wb, _ = self.build(self.reference, random_predictions(self.ids), clock=clock)
        rows = [(r[0].value, r[1].value) for r in wb["Execution Log"].iter_rows(min_row=2)]
        self.assertEqual([name for name, _ in rows], [
            "Evaluation Track", "Ground-truth workbook", "Prediction file",
            "Cases in ground truth", "Prediction records", "Conditions",
            "Expected paired labels", "Actual paired labels", "CaseID reconciliation",
            "Prediction validation", "Model", "Prompt version", "Evaluation generated (UTC)",
            "Metric scope", "Clinical interpretation"])
        log = dict(rows)
        self.assertEqual(log["Ground-truth workbook"], "Vetology_Matrix1_First100_Encoded.xlsx")
        self.assertEqual(log["Prediction file"], "predictions.jsonl")
        self.assertEqual(log["Expected paired labels"], 2000)
        self.assertEqual(log["Evaluation generated (UTC)"], "2026-11-10 14:05:09 UTC")

    def test_week4_terminology_preserved(self):
        wb, _ = self.build(self.reference, random_predictions(self.ids))
        summary = wb["Overall Summary"]
        self.assertEqual(summary.cell(6, 3).value, "GS Positive; model Positive")
        self.assertEqual(summary.cell(11, 4).value,
                         "Recall across all Gold Standard Positive labels.")
        definitions = {r[0].value: r[1].value
                       for r in wb["Metric Definitions"].iter_rows(min_row=2)}
        self.assertIn("Gold Standard Positive labels", definitions["Sensitivity / Recall"])

    def test_refuses_non_matrix1_labels(self):
        path = write_predictions(self.dir / "p.jsonl", random_predictions(self.ids))
        labels = reconcile(MATRIX2, as_reference(self.reference), path)
        result = compute_evaluation(labels)
        with self.assertRaisesRegex(ValueError, "matrix2"):
            build_matrix1_workbook(labels, result.per_condition, result.micro, result.macro,
                                   self.dir / "x.xlsx")


# Approved decision D1: the Matrix 1 layout follows the delivered A5 workbook, which
# differs from the committed Week 4 evaluator only in these presentation details.
A5_TEXT_CELLS = {
    ("Overall Summary", "D5"), ("Overall Summary", "D14"), ("Overall Summary", "D16"),
    ("Overall Summary", "D17"), ("Overall Summary", "D18"), ("Overall Summary", "D19"),
    ("Execution Log", "B12"), ("Execution Log", "B15"),
    ("Metric Definitions", "B10"), ("Metric Definitions", "B12"),
}
A5_STYLE_CELLS = {("Overall Summary", f"{col}2") for col in "ABCD"}
SHEETS = ("Overall Summary", "Condition Summary", "Case Predictions", "Confusion Matrix",
          "Execution Log", "Metric Definitions")


class TestMatrix1Week4Parity(EvalTestCase):
    """Week 5 vs the committed Week 4 evaluator, end to end (workbook + JSONL -> xlsx).

    Metrics must be identical. The workbooks may differ only by the documented
    A5 presentation differences (decision D1), and nowhere else.
    """

    def assert_only_a5_layout_differences(self, week4_path, week5_path):
        import re

        diffs = compare_workbooks(week4_path, week5_path, max_differences=200)
        values, styles, heights, widths, other = set(), set(), set(), set(), []
        for diff in diffs:
            if m := re.match(r"\[(.+?)!([A-Z]+\d+)\] value", diff):
                values.add((m[1], m[2]))
            elif m := re.match(r"\[(.+?)!([A-Z]+\d+)\] style", diff):
                styles.add((m[1], m[2]))
            elif m := re.match(r"\[(.+?)\] row (\d+) height 30.0 != 28", diff):
                heights.add((m[1], int(m[2])))
            elif m := re.match(r"\[(.+?)\] column ([A-Z]+) width 58.0 != 55", diff):
                widths.add((m[1], m[2]))
            else:
                other.append(diff)
        self.assertEqual(other, [])
        self.assertTrue(values <= A5_TEXT_CELLS, values - A5_TEXT_CELLS)
        self.assertEqual(styles, A5_STYLE_CELLS)
        self.assertEqual(heights, {(sheet, 1) for sheet in SHEETS})
        self.assertEqual(widths, {("Overall Summary", "C")})

    def compare_with_week4(self, predictions_by_id, gt_kwargs=None):
        from week_04.matrix_1 import matrix1_evaluator as week4

        gt = make_workbook(self.dir / "Vetology_Matrix1_First100_Encoded.xlsx", MATRIX1_HEADERS,
                           **(gt_kwargs or {}))
        pred = write_predictions(self.dir / "predictions.jsonl", predictions_by_id)
        week4_path, week5_path = self.dir / "week4.xlsx", self.dir / "week5.xlsx"
        with patch.object(week4, "datetime", FrozenDatetime(StepClock())):
            truth, preds = week4.load_matrix1_inputs(gt, pred)
            week4_metrics, _ = week4.build_evaluation_workbook(truth, preds, week4_path, gt, pred)
        result = evaluate_workflow(MATRIX1, gt, pred)
        write_evaluation_workbook(MATRIX1, result, week5_path, clock=StepClock())
        self.assertEqual({c: result.per_condition[c].as_dict() for c in CONDITION_KEYS},
                         week4_metrics)
        self.assert_only_a5_layout_differences(week4_path, week5_path)
        return result

    def test_random_predictions(self):
        for seed, rate in [(20, 0.1), (21, 0.3), (22, 0.6)]:
            with self.subTest(seed=seed):
                self.compare_with_week4(random_predictions(range(1, 101), seed=seed, rate=rate))

    def test_perfect_predictions(self):
        self.assertEqual(self.compare_with_week4(reference_for(range(1, 101))).micro.accuracy,
                         1.0)

    def test_all_negative_predictions_with_undefined_metrics(self):
        result = self.compare_with_week4(
            {cid: {c: N for c in CONDITION_KEYS} for cid in range(1, 101)})
        self.assertIsNone(result.micro.precision)

    def test_unsorted_worksheet_order(self):
        order = [*range(100, 0, -1)]
        self.compare_with_week4(random_predictions(order, seed=23), {"case_ids": order})

    def test_mixed_case_id_types_in_reference_and_predictions(self):
        ids = [1.0, "2", *range(3, 101)]
        predictions = {(str(int(float(c))) if i % 2 else int(float(c))): v for i, (c, v) in
                       enumerate(random_predictions(range(1, 101), seed=24).items())}
        self.compare_with_week4(predictions, {"case_ids": ids})

    def test_f1_edge_case_condition(self):
        predictions = reference_for(range(1, 101))
        for cid in range(1, 101):
            predictions[cid]["rtm"] = N if predictions[cid]["rtm"] == P else P
        rtm = self.compare_with_week4(predictions).per_condition["rtm"]
        self.assertEqual(rtm.tp, 0)
        self.assertGreater(rtm.fp, 0)
        self.assertGreater(rtm.fn, 0)
        self.assertIsNone(rtm.f1)


# ---------------------------------------------------------------------------
# Pipeline, Matrix 2, output guards, CLI, comparison tool
# ---------------------------------------------------------------------------

class TestPipeline(EvalTestCase):
    def test_batch_then_evaluate_matrix1_end_to_end(self):
        gt = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        out = self.dir / "matrix_1"
        all_negative = json.dumps({c: N for c in CONDITION_KEYS})
        run_workflow_batch(MATRIX1, gt, output_dir=out,
                           classifier=ScriptedClassifier(default=all_negative), clock=StepClock())
        result = evaluate_workflow(MATRIX1, gt, out / "predictions.jsonl")
        positives = sum(label == P for labels in reference_for(range(1, 101)).values()
                        for label in labels.values())
        self.assertEqual((result.micro.tp, result.micro.fp), (0, 0))
        self.assertEqual(result.micro.fn, positives)
        self.assertEqual(result.micro.tn, 2000 - positives)
        self.assertTrue(write_evaluation_workbook(MATRIX1, result, out / "e.xlsx").is_file())

    def test_matrix1_evaluation_reads_all_reference_rows_like_week4(self):
        gt = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS, case_ids=range(1, 126))
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        with self.assertRaisesRegex(EvaluationInputError, r"reference-only=\[101, 102"):
            evaluate_workflow(MATRIX1, gt, pred)

    def test_matrix2_end_to_end_with_synthetic_data(self):
        gt = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS)
        pred = write_predictions(self.dir / "p.jsonl", random_predictions(range(1, 101), seed=8))
        result = evaluate_workflow(MATRIX2, gt, pred)
        self.assertEqual(result.workflow, "matrix2")
        self.assertEqual(result.micro.total, 2000)
        target = self.dir / "matrix_2" / "Evaluation Workbook v2.xlsx"
        self.assertEqual(write_evaluation_workbook(MATRIX2, result, target), target.resolve())
        self.assertEqual(load_workbook(target).sheetnames,
                         ["Overall Summary", "Condition Summary", "Case Predictions",
                          "Confusion Matrix", "Execution Log"])

    def test_matrix2_uses_exact_set_matching_without_a_case_count(self):
        ids = range(1001, 1061)
        gt = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS, case_ids=ids)
        pred = write_predictions(self.dir / "p.jsonl", reference_for(ids))
        result = evaluate_workflow(MATRIX2, gt, pred)
        self.assertEqual(len(result.labels.case_ids), 60)        # no 100-case restriction
        self.assertEqual(result.micro.accuracy, 1.0)

    def test_matrix2_ambiguous_workbook_is_rejected_before_evaluation(self):
        gt = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS, case_ids=range(1, 126))
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        with self.assertRaisesRegex(ReferenceLoadError, "ambiguous"):
            evaluate_workflow(MATRIX2, gt, pred)

    def test_unknown_workflow_has_no_loader_or_layout(self):
        import dataclasses

        other = dataclasses.replace(MATRIX1, name="matrix3")
        with self.assertRaises(ReferenceLoadingPending):
            evaluate_workflow(other, self.dir / "x.xlsx", self.dir / "x.jsonl")

    def test_matrix2_set_mismatch_rejected(self):
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        with self.assertRaisesRegex(EvaluationInputError, "CaseID mismatch"):
            reconcile(MATRIX2, as_reference(reference_for(range(1, 126))), pred)

    def test_workflow_mismatch_rejected(self):
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        result = compute_evaluation(
            reconcile(MATRIX2, as_reference(reference_for(range(1, 101))), pred))
        with self.assertRaisesRegex(ValueError, "matrix2"):
            write_evaluation_workbook(MATRIX1, result, self.dir / "x.xlsx")

    def test_workbook_path_guards(self):
        self.assertEqual(resolve_workbook_path(MATRIX1, None),
                         MATRIX1.evaluation_workbook_path.resolve())
        week4 = config.REPO_ROOT / "outputs" / "week_04" / "matrix_1" / "x.xlsx"
        with self.assertRaisesRegex(ConfigurationError, "Week 4"):
            resolve_workbook_path(MATRIX1, week4)
        with self.assertRaisesRegex(ConfigurationError, "matrix2"):
            resolve_workbook_path(MATRIX1, MATRIX2.output_dir / "m1.xlsx")


class TestCli(EvalTestCase):
    def run_cli(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(argv)
        return code, out.getvalue()

    def test_matrix1_evaluate_writes_workbook(self):
        gt = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        output = self.dir / "eval.xlsx"
        code, out = self.run_cli(["evaluate", "--workflow", "matrix1", "--input", str(gt),
                                  "--predictions", str(pred), "--output", str(output)])
        self.assertEqual(code, 0)
        self.assertIn("Paired labels: 2000", out)
        self.assertIn("Micro accuracy=100.00%", out)
        self.assertIn("Evaluation workbook created", out)
        self.assertNotIn("WARNING", out)
        self.assertTrue(output.is_file())

    def test_evaluate_prints_skipped_lines(self):
        gt = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)),
                                 before=[PARTIAL_LINE])
        code, out = self.run_cli(["evaluate", "--workflow", "matrix1", "--input", str(gt),
                                  "--predictions", str(pred), "--output",
                                  str(self.dir / "e.xlsx")])
        self.assertEqual(code, 0)
        self.assertIn("WARNING: skipped prediction line 1: not valid JSON", out)

    def test_matrix2_evaluate_writes_workbook(self):
        gt = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS)
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        output = self.dir / "eval.xlsx"
        code, out = self.run_cli(["evaluate", "--workflow", "matrix2", "--input", str(gt),
                                  "--predictions", str(pred), "--output", str(output)])
        self.assertEqual(code, 0)
        self.assertIn("Micro accuracy=100.00%", out)
        self.assertIn("Evaluation workbook created", out)
        self.assertTrue(output.is_file())

    def test_matrix2_ambiguous_workbook_is_an_input_error(self):
        gt = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS, case_ids=range(1, 126))
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 101)))
        code, out = self.run_cli(["evaluate", "--workflow", "matrix2", "--input", str(gt),
                                  "--predictions", str(pred), "--output",
                                  str(self.dir / "e.xlsx")])
        self.assertEqual(code, 3)
        self.assertIn("ambiguous", out)

    def test_evaluate_input_errors(self):
        gt = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        pred = write_predictions(self.dir / "p.jsonl", reference_for(range(1, 100)))
        code, out = self.run_cli(["evaluate", "--workflow", "matrix1", "--input", str(gt),
                                  "--predictions", str(pred)])
        self.assertEqual(code, 3)
        self.assertIn("CaseID mismatch", out)

    def test_compare_references(self):
        clean = make_workbook(self.dir / "clean.xlsx", MATRIX1_HEADERS)
        code, out = self.run_cli(["compare-references", "--workflow", "matrix1",
                                  "--input", str(clean)])
        self.assertEqual(code, 0)
        self.assertIn("No differences", out)
        long = make_workbook(self.dir / "long.xlsx", MATRIX1_HEADERS, case_ids=range(1, 126))
        code, out = self.run_cli(["compare-references", "--workflow", "matrix1",
                                  "--input", str(long)])
        self.assertEqual(code, 1)
        self.assertIn("Case count differs: batch=100, evaluation=125", out)
        code, out = self.run_cli(["compare-references", "--workflow", "matrix2",
                                  "--input", str(clean)])
        self.assertEqual(code, 0)
        self.assertIn("No differences", out)


class TestWorkbookCompare(EvalTestCase):
    def make_pair(self):
        ids = range(1, 101)
        labels = reconcile(MATRIX1, as_reference(reference_for(ids)),
                           write_predictions(self.dir / "p.jsonl", random_predictions(ids)))
        result = compute_evaluation(labels)
        return [build_matrix1_workbook(labels, result.per_condition, result.micro, result.macro,
                                       self.dir / name, clock=StepClock())
                for name in ("a.xlsx", "b.xlsx")]

    def test_identical_workbooks(self):
        a, b = self.make_pair()
        self.assertEqual(compare_workbooks(a, b), [])

    def test_detects_value_style_and_structure_differences(self):
        from openpyxl.styles import Font

        a, b = self.make_pair()
        wb = load_workbook(b)
        wb["Condition Summary"]["B2"] = 999
        wb["Overall Summary"]["B12"].number_format = "0.0%"
        wb["Confusion Matrix"]["A3"].font = Font(bold=True)
        wb["Execution Log"].column_dimensions["B"].width = 10
        wb.save(b)
        joined = "\n".join(compare_workbooks(a, b))
        self.assertIn("[Condition Summary!B2] value", joined)
        self.assertIn("[Overall Summary!B12] style", joined)
        self.assertIn("[Confusion Matrix!A3] style", joined)
        self.assertIn("[Execution Log] column B width", joined)
        wb = load_workbook(b)
        wb["Metric Definitions"].title = "Definitions"
        wb.save(b)
        self.assertIn("Sheet names differ", compare_workbooks(a, b)[0])

    def test_numbers_compare_like_excel_but_other_types_stay_strict(self):
        from week_05.evaluation.workbook_compare import _values_equal

        self.assertTrue(_values_equal(1, 1.0, 0.0))
        self.assertTrue(_values_equal(0, 0.0, 0.0))
        self.assertFalse(_values_equal(True, 1, 0.0))
        self.assertFalse(_values_equal("1", 1, 0.0))
        self.assertFalse(_values_equal(None, 0, 0.0))
        self.assertFalse(_values_equal(0.5, 0.5000001, 0.0))

    def test_in_memory_workbooks_merges_heights_and_full_styles(self):
        from openpyxl.styles import Alignment, Border, Font, Side

        a, b = self.make_pair()
        expected, actual = load_workbook(a), load_workbook(b)
        self.assertEqual(compare_workbooks(expected, actual), [])
        sheet = actual["Overall Summary"]
        sheet.merge_cells("A1:D1")
        sheet.row_dimensions[5].height = 40
        sheet["A6"].alignment = Alignment(horizontal="right", vertical="top", wrap_text=True)
        sheet["A7"].font = Font(name="Arial")
        sheet["A8"].border = Border(left=Side(style="thin"))
        joined = "\n".join(compare_workbooks(expected, actual))
        self.assertIn("merged cells", joined)
        self.assertIn("row 5 height", joined)
        for cell in ("A6", "A7", "A8"):
            self.assertIn(f"[Overall Summary!{cell}] style", joined)

    def test_ignore_cells_and_float_tolerance(self):
        a, b = self.make_pair()
        wb = load_workbook(b)
        wb["Execution Log"]["B14"] = "2030-01-01 00:00:00 UTC"
        wb["Overall Summary"]["B10"] = wb["Overall Summary"]["B10"].value + 1e-12
        wb.save(b)
        self.assertEqual(len(compare_workbooks(a, b)), 2)
        self.assertEqual(compare_workbooks(a, b, ignore_cells=[("Execution Log", "B14")],
                                           float_tolerance=1e-9), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
