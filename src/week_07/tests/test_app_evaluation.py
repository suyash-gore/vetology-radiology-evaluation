"""Evaluation and workbooks for Feline Thorax and Canine Abdomen (synthetic, offline)."""
from __future__ import annotations

import json
import logging

from openpyxl import load_workbook

from week_07.dataset_loader import DatasetError
from week_07.evaluation.app_reconcile import load_application_prediction_records
from week_07.evaluation.evaluate import (
    evaluate_application,
    evaluate_workflow,
    write_application_workbook,
)
from week_07.evaluation.metrics import condition_metrics
from week_07.evaluation.reconcile import EvaluationInputError
from week_07.isolation import IsolationError, ProtectedFileModified
from week_07.tests.app_fixtures import AppEchoClassifier, SyntheticAppRepo, app_reference
from week_07.tests.gemini_fakes import StepClock
from week_07.tests.support import OfflineTestCase

M1_SHEETS = ["Overall Summary", "Condition Summary", "Case Predictions", "Confusion Matrix",
             "Execution Log", "Metric Definitions"]
M2_SHEETS = ["Overall Summary", "Condition Summary", "Case Predictions", "Confusion Matrix",
             "Execution Log"]


def sheet_rows(path, name):
    workbook = load_workbook(path, read_only=True)
    try:
        return [list(row) for row in workbook[name].iter_rows(values_only=True)]
    finally:
        workbook.close()


class EvaluationCase(OfflineTestCase):
    key = "feline_thorax"
    flips = {1: ("pneumonia",), 9: ("rtm", "cardiomegaly"), 50: ("Fe_Alveolar",)}

    def setUp(self):
        super().setUp()
        logging.getLogger("week_07").setLevel(logging.CRITICAL)
        self.addCleanup(logging.getLogger("week_07").setLevel, logging.NOTSET)
        self.repo = SyntheticAppRepo(self.key)
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()
        self.app = self.repo.app
        if self.key == "canine_abdomen":
            self.flips = {1: ("gastritis",), 9: ("ascites", "colitis"), 50: ("hepatomegaly",)}
        self.repo.run_batch(AppEchoClassifier(self.app, variant=0, flips=self.flips))

    def evaluate(self, workflow, **kwargs):
        spec = self.app.workflow(workflow)
        kwargs.setdefault("prediction_source_input", self.repo.m1.default_input_path
                          if workflow == "matrix2" else None)
        return evaluate_application(self.app, workflow, spec.default_input_path,
                                    isolation=self.repo.policy, **kwargs)

    def write(self, workflow, result):
        return write_application_workbook(self.app, workflow, result,
                                          isolation=self.repo.policy, clock=StepClock())


class TestMatrix1(EvaluationCase):
    def test_exact_metrics_against_matrix1_reference(self):
        result = self.evaluate("matrix1")
        flipped = sum(len(v) for v in self.flips.values())
        n = self.app.condition_count
        self.assertEqual(result.micro.total, 100 * n)
        self.assertEqual(result.micro.tp + result.micro.tn, 100 * n - flipped)
        self.assertEqual(result.application, self.key)
        self.assertEqual(tuple(result.per_condition), self.app.condition_keys)
        expected = condition_metrics(
            {c: app_reference(self.app, c, 0) for c in range(1, 101)},
            result.labels.predictions, list(range(1, 101)), conditions=self.app.condition_keys)
        self.assertEqual({k: v.as_dict() for k, v in result.per_condition.items()},
                         {k: v.as_dict() for k, v in expected.items()})
        self.assertIn("gpt-4.1-mini (OpenAI, temperature 0.0", result.model_record)

    def test_workbook_layout_counts_and_headers(self):
        path = self.write("matrix1", self.evaluate("matrix1"))
        self.assertEqual(path, self.repo.m1.evaluation_workbook_path)
        self.assertEqual(load_workbook(path, read_only=True).sheetnames, M1_SHEETS)
        keys = list(self.app.condition_keys)
        summary = sheet_rows(path, "Overall Summary")
        self.assertEqual(summary[3][:2], ["Conditions evaluated", len(keys)])
        self.assertEqual(summary[3][3], f"All {len(keys)} Matrix 1 conditions evaluated "
                                        "independently.")
        conditions = sheet_rows(path, "Condition Summary")
        self.assertEqual([row[0] for row in conditions[1:-1]], keys)
        self.assertEqual(conditions[-1][0], "TOTAL")
        header = sheet_rows(path, "Case Predictions")[0]
        self.assertEqual(len(header), 1 + 3 * len(keys))
        self.assertEqual(header[1:4], [f"{keys[0]} - Gold Standard",
                                       f"{keys[0]} - Model Prediction", f"{keys[0]} - Agreement"])
        self.assertEqual(header[-3], f"{keys[-1]} - Gold Standard")
        self.assertEqual(len(sheet_rows(path, "Case Predictions")), 101)
        confusion = sheet_rows(path, "Confusion Matrix")
        self.assertEqual([row[0] for row in confusion[1:-1]], keys)
        log = {row[0]: row[1] for row in sheet_rows(path, "Execution Log")}
        self.assertEqual(log["Conditions"], len(keys))
        self.assertEqual(log["Expected paired labels"], 100 * len(keys))
        self.assertEqual(log["Prompt version"], self.app.prompt.label)
        self.assertIn(f"exact {len(keys)} keys", log["Prediction validation"])
        self.assertIn("Matrix 1 only", log["Evaluation Track"])

    def test_matrix1_rejects_a_foreign_prediction_source_input(self):
        with self.assertRaises(ValueError):
            self.evaluate("matrix1", prediction_source_input=self.repo.m2.default_input_path)


class TestMatrix2(EvaluationCase):
    def test_same_predictions_against_gold_standard(self):
        r1, r2 = self.evaluate("matrix1"), self.evaluate("matrix2")
        self.assertEqual(dict(r1.labels.predictions), dict(r2.labels.predictions))
        self.assertNotEqual(dict(r1.labels.reference), dict(r2.labels.reference))
        self.assertEqual(r2.labels.reference[1], app_reference(self.app, 1, 1))
        self.assertEqual(r2.labels.predictions_source, self.repo.m1.predictions_path)

    def test_workbook_layout_counts_and_headers(self):
        path = self.write("matrix2", self.evaluate("matrix2"))
        self.assertEqual(path, self.repo.m2.evaluation_workbook_path)
        self.assertEqual(load_workbook(path, read_only=True).sheetnames, M2_SHEETS)
        keys = list(self.app.condition_keys)
        conditions = sheet_rows(path, "Condition Summary")
        self.assertEqual([row[0] for row in conditions[1:-1]], keys)
        self.assertEqual(conditions[-1][0], "MICRO TOTAL")
        self.assertEqual([row[0] for row in sheet_rows(path, "Confusion Matrix")[1:-1]], keys)
        self.assertEqual(len(sheet_rows(path, "Case Predictions")[0]), 1 + 3 * len(keys))
        summary = {row[0]: row for row in sheet_rows(path, "Overall Summary") if row[0]}
        self.assertEqual(summary["Conditions evaluated"][1], len(keys))
        self.assertEqual(summary["Total evaluated labels"][2],
                         f"100 cases × {len(keys)} conditions")
        log = {row[0]: row for row in sheet_rows(path, "Execution Log") if row[0]}
        self.assertEqual(log["Dataset"][1],
                         f"{self.app.region_phrase.capitalize()} Gold Standard pilot")
        self.assertEqual(log["Conditions per case"][1], len(keys))
        self.assertTrue(log["Prediction file"][2].startswith("Model: gpt-4.1-mini"))
        self.assertIn(f"exact {len(keys)} condition keys", log["Validation"][1])

    def test_cross_matrix_mismatch_refused(self):
        self.repo.write_inputs(m2_cases=[2, 1, *range(3, 101)])
        with self.assertRaises(DatasetError):
            self.evaluate("matrix2")

    def test_matrix2_requires_the_matrix1_source_workbook(self):
        with self.assertRaises(FileNotFoundError):
            self.evaluate("matrix2", prediction_source_input=self.repo.root / "missing.xlsx")


class TestManifestAndSourceChecks(EvaluationCase):
    def _rewrite_identity(self, **changes):
        path = self.repo.m1.manifest_path
        data = json.loads(path.read_text())
        data["identity"].update(changes)
        path.write_text(json.dumps(data))

    def test_manifest_of_another_application_refused(self):
        for changes in ({"application": "canine_abdomen"},
                        {"condition_keys": ["pneumonia"]},
                        {"provider": "Google Gemini via langchain-google-genai"},
                        {"prediction_source_workflow": "matrix2"},
                        {"prompt": {"name": "Canine Thorax Master Prompt", "version": "V1.3"}}):
            with self.subTest(changes=list(changes)):
                original = self.repo.m1.manifest_path.read_text()
                self._rewrite_identity(**changes)
                with self.assertRaises(EvaluationInputError):
                    self.evaluate("matrix1")
                self.repo.m1.manifest_path.write_text(original)

    def test_digest_mismatch_refused(self):
        def edit(case_id, row):
            row["Findings (original radiologist report)"] += " "
            return row
        self.repo.write_inputs(edit_m1=edit)
        with self.assertRaisesRegex(EvaluationInputError, "different input workbook"):
            self.evaluate("matrix1")

    def test_missing_manifest_refused(self):
        self.repo.m1.manifest_path.unlink()
        with self.assertRaisesRegex(EvaluationInputError, "No run manifest"):
            self.evaluate("matrix1")

    def test_predictions_outside_own_tree_refused(self):
        foreign = self.repo.week7 / "matrix_1" / "predictions.jsonl"
        foreign.parent.mkdir(parents=True)
        foreign.write_text(self.repo.m1.predictions_path.read_text())
        with self.assertRaises(EvaluationInputError):
            self.evaluate("matrix1", predictions_path=foreign)
        other = self.repo.week7 / "canine_abdomen" / "custom" / "predictions.jsonl"
        other.parent.mkdir(parents=True)
        other.write_text("{}\n")
        with self.assertRaises(EvaluationInputError):
            self.evaluate("matrix2", predictions_path=other)

    def test_strict_prediction_records(self):
        path = self.repo.m1.predictions_path
        lines = path.read_text().splitlines()
        record = json.loads(lines[0])
        record["predictions"]["extra"] = "Negative"
        path.write_text("\n".join([json.dumps(record), *lines[1:]]) + "\n")
        with self.assertRaisesRegex(EvaluationInputError, "keys mismatch"):
            load_application_prediction_records(path, self.app.condition_keys)

    def test_missing_case_refused(self):
        path = self.repo.m1.predictions_path
        lines = path.read_text().splitlines()
        path.write_text("\n".join(lines[:-1]) + "\n")
        with self.assertRaisesRegex(EvaluationInputError, "CaseID mismatch"):
            self.evaluate("matrix1")

    def test_workbook_isolation_and_result_identity(self):
        result = self.evaluate("matrix1")
        with self.assertRaises(ValueError):
            write_application_workbook(self.app, "matrix2", result, isolation=self.repo.policy)
        for target in (self.repo.m2.output_dir / "x.xlsx", self.repo.week7 / "matrix_1" / "x.xlsx",
                       self.repo.week7 / "canine_abdomen" / "x.xlsx"):
            with self.subTest(target=str(target)), self.assertRaises(IsolationError):
                write_application_workbook(self.app, "matrix1", result, target,
                                           isolation=self.repo.policy)

    def test_sources_are_read_only_checked(self):
        from unittest import mock

        from week_07.evaluation import app_reconcile

        original = app_reconcile.load_application_prediction_records

        def tamper(path, keys):
            records = original(path, keys)
            with path.open("a") as handle:
                handle.write("\n")
            return records

        with mock.patch.object(app_reconcile, "load_application_prediction_records", tamper):
            with self.assertRaises(ProtectedFileModified):
                self.evaluate("matrix1")

    def test_canine_thorax_evaluation_refuses_application_manifest(self):
        canine = self.repo.specs["canine_thorax/matrix1"]
        target = canine.output_dir / "predictions.jsonl"
        target.parent.mkdir(parents=True)
        target.write_text(self.repo.m1.predictions_path.read_text())
        (canine.output_dir / "run_manifest.json").write_text(
            self.repo.m1.manifest_path.read_text())
        with self.assertRaisesRegex(EvaluationInputError, "belongs to application"):
            evaluate_workflow(canine, self.repo.m1.default_input_path, target,
                              isolation=self.repo.policy)


class TestCanineAbdomenEvaluation(EvaluationCase):
    key = "canine_abdomen"

    def test_both_workbooks_with_ten_conditions(self):
        for workflow, sheets, total in (("matrix1", M1_SHEETS, "TOTAL"),
                                        ("matrix2", M2_SHEETS, "MICRO TOTAL")):
            with self.subTest(workflow=workflow):
                result = self.evaluate(workflow)
                self.assertEqual(result.micro.total, 1000)
                path = self.write(workflow, result)
                self.assertEqual(load_workbook(path, read_only=True).sheetnames, sheets)
                rows = sheet_rows(path, "Condition Summary")
                self.assertEqual([r[0] for r in rows[1:-1]], list(self.app.condition_keys))
                self.assertEqual(rows[-1][0], total)
                self.assertEqual(len(sheet_rows(path, "Case Predictions")[0]), 31)
