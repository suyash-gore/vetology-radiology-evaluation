"""Offline integrity tests for the V1.3 prompt. No API requests are made."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from week_05.config import REPO_ROOT
from week_05.prompts import prompt_loader
from week_05.prompts.prompt_loader import (
    PROMPT_PATH,
    PROMPT_VERSION,
    PromptIntegrityError,
    load_system_prompt,
    read_prompt_text,
    verify_prompt_file,
)

WEEK4_PROMPT = REPO_ROOT / "src" / "week_04" / "prompts" / "canine_thorax_master_prompt_v1_3.txt"
WEEK4_JSON = (REPO_ROOT / "src" / "week_04" / "optional_json_config" / "config"
              / "canine_thorax_v1_3.json")


class TestPromptIntegrity(unittest.TestCase):
    def test_file_is_byte_identical_to_week4(self):
        self.assertEqual(PROMPT_PATH.read_bytes(), WEEK4_PROMPT.read_bytes())

    def test_loaded_text_equals_week4_loader_output(self):
        from week_04.prompts.canine_thorax_prompt import load_system_prompt as week4_load

        week4_text = week4_load()
        week5_text = load_system_prompt()
        self.assertEqual(week5_text, week4_text)
        self.assertEqual(week5_text.encode("utf-8"), week4_text.encode("utf-8"))

    def test_loaded_text_equals_week4_json_configuration(self):
        config = json.loads(WEEK4_JSON.read_text(encoding="utf-8"))
        self.assertEqual(load_system_prompt(), config["system_prompt"])
        self.assertEqual(config["version"], PROMPT_VERSION)

    def test_pinned_digests_and_length(self):
        raw = PROMPT_PATH.read_bytes()
        text = load_system_prompt()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), prompt_loader.PROMPT_FILE_SHA256)
        self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(),
                         prompt_loader.PROMPT_TEXT_SHA256)
        self.assertEqual(len(text), 8710)  # length recorded in the Week 4 testing log
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r\n", raw)

    def test_stripping_matches_week4_behaviour(self):
        raw_text = PROMPT_PATH.read_text(encoding="utf-8")
        self.assertEqual(load_system_prompt(), raw_text.strip())
        self.assertTrue(raw_text.endswith("\n"))
        self.assertFalse(load_system_prompt().endswith("\n"))

    def test_key_v13_content_present(self):
        text = load_system_prompt()
        for fragment in (
            "Operational version: V1.3",
            "RTM means redundant tracheal membrane.",
            "Possible/suspected:",
            "Recommendation-only:",
            "Return only the final JSON object.",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_prompt_lists_all_condition_keys_in_canonical_order(self):
        from week_05.conditions import CONDITION_KEYS

        text = load_system_prompt()
        start = text.index("Required JSON structure:")
        positions = [text.index(f'"{key}": "Negative"', start) for key in CONDITION_KEYS]
        self.assertEqual(positions, sorted(positions))

    def test_loader_is_cached(self):
        self.assertIs(load_system_prompt(), load_system_prompt())


class TestPromptTamperDetection(unittest.TestCase):
    def _copy_with(self, mutate) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / PROMPT_PATH.name
        path.write_bytes(mutate(PROMPT_PATH.read_bytes()))
        return path

    def test_unmodified_copy_verifies(self):
        path = self._copy_with(lambda data: data)
        self.assertEqual(verify_prompt_file(path), load_system_prompt())

    def test_any_change_is_rejected(self):
        mutations = {
            "word change": lambda d: d.replace(b"Positive", b"Positiv", 1),
            "extra trailing space": lambda d: d + b" ",
            "CRLF line endings": lambda d: d.replace(b"\n", b"\r\n"),
            "BOM": lambda d: b"\xef\xbb\xbf" + d,
            "truncated": lambda d: d[:-200],
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                with self.assertRaises(PromptIntegrityError):
                    verify_prompt_file(self._copy_with(mutate))

    def test_missing_file_rejected(self):
        with self.assertRaisesRegex(PromptIntegrityError, "not found"):
            verify_prompt_file(Path("/nonexistent/prompt.txt"))
        with self.assertRaisesRegex(PromptIntegrityError, "not found"):
            read_prompt_text(Path("/nonexistent/prompt.txt"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
