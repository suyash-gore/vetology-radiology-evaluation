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
)


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
