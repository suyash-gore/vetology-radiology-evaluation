"""CLI for the shared-prediction applications, and Canine Thorax backward compatibility."""
from __future__ import annotations

import contextlib
import functools
import io
import logging
import os
import tempfile
from pathlib import Path
from unittest import mock

from week_07 import batch_runner, cli, config
from week_07.evaluation import evaluate as evaluate_module
from week_07.tests.app_fixtures import AppEchoClassifier, SyntheticAppRepo
from week_07.tests.gemini_fakes import RecordingSleep
from week_07.tests.support import OfflineTestCase


class AppCliCase(OfflineTestCase):
    key = "feline_thorax"

    def setUp(self):
        super().setUp()
        logging.getLogger("week_07").setLevel(logging.CRITICAL)
        self.addCleanup(logging.getLogger("week_07").setLevel, logging.NOTSET)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (mock.patch.object(config, "ENV_FILE", Path(tmp.name) / "absent.env"),
                        mock.patch.dict(os.environ, {}, clear=True)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.repo = SyntheticAppRepo(self.key)
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()
        self.app = self.repo.app

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(list(argv))
        return code, out.getvalue()

    @contextlib.contextmanager
    def offline_application(self):
        """Route the CLI to the synthetic application, isolation policy and a fake model."""
        real = cli.get_application
        policy = self.repo.policy
        run = functools.partial(batch_runner.run_application_batch,
                                classifier=AppEchoClassifier(self.app),
                                settings=config.OpenAIModelConfig(), isolation=policy,
                                sleep=RecordingSleep())
        patches = (
            mock.patch.object(cli, "get_application",
                              lambda key: self.app if key == self.key else real(key)),
            mock.patch.object(batch_runner, "run_application_batch", run),
            mock.patch.object(batch_runner, "resolve_application_outputs", functools.partial(
                batch_runner.resolve_application_outputs, isolation=policy)),
            mock.patch.object(evaluate_module, "evaluate_application", functools.partial(
                evaluate_module.evaluate_application, isolation=policy)),
            mock.patch.object(evaluate_module, "write_application_workbook", functools.partial(
                evaluate_module.write_application_workbook, isolation=policy)),
        )
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            yield


class TestEndToEnd(AppCliCase):
    def test_validate_batch_evaluate_both_matrices(self):
        m1, m2 = str(self.repo.m1.default_input_path), str(self.repo.m2.default_input_path)
        with self.offline_application():
            code, text = self.run_cli("validate-data", "--application", self.key,
                                      "--workflow", "matrix1", "--input", m1)
            self.assertEqual(code, 0, text)
            self.assertIn("Cases loaded: 100", text)
            self.assertIn("Normalised reference column pneumonia", text)
            code, text = self.run_cli("batch", "--application", self.key, "--workflow",
                                      "matrix1", "--provider", "openai", "--input", m1,
                                      "--matrix2-input", m2)
            self.assertEqual(code, 0, text)
            self.assertIn("billable OpenAI API requests", text)
            self.assertIn("Succeeded: 100", text)
            for workflow, source in (("matrix1", None), ("matrix2", m1)):
                argv = ["evaluate", "--application", self.key, "--workflow", workflow,
                        "--input", m1 if workflow == "matrix1" else m2]
                if source:
                    argv += ["--prediction-source-input", source]
                code, text = self.run_cli(*argv)
                self.assertEqual(code, 0, text)
                self.assertIn(f"Conditions: {self.app.condition_count}", text)
                self.assertIn("Evaluation workbook created", text)
        self.assertTrue(self.repo.m1.evaluation_workbook_path.is_file())
        self.assertTrue(self.repo.m2.evaluation_workbook_path.is_file())

    def test_compare_references(self):
        with self.offline_application():
            code, text = self.run_cli("compare-references", "--application", self.key,
                                      "--workflow", "matrix2", "--input",
                                      str(self.repo.m2.default_input_path))
        self.assertEqual(code, 0, text)
        self.assertIn("No differences", text)


class TestRefusals(AppCliCase):
    def test_matrix2_batch_refused(self):
        with self.offline_application():
            code, text = self.run_cli("batch", "--application", self.key, "--workflow",
                                      "matrix2", "--input", str(self.repo.m2.default_input_path))
        self.assertEqual(code, 4)
        self.assertIn("reuses them", text)

    def test_provider_mismatch_refused(self):
        with self.offline_application():
            code, text = self.run_cli("batch", "--application", self.key, "--workflow",
                                      "matrix1", "--provider", "gemini")
        self.assertEqual(code, 2)
        code, text = self.run_cli("batch", "--workflow", "matrix1", "--provider", "openai")
        self.assertEqual(code, 4)

    def test_limit_and_model_record_refused(self):
        with self.offline_application():
            code, _ = self.run_cli("batch", "--application", self.key, "--workflow", "matrix1",
                                   "--limit", "5")
            self.assertEqual(code, 4)
            code, _ = self.run_cli("evaluate", "--application", self.key, "--workflow",
                                   "matrix1", "--model-record", "x")
            self.assertEqual(code, 4)

    def test_pending_prompt_blocks_real_batch(self):
        # The REAL registered application (pending prompt) and the real default policy:
        # paths are only checked, and the run stops before anything is written.
        abdomen = SyntheticAppRepo("canine_abdomen")
        self.addCleanup(abdomen.cleanup)
        abdomen.write_inputs()
        real_tree = config.OUTPUT_ROOT / "canine_abdomen"
        existed = real_tree.exists()
        code, text = self.run_cli("batch", "--application", "canine_abdomen", "--workflow",
                                  "matrix1", "--input", str(abdomen.m1.default_input_path))
        self.assertEqual(code, 2)
        self.assertIn("pending approval", text)
        self.assertEqual(real_tree.exists(), existed)

    def test_wrong_application_workbook_is_an_input_error(self):
        code, _ = self.run_cli("validate-data", "--application", "canine_abdomen",
                               "--workflow", "matrix1",
                               "--input", str(self.repo.m1.default_input_path))
        self.assertEqual(code, 3)  # the feline workbook lacks the abdomen columns

    def test_compare_not_available(self):
        code, text = self.run_cli("compare", "--application", self.key, "--workflow", "matrix1")
        self.assertEqual(code, 5)

    def test_missing_inputs_are_input_errors(self):
        code, _ = self.run_cli("validate-data", "--application", self.key, "--workflow",
                               "matrix1", "--input", str(self.repo.root / "missing.xlsx"))
        self.assertEqual(code, 3)

    def test_unknown_application_rejected_by_parser(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli.main(["config", "--application", "equine_thorax", "--workflow", "matrix1"])


class TestConfigCommand(AppCliCase):
    def test_openai_configuration_offline(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy-offline",
                                          "OPENAI_MAX_RETRIES": "4"}):
            code, text = self.run_cli("config", "--application", "feline_thorax",
                                      "--workflow", "matrix1")
        self.assertEqual(code, 0)
        for expected in ("Application: feline_thorax", "Conditions: 21", "Model: gpt-4.1-mini",
                         "OpenAI via langchain-openai", "SDK transport retries: 0",
                         "PENDING approval", "OPENAI_API_KEY: set",
                         "OPENAI_MAX_RETRIES: set but IGNORED",
                         "pulmonary_nodules: Normal->Negative, Abnormal->Positive",
                         "outputs/week_07/feline_thorax/predictions"):
            self.assertIn(expected, text.replace("\\", "/"))
        self.assertNotIn("sk-dummy-offline", text)
        self.assertNotIn("GOOGLE_API_KEY", text)

    def test_abdomen_configuration(self):
        code, text = self.run_cli("config", "--application", "canine_abdomen",
                                  "--workflow", "matrix2")
        self.assertEqual(code, 0)
        self.assertIn("Conditions: 10", text)
        self.assertIn("Reference-label normalisation: none", text)
        self.assertIn("OPENAI_API_KEY: NOT SET", text)


class TestCanineThoraxBackwardCompatibility(AppCliCase):
    def test_existing_commands_unchanged_without_application(self):
        code, text = self.run_cli("config", "--workflow", "matrix1")
        self.assertEqual(code, 0)
        self.assertIn("Model: gemini-3.8-flash", text)
        self.assertIn("Prompt: Canine Thorax Master Prompt V1.3", text)
        self.assertNotIn("Application:", text)
        explicit = self.run_cli("config", "--application", "canine_thorax",
                                "--workflow", "matrix1")
        self.assertEqual(explicit, (code, text))

    def test_default_application_is_canine_thorax(self):
        args = cli.build_parser().parse_args(["batch", "--workflow", "matrix1"])
        self.assertEqual(args.application, "canine_thorax")
        self.assertIsNone(args.provider)

    def test_canine_only_options_refused_for_new_flags(self):
        code, text = self.run_cli("evaluate", "--workflow", "matrix1",
                                  "--prediction-source-input", "x.xlsx")
        self.assertEqual(code, 4)
        code, text = self.run_cli("batch", "--workflow", "matrix1", "--matrix2-input", "x")
        self.assertEqual(code, 4)

    def test_canine_gemini_provider_flag_accepted(self):
        with mock.patch.object(batch_runner, "run_workflow_batch",
                               return_value={"total": 0}) as run:
            code, _ = self.run_cli("batch", "--workflow", "matrix2", "--provider", "gemini",
                                   "--limit", "3")
        self.assertEqual(code, 0)
        self.assertEqual(run.call_args.kwargs["limit"], 3)
