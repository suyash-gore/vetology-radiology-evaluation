"""Output isolation and read-only source protection for Week 7.

Single write guard used by every Week 7 component that creates files (batch
predictions/errors, run manifest, evaluation workbooks, comparison workbooks):

1. The path is resolved (``Path.resolve()``, so symlinks and ``..`` cannot be
   used to escape).
2. It must not be inside — or contain — a protected root: ``outputs/week_04``,
   ``outputs/week_05``, ``data/``, ``src/`` or ``.git``.
3. It must be strictly inside ``outputs/week_07/`` (never the root itself).
4. When a workflow is given, it must not overlap any directory that belongs to
   the other workflow, nor the other output area of the same workflow (batch
   run outputs vs. comparison outputs).

Read-only sources (Week 5 OpenAI predictions and error logs, input workbooks)
are protected by ``ReadOnlyGuard``: SHA-256 digests are taken before use and
checked again afterwards; any change is an error.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import TracebackType

from week_07 import config
from week_07.config import ConfigurationError, WorkflowSpec

_CHUNK = 1024 * 1024


class IsolationError(ConfigurationError):
    """Raised when a write would break Week 7 output isolation."""


class ProtectedFileModified(RuntimeError):
    """Raised when a read-only source changed (or disappeared) while it was in use."""


class OutputArea(Enum):
    RUN = "run"                # predictions, errors, manifest, evaluation workbook
    COMPARISON = "comparison"  # OpenAI vs Gemini comparison workbook


def _overlaps(a: Path, b: Path) -> bool:
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def _area_dir(spec: WorkflowSpec, area: OutputArea) -> Path:
    return spec.output_dir if area is OutputArea.RUN else spec.comparison_dir


@dataclass(frozen=True)
class IsolationPolicy:
    """Where Week 7 may write. ``DEFAULT_POLICY`` uses the repository layout."""

    output_root: Path
    protected_roots: tuple[Path, ...]
    workflows: Mapping[str, WorkflowSpec] = field(default_factory=dict)

    def assert_writable(
        self,
        path: str | Path,
        spec: WorkflowSpec | None = None,
        area: OutputArea = OutputArea.RUN,
    ) -> Path:
        """Return the resolved path if Week 7 may write it; raise ``IsolationError`` otherwise."""
        target = Path(path).expanduser().resolve()
        root = self.output_root.resolve()

        for protected in self.protected_roots:
            protected = protected.resolve()
            if _overlaps(target, protected):
                raise IsolationError(
                    f"Week 7 must not write into or around a protected location "
                    f"({protected}): {target}"
                )
        if target == root or not target.is_relative_to(root):
            raise IsolationError(f"Week 7 may only write inside {root}: {target}")

        if spec is not None:
            foreign: list[tuple[str, Path]] = []
            for other in self.workflows.values():
                for other_area in OutputArea:
                    if other.name == spec.name and other_area is area:
                        continue
                    foreign.append((f"{other.name} {other_area.value}",
                                    _area_dir(other, other_area).resolve()))
            for label, directory in foreign:
                if _overlaps(target, directory):
                    raise IsolationError(
                        f"{spec.name} {area.value} output cannot be written to or around the "
                        f"{label} output directory ({directory}): {target}"
                    )
        return target


DEFAULT_POLICY = IsolationPolicy(
    output_root=config.OUTPUT_ROOT,
    protected_roots=(
        config.WEEK4_OUTPUTS,
        config.WEEK5_OUTPUTS,
        config.DATA_DIR,
        config.SRC_DIR,
        config.REPO_ROOT / ".git",
    ),
    workflows=config.WORKFLOWS,
)


def assert_writable(
    path: str | Path,
    spec: WorkflowSpec | None = None,
    area: OutputArea = OutputArea.RUN,
    *,
    policy: IsolationPolicy = DEFAULT_POLICY,
) -> Path:
    """Module-level shortcut for ``policy.assert_writable``."""
    return policy.assert_writable(path, spec, area)


# ---------------------------------------------------------------------------
# Read-only source protection
# ---------------------------------------------------------------------------

def sha256_file(path: str | Path) -> str:
    """SHA-256 of a file, read in binary mode only (never opened for writing)."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReadOnlyGuard:
    """Record SHA-256 digests on entry; verify them on exit.

    Usage::

        with ReadOnlyGuard([week5_predictions]) as guard:
            ...  # read the files
        guard.digests  # {resolved path: sha256}, e.g. for the Execution Log

    Every path must be an existing file on entry. On exit (also when the body
    raised) each file is hashed again; a changed or missing file raises
    ``ProtectedFileModified``.
    """

    def __init__(self, paths: Iterable[str | Path]) -> None:
        self._paths = tuple(dict.fromkeys(Path(p).expanduser().resolve() for p in paths))
        self.digests: dict[Path, str] = {}

    def __enter__(self) -> ReadOnlyGuard:
        for path in self._paths:
            if not path.is_file():
                raise FileNotFoundError(f"Read-only source not found: {path}")
            self.digests[path] = sha256_file(path)
        return self

    def verify(self) -> None:
        changed = []
        for path, expected in self.digests.items():
            if not path.is_file():
                changed.append(f"{path} (missing)")
            elif sha256_file(path) != expected:
                changed.append(f"{path} (content changed)")
        if changed:
            raise ProtectedFileModified(
                "Read-only source file(s) changed while in use: " + "; ".join(changed)
            )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.verify()
