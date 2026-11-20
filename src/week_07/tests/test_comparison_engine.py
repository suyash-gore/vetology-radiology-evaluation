"""Comparison engine: per-workflow results, refusals and read-only guarantees (synthetic)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from unittest import mock

from week_07.comparison import compare as compare_module
from week_07.comparison.compare import compare_workflow
from week_07.comparison.sources import ComparisonInputError, OPENAI_MODEL_RECORD
from week_07.conditions import CONDITION_KEYS
from week_07.config import REPO_ROOT
from week_07.evaluation.reconcile import EvaluationInputError
from week_07.isolation import ProtectedFileModified, sha256_file
from week_07.tests.fixtures import (
    GEMINI_FLIPS,
    OPENAI_FLIPS,
    SyntheticRepo,
    predicted_labels,
    reference_labels,
    run_week7_gemini,
    write_week5_openai,
)
from week_07.tests.support import OfflineTestCase, quiet

VARIANT = {"matrix1": 0, "matrix2": 1}


def brute_force(variant):
    ids = range(1, 101)
    out = {"agree": 0, "both_pos": 0, "only_gemini_correct": 0, "only_openai_correct": 0,
           "both_wrong": 0, "openai_tp": 0, "gemini_fp": 0}
    for c in ids:
        ref = reference_labels(c, variant)
        o = predicted_labels(c, variant, OPENAI_FLIPS)
        g = predicted_labels(c, variant, GEMINI_FLIPS)
        for k in CONDITION_KEYS:
            out["agree"] += o[k] == g[k]
            out["both_pos"] += o[k] == g[k] == "Positive"
            out["only_gemini_correct"] += g[k] == ref[k] != o[k]
            out["only_openai_correct"] += o[k] == ref[k] != g[k]
            out["both_wrong"] += o[k] != ref[k] and g[k] != ref[k]
            out["openai_tp"] += o[k] == ref[k] == "Positive"
            out["gemini_fp"] += g[k] == "Positive" and ref[k] == "Negative"
    return out


class EngineTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()

    def prepare(self, name, **openai_kwargs):
        write_week5_openai(self.repo, name, VARIANT[name], **openai_kwargs)
        run_week7_gemini(self.repo, name, VARIANT[name])

    def compare(self, name, **kwargs):
        return compare_workflow(self.repo.spec(name), isolation=self.repo.policy, **kwargs)


class TestResults(EngineTestCase):
    def test_both_workflows_match_brute_force(self):
        for name in ("matrix1", "matrix2"):
            with self.subTest(workflow=name):
                self.prepare(name)
                result = self.compare(name)
                expected = brute_force(VARIANT[name])
                self.assertEqual(result.workflow, name)
                self.assertEqual(result.case_ids, tuple(range(1, 101)))
                self.assertEqual(result.agreement_total.agreements, expected["agree"])
                self.assertEqual(result.agreement_total.both_positive, expected["both_pos"])
                self.assertEqual(result.correctness_total.only_gemini_correct,
                                 expected["only_gemini_correct"])
                self.assertEqual(result.correctness_total.only_openai_correct,
                                 expected["only_openai_correct"])
                self.assertEqual(result.correctness_total.both_wrong, expected["both_wrong"])
                self.assertEqual(result.openai_evaluation.micro.tp, expected["openai_tp"])
                self.assertEqual(result.gemini_evaluation.micro.fp, expected["gemini_fp"])
                self.assertEqual(len(result.disagreements), 2000 - expected["agree"])

    def test_reference_labels_are_the_workflows_own(self):
        self.prepare("matrix1")
        self.prepare("matrix2")
        m1, m2 = self.compare("matrix1"), self.compare("matrix2")
        self.assertEqual(m1.reference_description, "Original Vetology condition scores")
        self.assertEqual(m2.reference_description, "Gold Standard condition scores")
        self.assertNotEqual(m1.openai_evaluation.micro, m2.openai_evaluation.micro)

    def test_model_records_and_provenance(self):
        self.prepare("matrix2", error_case_ids=range(1, 101))
        result = self.compare("matrix2")
        self.assertEqual(result.openai.model_record, OPENAI_MODEL_RECORD)
        self.assertTrue(result.gemini.model_record.startswith("gemini-3.8-flash (Google Gemini"))
        self.assertEqual(result.openai_evaluation.model_record, OPENAI_MODEL_RECORD)
        self.assertEqual(result.openai.errors.superseded_records, 100)
        spec = self.repo.m2
        expected = {p.resolve(): sha256_file(p) for p in (
            spec.default_input_path, spec.week5_predictions_path, spec.week5_errors_path,
            spec.predictions_path, spec.manifest_path)}
        self.assertEqual(dict(result.source_digests), expected)
        self.assertEqual(result.reference.sha256, sha256_file(spec.default_input_path))

    def test_skipped_lines_are_reported_not_hidden(self):
        self.prepare("matrix2", extra_lines=['{"case_id": 9, "sta'])
        result = self.compare("matrix2")
        self.assertEqual([s.line_number for s in result.openai.records.skipped], [101])
        self.assertEqual([s.line_number for s in
                          result.openai_evaluation.labels.skipped_lines], [101])


class TestRefusals(EngineTestCase):
    def test_unresolved_failure_refused(self):
        self.prepare("matrix2", case_ids=range(1, 100), error_case_ids=[100])
        with self.assertRaisesRegex(ComparisonInputError, "final failures"):
            self.compare("matrix2")

    def test_missing_and_extra_cases_refused(self):
        for case_ids in (range(1, 100), range(1, 102)):
            with self.subTest(n=len(case_ids)):
                self.prepare("matrix2", case_ids=case_ids)
                with self.assertRaisesRegex(EvaluationInputError, "CaseID mismatch"):
                    self.compare("matrix2")

    def test_duplicate_records_refused(self):
        extra = [json.dumps({"case_id": 3, "status": "success", "attempts": 1,
                             "predictions": reference_labels(3, 1)})]
        self.prepare("matrix2", extra_lines=extra)
        with self.assertRaisesRegex(EvaluationInputError, "Duplicate"):
            self.compare("matrix2")

    def test_matrix1_needs_exactly_100_cases(self):
        self.repo.write_inputs(m1_cases=range(1, 101))
        self.prepare("matrix1", case_ids=range(1, 100))
        with self.assertRaises(EvaluationInputError):
            self.compare("matrix1")

    def test_same_file_and_identical_copy_refused(self):
        self.prepare("matrix2")
        with self.assertRaisesRegex(ComparisonInputError, "same file"):
            self.compare("matrix2", openai_path=self.repo.m2.predictions_path)
        shutil.copyfile(self.repo.m2.predictions_path, self.repo.m2.week5_predictions_path)
        with self.assertRaisesRegex(ComparisonInputError, "identical content"):
            self.compare("matrix2")

    def test_cross_matrix_inputs_refused(self):
        self.prepare("matrix1")
        self.prepare("matrix2")
        cases = {
            "matrix2 OpenAI as matrix1": {"openai_path": self.repo.m2.week5_predictions_path},
            "matrix2 Gemini as matrix1": {"gemini_path": self.repo.m2.predictions_path},
            "matrix2 reference for matrix1": {"reference_path": self.repo.m2.default_input_path},
        }
        for label, kwargs in cases.items():
            with self.subTest(case=label), self.assertRaises(EvaluationInputError):
                self.compare("matrix1", **kwargs)

    def test_missing_sources(self):
        with self.assertRaises(FileNotFoundError):
            self.compare("matrix1")


class TestReadOnly(EngineTestCase):
    def test_sources_unchanged(self):
        self.prepare("matrix1", error_case_ids=range(1, 101))
        spec = self.repo.m1
        files = [spec.default_input_path, spec.week5_predictions_path, spec.week5_errors_path,
                 spec.predictions_path, spec.manifest_path]
        before = [sha256_file(p) for p in files]
        self.compare("matrix1")
        self.assertEqual(before, [sha256_file(p) for p in files])

    def test_change_during_comparison_detected(self):
        self.prepare("matrix2")
        original = compare_module.reconcile
        target = self.repo.m2.week5_predictions_path

        def tampering(spec, reference, path, **kwargs):
            labels = original(spec, reference, path, **kwargs)
            with open(target, "a", encoding="utf-8") as handle:
                handle.write("\n")
            return labels

        with mock.patch.object(compare_module, "reconcile", tampering):
            with self.assertRaises(ProtectedFileModified):
                self.compare("matrix2")


class TestNoModelClientImported(OfflineTestCase):
    def test_comparison_imports_no_llm_client_or_sdk(self):
        code = (
            "import sys; import week_07.comparison.compare, week_07.comparison.sources, "
            "week_07.comparison.agreement; "
            "bad = [m for m in ('week_07.llm_client', 'week_07.batch_runner', "
            "'week_07.error_policy', 'langchain_google_genai', 'google.genai', 'openai', "
            "'langchain_openai', 'langchain_core') if m in sys.modules]; print(bad)"
        )
        result = subprocess.run([sys.executable, "-I", "-c",
                                 f"import sys; sys.path.insert(0, {str(REPO_ROOT / 'src')!r}); "
                                 + code],
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), "[]")
