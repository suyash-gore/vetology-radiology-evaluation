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


ACTIVE = {
    "feline_thorax": ("Feline Thorax Master Prompt", "V1.2",
                      "feline_thorax_master_prompt_v1_2.txt", 25892,
                      "9bbd36c4a1d9ac15cb24c39b3e9d0ad5af9106a9bddb3adf3401098e1c418f25",
                      "a7adb7078bc50df891f23110d6c4de9046db779b118e39201b4923f96f9c81c3", 25833),
    "canine_abdomen": ("Canine Abdomen Master Prompt", "V1.3",
                       "canine_abdomen_master_prompt_v1_3.txt", 17913,
                       "142d8e532fcd851dda98c3982e4ece1f4561c1f844c0232dc2ef1b312e654e93",
                       "4a0ee63a855853b0b9a931618affb6e1987ee244e502244ec755cfa60fdd9549", 17776),
}
ORIGINALS = {
    "feline_thorax": ("Feline Thorax Master Prompt", "V1.1",
                      "feline_thorax_master_prompt_v1_1.txt", 26060,
                      "7696598eda2faa39ef44df3e9c260ca7870d487094df40ae6e05c4b0c2665d27",
                      "bf9142f7b753e3bfdf67d64869332672082796859e02aaafac0c11e202eeb103", 25833),
    "canine_abdomen": ("Canine Abdomen Master Prompt", "V1.2",
                       "canine_abdomen_master_prompt_v1_2.txt", 17216,
                       "f25b56fb0fbd2a7e697be287ef51357a8e911243523464d860eff7726a5e17aa",
                       "1156c72a6ceaed5f466a77e5490add36ec25214bd3ccb1b785a0bef205402305", 17081),
}


def _check_spec(test, spec, expected):
    name, version, filename, size, file_sha, text_sha, length = expected
    test.assertEqual((spec.name, spec.version, spec.filename), (name, version, filename))
    test.assertEqual((spec.file_sha256, spec.text_sha256, spec.text_length),
                     (file_sha, text_sha, length))
    test.assertFalse(spec.is_pending)
    test.assertEqual(spec.directory, prompt_loader.PROMPT_PATH.parent)
    data = spec.path.read_bytes()
    test.assertEqual(len(data), size)
    test.assertEqual(hashlib.sha256(data).hexdigest(), file_sha)
    test.assertFalse(data.startswith(b"\xef\xbb\xbf"))   # no BOM
    test.assertNotIn(b"\r", data)                       # LF line endings
    test.assertEqual(prompt_identity(spec), {"name": name, "version": version,
                                             "file_sha256": file_sha, "text_sha256": text_sha})


def _json_example(text: str) -> str:
    return text[text.rindex("{"):text.rindex("}") + 1]


class TestActivePrompts(OfflineTestCase):
    def test_applications_use_the_corrected_versions(self):
        self.assertIs(FELINE_THORAX.prompt, FELINE_THORAX_PROMPT)
        self.assertIs(CANINE_ABDOMEN.prompt, CANINE_ABDOMEN_PROMPT)
        self.assertEqual((FELINE_THORAX.prompt.version, CANINE_ABDOMEN.prompt.version),
                         ("V1.2", "V1.3"))
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            with self.subTest(app=app.key):
                _check_spec(self, app.prompt, ACTIVE[app.key])
                text = load_prompt(app.prompt)
                self.assertEqual(text, verify_prompt(app.prompt))
                self.assertEqual(len(text), ACTIVE[app.key][6])
                self.assertEqual(text, app.prompt.path.read_text(encoding="utf-8").strip())

    def test_header_names_the_registered_version(self):
        self.assertIn("FELINE THORAX MASTER PROMPT\nV1.2 Application",
                      load_prompt(FELINE_THORAX_PROMPT))
        self.assertTrue(load_prompt(CANINE_ABDOMEN_PROMPT).startswith(
            "Canine Abdomen Master Prompt V1.3\n"))

    def test_output_examples_are_valid_json_with_the_application_keys_in_order(self):
        import json

        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            with self.subTest(app=app.key):
                example = json.loads(_json_example(load_prompt(app.prompt)))
                self.assertEqual(tuple(example), app.condition_keys)
                self.assertLessEqual(set(example.values()), {"Positive", "Negative"})

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
                "curly quote restored": original.replace(b'"', "\u201c".encode(), 1),
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


class TestSupersededOriginals(OfflineTestCase):
    def test_originals_retained_byte_for_byte_and_still_pinned(self):
        self.assertEqual(registry.SUPERSEDED_PROMPTS, {
            "feline_thorax": (registry.FELINE_THORAX_PROMPT_V1_1,),
            "canine_abdomen": (registry.CANINE_ABDOMEN_PROMPT_V1_2,)})
        for key, spec in (("feline_thorax", registry.FELINE_THORAX_PROMPT_V1_1),
                          ("canine_abdomen", registry.CANINE_ABDOMEN_PROMPT_V1_2)):
            with self.subTest(prompt=spec.label):
                _check_spec(self, spec, ORIGINALS[key])
                self.assertEqual(len(verify_prompt(spec)), ORIGINALS[key][6])

    def test_originals_are_not_used_by_any_application(self):
        used = {app.prompt for app in APPLICATIONS.values()}
        for specs in registry.SUPERSEDED_PROMPTS.values():
            for spec in specs:
                self.assertNotIn(spec, used)

    def test_original_feline_example_was_not_valid_json(self):
        import json

        with self.assertRaises(json.JSONDecodeError):
            json.loads(_json_example(load_prompt(registry.FELINE_THORAX_PROMPT_V1_1)))


def _lines(spec):
    return spec.path.read_text(encoding="utf-8").split("\n")


class TestFelineV12Correction(OfflineTestCase):
    def test_only_the_json_quotes_and_version_label_changed(self):
        old, new = _lines(registry.FELINE_THORAX_PROMPT_V1_1), _lines(FELINE_THORAX_PROMPT)
        self.assertEqual(len(old), len(new))
        changed = [i + 1 for i, (a, b) in enumerate(zip(old, new)) if a != b]
        self.assertEqual(changed, [2, *range(563, 574)])
        self.assertEqual(new[1], old[1].replace("V1.1", "V1.2", 1))
        replaced = 0
        for a, b in zip(old[562:573], new[562:573]):
            replaced += a.count("\u201c") + a.count("\u201d")
            self.assertEqual(b, a.replace("\u201c", '"').replace("\u201d", '"'))
            self.assertNotIn("\u201c", b)
            self.assertNotIn("\u201d", b)
        self.assertEqual(replaced, 84)

    def test_prose_curly_quotes_untouched(self):
        text = load_prompt(FELINE_THORAX_PROMPT)
        outside = text.replace(_json_example(text), "")
        self.assertEqual(outside.count("\u201c") + outside.count("\u201d"), 24)


class TestCanineAbdomenV13Hierarchy(OfflineTestCase):
    ALLOWED_CHANGED_V12_LINES = {1, 108, 111, 112, 114, 118, 122, 126, 128, 129, 131, 134, 144,
                                 147, 150, 372, 373}

    def setUp(self):
        super().setUp()
        self.old = _lines(registry.CANINE_ABDOMEN_PROMPT_V1_2)
        self.new = _lines(CANINE_ABDOMEN_PROMPT)
        self.text = load_prompt(CANINE_ABDOMEN_PROMPT)

    def test_changes_limited_to_the_approved_lines(self):
        import difflib

        changed = set()
        matcher = difflib.SequenceMatcher(a=self.old, b=self.new, autojunk=False)
        for tag, i1, i2, _, _ in matcher.get_opcodes():
            if tag != "equal":
                changed.update(range(i1 + 1, i2 + 1))
        self.assertLessEqual(changed, self.ALLOWED_CHANGED_V12_LINES)
        self.assertTrue({1, 111, 112, 126, 128, 129, 150, 372, 373} <= changed)

    def _section(self, lines, start, end):
        text = "\n".join(lines)
        return text[text.index(start):text.index(end)]

    def test_sections_4_41_and_condition_definitions_unchanged(self):
        for start, end in (("4.  Label definitions", "5.  General interpretation rules"),
                           ("6.1 gastritis", "8.  Output format")):
            with self.subTest(section=start):
                self.assertEqual(self._section(self.old, start, end),
                                 self._section(self.new, start, end))

    def test_contradictory_statements_removed(self):
        for removed in ("Classify Negative unless the report separately\n    establishes the "
                        "condition.",
                        "clearly qualified as uncertain",
                        "Equivocal, differential-only, \u201ccannot exclude,\u201d and\n    "
                        "recommendation-only statements are not treated as Positive."):
            with self.subTest(removed=removed[:40]):
                self.assertIn(removed, "\n".join(self.old))
                self.assertNotIn(removed, self.text)

    def test_inclusive_policy_stated_in_rule_6_and_checklist(self):
        flat = " ".join(self.text.split())
        self.assertIn("a suspected, likely, probable, or cannot-be-excluded condition may be "
                      "Positive only when it is explicitly identified in the "
                      "Conclusions/Impression as a principal or meaningful clinical "
                      "interpretation and is supported by the described findings", flat)
        self.assertIn("Classify Negative for broad or unranked differential lists, remote "
                      "possibilities, unsupported findings, recommendation-only mentions, and "
                      "negated conditions.", flat)
        self.assertIn("Give greatest weight to explicit diagnoses and to the radiologist\u2019s "
                      "primary Conclusions/Impression, provided they are not negated. Apply "
                      "Section 4.1 to qualified conclusions", flat)
        self.assertIn("Qualified statements (including \u201ccannot exclude\u201d) are Positive "
                      "only when they meet Section 4.1 item 2 and the relevant Section 6 "
                      "definition.", flat)
        self.assertIn("Differential-only, remote or unsupported, recommendation-only, and "
                      "negated statements are not treated as Positive.", flat)

    def test_numbering_corrected(self):
        import re

        general = self._section(self.new, "5.  General interpretation rules",
                                "6.  Condition-specific operational definitions")
        numbers = [int(n) for n in re.findall(r"^(\d+)\.\s", general, flags=re.M)]
        self.assertEqual(numbers, [5, *range(1, 11)])
        self.assertIn("\n6.  Condition-specific operational definitions\n", self.text)
        self.assertNotIn("16. Condition-specific", self.text)
        headings = ("1.  Role and task", "2.  Permitted input", "3.  Strict information boundaries",
                    "4.  Label definitions and evidence hierarchy",
                    "5.  General interpretation rules",
                    "6.  Condition-specific operational definitions",
                    "7.  Independent condition assessment", "8.  Output format — mandatory",
                    "9.  Final quality-control checklist")
        positions = [self.text.index("\n" + heading + "\n") for heading in headings]
        self.assertEqual(positions, sorted(positions))
        for heading in headings:
            self.assertEqual(self.text.count("\n" + heading + "\n"), 1, heading)


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
        self.assertEqual([i["version"] for i in identities], ["V1.3", "V1.2", "V1.3"])
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
