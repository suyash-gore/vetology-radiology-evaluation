"""Shared-prediction batch execution for Feline Thorax and Canine Abdomen (fake models)."""
from __future__ import annotations

import json
import logging
from dataclasses import replace
from unittest import mock

import httpx
import openai

from week_07 import config
from week_07.applications import CANINE_THORAX, FELINE_THORAX
from week_07.batch_runner import resolve_application_outputs, run_application_batch
from week_07.config import ConfigurationError, OpenAIModelConfig
from week_07.dataset_loader import DatasetError
from week_07.error_policy import FatalProviderError
from week_07.isolation import IsolationError
from week_07.run_manifest import ManifestMismatch, read_manifest
from week_07.tests.app_fixtures import AppEchoClassifier, SyntheticAppRepo
from week_07.tests.fixtures import LEAK_MARKER
from week_07.tests.gemini_fakes import RecordingSleep
from week_07.tests.support import OfflineTestCase

REQUEST = httpx.Request("POST", "https://api.openai.invalid/v1/chat/completions")


class BatchCase(OfflineTestCase):
    key = "feline_thorax"

    def setUp(self):
        super().setUp()
        logging.getLogger("week_07").setLevel(logging.CRITICAL)
        self.addCleanup(logging.getLogger("week_07").setLevel, logging.NOTSET)
        self.repo = SyntheticAppRepo(self.key)
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()
        self.app = self.repo.app


class TestSharedRun(BatchCase):
    def test_one_run_for_both_matrices(self):
        counts = self.repo.run_batch()
        self.assertEqual(counts, {"total": 100, "skipped": 0, "succeeded": 100, "failed": 0,
                                  "transient_backoffs": 0})
        shared = self.repo.m1.predictions_path
        self.assertEqual(shared, self.repo.m2.predictions_path)
        self.assertEqual(shared.parent, self.repo.week7 / self.key / "predictions")
        records = [json.loads(line) for line in shared.read_text().splitlines()]
        self.assertEqual([r["case_id"] for r in records], list(range(1, 101)))
        self.assertEqual(set(records[0]), {"case_id", "status", "attempts", "completed_at_utc",
                                           "predictions"})
        self.assertEqual(tuple(records[0]["predictions"]), self.app.condition_keys)
        self.assertFalse(self.repo.m1.output_dir.exists())  # workbook dirs untouched by batch
        self.assertFalse(self.repo.m2.output_dir.exists())

    def test_resume_skips_completed_cases(self):
        self.repo.run_batch()
        classifier = AppEchoClassifier(self.app)
        counts = self.repo.run_batch(classifier)
        self.assertEqual((counts["skipped"], counts["succeeded"]), (100, 0))
        self.assertEqual(classifier.calls, [])
        manifest = read_manifest(self.repo.m1.manifest_path)
        self.assertEqual([run["status"] for run in manifest["runs"]], ["completed", "completed"])

    def test_resume_after_partial_run(self):
        calls = []

        def interrupting(payload):
            calls.append(payload)
            if len(calls) == 31:
                raise KeyboardInterrupt
            return AppEchoClassifier(self.app)(payload)

        with self.assertRaises(KeyboardInterrupt):
            self.repo.run_batch(interrupting)
        counts = self.repo.run_batch()
        self.assertEqual((counts["skipped"], counts["succeeded"]), (30, 70))
        statuses = [r["status"] for r in read_manifest(self.repo.m1.manifest_path)["runs"]]
        self.assertEqual(statuses, ["stopped: interrupted or failed", "completed"])

    def test_checkpoint_with_wrong_keys_is_reclassified(self):
        self.repo.run_batch()
        lines = self.repo.m1.predictions_path.read_text().splitlines()
        first = json.loads(lines[0])
        del first["predictions"]["Fe_Alveolar"]
        lines[0] = json.dumps(first)
        self.repo.m1.predictions_path.write_text("\n".join(lines) + "\n")
        classifier = AppEchoClassifier(self.app)
        counts = self.repo.run_batch(classifier)
        self.assertEqual((counts["skipped"], counts["succeeded"]), (99, 1))

    def test_invalid_responses_retried_then_recorded_as_failures(self):
        def bad(payload):
            return json.dumps({"pneumonia": "Positive"})
        counts = self.repo.run_batch(bad)
        self.assertEqual(counts["failed"], 100)
        error = json.loads(self.repo.m1.errors_path.read_text().splitlines()[0])
        self.assertEqual(error["attempts"], 2)
        self.assertTrue(error["error"].startswith("ResponseValidationError: Missing keys"))

    def test_only_report_fields_reach_the_model(self):
        classifier = AppEchoClassifier(self.app)
        self.repo.run_batch(classifier)
        self.assertEqual(len(classifier.calls), 100)
        for payload in classifier.calls:
            self.assertEqual(set(payload), {"findings", "conclusions", "recommendations"})
            self.assertNotIn(LEAK_MARKER, json.dumps(payload))
            for label in ("Positive", "Negative", "Normal", "Abnormal"):
                self.assertNotIn(label, json.dumps(payload))
        self.assertNotIn(LEAK_MARKER, self.repo.all_output_text())

    def test_matrix2_input_cross_check(self):
        self.repo.run_batch(matrix2_input=self.repo.m2.default_input_path)
        self.repo.write_inputs(m2_cases=[*range(1, 100), 500])
        with self.assertRaisesRegex(DatasetError, "same CaseIDs"):
            self.repo.run_batch(matrix2_input=self.repo.m2.default_input_path)


class TestManifestIdentity(BatchCase):
    def test_identity_records_application_and_provenance(self):
        self.repo.run_batch()
        identity = read_manifest(self.repo.m1.manifest_path)["identity"]
        self.assertEqual(identity["application"], "feline_thorax")
        self.assertEqual(identity["workflow"], "matrix1")
        self.assertEqual(identity["prediction_source_workflow"], "matrix1")
        self.assertEqual(identity["predictions_reused_by_workflows"], ["matrix1", "matrix2"])
        self.assertEqual(identity["provider"], "OpenAI via langchain-openai ChatOpenAI")
        self.assertEqual((identity["model"], identity["temperature"],
                          identity["transport_max_retries"]), ("gpt-4.1-mini", 0.0, 0))
        self.assertEqual(identity["condition_keys"], list(self.app.condition_keys))
        self.assertEqual(identity["prompt"]["version"], "V1.1")
        self.assertEqual(identity["prompt"]["file_sha256"], self.app.prompt.file_sha256)
        self.assertEqual(set(identity["source_label_normalization"]),
                         {"pulmonary_nodules", "esophagitis", "pneumonia"})
        self.assertEqual(identity["input_workbook"]["file_name"],
                         self.repo.m1.default_input_path.name)
        run = read_manifest(self.repo.m1.manifest_path)["runs"][0]
        self.assertIn("langchain-openai", run["package_versions"])

    def test_resume_with_different_identity_refused(self):
        self.repo.run_batch()
        variants = {
            "model": dict(settings=OpenAIModelConfig(model="gpt-other")),
            "temperature": dict(settings=OpenAIModelConfig(temperature=0.7)),
        }
        for name, kwargs in variants.items():
            with self.subTest(changed=name), self.assertRaises(ManifestMismatch):
                self.repo.run_batch(**kwargs)
        prompt_file = self.app.prompt.path
        prompt_file.write_text("A DIFFERENT STAND-IN\n", encoding="utf-8")
        from week_07.tests.app_fixtures import pinned_prompt
        changed = replace(self.app, prompt=pinned_prompt(self.repo.base, self.repo.prompts,
                                                         "A DIFFERENT STAND-IN\n"))
        with self.assertRaises(ManifestMismatch):
            run_application_batch(changed, "matrix1", self.repo.m1.default_input_path,
                                  classifier=AppEchoClassifier(changed),
                                  settings=OpenAIModelConfig(), isolation=self.repo.policy,
                                  sleep=RecordingSleep())

    def test_different_input_workbook_refused(self):
        self.repo.run_batch()

        def edit(case_id, row):
            row["Recommendations (original radiologist report)"] += " (edited)"
            return row
        self.repo.write_inputs(edit_m1=edit)
        with self.assertRaisesRegex(ManifestMismatch, "input_workbook"):
            self.repo.run_batch()

    def test_existing_predictions_without_manifest_refused(self):
        path = self.repo.m1.predictions_path
        path.parent.mkdir(parents=True)
        path.write_text('{"case_id": 1}\n')
        with self.assertRaises(ManifestMismatch):
            self.repo.run_batch()


class TestExplicitSpecificationRequired(BatchCase):
    def test_application_and_workflow_must_be_explicit_and_valid(self):
        kwargs = dict(classifier=AppEchoClassifier(self.app), settings=OpenAIModelConfig(),
                      isolation=self.repo.policy)
        for app, workflow, error in ((None, "matrix1", ConfigurationError),
                                     ("feline_thorax", "matrix1", ConfigurationError),
                                     (self.app, None, ConfigurationError),
                                     (self.app, "", ConfigurationError),
                                     (self.app, "matrix3", ConfigurationError),
                                     (self.app, "matrix2", ValueError),
                                     (CANINE_THORAX, "matrix1", ConfigurationError)):
            with self.subTest(app=getattr(app, "key", app), workflow=workflow):
                with self.assertRaises(error):
                    run_application_batch(app, workflow, self.repo.m1.default_input_path,
                                          **kwargs)
        self.assertFalse(self.repo.week7.exists())

    def test_provider_mismatch_refused(self):
        with self.assertRaises(ConfigurationError):
            self.repo.run_batch(provider="gemini")
        self.assertEqual(self.repo.run_batch(provider="openai")["succeeded"], 100)

    def test_pending_prompt_refused_before_any_write(self):
        pending = SyntheticAppRepo("canine_abdomen", prompt="pending")
        self.addCleanup(pending.cleanup)
        pending.write_inputs()
        with self.assertRaisesRegex(ConfigurationError, "pending approval"):
            pending.run_batch()
        self.assertFalse(pending.week7.exists())
        self.assertFalse(FELINE_THORAX.prompt.is_pending)  # the registered prompt is approved


class TestCredentials(BatchCase):
    def test_real_client_requires_openai_key_before_writes(self):
        with mock.patch.object(config, "ENV_FILE", self.repo.root / "no.env"), \
                mock.patch.dict("os.environ", {"GOOGLE_API_KEY": "g"}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
                run_application_batch(self.app, "matrix1", self.repo.m1.default_input_path,
                                      isolation=self.repo.policy)
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
                run_application_batch(self.app, "matrix1", self.repo.m1.default_input_path,
                                      settings=OpenAIModelConfig(), isolation=self.repo.policy)
        self.assertFalse(self.repo.week7.exists())

    def test_no_key_needed_when_everything_is_checkpointed(self):
        self.repo.run_batch()
        with mock.patch.object(config, "ENV_FILE", self.repo.root / "no.env"), \
                mock.patch.dict("os.environ", {}, clear=True):
            counts = run_application_batch(self.app, "matrix1", self.repo.m1.default_input_path,
                                           isolation=self.repo.policy)
        self.assertEqual(counts["skipped"], 100)


class TestOpenAIRetryPolicyInBatch(BatchCase):
    def test_transient_backoff_then_success(self):
        state = {"n": 0}
        echo = AppEchoClassifier(self.app)

        def flaky(payload):
            state["n"] += 1
            if state["n"] == 1:
                raise openai.RateLimitError("slow down",
                                            response=httpx.Response(429, request=REQUEST),
                                            body=None)
            return echo(payload)

        sleep = RecordingSleep()
        counts = self.repo.run_batch(flaky, sleep=sleep)
        self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (100, 1))
        self.assertEqual(sleep.delays, [2.0])

    def test_fatal_error_stops_batch_and_keeps_case_pending(self):
        def unauthorised(payload):
            raise openai.AuthenticationError("no", response=httpx.Response(401, request=REQUEST),
                                             body=None)

        with self.assertRaises(FatalProviderError) as ctx:
            self.repo.run_batch(unauthorised)
        self.assertEqual(ctx.exception.decision.status_code, 401)
        self.assertFalse(self.repo.m1.predictions_path.exists())
        self.assertFalse(self.repo.m1.errors_path.exists())
        run = read_manifest(self.repo.m1.manifest_path)["runs"][0]
        self.assertEqual(run["status"], "stopped: fatal provider error")


class TestBatchIsolation(BatchCase):
    def test_override_inside_own_tree_allowed(self):
        target = self.repo.week7 / self.key / "rerun"
        counts = self.repo.run_batch(output_dir=target)
        self.assertEqual(counts["succeeded"], 100)
        self.assertTrue((target / "predictions.jsonl").is_file())

    def test_override_outside_own_tree_refused(self):
        for target in (self.repo.week7 / "matrix_1", self.repo.week7 / "canine_abdomen" / "x",
                       self.repo.week7 / "elsewhere", self.repo.m2.output_dir,
                       self.repo.root / "data" / "x"):
            with self.subTest(target=str(target)), self.assertRaises(IsolationError):
                resolve_application_outputs(self.repo.m1, target, isolation=self.repo.policy)
        self.assertFalse(self.repo.week7.exists())


class TestCanineAbdomenBatch(BatchCase):
    key = "canine_abdomen"

    def test_ten_condition_predictions(self):
        self.repo.run_batch()
        record = json.loads(self.repo.m1.predictions_path.read_text().splitlines()[0])
        self.assertEqual(tuple(record["predictions"]), self.app.condition_keys)
        self.assertEqual(len(record["predictions"]), 10)
        self.assertEqual(read_manifest(self.repo.m1.manifest_path)["identity"]
                         ["source_label_normalization"], {})


class TestOpenAIExecutionPathWithApprovedPrompts(OfflineTestCase):
    """The real OpenAIClassifier (only the chat model is faked) with the approved prompts."""

    def test_each_application_sends_its_prompt_and_gets_its_keys(self):
        from types import SimpleNamespace

        from week_07.openai_client import OpenAIClassifier
        from week_07.prompts.registry import load_prompt
        from week_07.tests.app_fixtures import app_reference
        from week_07.tests.fixtures import case_from_payload

        logging.getLogger("week_07").setLevel(logging.CRITICAL)
        self.addCleanup(logging.getLogger("week_07").setLevel, logging.NOTSET)
        for key, region in (("feline_thorax", "feline thorax"),
                            ("canine_abdomen", "canine abdomen")):
            repo = SyntheticAppRepo(key, prompt="approved")
            self.addCleanup(repo.cleanup)
            repo.write_inputs()
            app = repo.app
            sent = []

            class Chat:
                def invoke(self, messages, app=app, sent=sent):
                    sent.append(messages)
                    case_id = case_from_payload({"findings": messages[1].content.split(
                        "FINDINGS:\n")[1].split("\n\nCONCLUSIONS:")[0]})
                    return SimpleNamespace(content=json.dumps(app_reference(app, case_id, 0)))

            classifier = OpenAIClassifier(app, OpenAIModelConfig(), chat_model=Chat())
            counts = repo.run_batch(classifier)
            with self.subTest(app=key):
                self.assertEqual(counts["succeeded"], 100)
                self.assertEqual(len(sent), 100)
                for system, human in sent:
                    self.assertEqual(system.content, load_prompt(app.prompt))
                    self.assertTrue(human.content.startswith(
                        f"Classify the following {region} radiology report"))
                    self.assertNotIn(LEAK_MARKER, human.content)
                record = json.loads(repo.m1.predictions_path.read_text().splitlines()[0])
                self.assertEqual(tuple(record["predictions"]), app.condition_keys)
                identity = read_manifest(repo.m1.manifest_path)["identity"]
                self.assertEqual(identity["prompt"]["file_sha256"], app.prompt.file_sha256)
                self.assertEqual(identity["prompt"]["text_sha256"], app.prompt.text_sha256)
                self.assertEqual(identity["prompt"]["version"], app.prompt.version)
                self.assertEqual(identity["condition_keys"], list(app.condition_keys))
