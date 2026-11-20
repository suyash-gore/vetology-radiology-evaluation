"""Comparison sources: provenance, strict loading and transparent error-log reconciliation."""
from __future__ import annotations

import json
import shutil

from week_07.comparison.sources import (
    GEMINI,
    OPENAI,
    OPENAI_MODEL_RECORD,
    ComparisonInputError,
    load_prediction_source,
    read_error_log,
    source_files,
)
from week_07.evaluation.reconcile import EvaluationInputError
from week_07.isolation import sha256_file
from week_07.tests.fixtures import (
    SyntheticRepo,
    run_week7_gemini,
    write_week5_openai,
)
from week_07.tests.support import OfflineTestCase, quiet


class SourceTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()

    def load(self, role, name, path=None, errors=None):
        spec = self.repo.spec(name)
        return load_prediction_source(role, spec, path, spec.default_input_path, errors,
                                      isolation=self.repo.policy)


class TestOpenAISource(SourceTestCase):
    def test_week5_default_path_and_model_record(self):
        path = write_week5_openai(self.repo, "matrix1", 0)
        source = self.load(OPENAI, "matrix1")
        self.assertEqual(source.provenance.path, path.resolve())
        self.assertEqual(source.provenance.sha256, sha256_file(path))
        self.assertEqual(source.model_record, OPENAI_MODEL_RECORD)
        self.assertEqual(OPENAI_MODEL_RECORD,
                         "gpt-4.1-mini (Week 5 configuration; model identity inferred from "
                         "configuration, not embedded in prediction file)")
        self.assertEqual(len(source.labels), 100)
        self.assertIsNone(source.manifest_identity)
        self.assertEqual(source.errors.origin, "none")

    def test_b1_superseded_errors_are_not_final_failures(self):
        write_week5_openai(self.repo, "matrix1", 0, error_case_ids=range(1, 101))
        errors = self.load(OPENAI, "matrix1").errors
        self.assertEqual(errors.origin, "auto-detected")
        self.assertEqual((errors.records, errors.superseded_records, errors.unresolved_records),
                         (100, 100, 0))
        self.assertEqual(len(errors.superseded), 100)
        self.assertIn("100 superseded", errors.describe())

    def test_unresolved_error_is_reported(self):
        write_week5_openai(self.repo, "matrix2", 1, case_ids=range(1, 100),
                           error_case_ids=[100, 100, 5])
        errors = self.load(OPENAI, "matrix2").errors
        self.assertEqual(dict(errors.unresolved), {100: 2})
        self.assertEqual(dict(errors.superseded), {5: 1})

    def test_source_with_week7_manifest_is_refused_as_openai(self):
        run_week7_gemini(self.repo, "matrix2", 1)
        with self.assertRaisesRegex(ComparisonInputError, "run manifest"):
            self.load(OPENAI, "matrix2", self.repo.m2.predictions_path)

    def test_strict_loading_is_not_relaxed(self):
        cases = {
            "duplicate": ['{"case_id": 5, "status": "success", "predictions": {}}'],
            "non-success": ['{"case_id": 101, "status": "failed"}'],
        }
        for label, extra in cases.items():
            with self.subTest(case=label):
                write_week5_openai(self.repo, "matrix2", 1, extra_lines=extra)
                with self.assertRaises(EvaluationInputError):
                    self.load(OPENAI, "matrix2")

    def test_unparseable_lines_are_skipped_and_reported(self):
        write_week5_openai(self.repo, "matrix2", 1, extra_lines=['{"case_id": 101, "sta'])
        source = self.load(OPENAI, "matrix2")
        self.assertEqual(len(source.records.skipped), 1)
        self.assertEqual(source.records.skipped[0].line_number, 101)


class TestGeminiSource(SourceTestCase):
    def test_manifest_provenance(self):
        run_week7_gemini(self.repo, "matrix1", 0)
        source = self.load(GEMINI, "matrix1")
        self.assertEqual(source.model_record, "gemini-3.8-flash (Google Gemini, temperature 0.0, "
                                              "from Matrix 1 batch run manifest)")
        self.assertEqual(source.manifest_identity["workflow"], "matrix1")
        self.assertEqual(source.manifest_provenance.sha256,
                         sha256_file(self.repo.m1.manifest_path))

    def test_gemini_without_manifest_refused(self):
        run_week7_gemini(self.repo, "matrix2", 1)
        self.repo.m2.manifest_path.unlink()
        with self.assertRaisesRegex(ComparisonInputError, "no Week 7 run manifest"):
            self.load(GEMINI, "matrix2")

    def test_manifest_for_other_workflow_refused(self):
        run_week7_gemini(self.repo, "matrix1", 0)
        run_week7_gemini(self.repo, "matrix2", 1)
        shutil.copyfile(self.repo.m2.manifest_path, self.repo.m1.manifest_path)
        with self.assertRaisesRegex(ComparisonInputError, "belongs to workflow"):
            self.load(GEMINI, "matrix1")

    def test_reference_digest_mismatch_refused(self):
        run_week7_gemini(self.repo, "matrix2", 1)
        with open(self.repo.m2.default_input_path, "ab") as handle:
            handle.write(b"\0")
        with self.assertRaisesRegex(ComparisonInputError, "different input workbook"):
            self.load(GEMINI, "matrix2")

    def test_week7_error_log_auto_detected(self):
        def flaky(payload):
            from week_07.tests.fixtures import EchoClassifier, case_from_payload
            return "not json" if case_from_payload(payload) == 4 else EchoClassifier(1)(payload)

        from week_07.batch_runner import run_workflow_batch
        from week_07.config import GeminiModelConfig
        from week_07.tests.gemini_fakes import RecordingSleep, StepClock

        run_workflow_batch(self.repo.m2, classifier=flaky, settings=GeminiModelConfig(),
                           isolation=self.repo.policy, clock=StepClock(),
                           sleep=RecordingSleep(), limit=5)
        errors = self.load(GEMINI, "matrix2").errors
        self.assertEqual(dict(errors.unresolved), {4: 1})


class TestSeparationAndFiles(SourceTestCase):
    def test_other_matrix_sources_refused(self):
        write_week5_openai(self.repo, "matrix2", 1)
        run_week7_gemini(self.repo, "matrix2", 1)
        for role, path in ((OPENAI, self.repo.m2.week5_predictions_path),
                           (GEMINI, self.repo.m2.predictions_path)):
            with self.subTest(role=role), self.assertRaises(EvaluationInputError):
                self.load(role, "matrix1", path)

    def test_missing_files(self):
        with self.assertRaises(FileNotFoundError):
            self.load(OPENAI, "matrix1")
        write_week5_openai(self.repo, "matrix1", 0)
        with self.assertRaises(FileNotFoundError):
            self.load(OPENAI, "matrix1", errors=self.repo.root / "missing.jsonl")

    def test_source_files_lists_everything_read(self):
        write_week5_openai(self.repo, "matrix1", 0, error_case_ids=[3])
        run_week7_gemini(self.repo, "matrix1", 0)
        self.assertEqual(source_files(self.repo.m1.week5_predictions_path, None),
                         [self.repo.m1.week5_predictions_path, self.repo.m1.week5_errors_path])
        self.assertEqual(source_files(self.repo.m1.predictions_path, None),
                         [self.repo.m1.predictions_path, self.repo.m1.manifest_path])

    def test_loading_never_modifies_sources(self):
        write_week5_openai(self.repo, "matrix1", 0, error_case_ids=range(1, 11))
        files = [self.repo.m1.week5_predictions_path, self.repo.m1.week5_errors_path]
        before = [sha256_file(p) for p in files]
        self.load(OPENAI, "matrix1")
        self.assertEqual(before, [sha256_file(p) for p in files])


class TestErrorLogRules(SourceTestCase):
    def write(self, *lines):
        path = self.repo.root / "errors.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_malformed_records_are_errors_not_silent_exclusions(self):
        for line in ('["list"]', '{"status": "failed"}',
                     '{"case_id": "x", "status": "failed"}',
                     '{"case_id": 1, "status": "success"}',
                     '{"case_id": true, "status": "failed"}'):
            with self.subTest(line=line), self.assertRaises(ComparisonInputError):
                read_error_log(self.write(line), {1}, "supplied")

    def test_unparseable_line_skipped_and_reported(self):
        summary = read_error_log(self.write('{"case_id": 1, "status": "failed"}', '{"case'),
                                 {1}, "supplied")
        self.assertEqual((summary.records, len(summary.skipped_lines)), (1, 1))
        self.assertIn("1 unreadable line", summary.describe())

    def test_case_id_conversion_matches_prediction_loader(self):
        summary = read_error_log(self.write(json.dumps({"case_id": "7", "status": "failed"}),
                                            json.dumps({"case_id": 8.0, "status": "failed"})),
                                 {7}, "supplied")
        self.assertEqual((dict(summary.superseded), dict(summary.unresolved)), ({7: 1}, {8: 1}))
