"""CLI behaviour (offline; the real .env is never read — ENV_FILE is redirected)."""
from __future__ import annotations

import contextlib
import io
import os
import tempfile
from pathlib import Path
from unittest import mock

from week_07 import cli, config
from week_07.error_policy import FatalProviderError, classify_error
from week_07.isolation import ProtectedFileModified
from week_07.tests.gemini_fakes import sdk_error
from week_07.tests.support import OfflineTestCase


class CliTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (mock.patch.object(config, "ENV_FILE", Path(tmp.name) / "absent.env"),
                        mock.patch.dict(os.environ, {}, clear=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(list(argv))
        return code, out.getvalue()


class TestConfigCommand(CliTestCase):
    def test_shows_gemini_configuration_offline(self):
        code, text = self.run_cli("config", "--workflow", "matrix1")
        self.assertEqual(code, 0)
        for expected in ("Model: gemini-3.8-flash", "Temperature: 0.0",
                         "Timeout (seconds): 90.0", "application/json (no response schema)",
                         "SDK transport attempts per application attempt: 1",
                         "Application attempts per case (default): 2",
                         "[408, 429, 500, 502, 503, 504]", "[400, 401, 403, 404]",
                         "GOOGLE_API_KEY: NOT SET", "No API request was made.",
                         "Original Vetology condition scores", "outputs/week_07/matrix_1"):
            self.assertIn(expected, text.replace("\\", "/"))

    def test_key_presence_only(self):
        with mock.patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy-offline-key"}):
            code, text = self.run_cli("config", "--workflow", "matrix2")
        self.assertIn("GOOGLE_API_KEY: set", text)
        self.assertNotIn("dummy-offline-key", text)
        self.assertIn("Gold Standard condition scores", text)

    def test_forbidden_retry_variable(self):
        with mock.patch.dict(os.environ, {"GEMINI_MAX_RETRIES": "3"}):
            code, text = self.run_cli("config", "--workflow", "matrix1")
        self.assertEqual(code, 2)


class TestBatchCommand(CliTestCase):
    def test_matrix1_rejects_limit(self):
        code, text = self.run_cli("batch", "--workflow", "matrix1", "--limit", "5")
        self.assertEqual(code, 4)
        self.assertIn("--limit is not available", text)

    def test_missing_key_is_a_configuration_error_without_any_call(self):
        with mock.patch("week_07.batch_runner.load_dataset") as loader:
            loader.return_value = mock.Mock(cases=(mock.Mock(case_id=1),),
                                            source_path=Path("x.xlsx"), worksheet_name="Sheet1")
            with mock.patch("week_07.batch_runner.run_manifest.RunManifest.begin") as begin, \
                    mock.patch("week_07.batch_runner.run_batch") as batch:
                code, text = self.run_cli("batch", "--workflow", "matrix2", "--limit", "1")
        self.assertEqual(code, 2)
        self.assertIn("GOOGLE_API_KEY was not found", text)
        begin.assert_not_called()
        batch.assert_not_called()

    def test_exit_codes_for_fatal_and_protected_errors(self):
        fatal = FatalProviderError("stop", classify_error(sdk_error(401)))
        for error, expected in ((fatal, 6), (ProtectedFileModified("changed"), 7)):
            with self.subTest(error=type(error).__name__), \
                    mock.patch("week_07.batch_runner.run_workflow_batch", side_effect=error):
                code, _ = self.run_cli("batch", "--workflow", "matrix2", "--limit", "1")
                self.assertEqual(code, expected)

    def test_max_attempts_reaches_the_retry_policy(self):
        with mock.patch("week_07.batch_runner.run_workflow_batch", return_value={}) as runner:
            code, text = self.run_cli("batch", "--workflow", "matrix2", "--max-attempts", "1")
        self.assertEqual(code, 0)
        self.assertEqual(runner.call_args.kwargs["retry_policy"].max_attempts, 1)
        self.assertIn("billable Google Gemini", text)

    def test_invalid_max_attempts(self):
        code, _ = self.run_cli("batch", "--workflow", "matrix2", "--max-attempts", "0")
        self.assertEqual(code, 2)

    def test_output_dir_outside_week7_refused(self):
        code, text = self.run_cli("batch", "--workflow", "matrix1", "--output-dir",
                                  str(config.WEEK5_OUTPUTS / "matrix_1"))
        self.assertEqual(code, 2)
        self.assertIn("protected", text)


class TestOfflineCommands(CliTestCase):
    def test_missing_inputs_are_input_errors(self):
        missing = str(Path(tempfile.gettempdir()) / "week07-missing-input.xlsx")
        for argv in (("validate-data", "--workflow", "matrix1", "--input", missing),
                     ("evaluate", "--workflow", "matrix2", "--input", missing,
                      "--predictions", missing)):
            with self.subTest(argv=argv[0]):
                code, _ = self.run_cli(*argv)
                self.assertEqual(code, 3)

    def test_parser_lists_week7_commands(self):
        parser = cli.build_parser()
        self.assertEqual(parser.prog, "python -m week_07")
        self.assertEqual(set(cli.COMMANDS),
                         {"config", "validate-data", "batch", "evaluate", "compare-references",
                          "compare"})
