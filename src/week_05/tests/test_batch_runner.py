"""Offline tests for batch execution. Fake classifiers only; no OpenAI requests."""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import openai

from week_05 import batch_runner, cli, config
from week_05.batch_runner import resolve_outputs, run_batch, run_workflow_batch
from week_05.conditions import CONDITION_KEYS
from week_05.config import MATRIX1, MATRIX2, ConfigurationError
from week_05.dataset_loader import DatasetError
from week_05.tests.support import (
    VALID_RESPONSE,
    FrozenDatetime,
    ScriptedClassifier,
    StepClock,
    labels_json,
    make_cases,
    quiet,
    read_jsonl,
)
from week_05.tests.workbook_factory import (
    LEAK_MARKER,
    MATRIX1_HEADERS,
    MATRIX2_HEADERS,
    make_workbook,
)

LOGGERS = ("week_05.batch_runner", "week_05.jsonl_store", "week_05.dataset_loader")
FAKE_KEY = "sk-test-not-a-real-key-0123456789"
REQUEST = httpx.Request("POST", "https://api.openai.invalid/v1/chat/completions")


def api_errors() -> dict[str, Exception]:
    rate_limited = httpx.Response(429, request=REQUEST)
    server_error = httpx.Response(500, request=REQUEST)
    return {
        "connection": openai.APIConnectionError(request=REQUEST),
        "timeout": openai.APITimeoutError(request=REQUEST),
        "rate limit": openai.RateLimitError("Rate limit reached", response=rate_limited,
                                            body=None),
        "server": openai.InternalServerError("Server error", response=server_error, body=None),
        "builtin timeout": TimeoutError("read timed out"),
    }


class BatchTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.results = self.dir / "out" / "predictions.jsonl"
        self.errors = self.dir / "out" / "errors.jsonl"
        quiet(self, *LOGGERS)

    def run_batch(self, cases, classifier, **kwargs):
        kwargs.setdefault("clock", StepClock())
        return run_batch(cases, self.results, self.errors, classifier=classifier, **kwargs)


class TestSuccessfulExecution(BatchTestCase):
    def test_all_cases_succeed(self):
        classifier = ScriptedClassifier()
        counts = self.run_batch(make_cases(range(1, 6)), classifier)
        self.assertEqual(counts, {"total": 5, "skipped": 0, "succeeded": 5, "failed": 0})
        self.assertEqual(list(counts), ["total", "skipped", "succeeded", "failed"])
        records = read_jsonl(self.results)
        self.assertEqual([r["case_id"] for r in records], [1, 2, 3, 4, 5])
        self.assertTrue(all(r["status"] == "success" and r["attempts"] == 1 for r in records))
        self.assertFalse(self.errors.exists())
        self.assertEqual(len(classifier.calls), 5)

    def test_predictions_are_validated_canonical_order(self):
        reordered = json.dumps({k: "Positive" if k == "rtm" else "Negative"
                                for k in reversed(CONDITION_KEYS)})
        self.run_batch(make_cases([1]), ScriptedClassifier(default=reordered))
        predictions = read_jsonl(self.results)[0]["predictions"]
        self.assertEqual(tuple(predictions), CONDITION_KEYS)
        self.assertEqual(predictions["rtm"], "Positive")

    def test_classifier_receives_only_the_payload(self):
        classifier = ScriptedClassifier()
        self.run_batch(make_cases([10, 11]), classifier)
        self.assertEqual(classifier.calls, [
            {"findings": "findings 10", "conclusions": "", "recommendations": ""},
            {"findings": "findings 11", "conclusions": "", "recommendations": ""},
        ])

    def test_output_directories_are_created(self):
        results = self.dir / "a" / "b" / "predictions.jsonl"
        errors = self.dir / "c" / "errors.jsonl"
        run_batch(make_cases([1]), results, errors, classifier=ScriptedClassifier(default="x"),
                  max_attempts=1)
        self.assertFalse(results.exists())
        self.assertTrue(results.parent.is_dir())
        self.assertTrue(errors.is_file())

    def test_empty_case_list(self):
        counts = self.run_batch((), ScriptedClassifier())
        self.assertEqual(counts, {"total": 0, "skipped": 0, "succeeded": 0, "failed": 0})


class TestRetries(BatchTestCase):
    def test_invalid_then_valid_is_retried_and_saved(self):
        classifier = ScriptedClassifier({"findings 1": ["not json"]})
        counts = self.run_batch(make_cases([1]), classifier)
        self.assertEqual(counts["succeeded"], 1)
        self.assertEqual(len(classifier.calls), 2)
        self.assertEqual(read_jsonl(self.results)[0]["attempts"], 2)
        self.assertFalse(self.errors.exists())

    def test_exhausted_attempts_record_last_error_and_continue(self):
        classifier = ScriptedClassifier({
            "findings 1": ["```json\n{}\n```", labels_json(rtm="positive")],
        })
        counts = self.run_batch(make_cases([1, 2]), classifier)
        self.assertEqual(counts, {"total": 2, "skipped": 0, "succeeded": 1, "failed": 1})
        error = read_jsonl(self.errors)[0]
        self.assertEqual(error["case_id"], 1)
        self.assertEqual(error["status"], "failed")
        self.assertEqual(error["attempts"], 2)
        self.assertEqual(error["error"],
                         "ResponseValidationError: Invalid labels. Values must be exactly "
                         "'Positive' or 'Negative': rtm='positive'")
        self.assertEqual([r["case_id"] for r in read_jsonl(self.results)], [2])

    def test_max_attempts_controls_call_count(self):
        for attempts in (1, 2, 3, 5):
            with self.subTest(max_attempts=attempts):
                for path in (self.results, self.errors):
                    path.unlink(missing_ok=True)
                classifier = ScriptedClassifier(default="bad")
                self.run_batch(make_cases([1]), classifier, max_attempts=attempts)
                self.assertEqual(len(classifier.calls), attempts)
                self.assertEqual(read_jsonl(self.errors)[0]["attempts"], attempts)

    def test_success_on_last_permitted_attempt(self):
        classifier = ScriptedClassifier({"findings 1": ["bad", "bad"]})
        self.run_batch(make_cases([1]), classifier, max_attempts=3)
        self.assertEqual(read_jsonl(self.results)[0]["attempts"], 3)

    def test_invalid_max_attempts_rejected_before_any_work(self):
        for value in (0, -1, True, 2.0, "2", None):
            with self.subTest(value=value):
                classifier = ScriptedClassifier()
                with self.assertRaisesRegex(ValueError, "at least 1"):
                    self.run_batch(make_cases([1]), classifier, max_attempts=value)
                self.assertEqual(classifier.calls, [])
                self.assertFalse(self.results.parent.exists())

    def test_default_attempts_is_two(self):
        classifier = ScriptedClassifier(default="bad")
        run_batch(make_cases([1]), self.results, self.errors, classifier=classifier)
        self.assertEqual(len(classifier.calls), 2)


class TestApiExceptions(BatchTestCase):
    def test_api_errors_are_retried_then_succeed(self):
        for name, exc in api_errors().items():
            with self.subTest(error=name):
                for path in (self.results, self.errors):
                    path.unlink(missing_ok=True)
                classifier = ScriptedClassifier({"findings 1": [exc]})
                counts = self.run_batch(make_cases([1]), classifier)
                self.assertEqual(counts["succeeded"], 1)
                self.assertEqual(read_jsonl(self.results)[0]["attempts"], 2)

    def test_exhausted_api_errors_are_recorded_with_type_and_message(self):
        expected = {
            "connection": "APIConnectionError: Connection error.",
            "timeout": "APITimeoutError: Request timed out.",
            "rate limit": "RateLimitError: Rate limit reached",
            "server": "InternalServerError: Server error",
            "builtin timeout": "TimeoutError: read timed out",
        }
        for name, exc in api_errors().items():
            with self.subTest(error=name):
                for path in (self.results, self.errors):
                    path.unlink(missing_ok=True)
                counts = self.run_batch(make_cases([1, 2]),
                                        ScriptedClassifier({"findings 1": [exc, exc]}))
                self.assertEqual(counts, {"total": 2, "skipped": 0, "succeeded": 1, "failed": 1})
                self.assertEqual(read_jsonl(self.errors)[0]["error"], expected[name])

    def test_mixed_failures_keep_the_last_error(self):
        classifier = ScriptedClassifier({"findings 1": [openai.APITimeoutError(request=REQUEST),
                                                        "not json"]})
        self.run_batch(make_cases([1]), classifier)
        self.assertTrue(read_jsonl(self.errors)[0]["error"].startswith(
            "ResponseValidationError: Response is not valid JSON"))

    def test_configuration_error_during_run_is_fatal_not_retried(self):
        classifier = ScriptedClassifier({"findings 2": [ConfigurationError("key revoked")]})
        with self.assertRaisesRegex(ConfigurationError, "key revoked"):
            self.run_batch(make_cases([1, 2, 3]), classifier)
        self.assertEqual(len(classifier.calls), 2)
        self.assertEqual([r["case_id"] for r in read_jsonl(self.results)], [1])
        self.assertFalse(self.errors.exists())


class TestCheckpointAndResume(BatchTestCase):
    def test_completed_cases_are_skipped_on_restart(self):
        cases = make_cases(range(1, 4))
        self.run_batch(cases, ScriptedClassifier())
        classifier = ScriptedClassifier()
        counts = self.run_batch(cases, classifier)
        self.assertEqual(counts, {"total": 3, "skipped": 3, "succeeded": 0, "failed": 0})
        self.assertEqual(classifier.calls, [])
        self.assertEqual(len(read_jsonl(self.results)), 3)

    def test_failed_cases_are_retried_on_a_later_run(self):
        cases = make_cases(range(1, 5))
        first = self.run_batch(cases, ScriptedClassifier({"findings 3": ["bad", "bad"]}))
        self.assertEqual(first, {"total": 4, "skipped": 0, "succeeded": 3, "failed": 1})
        classifier = ScriptedClassifier()
        second = self.run_batch(cases, classifier)
        self.assertEqual(second, {"total": 4, "skipped": 3, "succeeded": 1, "failed": 0})
        self.assertEqual([c["findings"] for c in classifier.calls], ["findings 3"])
        self.assertEqual([r["case_id"] for r in read_jsonl(self.results)], [1, 2, 4, 3])
        # Week 4 keeps the stale failure line in errors.jsonl (P3: unchanged).
        self.assertEqual([r["case_id"] for r in read_jsonl(self.errors)], [3])

    def test_interrupted_run_resumes_without_duplicates(self):
        cases = make_cases(range(1, 7))
        crashing = ScriptedClassifier({"findings 4": [KeyboardInterrupt()]})
        with self.assertRaises(KeyboardInterrupt):
            self.run_batch(cases, crashing)
        self.assertEqual([r["case_id"] for r in read_jsonl(self.results)], [1, 2, 3])
        self.assertFalse(self.errors.exists())

        classifier = ScriptedClassifier()
        counts = self.run_batch(cases, classifier)
        self.assertEqual(counts, {"total": 6, "skipped": 3, "succeeded": 3, "failed": 0})
        self.assertEqual([c["findings"] for c in classifier.calls],
                         ["findings 4", "findings 5", "findings 6"])
        self.assertEqual([r["case_id"] for r in read_jsonl(self.results)], [1, 2, 3, 4, 5, 6])

    def test_partial_run_with_subset_then_full_set(self):
        all_cases = make_cases(range(1, 11))
        self.run_batch(all_cases[:4], ScriptedClassifier())
        classifier = ScriptedClassifier()
        counts = self.run_batch(all_cases, classifier)
        self.assertEqual(counts, {"total": 10, "skipped": 4, "succeeded": 6, "failed": 0})

    def test_existing_invalid_checkpoint_line_causes_reclassification(self):
        self.results.parent.mkdir(parents=True)
        bad = {"case_id": 1, "status": "success", "attempts": 1,
               "completed_at_utc": "2026-01-01T00:00:00+00:00",
               "predictions": {"rtm": "Negative"}}
        self.results.write_text(json.dumps(bad) + "\n", encoding="utf-8")
        classifier = ScriptedClassifier()
        counts = self.run_batch(make_cases([1]), classifier)
        self.assertEqual(counts["succeeded"], 1)
        self.assertEqual(len(read_jsonl(self.results)), 2)  # original line is kept

    def test_records_not_in_current_input_are_left_untouched(self):
        self.run_batch(make_cases([90, 91]), ScriptedClassifier())
        before = self.results.read_text(encoding="utf-8")
        counts = self.run_batch(make_cases([1]), ScriptedClassifier())
        self.assertEqual(counts, {"total": 1, "skipped": 0, "succeeded": 1, "failed": 0})
        self.assertTrue(self.results.read_text(encoding="utf-8").startswith(before))

    def test_checkpoint_identity_is_string_form_of_case_id(self):
        self.run_batch(make_cases([5]), ScriptedClassifier())
        classifier = ScriptedClassifier()
        counts = self.run_batch(make_cases(["5"]), classifier)
        self.assertEqual(counts["skipped"], 1)
        self.assertEqual(classifier.calls, [])


class TestDuplicateCaseIds(BatchTestCase):
    def test_duplicate_after_success_is_skipped(self):
        classifier = ScriptedClassifier()
        counts = self.run_batch(make_cases([5, 6, 5]), classifier)
        self.assertEqual(counts, {"total": 3, "skipped": 1, "succeeded": 2, "failed": 0})
        self.assertEqual(len(classifier.calls), 2)
        self.assertEqual([r["case_id"] for r in read_jsonl(self.results)], [5, 6])

    def test_int_and_string_duplicate_treated_as_same_case(self):
        counts = self.run_batch(make_cases([5, "5"]), ScriptedClassifier())
        self.assertEqual(counts, {"total": 2, "skipped": 1, "succeeded": 1, "failed": 0})

    def test_duplicate_after_failure_is_attempted_again(self):
        classifier = ScriptedClassifier(default="bad")
        counts = self.run_batch(make_cases([7, 7]), classifier)
        self.assertEqual(counts, {"total": 2, "skipped": 0, "succeeded": 0, "failed": 2})
        self.assertEqual([r["case_id"] for r in read_jsonl(self.errors)], [7, 7])


class TestTimestamps(BatchTestCase):
    def test_injected_clock_values(self):
        self.run_batch(make_cases([1, 2]), ScriptedClassifier({"findings 2": ["x", "y"]}))
        success = read_jsonl(self.results)[0]
        failure = read_jsonl(self.errors)[0]
        self.assertEqual(success["completed_at_utc"], "2026-11-10T09:30:00.123456+00:00")
        self.assertEqual(failure["failed_at_utc"], "2026-11-10T09:30:00.124456+00:00")
        self.assertNotIn("completed_at_utc", failure)
        self.assertNotIn("failed_at_utc", success)

    def test_real_clock_produces_increasing_utc_timestamps(self):
        run_batch(make_cases(range(1, 4)), self.results, self.errors,
                  classifier=ScriptedClassifier())
        stamps = [datetime.fromisoformat(r["completed_at_utc"]) for r in read_jsonl(self.results)]
        self.assertTrue(all(s.utcoffset().total_seconds() == 0 for s in stamps))
        self.assertEqual(stamps, sorted(stamps))


class TestFailFastConfiguration(BatchTestCase):
    def _patched(self, env):
        stack = contextlib.ExitStack()
        stack.enter_context(patch.dict(os.environ, env, clear=True))
        stack.enter_context(patch("week_05.config.load_dotenv"))
        return stack

    def test_missing_key_aborts_before_any_attempt_or_record(self):
        with self._patched({}), \
                patch("week_05.llm_client.create_chat_model") as factory:
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
                run_batch(make_cases([1, 2]), self.results, self.errors)
        factory.assert_not_called()
        self.assertFalse(self.results.exists())
        self.assertFalse(self.errors.exists())

    def test_invalid_setting_aborts_before_any_attempt(self):
        with self._patched({"OPENAI_API_KEY": FAKE_KEY, "OPENAI_TEMPERATURE": "warm"}), \
                patch("week_05.llm_client.create_chat_model") as factory:
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_TEMPERATURE"):
                run_batch(make_cases([1]), self.results, self.errors)
        factory.assert_not_called()
        self.assertFalse(self.errors.exists())

    def test_fully_checkpointed_run_needs_no_key(self):
        self.run_batch(make_cases([1, 2]), ScriptedClassifier())
        with self._patched({}):
            counts = run_batch(make_cases([1, 2]), self.results, self.errors)
        self.assertEqual(counts, {"total": 2, "skipped": 2, "succeeded": 0, "failed": 0})

    def test_default_classifier_creates_one_client_for_the_whole_batch(self):
        class FakeChat:
            def __init__(self):
                self.calls = 0

            def invoke(self, messages):
                self.calls += 1
                return SimpleNamespace(content=VALID_RESPONSE)

        chat = FakeChat()
        with self._patched({"OPENAI_API_KEY": FAKE_KEY}), \
                patch("week_05.llm_client.create_chat_model", return_value=chat) as factory:
            counts = run_batch(make_cases(range(1, 6)), self.results, self.errors,
                               clock=StepClock())
        self.assertEqual(counts["succeeded"], 5)
        factory.assert_called_once()
        self.assertEqual(chat.calls, 5)

    def test_injected_classifier_does_not_require_a_key(self):
        with self._patched({}):
            counts = self.run_batch(make_cases([1]), ScriptedClassifier())
        self.assertEqual(counts["succeeded"], 1)


class TestWorkflowSeparation(BatchTestCase):
    def make_inputs(self):
        m1 = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS, case_ids=range(1, 101))
        m2 = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS, case_ids=range(1001, 1101))
        return m1, m2

    def test_each_workflow_writes_only_its_own_cases_and_directory(self):
        m1_input, m2_input = self.make_inputs()
        m1_out, m2_out = self.dir / "w5" / "matrix_1", self.dir / "w5" / "matrix_2"
        all_positive = json.dumps({k: "Positive" for k in CONDITION_KEYS})
        m1_classifier = ScriptedClassifier(default=all_positive)
        m2_classifier = ScriptedClassifier()

        m1 = run_workflow_batch(MATRIX1, m1_input, output_dir=m1_out,
                                classifier=m1_classifier, clock=StepClock())
        self.assertFalse(m2_out.exists())
        m2 = run_workflow_batch(MATRIX2, m2_input, output_dir=m2_out,
                                classifier=m2_classifier, clock=StepClock())

        self.assertEqual(m1, {"total": 100, "skipped": 0, "succeeded": 100, "failed": 0})
        self.assertEqual(m2, {"total": 100, "skipped": 0, "succeeded": 100, "failed": 0})
        m1_records = read_jsonl(m1_out / "predictions.jsonl")
        m2_records = read_jsonl(m2_out / "predictions.jsonl")
        self.assertEqual([r["case_id"] for r in m1_records], list(range(1, 101)))
        self.assertEqual([r["case_id"] for r in m2_records], list(range(1001, 1101)))
        # Predictions are the classifier's output, never the workbook's reference labels.
        self.assertTrue(all(set(r["predictions"].values()) == {"Positive"} for r in m1_records))
        self.assertTrue(all(set(r["predictions"].values()) == {"Negative"} for r in m2_records))

    def test_classifier_never_receives_ids_labels_or_other_columns(self):
        m1_input, m2_input = self.make_inputs()
        for spec, path in ((MATRIX1, m1_input), (MATRIX2, m2_input)):
            with self.subTest(workflow=spec.name):
                classifier = ScriptedClassifier()
                run_workflow_batch(spec, path, output_dir=self.dir / spec.name,
                                   classifier=classifier, clock=StepClock())
                self.assertEqual(len(classifier.calls), 100)
                for payload in classifier.calls:
                    self.assertEqual(tuple(payload),
                                     ("findings", "conclusions", "recommendations"))
                    text = repr(payload)
                    for forbidden in (LEAK_MARKER, "Positive", "Negative", "CaseID"):
                        self.assertNotIn(forbidden, text)

    def test_matrix1_still_requires_exactly_100_cases(self):
        short = make_workbook(self.dir / "short.xlsx", MATRIX1_HEADERS, case_ids=range(1, 100))
        classifier = ScriptedClassifier()
        with self.assertRaises(DatasetError):
            run_workflow_batch(MATRIX1, short, output_dir=self.dir / "m1", classifier=classifier)
        self.assertEqual(classifier.calls, [])

    def test_matrix2_runs_a_short_dataset_with_warning(self):
        short = make_workbook(self.dir / "short.xlsx", MATRIX2_HEADERS, case_ids=range(1, 61))
        counts = run_workflow_batch(MATRIX2, short, output_dir=self.dir / "m2",
                                    classifier=ScriptedClassifier(), clock=StepClock())
        self.assertEqual(counts["total"], 60)

    def test_invalid_max_attempts_rejected_before_loading(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            run_workflow_batch(MATRIX1, self.dir / "absent.xlsx", max_attempts=0)


class TestOutputIsolation(unittest.TestCase):
    def test_default_outputs_are_separate_week5_directories(self):
        m1, m2 = resolve_outputs(MATRIX1), resolve_outputs(MATRIX2)
        self.assertEqual(m1.output_dir, MATRIX1.output_dir.resolve())
        self.assertEqual(m2.output_dir, MATRIX2.output_dir.resolve())
        self.assertNotEqual(m1.output_dir, m2.output_dir)
        self.assertEqual(m1.predictions_path.name, "predictions.jsonl")
        self.assertEqual(m2.errors_path.name, "errors.jsonl")

    def test_cannot_write_into_or_around_the_other_workflow(self):
        for spec, other in ((MATRIX1, MATRIX2), (MATRIX2, MATRIX1)):
            for target in (other.output_dir, other.output_dir / "sub", other.output_dir.parent):
                with self.subTest(workflow=spec.name, target=str(target)):
                    with self.assertRaisesRegex(ConfigurationError, other.name):
                        resolve_outputs(spec, target)

    def test_cannot_write_into_week4_outputs(self):
        week4 = config.REPO_ROOT / "outputs" / "week_04"
        for target in (week4, week4 / "matrix_1", week4 / "canine_thorax"):
            with self.subTest(target=str(target)):
                with self.assertRaisesRegex(ConfigurationError, "Week 4"):
                    resolve_outputs(MATRIX1, target)

    def test_custom_directory_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = resolve_outputs(MATRIX2, tmp)
        self.assertEqual(outputs.output_dir, Path(tmp).resolve())


class TestWeek4Compatibility(BatchTestCase):
    """Week 5 must write byte-identical JSONL files and accept Week 4 checkpoints."""

    def setUp(self):
        super().setUp()
        import logging

        week4_logger = logging.getLogger("vetology_week4.batch")
        previous = week4_logger.disabled
        week4_logger.disabled = True
        self.addCleanup(setattr, week4_logger, "disabled", previous)

    def run_both(self, cases, script, prepare=None, max_attempts=2):
        from week_04.batch_processor import run_batch as week4_run_batch

        outcomes = {}
        for name in ("week4", "week5"):
            directory = self.dir / name
            directory.mkdir()
            results, errors = directory / "predictions.jsonl", directory / "errors.jsonl"
            if prepare:
                prepare(results, errors)
            classifier = ScriptedClassifier(script)
            if name == "week4":
                with patch("week_04.batch_processor.datetime", FrozenDatetime(StepClock())):
                    counts = week4_run_batch(cases, results, errors, max_attempts=max_attempts,
                                             classifier=classifier)
            else:
                counts = run_batch(cases, results, errors, max_attempts=max_attempts,
                                   classifier=classifier, clock=StepClock())
            outcomes[name] = (
                counts,
                classifier.calls,
                results.read_bytes() if results.exists() else None,
                errors.read_bytes() if errors.exists() else None,
            )
        return outcomes

    def assert_identical(self, outcomes):
        self.assertEqual(outcomes["week5"], outcomes["week4"])

    def test_fresh_run_with_retries_failures_and_api_errors(self):
        script = {
            "findings 2": ["not json"],
            "findings 3": ["bad", openai.APITimeoutError(request=REQUEST)],
            "findings 4": [openai.APIConnectionError(request=REQUEST)],
            "findings café": [labels_json(rtm="Positive")],
        }
        cases = make_cases([1, 2, 3, 4, "café", 6.5])
        self.assert_identical(self.run_both(cases, script))

    def test_resume_from_existing_checkpoint(self):
        def prepare(results, errors):
            record = {"case_id": 2, "status": "success", "attempts": 1,
                      "completed_at_utc": "2026-11-07T05:10:39.561912+00:00",
                      "predictions": json.loads(VALID_RESPONSE)}
            results.write_text("garbage\n" + json.dumps(record) + "\n", encoding="utf-8")
            errors.write_text(json.dumps({"case_id": 9, "status": "failed"}) + "\n",
                              encoding="utf-8")

        outcomes = self.run_both(make_cases(range(1, 5)), {"findings 3": ["x", "y"]},
                                 prepare=prepare)
        self.assert_identical(outcomes)
        self.assertEqual(outcomes["week5"][0],
                         {"total": 4, "skipped": 1, "succeeded": 2, "failed": 1})

    def test_resume_with_text_and_mixed_type_case_ids(self):
        def prepare(results, errors):
            lines = [{"case_id": case_id, "status": "success", "attempts": 1,
                      "completed_at_utc": "2026-11-07T05:10:39.561912+00:00",
                      "predictions": json.loads(VALID_RESPONSE)}
                     for case_id in ("A-7", 5, "8")]
            results.write_text("".join(json.dumps(r) + "\n" for r in lines), encoding="utf-8")

        outcomes = self.run_both(make_cases(["A-7", "5", 8, "B-1"]), {}, prepare=prepare)
        self.assert_identical(outcomes)
        self.assertEqual(outcomes["week5"][0],
                         {"total": 4, "skipped": 3, "succeeded": 1, "failed": 0})

    def test_newline_terminated_existing_files_still_byte_identical(self):
        """The recovery fix must not change anything when files end with a newline."""
        def prepare(results, errors):
            record = {"case_id": 1, "status": "success", "attempts": 1,
                      "completed_at_utc": "2026-11-07T05:10:39.561912+00:00",
                      "predictions": json.loads(VALID_RESPONSE)}
            results.write_text(json.dumps(record) + "\n", encoding="utf-8")
            errors.write_text('{"case_id": 7, "status": "failed"}\n', encoding="utf-8")

        self.assert_identical(self.run_both(make_cases([1, 2, 3]), {"findings 3": ["x", "y"]},
                                            prepare=prepare))

    def test_interrupted_write_deviates_from_week4_by_design(self):
        """Approved deviation: Week 4 corrupts the next record; Week 5 does not."""
        def prepare(results, errors):
            results.write_text('{"case_id": 1, "status": "succ', encoding="utf-8")

        outcomes = self.run_both(make_cases([1, 2]), {}, prepare=prepare)
        week4_counts, week4_calls, week4_results, _ = outcomes["week4"]
        week5_counts, week5_calls, week5_results, _ = outcomes["week5"]
        self.assertEqual(week5_counts, week4_counts)   # same work done in this run
        self.assertEqual(week5_calls, week4_calls)
        self.assertNotEqual(week5_results, week4_results)
        # Week 4: the first new record is glued onto the partial line.
        self.assertEqual(len(week4_results.decode("utf-8").splitlines()), 2)
        # Week 5: partial line kept, then two independent records.
        week5_lines = week5_results.decode("utf-8").splitlines()
        self.assertEqual(week5_lines[0], '{"case_id": 1, "status": "succ')
        self.assertEqual([json.loads(line)["case_id"] for line in week5_lines[1:]], [1, 2])

    def test_other_attempt_limits(self):
        for attempts in (1, 3):
            with self.subTest(max_attempts=attempts):
                for name in ("week4", "week5"):
                    for path in (self.dir / name).glob("*") if (self.dir / name).exists() else []:
                        path.unlink()
                    if (self.dir / name).exists():
                        (self.dir / name).rmdir()
                outcomes = self.run_both(make_cases([1, 2]),
                                         {"findings 1": ["a", "b"]}, max_attempts=attempts)
                self.assert_identical(outcomes)

    def test_week4_reads_week5_checkpoints_and_vice_versa(self):
        from week_04.batch_processor import _load_successful_case_ids as week4_reader
        from week_05.jsonl_store import load_successful_case_ids as week5_reader

        self.run_batch(make_cases([1, "2", 3]), ScriptedClassifier({"findings 3": ["x", "y"]}))
        self.assertEqual(week4_reader(self.results), {"1", "2"})
        self.assertEqual(week5_reader(self.results), week4_reader(self.results))


class TestInterruptedWriteRecovery(BatchTestCase):
    """Approved Phase 5 deviation: recover cleanly from a partially written line."""

    PARTIAL = '{"case_id": 3, "status": "success", "attempts": 1, "complet'

    def complete_run_then_crash_mid_write(self):
        """Cases 1-2 written completely, then a write of case 3 cut off mid-line."""
        self.run_batch(make_cases([1, 2]), ScriptedClassifier())
        with self.results.open("a", encoding="utf-8") as handle:
            handle.write(self.PARTIAL)
        return self.results.read_text(encoding="utf-8")

    def test_next_run_appends_an_independently_readable_record(self):
        before = self.complete_run_then_crash_mid_write()
        classifier = ScriptedClassifier()
        with self.assertLogs("week_05.jsonl_store", level="WARNING") as logs:
            counts = self.run_batch(make_cases([1, 2, 3]), classifier)
        self.assertEqual(counts, {"total": 3, "skipped": 2, "succeeded": 1, "failed": 0})
        self.assertEqual([c["findings"] for c in classifier.calls], ["findings 3"])
        self.assertTrue(any("does not end with a newline" in m for m in logs.output))

        text = self.results.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(before))             # existing bytes untouched
        lines = text.splitlines()
        self.assertEqual(lines[2], self.PARTIAL)              # partial line preserved as-is
        recovered = json.loads(lines[3])                      # new record stands alone
        self.assertEqual(recovered["case_id"], 3)
        self.assertEqual(recovered["status"], "success")
        self.assertTrue(text.endswith("\n"))

    def test_checkpoint_reading_after_recovery(self):
        from week_05.jsonl_store import load_successful_case_ids

        self.complete_run_then_crash_mid_write()
        with self.assertLogs("week_05.jsonl_store", level="WARNING"):
            self.assertEqual(load_successful_case_ids(self.results), {"1", "2"})
        self.run_batch(make_cases([1, 2, 3]), ScriptedClassifier())
        with self.assertLogs("week_05.jsonl_store", level="WARNING") as logs:
            self.assertEqual(load_successful_case_ids(self.results), {"1", "2", "3"})
        self.assertEqual(len(logs.output), 1)                 # only the old partial line

    def test_resumption_does_not_reclassify_repeatedly(self):
        """Week 4 would re-classify case 3 on every later run; Week 5 does not."""
        self.complete_run_then_crash_mid_write()
        cases = make_cases([1, 2, 3, 4])
        first = ScriptedClassifier()
        self.run_batch(cases, first)
        self.assertEqual([c["findings"] for c in first.calls], ["findings 3", "findings 4"])
        for _ in range(3):
            later = ScriptedClassifier()
            counts = self.run_batch(cases, later)
            self.assertEqual(later.calls, [])
            self.assertEqual(counts, {"total": 4, "skipped": 4, "succeeded": 0, "failed": 0})

    def test_week4_would_reclassify_the_same_case_on_every_run(self):
        """Documents the Week 4 defect that the fix addresses."""
        import logging

        from week_04.batch_processor import run_batch as week4_run_batch

        logging.getLogger("vetology_week4.batch").disabled = True
        self.addCleanup(setattr, logging.getLogger("vetology_week4.batch"), "disabled", False)
        self.results.parent.mkdir(parents=True, exist_ok=True)
        self.results.write_text(self.PARTIAL, encoding="utf-8")
        calls_per_run = []
        for _ in range(2):
            classifier = ScriptedClassifier()
            week4_run_batch(make_cases([3]), self.results, self.errors, classifier=classifier)
            calls_per_run.append(len(classifier.calls))
        self.assertEqual(calls_per_run, [1, 1])

    def test_interrupted_error_log_is_recovered_too(self):
        self.errors.parent.mkdir(parents=True, exist_ok=True)
        self.errors.write_text('{"case_id": 9, "status": "fai', encoding="utf-8")
        with self.assertLogs("week_05.jsonl_store", level="WARNING"):
            self.run_batch(make_cases([1]), ScriptedClassifier(default="bad"))
        lines = self.errors.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], '{"case_id": 9, "status": "fai')
        self.assertEqual(json.loads(lines[1])["case_id"], 1)

    def test_file_containing_only_a_partial_line(self):
        self.results.parent.mkdir(parents=True, exist_ok=True)
        self.results.write_text(self.PARTIAL, encoding="utf-8")
        with self.assertLogs("week_05.jsonl_store", level="WARNING"):
            counts = self.run_batch(make_cases([3]), ScriptedClassifier())
        self.assertEqual(counts["succeeded"], 1)
        self.assertEqual(json.loads(self.results.read_text(encoding="utf-8")
                                    .splitlines()[1])["case_id"], 3)


class TestMatrix1FixedCaseCount(BatchTestCase):
    def test_matrix1_rejects_any_explicit_limit(self):
        path = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        for limit in (10, 99, 100, 101):
            with self.subTest(limit=limit):
                classifier = ScriptedClassifier()
                with self.assertRaisesRegex(ValueError, "not configurable"):
                    run_workflow_batch(MATRIX1, path, output_dir=self.dir / "m1",
                                       limit=limit, classifier=classifier)
                self.assertEqual(classifier.calls, [])
                self.assertFalse((self.dir / "m1").exists())

    def test_matrix1_default_processes_exactly_100(self):
        path = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS, case_ids=range(1, 126))
        counts = run_workflow_batch(MATRIX1, path, output_dir=self.dir / "m1",
                                    classifier=ScriptedClassifier(), clock=StepClock())
        self.assertEqual(counts["total"], 100)

    def test_matrix2_limit_remains_configurable(self):
        path = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS, case_ids=range(1, 151))
        for limit, expected in ((10, 10), (150, 150)):
            with self.subTest(limit=limit):
                out = self.dir / f"m2_{limit}"
                counts = run_workflow_batch(MATRIX2, path, output_dir=out, limit=limit,
                                            classifier=ScriptedClassifier(), clock=StepClock())
                self.assertEqual(counts["total"], expected)
        with self.assertRaises(DatasetError):
            run_workflow_batch(MATRIX2, path, output_dir=self.dir / "m2_0", limit=0,
                               classifier=ScriptedClassifier())


class TestCli(BatchTestCase):
    def test_matrix1_limit_rejected_by_batch_and_validate_data(self):
        path = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        out_dir = self.dir / "cli_out"
        for command in ("batch", "validate-data"):
            with self.subTest(command=command):
                argv = [command, "--workflow", "matrix1", "--input", str(path), "--limit", "10"]
                if command == "batch":
                    argv += ["--output-dir", str(out_dir)]
                with patch.object(batch_runner, "_default_classifier") as factory:
                    code, out = self.run_cli(argv, {"OPENAI_API_KEY": FAKE_KEY})
                self.assertEqual(code, 4)
                self.assertIn("--limit is not available for matrix1", out)
                factory.assert_not_called()
                self.assertFalse(out_dir.exists())

    def test_matrix2_limit_accepted_by_batch_and_validate_data(self):
        path = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS)
        code, out = self.run_cli(["validate-data", "--workflow", "matrix2", "--input", str(path),
                                  "--limit", "25"], {})
        self.assertEqual(code, 0)
        self.assertIn("Cases loaded: 25", out)
        out_dir = self.dir / "cli_m2"
        with patch.object(batch_runner, "_default_classifier", return_value=ScriptedClassifier()):
            code, out = self.run_cli(["batch", "--workflow", "matrix2", "--input", str(path),
                                      "--output-dir", str(out_dir), "--limit", "25"],
                                     {"OPENAI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 0)
        self.assertEqual(len(read_jsonl(out_dir / "predictions.jsonl")), 25)

    def test_help_describes_limit_as_matrix2_only(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            cli.main(["batch", "--help"])
        self.assertIn("matrix2 only", " ".join(out.getvalue().split()))

    def run_cli(self, argv, env):
        out = io.StringIO()
        with patch.dict(os.environ, env, clear=True), patch("week_05.config.load_dotenv"), \
                contextlib.redirect_stdout(out):
            code = cli.main(argv)
        return code, out.getvalue()

    def test_validate_data_reports_counts_without_labels(self):
        path = make_workbook(self.dir / "m2.xlsx", MATRIX2_HEADERS)
        code, out = self.run_cli(["validate-data", "--workflow", "matrix2", "--input", str(path)],
                                 {})
        self.assertEqual(code, 0)
        self.assertIn("Cases loaded: 100", out)
        self.assertIn("Reference labels validated: 2000 (Gold Standard condition scores)", out)
        self.assertIn("No API request was made.", out)
        self.assertNotIn("Positive", out)

    def test_validate_data_input_error(self):
        code, out = self.run_cli(["validate-data", "--workflow", "matrix1", "--input",
                                  str(self.dir / "absent.xlsx")], {})
        self.assertEqual(code, 3)
        self.assertIn("Input error", out)

    def test_batch_with_fake_client(self):
        path = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        out_dir = self.dir / "cli_out"
        with patch.object(batch_runner, "_default_classifier", return_value=ScriptedClassifier()):
            code, out = self.run_cli(["batch", "--workflow", "matrix1", "--input", str(path),
                                      "--output-dir", str(out_dir)], {"OPENAI_API_KEY": FAKE_KEY})
        self.assertEqual(code, 0)
        self.assertIn("billable", out)
        self.assertIn("Succeeded: 100", out)
        self.assertNotIn(FAKE_KEY, out)
        self.assertEqual(len(read_jsonl(out_dir / "predictions.jsonl")), 100)

    def test_batch_without_key_fails_fast_and_writes_nothing(self):
        path = make_workbook(self.dir / "m1.xlsx", MATRIX1_HEADERS)
        out_dir = self.dir / "cli_out"
        with patch.object(batch_runner, "_default_classifier") as factory:
            code, out = self.run_cli(["batch", "--workflow", "matrix1", "--input", str(path),
                                      "--output-dir", str(out_dir)], {})
        self.assertEqual(code, 2)
        self.assertIn("OPENAI_API_KEY", out)
        factory.assert_not_called()
        self.assertFalse((out_dir / "predictions.jsonl").exists())
        self.assertFalse((out_dir / "errors.jsonl").exists())

    def test_batch_refuses_week4_output_dir(self):
        code, out = self.run_cli(["batch", "--workflow", "matrix1", "--output-dir",
                                  str(config.REPO_ROOT / "outputs" / "week_04" / "matrix_1")], {})
        self.assertEqual(code, 2)
        self.assertIn("Week 4", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
