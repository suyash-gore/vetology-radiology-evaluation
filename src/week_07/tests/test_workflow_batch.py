"""Independent Matrix 1 / Matrix 2 workflow execution (synthetic data, fake classifier)."""
from __future__ import annotations

import json
import os
from unittest import mock

from week_07 import config, run_manifest
from week_07.batch_runner import resolve_outputs, run_workflow_batch
from week_07.config import ConfigurationError, GeminiModelConfig, RetryPolicy
from week_07.dataset_loader import DatasetError
from week_07.error_policy import FatalProviderError
from week_07.isolation import IsolationError, sha256_file
from week_07.prompts.prompt_loader import PROMPT_FILE_SHA256, PROMPT_TEXT_SHA256
from week_07.run_manifest import ManifestMismatch
from week_07.tests.fixtures import (
    LEAK_MARKER,
    EchoClassifier,
    SyntheticRepo,
    case_from_payload,
)
from week_07.tests.gemini_fakes import RecordingSleep, StepClock, sdk_error
from week_07.tests.support import OfflineTestCase, quiet

SETTINGS = GeminiModelConfig()


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


class WorkflowTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()
        self.sleep = RecordingSleep()

    def run_workflow(self, name, classifier, **kwargs):
        kwargs.setdefault("settings", SETTINGS)
        return run_workflow_batch(self.repo.spec(name), classifier=classifier,
                                  isolation=self.repo.policy, clock=StepClock(),
                                  sleep=self.sleep, **kwargs)


class TestMatrixWorkflows(WorkflowTestCase):
    def test_matrix1_runs_exactly_100_vetology_cases(self):
        classifier = EchoClassifier(variant=0)
        counts = self.run_workflow("matrix1", classifier)
        self.assertEqual((counts["total"], counts["succeeded"], counts["failed"]), (100, 100, 0))
        records = read_jsonl(self.repo.m1.predictions_path)
        self.assertEqual([r["case_id"] for r in records], list(range(1, 101)))
        self.assertFalse(self.repo.m1.errors_path.exists())

    def test_matrix1_rejects_limit(self):
        with self.assertRaises(ValueError):
            self.run_workflow("matrix1", EchoClassifier(), limit=10)

    def test_matrix1_requires_100_cases(self):
        self.repo.write_inputs(m1_cases=range(1, 60))
        with self.assertRaises(DatasetError):
            self.run_workflow("matrix1", EchoClassifier())
        self.assertFalse(self.repo.m1.manifest_path.exists())

    def test_matrix2_runs_gold_standard_input_with_limit(self):
        counts = self.run_workflow("matrix2", EchoClassifier(variant=1), limit=5)
        self.assertEqual((counts["total"], counts["succeeded"]), (5, 5))
        self.assertEqual([r["case_id"] for r in read_jsonl(self.repo.m2.predictions_path)],
                         [1, 2, 3, 4, 5])

    def test_first_100_reports_only(self):
        self.repo.write_inputs(m1_cases=range(1, 121), m2_cases=range(1, 121))
        m1, m2 = EchoClassifier(0), EchoClassifier(1)
        self.run_workflow("matrix1", m1)
        self.run_workflow("matrix2", m2)
        for classifier in (m1, m2):
            self.assertEqual(sorted(case_from_payload(p) for p in classifier.calls),
                             list(range(1, 101)))

    def test_workflows_write_only_their_own_directories(self):
        self.run_workflow("matrix1", EchoClassifier(0))
        self.assertTrue(self.repo.m1.predictions_path.exists())
        self.assertFalse(self.repo.m2.output_dir.exists())
        self.run_workflow("matrix2", EchoClassifier(1), limit=3)
        self.assertEqual(len(read_jsonl(self.repo.m1.predictions_path)), 100)
        self.assertEqual(len(read_jsonl(self.repo.m2.predictions_path)), 3)
        written = {p.relative_to(self.repo.root).as_posix()
                   for p in self.repo.root.rglob("*") if p.is_file()}
        self.assertEqual(written - {
            "data/week_04_inputs/Vetology_Matrix1_First100_Encoded.xlsx",
            "data/week_04_inputs/1_canine_thorax_gold_standard_score_draft.xlsx",
        }, {"outputs/week_07/matrix_1/predictions.jsonl",
            "outputs/week_07/matrix_1/run_manifest.json",
            "outputs/week_07/matrix_2/predictions.jsonl",
            "outputs/week_07/matrix_2/run_manifest.json"})


class TestModelInputRestriction(WorkflowTestCase):
    def test_only_findings_conclusions_recommendations_reach_gemini(self):
        for name, variant in (("matrix1", 0), ("matrix2", 1)):
            with self.subTest(workflow=name):
                classifier = EchoClassifier(variant)
                self.run_workflow(name, classifier, **({"limit": 20} if name == "matrix2" else {}))
                for payload in classifier.calls:
                    self.assertEqual(set(payload), {"findings", "conclusions", "recommendations"})
                    text = json.dumps(payload)
                    self.assertNotIn(LEAK_MARKER, text)          # AI fields, radiologist, legacy
                    self.assertNotIn("Positive", text)            # reference labels
                    self.assertNotIn("Negative", text)
                    self.assertNotIn("case_id", text.lower().replace("caseid", "case_id"))

    def test_outputs_contain_no_report_text_or_reference_labels_marker(self):
        self.run_workflow("matrix1", EchoClassifier(0))
        text = self.repo.all_output_text()
        self.assertNotIn("Synthetic findings", text)
        self.assertNotIn(LEAK_MARKER, text)

    def test_gemini_classifier_messages_carry_only_the_report(self):
        """The real message builder is used: system = V1.3 prompt, human = report only."""
        from week_07.llm_client import GeminiClassifier
        from week_07.prompts.prompt_loader import load_system_prompt
        from week_07.tests.gemini_fakes import VALID_RESPONSE

        sent = []

        class Recorder:
            def invoke(self, messages):
                sent.append(messages)
                return mock.Mock(content=VALID_RESPONSE)

        self.run_workflow("matrix2", GeminiClassifier(chat_model=Recorder()), limit=3)
        self.assertEqual(len(sent), 3)
        for system, human in sent:
            self.assertEqual(system.content, load_system_prompt())
            self.assertNotIn(LEAK_MARKER, human.content)
            self.assertNotIn("Positive", human.content)
            self.assertTrue(human.content.startswith("Classify the following canine thorax"))


class TestResumeAndManifest(WorkflowTestCase):
    def test_manifest_identity_and_run_entry(self):
        self.run_workflow("matrix2", EchoClassifier(1), limit=4)
        data = json.loads(self.repo.m2.manifest_path.read_text(encoding="utf-8"))
        identity = data["identity"]
        self.assertEqual(identity["workflow"], "matrix2")
        self.assertEqual(identity["reference_labels"], "Gold Standard condition scores")
        self.assertEqual(identity["model"], "gemini-3.8-flash")
        self.assertEqual(identity["temperature"], 0.0)
        self.assertEqual(identity["response_mime_type"], "application/json")
        self.assertIsNone(identity["response_schema"])
        self.assertEqual(identity["prompt"]["version"], "V1.3")
        self.assertEqual(identity["prompt"]["file_sha256"], PROMPT_FILE_SHA256)
        self.assertEqual(identity["prompt"]["text_sha256"], PROMPT_TEXT_SHA256)
        self.assertEqual(identity["input_workbook"]["sha256"],
                         sha256_file(self.repo.m2.default_input_path))
        run = data["runs"][0]
        self.assertEqual(run["status"], "completed")
        self.assertEqual((run["requested_limit"], run["cases_selected"]), (4, 4))
        self.assertEqual(run["summary"]["succeeded"], 4)
        self.assertEqual(run["retry_policy"]["application_max_attempts"], 2)
        self.assertEqual(run["retry_policy"]["transport_attempts_per_application_attempt"], 1)
        self.assertIn("google-genai", run["package_versions"])
        self.assertNotIn("api_key", json.dumps(data).lower())

    def test_smoke_test_then_full_run_resumes(self):
        first = EchoClassifier(1)
        self.run_workflow("matrix2", first, limit=1)
        second = EchoClassifier(1)
        counts = self.run_workflow("matrix2", second)
        self.assertEqual((counts["skipped"], counts["succeeded"]), (1, 99))
        self.assertEqual(sorted(case_from_payload(p) for p in second.calls), list(range(2, 101)))
        runs = json.loads(self.repo.m2.manifest_path.read_text(encoding="utf-8"))["runs"]
        self.assertEqual([r["status"] for r in runs], ["completed", "completed"])

    def test_resume_with_different_model_is_refused(self):
        self.run_workflow("matrix2", EchoClassifier(1), limit=2)
        with self.assertRaises(ManifestMismatch) as ctx:
            self.run_workflow("matrix2", EchoClassifier(1), limit=3,
                              settings=GeminiModelConfig(model="gemini-other", temperature=0.0))
        self.assertIn("model", str(ctx.exception))

    def test_resume_with_different_temperature_or_input_is_refused(self):
        self.run_workflow("matrix2", EchoClassifier(1), limit=2)
        with self.assertRaises(ManifestMismatch):
            self.run_workflow("matrix2", EchoClassifier(1),
                              settings=GeminiModelConfig(temperature=0.5))
        self.repo.write_inputs(m2_cases=range(1, 50))
        with self.assertRaises(ManifestMismatch):
            self.run_workflow("matrix2", EchoClassifier(1), limit=2)

    def test_predictions_without_manifest_are_refused(self):
        self.repo.m2.output_dir.mkdir(parents=True)
        self.repo.m2.predictions_path.write_text('{"case_id": 1}\n', encoding="utf-8")
        classifier = EchoClassifier(1)
        with self.assertRaises(ManifestMismatch):
            self.run_workflow("matrix2", classifier, limit=2)
        self.assertEqual(classifier.calls, [])

    def test_fatal_error_is_recorded_and_case_stays_pending(self):
        calls = {"n": 0}

        def classifier(payload):
            calls["n"] += 1
            if case_from_payload(payload) == 3:
                raise sdk_error(403)
            return EchoClassifier(1)(payload)

        with self.assertRaises(FatalProviderError):
            self.run_workflow("matrix2", classifier, limit=5)
        run = json.loads(self.repo.m2.manifest_path.read_text(encoding="utf-8"))["runs"][-1]
        self.assertEqual(run["status"], run_manifest.STATUS_FATAL)
        self.assertEqual(run["summary"]["succeeded"], 2)
        self.assertEqual([r["case_id"] for r in read_jsonl(self.repo.m2.predictions_path)], [1, 2])
        self.assertFalse(self.repo.m2.errors_path.exists())
        counts = self.run_workflow("matrix2", EchoClassifier(1), limit=5)
        self.assertEqual((counts["skipped"], counts["succeeded"]), (2, 3))

    def test_failures_logged_with_week5_schema(self):
        def classifier(payload):
            if case_from_payload(payload) == 2:
                return "not json"
            return EchoClassifier(1)(payload)

        counts = self.run_workflow("matrix2", classifier, limit=3,
                                   retry_policy=RetryPolicy(max_attempts=2))
        self.assertEqual(counts["failed"], 1)
        failure = read_jsonl(self.repo.m2.errors_path)[0]
        self.assertEqual(list(failure), ["case_id", "status", "attempts", "failed_at_utc", "error"])
        self.assertEqual(failure["case_id"], 2)


class TestConfigurationAndIsolation(WorkflowTestCase):
    def test_missing_key_stops_before_anything_is_written(self):
        with mock.patch.object(config, "ENV_FILE", self.repo.root / "absent.env"), \
                mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                run_workflow_batch(self.repo.m1, isolation=self.repo.policy, sleep=self.sleep)
        self.assertFalse(self.repo.week7.exists())

    def test_output_dir_override_must_stay_isolated(self):
        for target in (self.repo.week5 / "matrix_1", self.repo.m2.output_dir,
                       self.repo.m1.comparison_dir, self.repo.root / "elsewhere",
                       self.repo.root / "data"):
            with self.subTest(target=target), self.assertRaises(IsolationError):
                self.run_workflow("matrix1", EchoClassifier(0), output_dir=target)
        self.assertFalse((self.repo.week5).exists())

    def test_override_inside_week7_is_allowed(self):
        outputs = resolve_outputs(self.repo.m1, self.repo.week7 / "matrix_1_rerun",
                                  isolation=self.repo.policy)
        self.run_workflow("matrix1", EchoClassifier(0), output_dir=outputs.output_dir)
        self.assertEqual(len(read_jsonl(outputs.predictions_path)), 100)

    def test_inputs_are_not_modified(self):
        before = {spec.name: sha256_file(spec.default_input_path)
                  for spec in (self.repo.m1, self.repo.m2)}
        self.run_workflow("matrix1", EchoClassifier(0))
        self.run_workflow("matrix2", EchoClassifier(1))
        after = {spec.name: sha256_file(spec.default_input_path)
                 for spec in (self.repo.m1, self.repo.m2)}
        self.assertEqual(before, after)
