"""Week 7 evaluation: metrics, model identification, source separation and isolation.

Synthetic inputs and fake-classifier predictions only.
"""
from __future__ import annotations

import json
import shutil
from unittest import mock

from openpyxl import load_workbook

from week_07.batch_runner import run_workflow_batch
from week_07.conditions import CONDITION_KEYS
from week_07.config import GeminiModelConfig
from week_07.evaluation import evaluate as evaluate_module
from week_07.evaluation.evaluate import evaluate_workflow, write_evaluation_workbook
from week_07.evaluation.reconcile import EvaluationInputError
from week_07.isolation import IsolationError, ProtectedFileModified, sha256_file
from week_07.tests.fixtures import EchoClassifier, SyntheticRepo, reference_labels
from week_07.tests.gemini_fakes import RecordingSleep, StepClock
from week_07.tests.support import OfflineTestCase, quiet

M1_MODEL = "gemini-3.8-flash (Google Gemini, temperature 0.0, from Matrix 1 batch run manifest)"
M2_MODEL = "gemini-3.8-flash (Google Gemini, temperature 0.0, from Matrix 2 batch run manifest)"
FLIPS = {1: ("pneumonia", "rtm"), 7: ("cardiomegaly",), 42: ("esophagitis", "bronchitis")}


def expected_counts(case_ids, variant, flips):
    tp = fn = tn = fp = 0
    for case_id in case_ids:
        labels = reference_labels(case_id, variant)
        for condition in CONDITION_KEYS:
            actual = labels[condition]
            flipped = condition in flips.get(case_id, ())
            if actual == "Positive":
                fn, tp = (fn + 1, tp) if flipped else (fn, tp + 1)
            else:
                fp, tn = (fp + 1, tn) if flipped else (fp, tn + 1)
    return tp, fn, tn, fp


class EvaluationTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()

    def batch(self, name, variant, **kwargs):
        run_workflow_batch(self.repo.spec(name), classifier=EchoClassifier(variant, FLIPS),
                           settings=GeminiModelConfig(), isolation=self.repo.policy,
                           clock=StepClock(), sleep=RecordingSleep(), **kwargs)

    def evaluate(self, name, **kwargs):
        return evaluate_workflow(self.repo.spec(name), isolation=self.repo.policy, **kwargs)

    def write(self, name, result, output=None):
        return write_evaluation_workbook(self.repo.spec(name), result, output,
                                         isolation=self.repo.policy, clock=StepClock())


class TestMetricsAndWorkbooks(EvaluationTestCase):
    def test_matrix1_counts_against_vetology_labels(self):
        self.batch("matrix1", 0)
        result = self.evaluate("matrix1")
        m = result.micro
        self.assertEqual((m.tp, m.fn, m.tn, m.fp), expected_counts(range(1, 101), 0, FLIPS))
        self.assertEqual(m.total, 2000)
        self.assertEqual(result.model_record, M1_MODEL)

    def test_matrix2_counts_against_gold_standard_labels(self):
        self.batch("matrix2", 1)
        result = self.evaluate("matrix2")
        m = result.micro
        self.assertEqual((m.tp, m.fn, m.tn, m.fp), expected_counts(range(1, 101), 1, FLIPS))
        self.assertEqual(result.model_record, M2_MODEL)

    def test_matrices_use_different_reference_labels(self):
        self.batch("matrix1", 0)
        self.batch("matrix2", 1)
        m1, m2 = self.evaluate("matrix1"), self.evaluate("matrix2")
        self.assertNotEqual(dict(m1.labels.reference[1]), dict(m2.labels.reference[1]))
        self.assertEqual(dict(m1.labels.reference[1]), reference_labels(1, 0))
        self.assertEqual(dict(m2.labels.reference[1]), reference_labels(1, 1))

    def test_matrix1_workbook_identifies_gemini(self):
        self.batch("matrix1", 0)
        path = self.write("matrix1", self.evaluate("matrix1"))
        self.assertEqual(path, self.repo.m1.evaluation_workbook_path)
        book = load_workbook(path)
        self.assertEqual(book.sheetnames, ["Overall Summary", "Condition Summary",
                                           "Case Predictions", "Confusion Matrix",
                                           "Execution Log", "Metric Definitions"])
        log = book["Execution Log"]
        self.assertEqual((log["A12"].value, log["B12"].value), ("Model", M1_MODEL))
        self.assertEqual(log["B13"].value, "Canine Thorax Master Prompt V1.3")
        texts = [c.value for ws in book for row in ws.iter_rows() for c in row
                 if isinstance(c.value, str)]
        self.assertFalse(any("gpt" in t.lower() or "openai" in t.lower() for t in texts))

    def test_matrix2_workbook_identifies_gemini_and_week7(self):
        self.batch("matrix2", 1)
        path = self.write("matrix2", self.evaluate("matrix2"))
        book = load_workbook(path)
        self.assertEqual(book.sheetnames, ["Overall Summary", "Condition Summary",
                                           "Case Predictions", "Confusion Matrix",
                                           "Execution Log"])
        self.assertEqual(book["Overall Summary"]["A1"].value,
                         "VETOLOGY WEEK 7 - OVERALL EVALUATION SUMMARY")
        log = book["Execution Log"]
        self.assertEqual((log["A3"].value, log["C3"].value),
                         ("Prediction file", f"Model: {M2_MODEL}"))
        texts = [c.value for ws in book for row in ws.iter_rows() for c in row
                 if isinstance(c.value, str)]
        self.assertFalse(any("WEEK 4" in t or "gpt" in t.lower() for t in texts))

    def test_matrix1_requires_all_100_predictions(self):
        self.batch("matrix1", 0)
        lines = self.repo.m1.predictions_path.read_text(encoding="utf-8").splitlines()
        self.repo.m1.predictions_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(EvaluationInputError, "CaseID mismatch"):
            self.evaluate("matrix1")


class TestModelRecordAndProvenance(EvaluationTestCase):
    def _week5_style_copy(self, name):
        """Simulate a pre-existing Week 5 file (no Week 7 manifest) in the protected tree."""
        spec = self.repo.spec(name)
        spec.week5_output_dir.mkdir(parents=True)
        target = spec.week5_output_dir / "predictions.jsonl"
        shutil.copyfile(spec.predictions_path, target)
        return target

    def test_replay_without_manifest_is_marked_not_recorded(self):
        self.batch("matrix1", 0)
        replay = self._week5_style_copy("matrix1")
        result = self.evaluate("matrix1", predictions_path=replay)
        self.assertTrue(result.model_record.startswith("Not recorded"))
        override = self.evaluate("matrix1", predictions_path=replay,
                                 model_record="gpt-4.1-mini (Week 5 OpenAI predictions)")
        self.assertEqual(override.model_record, "gpt-4.1-mini (Week 5 OpenAI predictions)")
        with self.assertRaises(ValueError):
            self.evaluate("matrix1", predictions_path=replay, model_record="  ")

    def test_manifest_from_other_workflow_is_refused(self):
        self.batch("matrix1", 0)
        self.batch("matrix2", 1)
        rerun = self.repo.week7 / "matrix_1_rerun"
        rerun.mkdir()
        shutil.copyfile(self.repo.m1.predictions_path, rerun / "predictions.jsonl")
        shutil.copyfile(self.repo.m2.manifest_path, rerun / "run_manifest.json")
        with self.assertRaisesRegex(EvaluationInputError, "belongs to workflow"):
            self.evaluate("matrix1", predictions_path=rerun / "predictions.jsonl")

    def test_different_input_workbook_is_refused(self):
        self.batch("matrix2", 1)
        other = self.repo.root / "other_input.xlsx"
        shutil.copyfile(self.repo.m2.default_input_path, other)
        with open(other, "ab") as handle:
            handle.write(b"\0")  # different bytes, same content as far as openpyxl reads
        with self.assertRaisesRegex(EvaluationInputError, "different input workbook"):
            self.evaluate("matrix2", input_path=other)


class TestSourceSeparation(EvaluationTestCase):
    def test_other_matrix_sources_are_refused(self):
        self.batch("matrix2", 1)
        m2_week5 = self._place(self.repo.m2.week5_output_dir)
        m2_cmp = self._place(self.repo.m2.comparison_dir)
        for source in (self.repo.m2.predictions_path, m2_week5, m2_cmp):
            with self.subTest(source=source), self.assertRaises(EvaluationInputError):
                self.evaluate("matrix1", predictions_path=source)

    def _place(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "predictions.jsonl"
        shutil.copyfile(self.repo.m2.predictions_path, target)
        return target

    def test_workbook_output_isolation(self):
        self.batch("matrix1", 0)
        result = self.evaluate("matrix1")
        for target in (self.repo.week5 / "matrix_1" / "x.xlsx",
                       self.repo.m2.output_dir / "x.xlsx",
                       self.repo.m1.comparison_dir / "x.xlsx",
                       self.repo.root / "data" / "x.xlsx",
                       self.repo.root / "x.xlsx"):
            with self.subTest(target=target), self.assertRaises(IsolationError):
                self.write("matrix1", result, target)

    def test_result_cannot_be_written_as_the_other_matrix(self):
        self.batch("matrix1", 0)
        with self.assertRaises(ValueError):
            self.write("matrix2", self.evaluate("matrix1"))


class TestReadOnlySources(EvaluationTestCase):
    def test_digests_reported_and_sources_unchanged(self):
        self.batch("matrix2", 1)
        before = {p: sha256_file(p) for p in (self.repo.m2.default_input_path,
                                              self.repo.m2.predictions_path)}
        result = self.evaluate("matrix2")
        self.write("matrix2", result)
        self.assertEqual({p.resolve(): d for p, d in before.items()},
                         dict(result.source_digests))
        self.assertEqual(before, {p: sha256_file(p) for p in before})

    def test_change_during_evaluation_is_detected(self):
        self.batch("matrix2", 1)
        original = evaluate_module.reconcile

        def tampering_reconcile(spec, reference, path, **kwargs):
            labels = original(spec, reference, path, **kwargs)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write("\n")
            return labels

        with mock.patch.object(evaluate_module, "reconcile", tampering_reconcile):
            with self.assertRaises(ProtectedFileModified):
                self.evaluate("matrix2")

    def test_prediction_records_keep_week5_schema(self):
        self.batch("matrix2", 1, limit=3)
        for line in self.repo.m2.predictions_path.read_text(encoding="utf-8").splitlines():
            self.assertEqual(list(json.loads(line)),
                             ["case_id", "status", "attempts", "completed_at_utc", "predictions"])
