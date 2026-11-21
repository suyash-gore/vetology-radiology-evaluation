"""Stage 2: application-aware prompt registry, pinned digests and pending prompts."""
from __future__ import annotations

import hashlib
import tempfile
from dataclasses import replace
from pathlib import Path

from week_07.applications import APPLICATIONS, CANINE_ABDOMEN, CANINE_THORAX, FELINE_THORAX
from week_07.prompts import prompt_loader, registry
from week_07.prompts.prompt_loader import PromptIntegrityError
from week_07.prompts.registry import (
    CANINE_ABDOMEN_PROMPT,
    CANINE_THORAX_PROMPT,
    FELINE_THORAX_PROMPT,
    PromptSpec,
    load_prompt,
    prompt_identity,
    verify_prompt,
)
from week_07.tests.support import OfflineTestCase


def _pinned(directory: Path, filename: str, content: bytes, **overrides) -> PromptSpec:
    path = directory / filename
    path.write_bytes(content)
    text = path.read_text(encoding="utf-8").strip()
    values = dict(name="Test Prompt", version="V9.9", filename=filename,
                  file_sha256=hashlib.sha256(content).hexdigest(),
                  text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                  text_length=len(text), directory=directory)
    values.update(overrides)
    return PromptSpec(**values)


class TempDirCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        handle = tempfile.TemporaryDirectory()
        self.addCleanup(handle.cleanup)
        self.dir = Path(handle.name)


class TestCanineThoraxPromptUnchanged(OfflineTestCase):
    def test_registry_entry_uses_the_pinned_v13_constants(self):
        spec = CANINE_THORAX_PROMPT
        self.assertEqual(spec.path, prompt_loader.PROMPT_PATH)
        self.assertEqual(spec.version, "V1.3")
        self.assertEqual(spec.file_sha256,
                         "31a7dab6e535e6f0af6a54106cf449ecadfe3644c7b3c805710309f0e85ab7b1")
        self.assertEqual(spec.text_sha256,
                         "97ad5b74be0ebaa8655227e50e6fcc9cee1a96e7ba072c45ee6f822673d44d29")
        self.assertEqual(spec.text_length, 8710)
        self.assertFalse(spec.is_pending)
        self.assertIs(CANINE_THORAX.prompt, spec)

    def test_load_delegates_to_original_loader(self):
        self.assertIs(load_prompt(CANINE_THORAX_PROMPT), prompt_loader.load_system_prompt())
        self.assertEqual(verify_prompt(CANINE_THORAX_PROMPT),
                         prompt_loader.verify_prompt_file())

    def test_identity_matches_the_existing_manifest_block(self):
        self.assertEqual(prompt_identity(CANINE_THORAX_PROMPT), {
            "name": "Canine Thorax Master Prompt",
            "version": "V1.3",
            "file_sha256": prompt_loader.PROMPT_FILE_SHA256,
            "text_sha256": prompt_loader.PROMPT_TEXT_SHA256,
        })

    def test_identity_equals_run_manifest_prompt_block(self):
        from week_07 import run_manifest

        expected = {"name": run_manifest.PROMPT_NAME, "version": run_manifest.PROMPT_VERSION,
                    "file_sha256": run_manifest.PROMPT_FILE_SHA256,
                    "text_sha256": run_manifest.PROMPT_TEXT_SHA256}
        self.assertEqual(prompt_identity(CANINE_THORAX_PROMPT), expected)


APPROVED = {
    "feline_thorax": ("Feline Thorax Master Prompt", "V1.1",
                      "feline_thorax_master_prompt_v1_1.txt", 26060,
                      "7696598eda2faa39ef44df3e9c260ca7870d487094df40ae6e05c4b0c2665d27",
                      "bf9142f7b753e3bfdf67d64869332672082796859e02aaafac0c11e202eeb103", 25833),
    "canine_abdomen": ("Canine Abdomen Master Prompt", "V1.2",
                       "canine_abdomen_master_prompt_v1_2.txt", 17216,
                       "f25b56fb0fbd2a7e697be287ef51357a8e911243523464d860eff7726a5e17aa",
                       "1156c72a6ceaed5f466a77e5490add36ec25214bd3ccb1b785a0bef205402305", 17081),
}


class TestApprovedPrompts(OfflineTestCase):
    def test_registered_identity_and_pins(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            name, version, filename, size, file_sha, text_sha, length = APPROVED[app.key]
            spec = app.prompt
            with self.subTest(app=app.key):
                self.assertEqual((spec.name, spec.version, spec.filename),
                                 (name, version, filename))
                self.assertEqual((spec.file_sha256, spec.text_sha256, spec.text_length),
                                 (file_sha, text_sha, length))
                self.assertFalse(spec.is_pending)
                self.assertEqual(spec.directory, prompt_loader.PROMPT_PATH.parent)
                self.assertEqual(spec.path.stat().st_size, size)
        self.assertIs(FELINE_THORAX.prompt, FELINE_THORAX_PROMPT)
        self.assertIs(CANINE_ABDOMEN.prompt, CANINE_ABDOMEN_PROMPT)

    def test_files_are_stored_exactly(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            data = app.prompt.path.read_bytes()
            with self.subTest(app=app.key):
                self.assertEqual(hashlib.sha256(data).hexdigest(), APPROVED[app.key][4])
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"))   # no BOM
                self.assertNotIn(b"\r", data)                       # LF line endings
                data.decode("utf-8")                                # valid UTF-8

    def test_prompts_load_and_identify(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            with self.subTest(app=app.key):
                text = load_prompt(app.prompt)
                self.assertEqual(text, verify_prompt(app.prompt))
                self.assertEqual(len(text), APPROVED[app.key][6])
                self.assertEqual(text, app.prompt.path.read_text(encoding="utf-8").strip())
                self.assertEqual(prompt_identity(app.prompt), {
                    "name": APPROVED[app.key][0], "version": APPROVED[app.key][1],
                    "file_sha256": APPROVED[app.key][4],
                    "text_sha256": APPROVED[app.key][5]})
        self.assertIn("FELINE THORAX MASTER PROMPT", load_prompt(FELINE_THORAX_PROMPT))
        self.assertTrue(load_prompt(CANINE_ABDOMEN_PROMPT).startswith(
            "Canine Abdomen Master Prompt V1.2"))

    def test_output_contract_lists_exactly_the_application_keys_in_order(self):
        import re

        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            text = load_prompt(app.prompt)
            contract = text[text.rindex("{"):text.rindex("}") + 1]
            keys = tuple(re.findall(r'["\u201c]([A-Za-z_]+)["\u201d]\s*:', contract))
            with self.subTest(app=app.key):
                self.assertEqual(keys, app.condition_keys)

    def test_any_modification_fails_integrity_verification(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            original = app.prompt.path.read_bytes()
            edits = {
                "trailing whitespace": original + b" ",
                "extra newline": original + b"\n",
                "one character changed": original.replace(b"Positive", b"positive", 1),
                "CRLF line endings": original.replace(b"\n", b"\r\n"),
                "BOM added": b"\xef\xbb\xbf" + original,
                "truncated": original[:-200],
            }
            for label, content in edits.items():
                with self.subTest(app=app.key, edit=label), tempfile.TemporaryDirectory() as tmp:
                    (Path(tmp) / app.prompt.filename).write_bytes(content)
                    copy = replace(app.prompt, directory=Path(tmp))
                    with self.assertRaisesRegex(PromptIntegrityError, "does not match the pinned"):
                        verify_prompt(copy)
                    with self.assertRaises(PromptIntegrityError):
                        prompt_identity(copy)
            with self.subTest(app=app.key, edit="unchanged copy"), \
                    tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / app.prompt.filename).write_bytes(original)
                self.assertEqual(verify_prompt(replace(app.prompt, directory=Path(tmp))),
                                 load_prompt(app.prompt))

    def test_wrong_text_pins_rejected(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            with self.subTest(app=app.key):
                with self.assertRaisesRegex(PromptIntegrityError, "Loaded prompt text"):
                    verify_prompt(replace(app.prompt, text_sha256="0" * 64))
                with self.assertRaisesRegex(PromptIntegrityError, "Loaded prompt text"):
                    verify_prompt(replace(app.prompt, text_length=app.prompt.text_length - 1))

    def test_prompts_are_distinct(self):
        texts = {load_prompt(app.prompt) for app in APPLICATIONS.values()}
        self.assertEqual(len(texts), 3)


class TestPendingMechanism(OfflineTestCase):
    """The pending state still blocks loading for any prompt registered without pins."""

    def pending(self, base=FELINE_THORAX_PROMPT, **kwargs):
        return replace(base, file_sha256=None, text_sha256=None, text_length=None, **kwargs)

    def test_pending_prompt_cannot_be_loaded_or_identified(self):
        for base in (FELINE_THORAX_PROMPT, CANINE_ABDOMEN_PROMPT):
            spec = self.pending(base)
            self.assertTrue(spec.is_pending)
            for function in (load_prompt, verify_prompt, prompt_identity):
                with self.subTest(prompt=spec.label, function=function.__name__):
                    with self.assertRaisesRegex(PromptIntegrityError, "pending approval"):
                        function(spec)

    def test_pending_refused_even_if_the_approved_file_is_present(self):
        spec = self.pending()
        self.assertTrue(spec.path.is_file())
        with self.assertRaisesRegex(PromptIntegrityError, "pending approval"):
            load_prompt(spec)

    def test_partial_pins_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.pending(), file_sha256="a" * 64)
        with self.assertRaises(ValueError):
            replace(self.pending(), file_sha256="a" * 64, text_sha256="b" * 64)


class TestPinnedPromptVerification(TempDirCase):
    def test_pinned_prompt_loads_stripped_text(self):
        spec = _pinned(self.dir, "p.txt", "\n  Prompt body.\nLine 2.  \n".encode("utf-8"))
        self.assertEqual(verify_prompt(spec), "Prompt body.\nLine 2.")
        self.assertEqual(load_prompt(spec), "Prompt body.\nLine 2.")
        self.assertEqual(prompt_identity(spec)["file_sha256"], spec.file_sha256)

    def test_any_byte_change_is_rejected(self):
        spec = _pinned(self.dir, "p.txt", b"Prompt body.\n")
        spec.path.write_bytes(b"Prompt body.\n\n")  # whitespace-only edit
        with self.assertRaisesRegex(PromptIntegrityError, "does not match the pinned"):
            verify_prompt(spec)

    def test_text_digest_and_length_checked(self):
        spec = _pinned(self.dir, "p.txt", b"Prompt body.\n")
        with self.assertRaisesRegex(PromptIntegrityError, "Loaded prompt text"):
            verify_prompt(replace(spec, text_sha256="0" * 64))
        with self.assertRaisesRegex(PromptIntegrityError, "Loaded prompt text"):
            verify_prompt(replace(spec, text_length=spec.text_length + 1))

    def test_missing_file_rejected(self):
        spec = _pinned(self.dir, "p.txt", b"Prompt body.\n")
        spec.path.unlink()
        with self.assertRaisesRegex(PromptIntegrityError, "not found"):
            verify_prompt(spec)

    def test_identity_verifies_the_file(self):
        spec = _pinned(self.dir, "q.txt", b"Body.\n")
        spec.path.write_bytes(b"Changed.\n")
        with self.assertRaises(PromptIntegrityError):
            prompt_identity(spec)

    def test_independent_identities_per_application(self):
        feline = _pinned(self.dir, FELINE_THORAX_PROMPT.filename, b"Feline prompt text.\n",
                         name=FELINE_THORAX_PROMPT.name, version=FELINE_THORAX_PROMPT.version)
        abdomen = _pinned(self.dir, CANINE_ABDOMEN_PROMPT.filename, b"Abdomen prompt text.\n",
                          name=CANINE_ABDOMEN_PROMPT.name, version=CANINE_ABDOMEN_PROMPT.version)
        identities = [prompt_identity(CANINE_THORAX_PROMPT), prompt_identity(feline),
                      prompt_identity(abdomen)]
        self.assertEqual(len({i["file_sha256"] for i in identities}), 3)
        self.assertEqual([i["version"] for i in identities], ["V1.3", "V1.1", "V1.2"])
        self.assertEqual(load_prompt(feline), "Feline prompt text.")
        self.assertEqual(load_prompt(abdomen), "Abdomen prompt text.")
        self.assertNotEqual(load_prompt(feline), load_prompt(CANINE_THORAX_PROMPT))

    def test_spec_validation(self):
        valid = _pinned(self.dir, "v.txt", b"x\n")
        for bad in (dict(filename="../x.txt"), dict(file_sha256="XYZ"),
                    dict(text_sha256="A" * 64), dict(text_length=0), dict(name=" ")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                replace(valid, **bad)


class TestEveryApplicationHasAPrompt(OfflineTestCase):
    def test_each_application_prompt_is_distinct(self):
        prompts = [app.prompt for app in APPLICATIONS.values()]
        self.assertEqual(len({(p.name, p.version, p.filename) for p in prompts}), 3)
        self.assertEqual(registry.PROMPTS_DIR, prompt_loader.PROMPT_PATH.parent)
