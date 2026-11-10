"""Load the operational V1.3 system prompt with an integrity guard.

The prompt file is a byte-for-byte copy of
``src/week_04/prompts/canine_thorax_master_prompt_v1_3.txt``. Loading applies
the same behaviour as Week 4: read as UTF-8, then ``str.strip()``.

The SHA-256 digests below pin both the file bytes and the loaded (stripped)
text. Any edit to the prompt — even whitespace — makes loading fail instead of
silently changing the classification instruction.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Final

PROMPT_VERSION: Final[str] = "V1.3"
PROMPT_PATH: Final[Path] = Path(__file__).with_name("canine_thorax_master_prompt_v1_3.txt")

# SHA-256 of the file exactly as stored (8,715 bytes, UTF-8, LF, no BOM).
PROMPT_FILE_SHA256: Final[str] = (
    "31a7dab6e535e6f0af6a54106cf449ecadfe3644c7b3c805710309f0e85ab7b1"
)
# SHA-256 of the UTF-8 encoding of the stripped text sent to the model (8,710 chars).
PROMPT_TEXT_SHA256: Final[str] = (
    "97ad5b74be0ebaa8655227e50e6fcc9cee1a96e7ba072c45ee6f822673d44d29"
)
PROMPT_TEXT_LENGTH: Final[int] = 8710


class PromptIntegrityError(RuntimeError):
    """Raised when the prompt file is missing or differs from the pinned V1.3 text."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_prompt_text(path: Path = PROMPT_PATH) -> str:
    """Read and strip a prompt file exactly as Week 4 does, without verification."""
    if not path.is_file():
        raise PromptIntegrityError(f"Canine thorax prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def verify_prompt_file(path: Path = PROMPT_PATH) -> str:
    """Return the stripped prompt after checking both pinned digests."""
    if not path.is_file():
        raise PromptIntegrityError(f"Canine thorax prompt file not found: {path}")

    file_digest = _sha256(path.read_bytes())
    if file_digest != PROMPT_FILE_SHA256:
        raise PromptIntegrityError(
            f"Prompt file {path.name} does not match the pinned V1.3 file "
            f"(sha256 {file_digest}, expected {PROMPT_FILE_SHA256})."
        )

    text = read_prompt_text(path)
    text_digest = _sha256(text.encode("utf-8"))
    if text_digest != PROMPT_TEXT_SHA256 or len(text) != PROMPT_TEXT_LENGTH:
        raise PromptIntegrityError(
            "Loaded prompt text does not match the pinned V1.3 text "
            f"(sha256 {text_digest}, length {len(text)})."
        )
    return text


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """Return the verified V1.3 system prompt (read and checked once per process)."""
    return verify_prompt_file(PROMPT_PATH)
