"""Offline tests for model/workflow configuration. No API requests are made."""
from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from week_05 import cli, config
from week_05.config import (
    MATRIX1,
    MATRIX2,
    ConfigurationError,
    ModelConfig,
    api_key_is_configured,
    get_workflow,
    load_model_config,
    require_api_key,
    validate_runtime_configuration,
)

FAKE_KEY = "sk-test-not-a-real-key-0123456789"


class TestModelConfig(unittest.TestCase):
    def test_defaults_match_week4(self):
        cfg = load_model_config(environ={})
        self.assertEqual(cfg, ModelConfig("gpt-4.1-mini", 0.0, 90.0, 2))

    def test_env_example_values_parse_to_defaults(self):
        env = {
            "OPENAI_MODEL": "gpt-4.1-mini",
            "OPENAI_TEMPERATURE": "0",
            "OPENAI_TIMEOUT_SECONDS": "90",
            "OPENAI_MAX_RETRIES": "2",
        }
        self.assertEqual(load_model_config(environ=env), ModelConfig())

    def test_env_example_file_matches_defaults(self):
        """The committed .env.example must agree with the code defaults."""
        values = {}
        for line in (config.REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                name, _, value = line.partition("=")
                values[name.strip()] = value.strip()
        self.assertEqual(values["OPENAI_MODEL"], config.DEFAULT_MODEL)
        self.assertEqual(values["OPENAI_TEMPERATURE"], config.DEFAULT_TEMPERATURE)
        self.assertEqual(values["OPENAI_TIMEOUT_SECONDS"], config.DEFAULT_TIMEOUT_SECONDS)
        self.assertEqual(values["OPENAI_MAX_RETRIES"], config.DEFAULT_MAX_RETRIES)

    def test_model_name_is_stripped(self):
        self.assertEqual(load_model_config(environ={"OPENAI_MODEL": "  gpt-4.1-mini \n"}).model,
                         "gpt-4.1-mini")

    def test_empty_model_rejected(self):
        with self.assertRaisesRegex(ConfigurationError, "OPENAI_MODEL is empty"):
            load_model_config(environ={"OPENAI_MODEL": "   "})

    def test_invalid_numbers_rejected_with_variable_name(self):
        cases = {
            "OPENAI_TEMPERATURE": ["abc", "nan", "inf", "-0.1", "2.5"],
            "OPENAI_TIMEOUT_SECONDS": ["ninety", "0", "-5"],
            "OPENAI_MAX_RETRIES": ["two", "1.5", "-1"],
        }
        for name, values in cases.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(ConfigurationError, name):
                        load_model_config(environ={name: value})

    def test_config_object_holds_no_credential(self):
        cfg = load_model_config(environ={"OPENAI_API_KEY": FAKE_KEY})
        self.assertNotIn(FAKE_KEY, repr(cfg))
        self.assertNotIn("api_key", {field.lower() for field in cfg.__dataclass_fields__})


class TestApiKeyChecks(unittest.TestCase):
    def test_missing_or_blank_key_fails_fast(self):
        for env in ({}, {"OPENAI_API_KEY": ""}, {"OPENAI_API_KEY": "   "}):
            with self.subTest(env=env):
                self.assertFalse(api_key_is_configured(environ=env))
                with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY was not found"):
                    require_api_key(environ=env)
                with self.assertRaises(ConfigurationError):
                    validate_runtime_configuration(environ=env)

    def test_present_key_passes_and_is_not_returned_or_echoed(self):
        env = {"OPENAI_API_KEY": FAKE_KEY}
        self.assertIs(api_key_is_configured(environ=env), True)
        self.assertIsNone(require_api_key(environ=env))
        cfg = validate_runtime_configuration(environ=env)
        self.assertEqual(cfg, ModelConfig())

    def test_invalid_settings_fail_even_with_key(self):
        with self.assertRaises(ConfigurationError):
            validate_runtime_configuration(
                environ={"OPENAI_API_KEY": FAKE_KEY, "OPENAI_TEMPERATURE": "hot"}
            )


class TestDotenvLoading(unittest.TestCase):
    def test_env_file_loaded_without_overriding_existing_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "OPENAI_MODEL=model-from-file\nOPENAI_TIMEOUT_SECONDS=45\n", encoding="utf-8"
            )
            with patch.dict(os.environ, {"OPENAI_MODEL": "model-from-process"}, clear=True):
                cfg = load_model_config(env_file=env_file)
        self.assertEqual(cfg.model, "model-from-process")  # process env wins (Week 4)
        self.assertEqual(cfg.timeout_seconds, 45.0)          # filled from .env

    def test_missing_env_file_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {}, clear=True):
                cfg = load_model_config(env_file=Path(tmp) / "absent.env")
        self.assertEqual(cfg, ModelConfig())


class TestWorkflowSpecs(unittest.TestCase):
    def test_lookup(self):
        self.assertIs(get_workflow("matrix1"), MATRIX1)
        self.assertIs(get_workflow("matrix2"), MATRIX2)
        for bad in ("matrix_1", "Matrix1", "1", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ConfigurationError):
                    get_workflow(bad)

    def test_inputs_and_references_are_distinct(self):
        self.assertEqual(MATRIX1.input_filename, "Vetology_Matrix1_First100_Encoded.xlsx")
        self.assertEqual(MATRIX2.input_filename, "1_canine_thorax_gold_standard_score_draft.xlsx")
        self.assertIn("Original Vetology", MATRIX1.reference_description)
        self.assertIn("Gold Standard", MATRIX2.reference_description)

    def test_outputs_never_overlap(self):
        m1 = {MATRIX1.predictions_path, MATRIX1.errors_path, MATRIX1.single_case_path,
              MATRIX1.evaluation_workbook_path}
        m2 = {MATRIX2.predictions_path, MATRIX2.errors_path, MATRIX2.single_case_path,
              MATRIX2.evaluation_workbook_path}
        self.assertEqual(len(m1), 4)
        self.assertEqual(len(m2), 4)
        self.assertFalse(m1 & m2)
        self.assertNotEqual(MATRIX1.output_dir, MATRIX2.output_dir)
        self.assertEqual(MATRIX1.evaluation_workbook_filename, "matrix1_evaluation_workbook.xlsx")
        self.assertEqual(MATRIX2.evaluation_workbook_filename, "Evaluation Workbook v2.xlsx")

    def test_week4_output_contract_names_and_scope(self):
        for spec in (MATRIX1, MATRIX2):
            with self.subTest(spec=spec.name):
                self.assertEqual(spec.predictions_path.name, "predictions.jsonl")
                self.assertEqual(spec.errors_path.name, "errors.jsonl")
                self.assertEqual(spec.case_limit, 100)
                self.assertEqual(spec.worksheet_name, "Sheet1")
        self.assertTrue(MATRIX1.require_exact_case_count)   # Week 4 M1 loader raises
        self.assertFalse(MATRIX2.require_exact_case_count)  # Week 4 M2 loader warns
        self.assertFalse(MATRIX1.configurable_limit)        # Week 4 M1 batch: fixed 100
        self.assertTrue(MATRIX2.configurable_limit)         # Week 4 M2 batch: --limit

    def test_paths_are_anchored_to_repository_and_isolated_from_week4(self):
        week5_outputs = config.REPO_ROOT / "outputs" / "week_05"
        week4_outputs = config.REPO_ROOT / "outputs" / "week_04"
        for spec in (MATRIX1, MATRIX2):
            with self.subTest(spec=spec.name):
                self.assertTrue(spec.output_dir.is_absolute())
                self.assertTrue(spec.output_dir.is_relative_to(week5_outputs))
                self.assertFalse(spec.output_dir.is_relative_to(week4_outputs))
        self.assertTrue((config.REPO_ROOT / "src" / "week_05").is_dir())


class TestCliConfigCommand(unittest.TestCase):
    def _run(self, argv, env):
        buffer = io.StringIO()
        # load_dotenv is patched so a developer's real .env can never leak in.
        with patch.dict(os.environ, env, clear=True), \
                patch("week_05.config.load_dotenv"), \
                contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
        return code, buffer.getvalue()

    def test_reports_settings_without_revealing_key(self):
        code, out = self._run(["config", "--workflow", "matrix1"], {"OPENAI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 0)
        self.assertIn("matrix1", out)
        self.assertIn("gpt-4.1-mini", out)
        self.assertIn("OPENAI_API_KEY: set", out)
        self.assertNotIn(FAKE_KEY, out)
        self.assertIn("No API request was made.", out)

    def test_reports_missing_key(self):
        code, out = self._run(["config", "--workflow", "matrix2"], {})
        self.assertEqual(code, 0)
        self.assertIn("OPENAI_API_KEY: NOT SET", out)
        self.assertIn("Evaluation Workbook v2.xlsx", out)

    def test_invalid_setting_returns_error_code(self):
        code, out = self._run(["config", "--workflow", "matrix1"], {"OPENAI_MAX_RETRIES": "x"})
        self.assertEqual(code, 2)
        self.assertIn("OPENAI_MAX_RETRIES", out)

    def test_workflow_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.main(["config"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
