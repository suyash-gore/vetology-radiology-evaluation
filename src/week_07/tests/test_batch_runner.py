"""Batch retry handling with the approved Gemini error policy (synthetic cases only)."""
from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest import mock

import httpx

from week_07 import config
from week_07.batch_runner import run_batch
from week_07.config import ConfigurationError, RetryPolicy
from week_07.error_policy import ErrorClass, FatalProviderError
from week_07.isolation import IsolationError, IsolationPolicy
from week_07.tests.gemini_fakes import (
    VALID_RESPONSE,
    MockGemini,
    RecordingSleep,
    ScriptedClassifier,
    StepClock,
    findings,
    labels_json,
    langchain_error,
    make_cases,
    offline_chat_model,
    ok_body,
    sdk_error,
    timeout_error,
)
from week_07.tests.support import OfflineTestCase, quiet

SUCCESS_KEYS = ["case_id", "status", "attempts", "completed_at_utc", "predictions"]
FAILURE_KEYS = ["case_id", "status", "attempts", "failed_at_utc", "error"]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


class BatchTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        out = self.root / "outputs" / "week_07"
        self.spec = replace(config.MATRIX2, output_dir=out / "matrix_2",
                            comparison_dir=out / "comparison" / "matrix_2")
        other = replace(config.MATRIX1, output_dir=out / "matrix_1",
                        comparison_dir=out / "comparison" / "matrix_1")
        self.policy = IsolationPolicy(
            output_root=out,
            protected_roots=(self.root / "outputs" / "week_05", self.root / "data"),
            workflows={"matrix1": other, "matrix2": self.spec},
        )
        self.results = self.spec.predictions_path
        self.errors = self.spec.errors_path
        self.sleep = RecordingSleep()

    def run_cases(self, cases, classifier, retry_policy=config.DEFAULT_RETRY_POLICY):
        return run_batch(cases, self.results, self.errors, retry_policy, classifier,
                         spec=self.spec, isolation=self.policy, clock=StepClock(),
                         sleep=self.sleep)

    def success_lines(self):
        return read_jsonl(self.results)

    def failure_lines(self):
        return read_jsonl(self.errors)


class TestSuccessAndValidation(BatchTestCase):
    def test_success_first_attempt(self):
        counts = self.run_cases(make_cases([1, 2]), ScriptedClassifier())
        self.assertEqual(counts, {"total": 2, "skipped": 0, "succeeded": 2, "failed": 0,
                                  "transient_backoffs": 0})
        lines = self.success_lines()
        self.assertEqual([list(line) for line in lines], [SUCCESS_KEYS, SUCCESS_KEYS])
        self.assertEqual([line["attempts"] for line in lines], [1, 1])
        self.assertEqual(lines[0]["predictions"], json.loads(VALID_RESPONSE))
        self.assertEqual(self.failure_lines(), [])
        self.assertEqual(self.sleep.delays, [])

    def test_malformed_json_then_success_retries_without_backoff(self):
        classifier = ScriptedClassifier({findings(1): ['{"pneumonia": "Positive"', VALID_RESPONSE]})
        counts = self.run_cases(make_cases([1]), classifier)
        self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 0))
        self.assertEqual(self.success_lines()[0]["attempts"], 2)
        self.assertEqual(self.sleep.delays, [])

    def test_validation_failures_exhaust_attempts(self):
        bad = labels_json(pneumonia="positive")
        classifier = ScriptedClassifier({findings(1): [bad, bad]})
        counts = self.run_cases(make_cases([1, 2]), classifier)
        self.assertEqual((counts["succeeded"], counts["failed"]), (1, 1))
        failure = self.failure_lines()[0]
        self.assertEqual(list(failure), FAILURE_KEYS)
        self.assertEqual((failure["case_id"], failure["status"], failure["attempts"]),
                         (1, "failed", 2))
        self.assertTrue(failure["error"].startswith("ResponseValidationError: Invalid labels."))
        self.assertEqual(self.sleep.delays, [])
        self.assertEqual(len(classifier.calls), 3)

    def test_fenced_and_empty_responses_are_rejected_not_repaired(self):
        fenced = f"```json\n{VALID_RESPONSE}\n```"
        classifier = ScriptedClassifier({findings(1): [fenced, ""]})
        self.run_cases(make_cases([1]), classifier)
        self.assertEqual(self.success_lines(), [])
        self.assertIn("Model response is empty", self.failure_lines()[0]["error"])

    def test_missing_and_extra_keys_rejected(self):
        data = json.loads(VALID_RESPONSE)
        missing = dict(data)
        missing.pop("rtm")
        extra = {**data, "other": "Negative"}
        classifier = ScriptedClassifier({findings(1): [json.dumps(missing), json.dumps(extra)]})
        self.run_cases(make_cases([1]), classifier)
        self.assertIn("Unexpected keys", self.failure_lines()[0]["error"])

    def test_only_the_three_report_fields_reach_the_classifier(self):
        classifier = ScriptedClassifier()
        self.run_cases(make_cases([1, 2]), classifier)
        for payload in classifier.calls:
            self.assertEqual(set(payload), {"findings", "conclusions", "recommendations"})

    def test_checkpoint_skip_and_failed_case_retried_later(self):
        bad = "not json"
        self.run_cases(make_cases([1, 2]), ScriptedClassifier({findings(2): [bad, bad]}))
        second = ScriptedClassifier()
        counts = self.run_cases(make_cases([1, 2]), second)
        self.assertEqual((counts["skipped"], counts["succeeded"]), (1, 1))
        self.assertEqual([call["findings"] for call in second.calls], [findings(2)])


class TestTransientErrors(BatchTestCase):
    def test_transient_http_then_success_backs_off_once(self):
        for code in (408, 429, 500, 502, 503, 504):
            with self.subTest(code=code):
                self.results.unlink(missing_ok=True)
                self.sleep.delays.clear()
                classifier = ScriptedClassifier(
                    {findings(1): [lambda c=code: langchain_error(c), VALID_RESPONSE]})
                counts = self.run_cases(make_cases([1]), classifier)
                self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 1))
                self.assertEqual(self.sleep.delays, [2.0])
                self.assertEqual(self.success_lines()[0]["attempts"], 2)

    def test_transient_twice_fails_without_sleeping_after_last_attempt(self):
        classifier = ScriptedClassifier(
            {findings(1): [lambda: langchain_error(503), lambda: langchain_error(503)]})
        counts = self.run_cases(make_cases([1, 2]), classifier)
        self.assertEqual((counts["failed"], counts["succeeded"], counts["transient_backoffs"]),
                         (1, 1, 1))
        self.assertEqual(self.sleep.delays, [2.0])
        failure = self.failure_lines()[0]
        self.assertEqual(failure["attempts"], 2)
        self.assertTrue(failure["error"].startswith("GoogleAPIError: 503"))

    def test_network_timeout_backs_off_like_408(self):
        for cls in (httpx.ReadTimeout, httpx.ConnectTimeout):
            with self.subTest(cls=cls.__name__):
                self.results.unlink(missing_ok=True)
                self.sleep.delays.clear()
                classifier = ScriptedClassifier(
                    {findings(1): [lambda c=cls: timeout_error(c), VALID_RESPONSE]})
                counts = self.run_cases(make_cases([1]), classifier)
                self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 1))
                self.assertEqual(self.sleep.delays, [2.0])

    def test_connection_error_then_success_backs_off_once(self):
        for cls in (httpx.ConnectError, httpx.ReadError, httpx.WriteError):
            with self.subTest(cls=cls.__name__):
                self.results.unlink(missing_ok=True)
                self.sleep.delays.clear()
                classifier = ScriptedClassifier(
                    {findings(1): [lambda c=cls: c("synthetic"), VALID_RESPONSE]})
                counts = self.run_cases(make_cases([1]), classifier)
                self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 1))
                self.assertEqual(self.sleep.delays, [2.0])
                self.assertEqual(self.success_lines()[0]["attempts"], 2)

    def test_repeated_connection_errors_fail_with_no_wait_after_last_attempt(self):
        classifier = ScriptedClassifier(
            {findings(1): [lambda: httpx.ConnectError("synthetic"),
                           lambda: httpx.ConnectError("synthetic")]})
        counts = self.run_cases(make_cases([1, 2]), classifier)
        self.assertEqual((counts["failed"], counts["succeeded"], counts["transient_backoffs"]),
                         (1, 1, 1))
        self.assertEqual(self.sleep.delays, [2.0])  # one wait, between attempts 1 and 2 only
        failure = self.failure_lines()[0]
        self.assertEqual(list(failure), FAILURE_KEYS)
        self.assertEqual((failure["attempts"], failure["error"]),
                         (2, "ConnectError: synthetic"))
        self.assertEqual(len(classifier.calls), 3)  # 2 attempts for case 1, 1 for case 2

    def test_programming_error_retries_immediately(self):
        classifier = ScriptedClassifier({findings(1): [TypeError("bug"), VALID_RESPONSE]})
        counts = self.run_cases(make_cases([1]), classifier)
        self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 0))
        self.assertEqual(self.sleep.delays, [])

    def test_mixed_transient_then_validation_failure(self):
        classifier = ScriptedClassifier(
            {findings(1): [lambda: langchain_error(429), "not json"]})
        self.run_cases(make_cases([1]), classifier)
        self.assertEqual(self.sleep.delays, [2.0])
        self.assertTrue(self.failure_lines()[0]["error"].startswith("ResponseValidationError"))

    def test_bounded_exponential_backoff_with_more_attempts(self):
        policy = RetryPolicy(max_attempts=4, backoff_max_seconds=5.0)
        classifier = ScriptedClassifier(
            {findings(1): [lambda: sdk_error(503)] * 3 + [VALID_RESPONSE]})
        counts = self.run_cases(make_cases([1]), classifier, policy)
        self.assertEqual(self.sleep.delays, [2.0, 4.0, 5.0])
        self.assertEqual((counts["transient_backoffs"], self.success_lines()[0]["attempts"]),
                         (3, 4))

    def test_single_attempt_policy_never_sleeps(self):
        policy = RetryPolicy(max_attempts=1)
        classifier = ScriptedClassifier({findings(1): [lambda: sdk_error(503)]})
        self.run_cases(make_cases([1]), classifier, policy)
        self.assertEqual(self.sleep.delays, [])
        self.assertEqual(self.failure_lines()[0]["attempts"], 1)


class TestFatalErrors(BatchTestCase):
    def test_fatal_http_codes_stop_the_batch(self):
        for code in (400, 401, 403, 404):
            with self.subTest(code=code):
                self.results.unlink(missing_ok=True)
                self.errors.unlink(missing_ok=True)
                classifier = ScriptedClassifier({findings(2): [lambda c=code: langchain_error(c)]})
                with self.assertRaises(FatalProviderError) as ctx:
                    self.run_cases(make_cases([1, 2, 3]), classifier)
                error = ctx.exception
                self.assertIs(error.decision.error_class, ErrorClass.FATAL)
                self.assertEqual(error.decision.status_code, code)
                self.assertEqual(error.counts["succeeded"], 1)
                # Case 1 saved; case 2 not written anywhere (stays pending); case 3 untouched.
                self.assertEqual([line["case_id"] for line in self.success_lines()], [1])
                self.assertEqual(self.failure_lines(), [])
                self.assertEqual([call["findings"] for call in classifier.calls],
                                 [findings(1), findings(2)])
                self.assertEqual(self.sleep.delays, [])

    def test_fatal_error_is_not_retried(self):
        classifier = ScriptedClassifier({findings(1): [lambda: langchain_error(400),
                                                       VALID_RESPONSE]})
        with self.assertRaises(FatalProviderError):
            self.run_cases(make_cases([1]), classifier)
        self.assertEqual(len(classifier.calls), 1)

    def test_configuration_error_is_reraised_unchanged(self):
        classifier = ScriptedClassifier({findings(1): [ConfigurationError("missing key")]})
        with self.assertRaises(ConfigurationError) as ctx:
            self.run_cases(make_cases([1]), classifier)
        self.assertNotIsInstance(ctx.exception, FatalProviderError)
        self.assertEqual(len(classifier.calls), 1)

    def test_rerun_after_fatal_resumes_with_pending_case(self):
        with self.assertRaises(FatalProviderError):
            self.run_cases(make_cases([1, 2]), ScriptedClassifier({findings(2): [sdk_error(401)]}))
        resumed = ScriptedClassifier()
        counts = self.run_cases(make_cases([1, 2]), resumed)
        self.assertEqual((counts["skipped"], counts["succeeded"]), (1, 1))

    def test_default_classifier_validates_configuration_first(self):
        with mock.patch("week_07.batch_runner.config.validate_runtime_configuration",
                        side_effect=ConfigurationError("GOOGLE_API_KEY was not found.")), \
                mock.patch("week_07.batch_runner._default_classifier") as factory:
            with self.assertRaises(ConfigurationError):
                self.run_cases(make_cases([1]), None)
        factory.assert_not_called()
        self.assertFalse(self.results.exists())


class TestIsolationEnforced(BatchTestCase):
    def test_outputs_must_pass_the_guard(self):
        week5 = self.root / "outputs" / "week_05" / "matrix_2" / "predictions.jsonl"
        for results, errors in ((week5, self.errors), (self.results, self.root / "x.jsonl"),
                                (self.policy.workflows["matrix1"].predictions_path,
                                 self.errors)):
            with self.subTest(results=results, errors=errors):
                with self.assertRaises(IsolationError):
                    run_batch(make_cases([1]), results, errors, classifier=ScriptedClassifier(),
                              spec=self.spec, isolation=self.policy, sleep=self.sleep)
        self.assertFalse(week5.exists())


class TestRealSdkThroughBatch(BatchTestCase):
    """Real ChatGoogleGenerativeAI on a mock transport, driven by the batch runner."""

    def setUp(self):
        super().setUp()
        import os

        from week_07.tests.gemini_fakes import DUMMY_KEY

        patcher = mock.patch.dict(os.environ, {"GOOGLE_API_KEY": DUMMY_KEY})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("GEMINI_API_KEY", None)
        self.env = {"GOOGLE_API_KEY": DUMMY_KEY}

    def classifier(self, outcomes):
        from week_07.config import GeminiModelConfig
        from week_07.llm_client import GeminiClassifier, create_chat_model

        gemini = MockGemini(outcomes)
        model = offline_chat_model(
            lambda: create_chat_model(GeminiModelConfig(), environ=self.env), gemini)
        return GeminiClassifier(chat_model=model), gemini

    def test_503_then_success(self):
        classifier, gemini = self.classifier(
            [(503, None), (200, ok_body([{"text": VALID_RESPONSE}]))])
        counts = self.run_cases(make_cases([1]), classifier)
        self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 1))
        self.assertEqual(len(gemini.requests), 2)  # 2 application attempts x 1 transport attempt
        self.assertEqual(self.sleep.delays, [2.0])

    def test_timeout_twice_gives_failure_record(self):
        classifier, gemini = self.classifier([httpx.ReadTimeout, httpx.ReadTimeout])
        self.run_cases(make_cases([1]), classifier)
        self.assertEqual(len(gemini.requests), 2)
        self.assertTrue(self.failure_lines()[0]["error"].startswith("ReadTimeout"))

    def test_connect_error_then_success(self):
        classifier, gemini = self.classifier(
            [httpx.ConnectError, (200, ok_body([{"text": VALID_RESPONSE}]))])
        counts = self.run_cases(make_cases([1]), classifier)
        self.assertEqual((counts["succeeded"], counts["transient_backoffs"]), (1, 1))
        self.assertEqual(len(gemini.requests), 2)
        self.assertEqual(self.sleep.delays, [2.0])

    def test_connect_error_twice_gives_failure_record(self):
        classifier, gemini = self.classifier([httpx.ConnectError, httpx.ConnectError])
        self.run_cases(make_cases([1]), classifier)
        self.assertEqual(len(gemini.requests), 2)
        self.assertEqual(self.sleep.delays, [2.0])
        self.assertTrue(self.failure_lines()[0]["error"].startswith("ConnectError"))

    def test_safety_blocked_twice_keeps_week5_failure_schema(self):
        blocked = (200, {"candidates": [{"finishReason": "SAFETY",
                                         "content": {"role": "model"}}]})
        classifier, gemini = self.classifier([blocked, blocked])
        counts = self.run_cases(make_cases([1]), classifier)
        self.assertEqual((counts["failed"], counts["transient_backoffs"]), (1, 0))
        self.assertEqual(self.sleep.delays, [])  # validation failure: no backoff
        self.assertEqual(self.success_lines(), [])
        failure = self.failure_lines()[0]
        self.assertEqual(list(failure), FAILURE_KEYS)
        self.assertEqual(failure["error"],
                         "ResponseValidationError: Model response is empty or is not text.")

    def test_401_stops_after_one_request(self):
        classifier, gemini = self.classifier([(401, None)])
        with self.assertRaises(FatalProviderError):
            self.run_cases(make_cases([1, 2]), classifier)
        self.assertEqual(len(gemini.requests), 1)
