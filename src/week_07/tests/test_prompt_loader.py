"""Canine Thorax Master Prompt V1.3 integrity checks."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from week_07.config import REPO_ROOT
from week_07.prompts import prompt_loader
from week_07.prompts.prompt_loader import (
    PROMPT_FILE_SHA256,
    PROMPT_PATH,
    PROMPT_TEXT_LENGTH,
    PROMPT_TEXT_SHA256,
    PROMPT_VERSION,
    PromptIntegrityError,
    load_system_prompt,
    read_prompt_text,
    verify_prompt_file,
)
from week_07.tests.support import OfflineTestCase

WEEK4_PROMPT = REPO_ROOT / "src" / "week_04" / "prompts" / "canine_thorax_master_prompt_v1_3.txt"
WEEK5_PROMPT = REPO_ROOT / "src" / "week_05" / "prompts" / "canine_thorax_master_prompt_v1_3.txt"


class TestPinnedPrompt(OfflineTestCase):
    def test_file_location_and_version(self):
        self.assertEqual(PROMPT_PATH.parent, REPO_ROOT / "src" / "week_07" / "prompts")
        self.assertEqual(PROMPT_VERSION, "V1.3")

    def test_file_digest_and_size(self):
        data = PROMPT_PATH.read_bytes()
        self.assertEqual(len(data), 8715)
        self.assertEqual(hashlib.sha256(data).hexdigest(), PROMPT_FILE_SHA256)
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"), "prompt must not have a BOM")
        self.assertNotIn(b"\r\n", data, "prompt must use LF line endings")

    def test_loaded_text_digest_and_length(self):
        text = verify_prompt_file()
        self.assertEqual(len(text), PROMPT_TEXT_LENGTH)
        self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), PROMPT_TEXT_SHA256)
        self.assertEqual(text, text.strip())

    def test_byte_identical_to_week4_and_week5_copies(self):
        week7 = PROMPT_PATH.read_bytes()
        self.assertEqual(week7, WEEK4_PROMPT.read_bytes())
        self.assertEqual(week7, WEEK5_PROMPT.read_bytes())

    def test_load_system_prompt_is_cached_and_verified(self):
        first = load_system_prompt()
        self.assertIs(first, load_system_prompt())
        self.assertEqual(first, read_prompt_text())

    def test_prompt_states_the_json_contract(self):
        text = load_system_prompt()
        self.assertIn("Positive", text)
        self.assertIn("Negative", text)


class TestTamperDetection(OfflineTestCase):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.copy = self.tmp / PROMPT_PATH.name
        shutil.copyfile(PROMPT_PATH, self.copy)

    def test_unmodified_copy_verifies(self):
        self.assertEqual(verify_prompt_file(self.copy), load_system_prompt())

    def test_whitespace_change_is_rejected(self):
        self.copy.write_bytes(self.copy.read_bytes() + b"\n")
        with self.assertRaises(PromptIntegrityError):
            verify_prompt_file(self.copy)

    def test_single_character_change_is_rejected(self):
        data = bytearray(self.copy.read_bytes())
        index = data.index(b"Positive")
        data[index] = ord("p")
        self.copy.write_bytes(bytes(data))
        with self.assertRaises(PromptIntegrityError):
            verify_prompt_file(self.copy)

    def test_crlf_conversion_is_rejected(self):
        self.copy.write_bytes(self.copy.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaises(PromptIntegrityError):
            verify_prompt_file(self.copy)

    def test_missing_file_is_rejected(self):
        with self.assertRaises(PromptIntegrityError):
            verify_prompt_file(self.tmp / "missing.txt")
        with self.assertRaises(PromptIntegrityError):
            read_prompt_text(self.tmp / "missing.txt")

    def test_text_digest_is_checked_independently(self):
        # Same file digest pinned to the copy, but a different pinned text digest must fail.
        original = prompt_loader.PROMPT_TEXT_SHA256
        prompt_loader.PROMPT_TEXT_SHA256 = "0" * 64
        self.addCleanup(setattr, prompt_loader, "PROMPT_TEXT_SHA256", original)
        with self.assertRaises(PromptIntegrityError):
            verify_prompt_file(self.copy)
