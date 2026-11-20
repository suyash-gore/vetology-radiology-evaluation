"""Parity with Week 5 — the ONLY Week 7 test module that imports ``week_05``.

Phase 1 scope: the verbatim-copied foundation modules (conditions, prompt
loader) and the prompt file. "Verbatim" is checked on the code itself: the AST
of each Week 7 copy, with docstrings removed and ``week_05`` renamed to
``week_07``, must equal the Week 5 source. Later phases extend this module.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from week_07.config import REPO_ROOT
from week_07.tests.support import OfflineTestCase, code_without_docstrings

WEEK5 = REPO_ROOT / "src" / "week_05"
WEEK7 = REPO_ROOT / "src" / "week_07"

VERBATIM_COPIES = (
    "conditions.py",
    "prompts/prompt_loader.py",
    "response_validator.py",
    "jsonl_store.py",
    "dataset_loader.py",
    "evaluation/metrics.py",
    "evaluation/reconcile.py",
    "evaluation/reference_loader.py",
    "evaluation/workbook_compare.py",
)

# Synthetic responses covering every validator stage (valid and invalid).
_VALID = {key: "Negative" for key in (
    "perihilar_infiltrate", "pneumonia", "bronchitis", "interstitial", "diseased_lungs",
    "hypo_plastic_trachea", "cardiomegaly", "pulmonary_nodules", "pleural_effusion", "rtm",
    "focal_caudodorsal_lung", "focal_perihilar", "pulmonary_hypoinflation",
    "right_sided_cardiomegaly", "pericardial_effusion", "bronchiectasis",
    "pulmonary_vessel_enlargement", "left_sided_cardiomegaly", "thoracic_lymphadenopathy",
    "esophagitis")}


def _validator_corpus() -> list:
    import json

    valid = json.dumps(_VALID)
    reordered = json.dumps(dict(reversed(list(_VALID.items()))))
    missing = json.dumps({k: v for k, v in _VALID.items() if k != "rtm"})
    extra = json.dumps({**_VALID, "other": "Negative"})
    lower = json.dumps({**_VALID, "pneumonia": "positive"})
    padded = json.dumps({**_VALID, "pneumonia": " Positive"})
    non_str = json.dumps({**_VALID, "pneumonia": True})
    duplicate = valid[:-1] + ', "rtm": "Positive"}'
    return [valid, reordered, f"  {valid}\n", f"```json\n{valid}\n```", f"Here: {valid}",
            "﻿" + valid, valid + valid, missing, extra, lower, padded, non_str, duplicate,
            "", "   ", None, 5, "[]", '"text"', "{", "null", '{"a": {"a": 1, "a": 2}}']


class TestVerbatimCopies(OfflineTestCase):
    def test_code_identical_to_week5_apart_from_docstrings(self):
        for relative in VERBATIM_COPIES:
            with self.subTest(module=relative):
                self.assertEqual(code_without_docstrings(WEEK7 / relative),
                                 code_without_docstrings(WEEK5 / relative))

    def test_comparison_ignores_docstrings_but_detects_code_changes(self):
        original = WEEK7 / "conditions.py"
        source = original.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            docstring_only = Path(tmp) / "doc.py"
            docstring_only.write_text(source.replace("Single source of truth",
                                                     "Reworded note"), encoding="utf-8")
            code_change = Path(tmp) / "code.py"
            code_change.write_text(source.replace('"esophagitis",', '"esophagitis_x",'),
                                   encoding="utf-8")
            self.assertEqual(code_without_docstrings(docstring_only),
                             code_without_docstrings(original))
            self.assertNotEqual(code_without_docstrings(code_change),
                                code_without_docstrings(original))


class TestBehaviouralParity(OfflineTestCase):
    def test_conditions(self):
        from week_05 import conditions as w5
        from week_07 import conditions as w7

        self.assertEqual(w7.CONDITION_KEYS, w5.CONDITION_KEYS)
        self.assertEqual(w7.VALID_LABELS, w5.VALID_LABELS)
        self.assertEqual((w7.POSITIVE, w7.NEGATIVE), (w5.POSITIVE, w5.NEGATIVE))

    def test_prompt(self):
        from week_05.prompts import prompt_loader as w5
        from week_07.prompts import prompt_loader as w7

        self.assertEqual(w7.PROMPT_FILE_SHA256, w5.PROMPT_FILE_SHA256)
        self.assertEqual(w7.PROMPT_TEXT_SHA256, w5.PROMPT_TEXT_SHA256)
        self.assertEqual(w7.PROMPT_TEXT_LENGTH, w5.PROMPT_TEXT_LENGTH)
        self.assertEqual(w7.PROMPT_VERSION, w5.PROMPT_VERSION)
        self.assertEqual(w7.load_system_prompt(), w5.load_system_prompt())
        self.assertEqual(w7.PROMPT_PATH.read_bytes(), w5.PROMPT_PATH.read_bytes())

    def test_response_validator_outcomes_and_messages_identical(self):
        from week_05 import response_validator as w5
        from week_07 import response_validator as w7

        def outcome(module, raw):
            try:
                return ("ok", module.validate_model_response(raw))
            except module.ResponseValidationError as exc:
                return ("error", str(exc))

        corpus = _validator_corpus()
        self.assertGreater(len(corpus), 20)
        for raw in corpus:
            with self.subTest(raw=repr(raw)[:40]):
                self.assertEqual(outcome(w7, raw), outcome(w5, raw))
        self.assertEqual(outcome(w7, corpus[0])[0], "ok")

    def test_jsonl_records_identical(self):
        from week_05 import jsonl_store as w5
        from week_07 import jsonl_store as w7
        from week_07.tests.gemini_fakes import StepClock

        self.assertEqual(w7.success_record(3, 2, _VALID, StepClock()),
                         w5.success_record(3, 2, _VALID, StepClock()))
        self.assertEqual(w7.failure_record("4", 2, "X: y", StepClock()),
                         w5.failure_record("4", 2, "X: y", StepClock()))
        self.assertEqual(w7.failure_record(5, 2, None, StepClock()),
                         w5.failure_record(5, 2, None, StepClock()))
        self.assertEqual(w7.format_error(ValueError("v")), w5.format_error(ValueError("v")))
        self.assertEqual(w7.checkpoint_key(5.0), w5.checkpoint_key(5.0))

    def test_checkpoint_reading_identical(self):
        import json

        from week_05 import jsonl_store as w5
        from week_07 import jsonl_store as w7

        lines = [json.dumps({"case_id": 1, "status": "success", "predictions": _VALID}),
                 json.dumps({"case_id": 2, "status": "failed"}),
                 json.dumps({"case_id": 3, "status": "success",
                             "predictions": {**_VALID, "rtm": "maybe"}}),
                 '{"case_id": 4, "status": "succ',
                 "", json.dumps({"case_id": "5", "status": "success", "predictions": _VALID})]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.jsonl"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            import logging
            logging.getLogger("week_05").setLevel(logging.CRITICAL)
            logging.getLogger("week_07").setLevel(logging.CRITICAL)
            self.addCleanup(logging.getLogger("week_05").setLevel, logging.NOTSET)
            self.addCleanup(logging.getLogger("week_07").setLevel, logging.NOTSET)
            self.assertEqual(w7.load_successful_case_ids(path), w5.load_successful_case_ids(path))
            self.assertEqual(w7.load_successful_case_ids(path), {"1", "5"})

    def test_appended_bytes_identical(self):
        from week_05 import jsonl_store as w5
        from week_07 import jsonl_store as w7
        from week_07.tests.gemini_fakes import StepClock

        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.jsonl", Path(tmp) / "b.jsonl"
            for module, path in ((w5, a), (w7, b)):
                path.write_bytes(b'{"partial')  # interrupted write
                module.append_jsonl(path, module.success_record(1, 1, _VALID, StepClock()))
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_llm_messages_identical(self):
        from week_05 import llm_client as w5
        from week_07 import llm_client as w7

        payloads = [
            {"findings": "Synthetic A.", "conclusions": "Synthetic B.", "recommendations": "C"},
            {"findings": None, "conclusions": "", "recommendations": "  spaced  "},
            {"findings": "Line 1\nLine 2", "conclusions": "ü é", "recommendations": ""},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                m5, m7 = w5.build_messages(payload), w7.build_messages(payload)
                self.assertEqual([(m.type, m.content) for m in m7],
                                 [(m.type, m.content) for m in m5])
        self.assertEqual(w7.REPORT_FIELDS, w5.REPORT_FIELDS)
        self.assertEqual(w7.HUMAN_INSTRUCTION, w5.HUMAN_INSTRUCTION)
        self.assertEqual(w7.NOT_PROVIDED, w5.NOT_PROVIDED)
        for bad in ({"findings": "a"}, {**payloads[0], "case_id": 1}, ["x"]):
            with self.subTest(bad=bad):
                with self.assertRaises(w5.PayloadError):
                    w5.build_messages(bad)
                with self.assertRaises(w7.PayloadError):
                    w7.build_messages(bad)

    def test_week5_response_validator_and_store_unchanged_in_git(self):
        import subprocess

        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain", "--",
             "src/week_04", "src/week_05"],
            capture_output=True, text=True, check=False)
        if result.returncode != 0:
            self.skipTest("git is not available")
        self.assertEqual(result.stdout.strip(), "", "Week 4/5 sources must be unchanged")

    def test_workflow_rules_match_week5(self):
        from week_05 import config as w5
        from week_07 import config as w7

        fields = ("name", "title", "reference_description", "input_filename",
                  "evaluation_workbook_filename", "worksheet_name", "case_limit",
                  "require_exact_case_count", "max_case_limit", "configurable_limit",
                  "input_dir", "default_input_path")
        for name in ("matrix1", "matrix2"):
            for field in fields:
                with self.subTest(workflow=name, field=field):
                    self.assertEqual(getattr(w7.WORKFLOWS[name], field),
                                     getattr(w5.WORKFLOWS[name], field))
            # Week 7 reads Week 5's outputs only as comparison sources.
            self.assertEqual(w7.WORKFLOWS[name].week5_output_dir, w5.WORKFLOWS[name].output_dir)
            self.assertNotEqual(w7.WORKFLOWS[name].output_dir, w5.WORKFLOWS[name].output_dir)
        self.assertEqual(w7.DEFAULT_MAX_ATTEMPTS, w5.DEFAULT_MAX_ATTEMPTS)
        self.assertEqual(w7.PREDICTIONS_FILENAME, w5.PREDICTIONS_FILENAME)
        self.assertEqual(w7.ERRORS_FILENAME, w5.ERRORS_FILENAME)


# ---------------------------------------------------------------------------
# Phase 3: dataset loading, reference loading, metrics and workbooks
# ---------------------------------------------------------------------------

class SyntheticParityCase(OfflineTestCase):
    """Runs Week 5 and Week 7 code on the SAME synthetic files (temporary directory)."""

    def setUp(self):
        super().setUp()
        import logging

        from week_07.tests.fixtures import SyntheticRepo

        for name in ("week_05", "week_07"):
            logging.getLogger(name).setLevel(logging.CRITICAL)
            self.addCleanup(logging.getLogger(name).setLevel, logging.NOTSET)
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write_inputs()

    def week7_predictions(self, name, variant):
        from week_07.batch_runner import run_workflow_batch
        from week_07.config import GeminiModelConfig
        from week_07.tests.fixtures import EchoClassifier
        from week_07.tests.gemini_fakes import RecordingSleep, StepClock

        flips = {1: ("pneumonia",), 9: ("rtm", "cardiomegaly"), 50: ("esophagitis",)}
        run_workflow_batch(self.repo.spec(name), classifier=EchoClassifier(variant, flips),
                           settings=GeminiModelConfig(), isolation=self.repo.policy,
                           clock=StepClock(), sleep=RecordingSleep())
        return self.repo.spec(name).predictions_path


class TestDatasetAndReferenceParity(SyntheticParityCase):
    def test_batch_loader_identical(self):
        from week_05 import config as c5
        from week_05.dataset_loader import load_dataset as load5
        from week_07.dataset_loader import load_dataset as load7

        for name in ("matrix1", "matrix2"):
            spec7 = self.repo.spec(name)
            with self.subTest(workflow=name):
                d5 = load5(c5.WORKFLOWS[name], spec7.default_input_path)
                d7 = load7(spec7)
                self.assertEqual(
                    [(c.case_id, c.to_llm_payload()) for c in d7.cases],
                    [(c.case_id, c.to_llm_payload()) for c in d5.cases])
                self.assertEqual({k: dict(v) for k, v in d7.reference_labels.items()},
                                 {k: dict(v) for k, v in d5.reference_labels.items()})
                self.assertEqual((d7.workflow, d7.reference_description, d7.worksheet_name),
                                 (d5.workflow, d5.reference_description, d5.worksheet_name))

    def test_evaluation_reference_loaders_identical(self):
        from week_05 import config as c5
        from week_05.evaluation import reference_loader as r5
        from week_07.evaluation import reference_loader as r7

        for name in ("matrix1", "matrix2"):
            path = self.repo.spec(name).default_input_path
            with self.subTest(workflow=name):
                ref5 = r5.reference_loader_for(c5.WORKFLOWS[name])(path)
                ref7 = r7.reference_loader_for(self.repo.spec(name))(path)
                self.assertEqual(ref7.case_ids, ref5.case_ids)
                self.assertEqual({k: dict(v) for k, v in ref7.labels.items()},
                                 {k: dict(v) for k, v in ref5.labels.items()})
                self.assertEqual(r7.compare_reference_loaders(self.repo.spec(name), path),
                                 r5.compare_reference_loaders(c5.WORKFLOWS[name], path))


class TestEvaluationParity(SyntheticParityCase):
    def _both(self, name, variant):
        from week_05 import config as c5
        from week_05.evaluation.evaluate import evaluate_workflow as eval5
        from week_07.evaluation.evaluate import evaluate_workflow as eval7

        predictions = self.week7_predictions(name, variant)
        spec7 = self.repo.spec(name)
        result5 = eval5(c5.WORKFLOWS[name], spec7.default_input_path, predictions)
        result7 = eval7(spec7, isolation=self.repo.policy)
        return result5, result7

    def test_metrics_identical(self):
        for name, variant in (("matrix1", 0), ("matrix2", 1)):
            with self.subTest(workflow=name):
                r5, r7 = self._both(name, variant)
                self.assertEqual({c: m.as_dict() for c, m in r7.per_condition.items()},
                                 {c: m.as_dict() for c, m in r5.per_condition.items()})
                self.assertEqual(r7.micro.as_dict(), r5.micro.as_dict())
                self.assertEqual(r7.macro.__dict__, r5.macro.__dict__)
                self.assertEqual(r7.labels.case_ids, r5.labels.case_ids)

    def _workbooks(self, name, variant):
        from week_05 import config as c5
        from week_05.evaluation.evaluate import write_evaluation_workbook as write5
        from week_07.evaluation.evaluate import write_evaluation_workbook as write7
        from week_07.tests.gemini_fakes import StepClock

        r5, r7 = self._both(name, variant)
        book5 = write5(c5.WORKFLOWS[name], r5, self.repo.root / f"week5_{name}.xlsx",
                       clock=StepClock())
        book7 = write7(self.repo.spec(name), r7, isolation=self.repo.policy, clock=StepClock())
        return book5, book7, r7

    def test_matrix1_workbook_differs_only_in_the_model_record(self):
        from week_07.evaluation.workbook_compare import compare_workbooks

        book5, book7, r7 = self._workbooks("matrix1", 0)
        self.assertEqual(compare_workbooks(book5, book7), [
            "[Execution Log!B12] value 'gpt-4.1-mini (from Matrix 1 batch execution record)' "
            f"!= {r7.model_record!r}",
        ])

    def test_matrix2_workbook_differs_only_in_title_and_model_note(self):
        from week_07.evaluation.workbook_compare import compare_workbooks

        book5, book7, r7 = self._workbooks("matrix2", 1)
        self.assertEqual(compare_workbooks(book5, book7), [
            "[Overall Summary!A1] value 'VETOLOGY WEEK 4 - OVERALL EVALUATION SUMMARY' != "
            "'VETOLOGY WEEK 7 - OVERALL EVALUATION SUMMARY'",
            f"[Execution Log!C3] value None != {'Model: ' + r7.model_record!r}",
        ])
