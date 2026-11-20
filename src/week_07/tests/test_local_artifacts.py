"""LOCAL-ONLY verification on the real (confidential, gitignored) artifacts.

Runs ONLY when all three gates pass; otherwise every test is skipped:

1. explicit opt-in: environment variable ``WEEK07_RUN_LOCAL_ARTIFACTS=1``;
2. not a Claude cloud session: ``CLAUDE_CODE_REMOTE`` is not set;
3. the real files are present (inputs in ``data/week_04_inputs``; Week 5
   predictions in ``outputs/week_05``).

Run locally (PowerShell, repository root, project venv active)::

    $env:PYTHONPATH = "src"; $env:WEEK07_RUN_LOCAL_ARTIFACTS = "1"
    python -m unittest week_07.tests.test_local_artifacts -v

Guarantees: no API request (network blocked by ``OfflineTestCase``; no model
client is used), nothing is written (workbooks are built in memory only), and
every real file is SHA-256-checked before and after. Digests are printed so they
can be recorded in the project documentation.
"""
from __future__ import annotations

import os
import unittest

from week_07 import config
from week_07.comparison.sources import read_error_log
from week_07.evaluation.evaluate import evaluate_workflow
from week_07.evaluation.reconcile import load_prediction_records
from week_07.evaluation.reference_loader import compare_reference_loaders
from week_07.isolation import ReadOnlyGuard, sha256_file
from week_07.tests.support import OfflineTestCase

OPT_IN = os.environ.get("WEEK07_RUN_LOCAL_ARTIFACTS") == "1"
IN_CLAUDE_CLOUD = bool(os.environ.get("CLAUDE_CODE_REMOTE"))
M1, M2 = config.MATRIX1, config.MATRIX2
REQUIRED = (M1.default_input_path, M2.default_input_path,
            M1.week5_predictions_path, M2.week5_predictions_path)
FILES_PRESENT = all(path.is_file() for path in REQUIRED)
ENABLED = OPT_IN and not IN_CLAUDE_CLOUD and FILES_PRESENT
REASON = ("local-only real-artifact tests: set WEEK07_RUN_LOCAL_ARTIFACTS=1 on the local "
          "machine with the real files present (never run in Claude's cloud environment)")

# Week 5 live results (2026-11-12, docs/testing_log.md): TP, FN, TN, FP.
WEEK5_LIVE_COUNTS = {"matrix1": (126, 923, 916, 35), "matrix2": (126, 32, 1806, 36)}
WEEK5_REPLAY_RECORD = ("gpt-4.1-mini (Week 5 configuration; model identity inferred from "
                       "configuration, not embedded in prediction file)")


def _existing(*paths):
    return [p for p in paths if p.is_file()]


@unittest.skipUnless(ENABLED, REASON)
class TestWeek5Replay(OfflineTestCase):
    """The Week 7 evaluation stack reproduces the recorded Week 5 OpenAI results."""

    def test_replay_reproduces_week5_live_counts(self):
        for spec in (M1, M2):
            files = [spec.default_input_path, spec.week5_predictions_path]
            with self.subTest(workflow=spec.name), ReadOnlyGuard(files) as guard:
                result = evaluate_workflow(spec, predictions_path=spec.week5_predictions_path,
                                           model_record=WEEK5_REPLAY_RECORD)
                m = result.micro
                self.assertEqual((m.tp, m.fn, m.tn, m.fp), WEEK5_LIVE_COUNTS[spec.name])
                self.assertEqual(m.total, 2000)
                for path, digest in guard.digests.items():
                    print(f"[{spec.name}] {path.name} sha256 {digest}")

    def test_reference_loaders_agree_on_real_inputs(self):
        for spec in (M1, M2):
            with self.subTest(workflow=spec.name), ReadOnlyGuard([spec.default_input_path]):
                self.assertEqual(compare_reference_loaders(spec, spec.default_input_path), [])


@unittest.skipUnless(ENABLED, REASON)
class TestWeek5ErrorLogs(OfflineTestCase):
    """B1: historical Week 5 failure records are superseded, not final failures."""

    def test_matrix1_errors_are_all_superseded(self):
        if not M1.week5_errors_path.is_file():
            self.skipTest("Week 5 Matrix 1 errors.jsonl is not present")
        files = [M1.week5_predictions_path, M1.week5_errors_path]
        with ReadOnlyGuard(files):
            success = set(load_prediction_records(M1.week5_predictions_path).labels)
            summary = read_error_log(M1.week5_errors_path, success, "supplied")
        self.assertEqual(len(success), 100)
        self.assertEqual(summary.records, 100)
        self.assertEqual(summary.superseded_records, 100)
        self.assertEqual(summary.unresolved_records, 0)
        print(f"[matrix1] Week 5 errors.jsonl: {summary.describe()}")

    def test_matrix2_has_no_unresolved_failures(self):
        if not M2.week5_errors_path.is_file():
            self.skipTest("Week 5 Matrix 2 errors.jsonl is not present")
        with ReadOnlyGuard([M2.week5_predictions_path, M2.week5_errors_path]):
            success = set(load_prediction_records(M2.week5_predictions_path).labels)
            summary = read_error_log(M2.week5_errors_path, success, "supplied")
        self.assertEqual(len(success), 100)
        self.assertEqual(summary.unresolved_records, 0)
        print(f"[matrix2] Week 5 errors.jsonl: {summary.describe()}")


@unittest.skipUnless(ENABLED, REASON)
class TestGeminiComparisonWhenAvailable(OfflineTestCase):
    """Runs only after the real Week 7 Gemini batches exist; builds workbooks in memory."""

    def test_comparison_per_workflow(self):
        from week_07.comparison.compare import compare_workflow
        from week_07.comparison.comparison_workbook import SHEETS, build_comparison_workbook

        ran = False
        for spec in (M1, M2):
            if not (spec.predictions_path.is_file() and spec.manifest_path.is_file()):
                continue
            ran = True
            with self.subTest(workflow=spec.name):
                before = {p: sha256_file(p) for p in _existing(
                    spec.week5_predictions_path, spec.week5_errors_path)}
                result = compare_workflow(spec)
                book = build_comparison_workbook(result)  # in memory; nothing is written
                self.assertEqual(tuple(book.sheetnames), SHEETS)
                self.assertEqual(len(result.case_ids), 100)
                self.assertEqual(result.openai.errors.unresolved_records, 0)
                self.assertEqual(before, {p: sha256_file(p) for p in before})
                print(f"[{spec.name}] agreement {result.agreement_total.agreements}/"
                      f"{result.agreement_total.total}; disagreements "
                      f"{len(result.disagreements)}")
        if not ran:
            self.skipTest("no Week 7 Gemini predictions with a run manifest yet")


class TestGatesInThisEnvironment(unittest.TestCase):
    """Always runs: documents why the local-only tests are (not) enabled here."""

    def test_gates_are_consistent(self):
        self.assertEqual(ENABLED, OPT_IN and not IN_CLAUDE_CLOUD and FILES_PRESENT)
        if IN_CLAUDE_CLOUD:
            self.assertFalse(ENABLED, "local-only tests must never run in Claude's cloud")
