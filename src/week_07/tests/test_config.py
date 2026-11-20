"""Gemini model settings, retry policy and workflow specifications."""
from __future__ import annotations

import os
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest import mock

from week_07 import config
from week_07.config import (
    ConfigurationError,
    GeminiModelConfig,
    RetryPolicy,
    api_key_is_configured,
    get_workflow,
    load_model_config,
    require_api_key,
    validate_runtime_configuration,
)
from week_07.tests.support import OfflineTestCase

KEY = "GOOGLE_API_KEY"


class TestModelDefaults(OfflineTestCase):
    def test_defaults_without_variables(self):
        settings = load_model_config({})
        self.assertEqual(settings, GeminiModelConfig())
        self.assertEqual(settings.model, "gemini-3.8-flash")
        self.assertEqual(settings.temperature, 0.0)
        self.assertEqual(settings.timeout_seconds, 90.0)
        self.assertEqual(settings.response_mime_type, "application/json")
        self.assertEqual(settings.transport_max_retries, 0)

    def test_config_holds_no_credential(self):
        settings = load_model_config({KEY: "secret-value"})
        self.assertNotIn("secret-value", repr(settings))
        self.assertFalse(any("key" in name.lower() for name in vars(settings)))

    def test_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            GeminiModelConfig().model = "other"  # type: ignore[misc]


class TestModelParsing(OfflineTestCase):
    def test_values_are_read_and_stripped(self):
        settings = load_model_config({"GEMINI_MODEL": "  gemini-3.8-flash  ",
                                      "GEMINI_TEMPERATURE": "0.5",
                                      "GEMINI_TIMEOUT_SECONDS": "30"})
        self.assertEqual((settings.model, settings.temperature, settings.timeout_seconds),
                         ("gemini-3.8-flash", 0.5, 30.0))

    def test_blank_model_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_model_config({"GEMINI_MODEL": "   "})

    def test_temperature_validation(self):
        for raw in ("-0.1", "2.01", "abc", "nan", "inf"):
            with self.subTest(raw=raw), self.assertRaises(ConfigurationError):
                load_model_config({"GEMINI_TEMPERATURE": raw})
        for raw in ("0", "2"):
            with self.subTest(raw=raw):
                load_model_config({"GEMINI_TEMPERATURE": raw})

    def test_timeout_validation(self):
        for raw in ("0", "-5", "x", "inf"):
            with self.subTest(raw=raw), self.assertRaises(ConfigurationError):
                load_model_config({"GEMINI_TIMEOUT_SECONDS": raw})

    def test_transport_retries_cannot_be_configured(self):
        for raw in ("0", "2", ""):
            with self.subTest(raw=raw), self.assertRaises(ConfigurationError):
                load_model_config({"GEMINI_MAX_RETRIES": raw})
        with self.assertRaises(ConfigurationError):
            GeminiModelConfig(transport_max_retries=2)

    def test_mime_type_is_fixed(self):
        with self.assertRaises(ConfigurationError):
            GeminiModelConfig(response_mime_type="text/plain")

    def test_openai_variables_are_ignored(self):
        settings = load_model_config({"OPENAI_MODEL": "gpt-4.1-mini",
                                      "OPENAI_TEMPERATURE": "1.5",
                                      "OPENAI_TIMEOUT_SECONDS": "5",
                                      "OPENAI_MAX_RETRIES": "9"})
        self.assertEqual(settings, GeminiModelConfig())
        self.assertFalse(api_key_is_configured({"OPENAI_API_KEY": "x"}))


class TestApiKey(OfflineTestCase):
    def test_presence_only(self):
        self.assertTrue(api_key_is_configured({KEY: "abc"}))
        self.assertFalse(api_key_is_configured({}))
        self.assertFalse(api_key_is_configured({KEY: "   "}))
        self.assertIs(api_key_is_configured({KEY: "abc"}), True)  # a bool, never the value

    def test_missing_key_message_does_not_leak_values(self):
        with self.assertRaises(ConfigurationError) as ctx:
            require_api_key({"GEMINI_MODEL": "m"})
        self.assertIn(KEY, str(ctx.exception))

    def test_validate_runtime_configuration(self):
        with self.assertRaises(ConfigurationError):
            validate_runtime_configuration({})
        self.assertEqual(validate_runtime_configuration({KEY: "k"}), GeminiModelConfig())

    def test_key_checked_before_settings(self):
        with self.assertRaises(ConfigurationError) as ctx:
            validate_runtime_configuration({"GEMINI_TEMPERATURE": "bad"})
        self.assertIn(KEY, str(ctx.exception))


class TestDotEnvLoading(OfflineTestCase):
    """Uses a temporary .env file; the repository .env is never read."""

    def setUp(self):
        super().setUp()
        handle, name = tempfile.mkstemp(suffix=".env")
        os.close(handle)
        self.env_file = Path(name)
        self.addCleanup(self.env_file.unlink)
        self.env_file.write_text("GEMINI_TEMPERATURE=0.7\nGOOGLE_API_KEY=from-file\n",
                                 encoding="utf-8")

    def test_env_file_is_loaded(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            settings = load_model_config(env_file=self.env_file)
            self.assertEqual(settings.temperature, 0.7)
            self.assertTrue(api_key_is_configured(env_file=self.env_file))

    def test_existing_environment_takes_precedence(self):
        with mock.patch.dict(os.environ, {"GEMINI_TEMPERATURE": "0.2"}, clear=True):
            self.assertEqual(load_model_config(env_file=self.env_file).temperature, 0.2)


class TestRetryPolicy(OfflineTestCase):
    def test_approved_defaults(self):
        policy = config.DEFAULT_RETRY_POLICY
        self.assertEqual(policy.max_attempts, 2)
        self.assertEqual(policy.transient_status_codes, {408, 429, 500, 502, 503, 504})
        self.assertEqual(policy.fatal_status_codes, {400, 401, 403, 404})
        self.assertEqual(config.TRANSPORT_ATTEMPTS, 1)

    def test_backoff_is_bounded_exponential(self):
        policy = RetryPolicy(max_attempts=6, backoff_base_seconds=2, backoff_factor=2,
                             backoff_max_seconds=10)
        self.assertEqual([policy.backoff_seconds(n) for n in range(1, 6)],
                         [2.0, 4.0, 8.0, 10.0, 10.0])
        self.assertEqual(config.DEFAULT_RETRY_POLICY.backoff_seconds(1), 2.0)

    def test_backoff_argument_validation(self):
        for bad in (0, -1, 1.5, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                config.DEFAULT_RETRY_POLICY.backoff_seconds(bad)

    def test_invalid_policies_rejected(self):
        for kwargs in ({"max_attempts": 0}, {"max_attempts": True}, {"max_attempts": 1.0},
                       {"transient_status_codes": frozenset({400})},
                       {"backoff_base_seconds": -1}, {"backoff_factor": 0.5},
                       {"backoff_max_seconds": float("inf")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ConfigurationError):
                RetryPolicy(**kwargs)

    def test_manifest_description(self):
        described = config.DEFAULT_RETRY_POLICY.as_manifest()
        self.assertEqual(described["transport_attempts_per_application_attempt"], 1)
        self.assertEqual(described["application_max_attempts"], 2)
        self.assertEqual(described["transient_http_status_codes"], [408, 429, 500, 502, 503, 504])
        self.assertEqual(described["fatal_http_status_codes"], [400, 401, 403, 404])
        self.assertIn("never parsed", described["classification_basis"])


class TestWorkflows(OfflineTestCase):
    def test_lookup(self):
        self.assertIs(get_workflow("matrix1"), config.MATRIX1)
        self.assertIs(get_workflow("matrix2"), config.MATRIX2)
        with self.assertRaises(ConfigurationError):
            get_workflow("matrix3")

    def test_week7_output_locations(self):
        root = config.REPO_ROOT / "outputs" / "week_07"
        self.assertEqual(config.MATRIX1.output_dir, root / "matrix_1")
        self.assertEqual(config.MATRIX2.output_dir, root / "matrix_2")
        self.assertEqual(config.MATRIX1.comparison_dir, root / "comparison" / "matrix_1")
        self.assertEqual(config.MATRIX2.comparison_dir, root / "comparison" / "matrix_2")
        self.assertEqual(config.MATRIX1.manifest_path.name, "run_manifest.json")
        self.assertEqual(config.MATRIX2.evaluation_workbook_path.name,
                         "Evaluation Workbook v2.xlsx")

    def test_week5_sources_are_the_matching_matrix(self):
        week5 = config.REPO_ROOT / "outputs" / "week_05"
        self.assertEqual(config.MATRIX1.week5_predictions_path,
                         week5 / "matrix_1" / "predictions.jsonl")
        self.assertEqual(config.MATRIX2.week5_predictions_path,
                         week5 / "matrix_2" / "predictions.jsonl")
        self.assertEqual(config.MATRIX1.week5_errors_path, week5 / "matrix_1" / "errors.jsonl")

    def test_inputs_and_case_rules_match_week5(self):
        m1, m2 = config.MATRIX1, config.MATRIX2
        inputs = config.REPO_ROOT / "data" / "week_04_inputs"
        self.assertEqual(m1.default_input_path, inputs / "Vetology_Matrix1_First100_Encoded.xlsx")
        self.assertEqual(m2.default_input_path,
                         inputs / "1_canine_thorax_gold_standard_score_draft.xlsx")
        self.assertEqual((m1.case_limit, m1.max_case_limit, m1.require_exact_case_count,
                          m1.configurable_limit), (100, 100, True, False))
        self.assertEqual((m2.case_limit, m2.max_case_limit, m2.require_exact_case_count,
                          m2.configurable_limit), (100, None, False, True))
        self.assertEqual(m1.worksheet_name, "Sheet1")
        self.assertEqual(m1.evaluation_workbook_filename, "matrix1_evaluation_workbook.xlsx")

    def test_workflow_directories_are_disjoint(self):
        dirs = [config.MATRIX1.output_dir, config.MATRIX2.output_dir,
                config.MATRIX1.comparison_dir, config.MATRIX2.comparison_dir]
        for a in dirs:
            for b in dirs:
                if a is not b:
                    self.assertFalse(a.is_relative_to(b), f"{a} inside {b}")
