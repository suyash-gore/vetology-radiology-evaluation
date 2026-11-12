"""Offline tests for the prediction/error JSONL contract and checkpoint reading."""
from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from week_05.conditions import CONDITION_KEYS
from week_05.jsonl_store import (
    append_jsonl,
    checkpoint_key,
    failure_record,
    format_error,
    load_successful_case_ids,
    success_record,
    timestamp,
)
from week_05.tests.support import FIXED_START, StepClock, quiet

PREDICTIONS = {key: "Negative" for key in CONDITION_KEYS}
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{6})?\+00:00$")
LOGGER = "week_05.jsonl_store"


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        quiet(self, LOGGER)


class TestRecordStructure(StoreTestCase):
    def test_success_record_fields_and_order(self):
        record = success_record(7, 2, PREDICTIONS, StepClock())
        self.assertEqual(list(record),
                         ["case_id", "status", "attempts", "completed_at_utc", "predictions"])
        self.assertEqual(record["case_id"], 7)
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["attempts"], 2)
        self.assertEqual(record["completed_at_utc"], "2026-11-10T09:30:00.123456+00:00")
        self.assertEqual(record["predictions"], PREDICTIONS)
        self.assertEqual(tuple(record["predictions"]), CONDITION_KEYS)

    def test_failure_record_fields_and_order(self):
        record = failure_record(7, 2, "ResponseValidationError: bad", StepClock())
        self.assertEqual(list(record),
                         ["case_id", "status", "attempts", "failed_at_utc", "error"])
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["error"], "ResponseValidationError: bad")

    def test_failure_without_error_text_uses_week4_default(self):
        self.assertEqual(failure_record(1, 2, None)["error"], "Unknown error")
        self.assertEqual(failure_record(1, 2, "")["error"], "Unknown error")

    def test_no_provenance_or_label_fields(self):
        forbidden = {"model", "prompt_version", "prompt_sha256", "raw_response", "workflow",
                     "reference_labels", "ground_truth", "gold_labels", "temperature"}
        self.assertFalse(forbidden & set(success_record(1, 1, PREDICTIONS)))
        self.assertFalse(forbidden & set(failure_record(1, 1, "x")))

    def test_real_clock_timestamp_is_iso_utc(self):
        value = timestamp()
        self.assertRegex(value, ISO_UTC)
        self.assertEqual(datetime.fromisoformat(value).utcoffset(), timezone.utc.utcoffset(None))
        self.assertRegex(success_record(1, 1, PREDICTIONS)["completed_at_utc"], ISO_UTC)
        self.assertRegex(failure_record(1, 1, "x")["failed_at_utc"], ISO_UTC)

    def test_error_formatting(self):
        self.assertEqual(format_error(ValueError("boom")), "ValueError: boom")
        self.assertEqual(format_error(TimeoutError()), "TimeoutError: ")

    def test_checkpoint_key_is_string_form(self):
        self.assertEqual(checkpoint_key(5), "5")
        self.assertEqual(checkpoint_key("5"), "5")
        self.assertEqual(checkpoint_key("A-3"), "A-3")


class TestAppend(StoreTestCase):
    def test_one_line_per_record_appended_utf8_unescaped(self):
        path = self.dir / "nested" / "predictions.jsonl"
        append_jsonl(path, {"case_id": 1, "note": "café — ok"})
        append_jsonl(path, {"case_id": 2})
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text, '{"case_id": 1, "note": "café — ok"}\n{"case_id": 2}\n')

    def test_recovery_inserts_newline_only_after_a_partial_line(self):
        record = {"case_id": 2}
        line = json.dumps(record) + os.linesep
        cases = {
            "missing file": (None, line),
            "empty file": ("", line),
            "ends with newline": ('{"case_id": 1}\n', '{"case_id": 1}\n' + line),
            "ends with CRLF": ('{"case_id": 1}\r\n', '{"case_id": 1}\r\n' + line),
            "partial line": ('{"case_id": 1}\n{"case_id": 9, "sta',
                             '{"case_id": 1}\n{"case_id": 9, "sta' + os.linesep + line),
            "partial only": ('{"cas', '{"cas' + os.linesep + line),
        }
        for name, (existing, expected) in cases.items():
            with self.subTest(case=name):
                path = self.dir / f"{name.replace(' ', '_')}.jsonl"
                if existing is not None:
                    path.write_bytes(existing.encode("utf-8"))
                append_jsonl(path, record)
                self.assertEqual(path.read_bytes().decode("utf-8"), expected)

    def test_recovery_is_logged_only_when_needed(self):
        path = self.dir / "p.jsonl"
        path.write_text('{"cas', encoding="utf-8")
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            append_jsonl(path, {"case_id": 1})
        self.assertEqual(len(logs.output), 1)
        with self.assertNoLogs(LOGGER, level="WARNING"):
            append_jsonl(path, {"case_id": 2})

    def test_line_bytes_match_week4_serialisation(self):
        record = success_record(3, 1, PREDICTIONS, StepClock())
        path = self.dir / "p.jsonl"
        append_jsonl(path, record)
        self.assertEqual(path.read_bytes(),
                         (json.dumps(record, ensure_ascii=False) + os.linesep).encode("utf-8"))


class TestLoadSuccessfulCaseIds(StoreTestCase):
    def write(self, *lines: str) -> Path:
        path = self.dir / "predictions.jsonl"
        path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        return path

    def ok(self, case_id) -> str:
        return json.dumps(success_record(case_id, 1, PREDICTIONS, StepClock()))

    def test_missing_file_means_nothing_completed(self):
        self.assertEqual(load_successful_case_ids(self.dir / "absent.jsonl"), set())

    def test_valid_lines_and_blank_lines(self):
        path = self.write(self.ok(1), "", "   ", self.ok("2"), self.ok("A-3"))
        self.assertEqual(load_successful_case_ids(path), {"1", "2", "A-3"})

    def test_invalid_lines_are_ignored_with_warning(self):
        bad_predictions = dict(PREDICTIONS, rtm="positive")
        missing_key = {k: v for k, v in PREDICTIONS.items() if k != "rtm"}
        lines = [
            self.ok(1),
            "not json",
            '{"case_id": 2, "status": "succ',                       # truncated write
            "[1, 2]",                                                 # not an object
            json.dumps({"case_id": 4, "status": "success", "predictions": bad_predictions}),
            json.dumps({"case_id": 5, "status": "success", "predictions": missing_key}),
            json.dumps({"case_id": 6, "status": "success"}),          # no predictions
        ]
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            completed = load_successful_case_ids(self.write(*lines))
        self.assertEqual(completed, {"1"})
        self.assertEqual(len(logs.output), 6)
        self.assertTrue(all("Ignoring invalid checkpoint line" in m for m in logs.output))

    def test_non_success_or_null_case_id_silently_not_completed(self):
        lines = [
            json.dumps(failure_record(1, 2, "x")),
            json.dumps({"case_id": None, "status": "success", "predictions": PREDICTIONS}),
            json.dumps({"status": "success", "predictions": PREDICTIONS}),
            json.dumps({"case_id": 9, "status": "Success", "predictions": PREDICTIONS}),
        ]
        self.assertEqual(load_successful_case_ids(self.write(*lines)), set())

    def test_predictions_in_any_key_order_still_count(self):
        reordered = {k: "Negative" for k in reversed(CONDITION_KEYS)}
        line = json.dumps({"case_id": 8, "status": "success", "predictions": reordered})
        self.assertEqual(load_successful_case_ids(self.write(line)), {"8"})

    def test_duplicate_success_lines_are_harmless(self):
        self.assertEqual(load_successful_case_ids(self.write(self.ok(1), self.ok(1))), {"1"})

    def test_matches_week4_reader_on_the_same_file(self):
        import logging

        from week_04.batch_processor import _load_successful_case_ids as week4_reader

        logging.getLogger("vetology_week4.batch").disabled = True
        self.addCleanup(setattr, logging.getLogger("vetology_week4.batch"), "disabled", False)
        lines = [self.ok(1), "garbage", self.ok("2"), json.dumps(failure_record(3, 2, "x")),
                 json.dumps({"case_id": 4, "status": "success",
                             "predictions": dict(PREDICTIONS, rtm="maybe")}), "", self.ok(5.5)]
        path = self.write(*lines)
        self.assertEqual(load_successful_case_ids(path), week4_reader(path))

    def test_fixed_start_constant(self):
        self.assertEqual(FIXED_START.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
