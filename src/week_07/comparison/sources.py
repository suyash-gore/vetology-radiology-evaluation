"""Read-only prediction sources for the OpenAI vs Gemini comparison, with provenance.

* Week 5 OpenAI predictions — default ``outputs/week_05/<matrix>/predictions.jsonl``.
  Week 5 files do not embed the model; the approved description is
  ``OPENAI_MODEL_RECORD``. A file that has a Week 7 run manifest beside it is
  refused as an OpenAI source (it would be Gemini output).
* Week 7 Gemini predictions — default ``outputs/week_07/<matrix>/predictions.jsonl``.
  A Week 7 run manifest for the SAME workflow must sit beside the file, and its
  recorded input-workbook digest must equal the reference workbook's digest.

Both prediction files are read with the strict Week 5 loader
(``evaluation.reconcile.load_prediction_records``): non-success records,
duplicate CaseIDs, wrong keys or labels and non-object lines are errors; only
unparseable (interrupted-write) lines are skipped, and every skipped line is
reported. Sources in any directory of the other workflow are refused.

Error logs (``errors.jsonl``, optional): every failure record is classified as
SUPERSEDED (the same CaseID has a valid success record — not a final failure;
reported for transparency, e.g. Week 5 Matrix 1's 100 historical records) or
UNRESOLVED (no success record — a final failure; the comparison is refused).
Unparseable lines are skipped and reported; records without a usable CaseID
or with a status other than ``failed`` are errors. When no error log is named,
one beside the predictions file is used if present (recorded as auto-detected).

Nothing here writes a file. Callers wrap the reads in ``ReadOnlyGuard``.
"""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from week_07 import config, run_manifest
from week_07.config import WorkflowSpec
from week_07.evaluation.evaluate import WORKFLOW_LABELS, check_prediction_source
from week_07.evaluation.reconcile import (
    EvaluationInputError,
    PredictionRecords,
    SkippedLine,
    load_prediction_records,
)
from week_07.isolation import DEFAULT_POLICY, IsolationPolicy, sha256_file
from week_07.jsonl_store import STATUS_FAILED

OPENAI_MODEL_RECORD: Final[str] = (
    "gpt-4.1-mini (Week 5 configuration; model identity inferred from configuration, "
    "not embedded in prediction file)"
)
OPENAI: Final[str] = "openai"
GEMINI: Final[str] = "gemini"
SOURCE_LABELS: Final[Mapping[str, str]] = {OPENAI: "Week 5 OpenAI", GEMINI: "Week 7 Gemini"}


class ComparisonInputError(EvaluationInputError):
    """A comparison source is missing, inconsistent or of the wrong provenance."""


@dataclass(frozen=True)
class FileProvenance:
    path: Path
    sha256: str
    size_bytes: int

    @classmethod
    def of(cls, path: Path) -> FileProvenance:
        return cls(path, sha256_file(path), path.stat().st_size)


@dataclass(frozen=True)
class ErrorLogSummary:
    """Reconciliation of an error log against the matching prediction file."""

    provenance: FileProvenance | None
    origin: str                                   # "supplied", "auto-detected", "none"
    records: int = 0
    superseded: Mapping[int, int] = field(default_factory=dict)   # CaseID -> records
    unresolved: Mapping[int, int] = field(default_factory=dict)
    skipped_lines: tuple[SkippedLine, ...] = ()

    @property
    def superseded_records(self) -> int:
        return sum(self.superseded.values())

    @property
    def unresolved_records(self) -> int:
        return sum(self.unresolved.values())

    def describe(self) -> str:
        if self.provenance is None:
            return "No error log supplied or found beside the prediction file."
        text = (f"{self.records} failure record(s): {self.superseded_records} superseded by a "
                f"later success ({len(self.superseded)} case(s)); {self.unresolved_records} "
                f"unresolved ({len(self.unresolved)} case(s))")
        if self.skipped_lines:
            text += f"; {len(self.skipped_lines)} unreadable line(s) skipped"
        return text + "."


@dataclass(frozen=True)
class PredictionSource:
    role: str
    label: str
    model_record: str
    provenance: FileProvenance
    records: PredictionRecords
    errors: ErrorLogSummary
    manifest_provenance: FileProvenance | None = None
    manifest_identity: Mapping[str, Any] | None = None

    @property
    def labels(self) -> Mapping[int, Mapping[str, str]]:
        return self.records.labels


def _error_case_id(value: Any, line_number: int, path: Path) -> int:
    if value is None or isinstance(value, bool):
        raise ComparisonInputError(f"{path.name} line {line_number} has no usable case_id.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ComparisonInputError(
            f"{path.name} line {line_number}: case_id {value!r} cannot be converted to an "
            f"integer."
        ) from exc


def read_error_log(path: Path, success_ids: set[int], origin: str) -> ErrorLogSummary:
    """Classify every failure record as superseded or unresolved (nothing dropped silently)."""
    superseded: Counter[int] = Counter()
    unresolved: Counter[int] = Counter()
    skipped: list[SkippedLine] = []
    records = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                skipped.append(SkippedLine(
                    line_number, f"not valid JSON ({exc.msg}); ignored as an interrupted write"))
                continue
            if not isinstance(record, dict):
                raise ComparisonInputError(f"{path.name} line {line_number} is not a JSON object.")
            if record.get("status") != STATUS_FAILED:
                raise ComparisonInputError(
                    f"{path.name} line {line_number}: expected status 'failed', found "
                    f"{record.get('status')!r}."
                )
            case_id = _error_case_id(record.get("case_id"), line_number, path)
            records += 1
            (superseded if case_id in success_ids else unresolved)[case_id] += 1
    return ErrorLogSummary(FileProvenance.of(path), origin, records,
                           dict(sorted(superseded.items())), dict(sorted(unresolved.items())),
                           tuple(skipped))


def _resolve_error_log(predictions: Path, errors_path: str | Path | None
                       ) -> tuple[Path | None, str]:
    if errors_path is not None:
        path = Path(errors_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Error log not found: {path}")
        return path, "supplied"
    candidate = predictions.parent / config.ERRORS_FILENAME
    return (candidate, "auto-detected") if candidate.is_file() else (None, "none")


def source_files(predictions_path: Path, errors_path: str | Path | None) -> list[Path]:
    """Every file a source will read (for the caller's ReadOnlyGuard)."""
    files = [predictions_path]
    errors, _ = _resolve_error_log(predictions_path, errors_path)
    if errors is not None:
        files.append(errors)
    manifest = predictions_path.parent / config.MANIFEST_FILENAME
    if manifest.is_file():
        files.append(manifest)
    return files


def load_prediction_source(
    role: str,
    spec: WorkflowSpec,
    predictions_path: str | Path | None,
    reference_path: Path,
    errors_path: str | Path | None = None,
    *,
    isolation: IsolationPolicy = DEFAULT_POLICY,
) -> PredictionSource:
    """Load one model's predictions for ``spec`` with provenance checks."""
    if role not in SOURCE_LABELS:
        raise ValueError(f"Unknown prediction source role {role!r}.")
    default = spec.week5_predictions_path if role == OPENAI else spec.predictions_path
    path = Path(default if predictions_path is None else predictions_path).expanduser().resolve()
    label = SOURCE_LABELS[role]
    if not path.is_file():
        raise FileNotFoundError(f"{label} predictions file not found: {path}")
    check_prediction_source(spec, path, isolation)

    manifest_path = path.parent / config.MANIFEST_FILENAME
    manifest = run_manifest.read_manifest(manifest_path)
    if role == OPENAI:
        if manifest is not None:
            raise ComparisonInputError(
                f"The OpenAI source {path} has a Week 7 run manifest beside it, so it is Week 7 "
                "output, not Week 5 OpenAI predictions."
            )
        model = OPENAI_MODEL_RECORD
        identity = None
    else:
        if manifest is None:
            raise ComparisonInputError(
                f"The Gemini source {path} has no Week 7 run manifest beside it; its provenance "
                "cannot be established."
            )
        identity = manifest["identity"]
        if identity.get("workflow") != spec.name:
            raise ComparisonInputError(
                f"The Gemini run manifest beside {path.name} belongs to workflow "
                f"{identity.get('workflow')!r}, not {spec.name!r}."
            )
        recorded = identity.get("input_workbook", {}).get("sha256")
        actual = sha256_file(reference_path)
        if recorded != actual:
            raise ComparisonInputError(
                f"The Gemini predictions were produced from a different input workbook than "
                f"{reference_path.name} (manifest digest {recorded}, reference digest {actual})."
            )
        model = run_manifest.model_record(identity, WORKFLOW_LABELS.get(spec.name, spec.name))

    records = load_prediction_records(path)
    errors_file, origin = _resolve_error_log(path, errors_path)
    if errors_file is None:
        errors = ErrorLogSummary(None, origin)
    else:
        errors = read_error_log(errors_file, set(records.labels), origin)
    return PredictionSource(
        role=role,
        label=label,
        model_record=model,
        provenance=FileProvenance.of(path),
        records=records,
        errors=errors,
        manifest_provenance=FileProvenance.of(manifest_path) if manifest is not None else None,
        manifest_identity=identity,
    )
