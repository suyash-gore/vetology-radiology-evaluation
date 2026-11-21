"""Application-aware prompt registry with pinned SHA-256 integrity checks.

Every application has its own prompt identity (name, version, file name and two
pinned digests). The integrity rule is the same for all of them and is the
rule of ``prompt_loader`` (verbatim Week 5 copy, not modified):

* the SHA-256 of the file bytes must equal ``file_sha256``;
* the file is read as UTF-8 and ``str.strip()``-ed (Weeks 4/5 behaviour);
* the SHA-256 of the stripped UTF-8 text must equal ``text_sha256`` and its
  length must equal ``text_length``.

Canine Thorax V1.3 is NOT re-implemented here: ``load_prompt`` delegates to
``prompt_loader.load_system_prompt()`` and its identity is built from the
constants pinned in ``prompt_loader``, so its behaviour and digests are
unchanged.

Feline Thorax V1.1 and Canine Abdomen V1.2 are the approved files supplied by
the project owner, stored byte-for-byte and pinned below. A prompt whose pins
are ``None`` is PENDING: it cannot be loaded and has no run identity (both raise
``PromptIntegrityError``); that mechanism remains for any future prompt.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from week_07.prompts import prompt_loader
from week_07.prompts.prompt_loader import PromptIntegrityError

PROMPTS_DIR: Final[Path] = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PromptSpec:
    """Identity and pinned digests of one application's system prompt."""

    name: str
    version: str
    filename: str
    file_sha256: str | None
    text_sha256: str | None
    text_length: int | None
    directory: Path = PROMPTS_DIR

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.version.strip() or not self.filename.strip():
            raise ValueError("A prompt needs a name, a version and a file name.")
        if Path(self.filename).name != self.filename:
            raise ValueError(f"Prompt file name must not contain a path: {self.filename!r}")
        pins = (self.file_sha256, self.text_sha256, self.text_length)
        if any(pin is None for pin in pins) and any(pin is not None for pin in pins):
            raise ValueError(
                f"{self.label}: pin all of file_sha256, text_sha256 and text_length, or none "
                "(pending)."
            )
        for digest in (self.file_sha256, self.text_sha256):
            if digest is not None and (len(digest) != 64
                                       or any(c not in "0123456789abcdef" for c in digest)):
                raise ValueError(f"{self.label}: digests must be lowercase SHA-256 hex.")
        if self.text_length is not None and (isinstance(self.text_length, bool)
                                             or not isinstance(self.text_length, int)
                                             or self.text_length < 1):
            raise ValueError(f"{self.label}: text_length must be a positive integer.")

    @property
    def label(self) -> str:
        return f"{self.name} {self.version}"

    @property
    def path(self) -> Path:
        return self.directory / self.filename

    @property
    def is_pending(self) -> bool:
        """True until the approved prompt file and its digests are pinned."""
        return self.file_sha256 is None


CANINE_THORAX_PROMPT: Final[PromptSpec] = PromptSpec(
    name="Canine Thorax Master Prompt",
    version=prompt_loader.PROMPT_VERSION,
    filename=prompt_loader.PROMPT_PATH.name,
    file_sha256=prompt_loader.PROMPT_FILE_SHA256,
    text_sha256=prompt_loader.PROMPT_TEXT_SHA256,
    text_length=prompt_loader.PROMPT_TEXT_LENGTH,
    directory=prompt_loader.PROMPT_PATH.parent,
)

# Approved file supplied by the project owner, stored byte-for-byte
# (26,060 bytes, UTF-8, LF, no BOM; 25,833 characters after strip()).
FELINE_THORAX_PROMPT: Final[PromptSpec] = PromptSpec(
    name="Feline Thorax Master Prompt",
    version="V1.1",
    filename="feline_thorax_master_prompt_v1_1.txt",
    file_sha256="7696598eda2faa39ef44df3e9c260ca7870d487094df40ae6e05c4b0c2665d27",
    text_sha256="bf9142f7b753e3bfdf67d64869332672082796859e02aaafac0c11e202eeb103",
    text_length=25833,
)

# Approved file supplied by the project owner, stored byte-for-byte
# (17,216 bytes, UTF-8, LF, no BOM; 17,081 characters after strip()).
CANINE_ABDOMEN_PROMPT: Final[PromptSpec] = PromptSpec(
    name="Canine Abdomen Master Prompt",
    version="V1.2",
    filename="canine_abdomen_master_prompt_v1_2.txt",
    file_sha256="f25b56fb0fbd2a7e697be287ef51357a8e911243523464d860eff7726a5e17aa",
    text_sha256="1156c72a6ceaed5f466a77e5490add36ec25214bd3ccb1b785a0bef205402305",
    text_length=17081,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_pinned(spec: PromptSpec) -> None:
    if spec.is_pending:
        raise PromptIntegrityError(
            f"{spec.label} is pending approval: the approved prompt file and its SHA-256 "
            "digests have not been registered, so it cannot be loaded or used for a run."
        )


def verify_prompt(spec: PromptSpec) -> str:
    """Return the stripped prompt text after checking all pinned values (no cache)."""
    _require_pinned(spec)
    path = spec.path
    if not path.is_file():
        raise PromptIntegrityError(f"{spec.label} prompt file not found: {path}")

    file_digest = _sha256(path.read_bytes())
    if file_digest != spec.file_sha256:
        raise PromptIntegrityError(
            f"Prompt file {path.name} does not match the pinned {spec.label} file "
            f"(sha256 {file_digest}, expected {spec.file_sha256})."
        )
    text = path.read_text(encoding="utf-8").strip()
    text_digest = _sha256(text.encode("utf-8"))
    if text_digest != spec.text_sha256 or len(text) != spec.text_length:
        raise PromptIntegrityError(
            f"Loaded prompt text does not match the pinned {spec.label} text "
            f"(sha256 {text_digest}, length {len(text)})."
        )
    return text


@lru_cache(maxsize=16)
def _load_cached(spec: PromptSpec) -> str:
    return verify_prompt(spec)


def load_prompt(spec: PromptSpec) -> str:
    """Return an application's verified system prompt (read and checked once per process).

    Canine Thorax V1.3 goes through the original ``load_system_prompt()``.
    """
    if spec == CANINE_THORAX_PROMPT:
        return prompt_loader.load_system_prompt()
    return _load_cached(spec)


def prompt_identity(spec: PromptSpec) -> dict[str, str]:
    """The prompt part of a run identity (same keys as the Canine Thorax manifest).

    Refuses a pending prompt, and verifies the file before reporting digests
    for every prompt other than Canine Thorax (whose identity is the pinned
    constants, exactly as ``run_manifest.run_identity`` records them).
    """
    _require_pinned(spec)
    if spec != CANINE_THORAX_PROMPT:
        load_prompt(spec)
    return {
        "name": spec.name,
        "version": spec.version,
        "file_sha256": spec.file_sha256,
        "text_sha256": spec.text_sha256,
    }
