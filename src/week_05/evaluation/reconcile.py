"""Load a workflow's predictions and align them with its reference labels.

Prediction-file rules follow the Week 4 Matrix 1 evaluator: every record must
have ``status == "success"``, a unique ``case_id`` (converted with ``int()``,
as Week 4 does), exactly the 20 condition keys and only Positive/Negative
values, and the set of prediction CaseIDs must equal the set of reference
CaseIDs exactly.

Approved exception (Option B): a line that is not valid JSON — the signature
of an interrupted write, which the batch checkpoint reader also ignores — is
skipped instead of failing the evaluation. Every skipped line is returned with
its line number and reason and must be reported (the Matrix 1 workbook lists
them in its Execution Log). Skipping never hides missing predictions: the
exact CaseID-set match is still enforced afterwards. Everything else that is
wrong — non-object JSON, missing/unconvertible CaseIDs, duplicates, non-success
records, wrong keys or labels — is rejected.

Reference labels and predictions stay in two separate mappings.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from week_05 import config
from week_05.conditions import CONDITION_KEYS, VALID_LABELS
from week_05.config import WorkflowSpec
from week_05.evaluation.reference_loader import EvaluationReference
from week_05.jsonl_store import STATUS_SUCCESS


class EvaluationInputError(ValueError):
    """Raised when predictions or reference labels cannot be evaluated together."""


@dataclass(frozen=True)
class SkippedLine:
    line_number: int
    reason: str

    def describe(self) -> str:
        return f"line {self.line_number}: {self.reason}"


@dataclass(frozen=True)
class PredictionRecords:
    labels: Mapping[int, Mapping[str, str]]            # file order
    skipped: tuple[SkippedLine, ...] = field(default=())


@dataclass(frozen=True)
class ReconciledLabels:
    """Reference labels and predictions for the same cases, held separately."""

    workflow: str
    case_ids: tuple[int, ...]                           # reference (worksheet) order
    reference: Mapping[int, Mapping[str, str]]
    predictions: Mapping[int, Mapping[str, str]]
    reference_source: Path | None = None
    predictions_source: Path | None = None
    skipped_lines: tuple[SkippedLine, ...] = ()

    def __repr__(self) -> str:
        return (f"ReconciledLabels(workflow={self.workflow!r}, cases={len(self.case_ids)}, "
                f"skipped_lines={len(self.skipped_lines)}, "
                f"predictions_source={self.predictions_source!s})")


def check_predictions_location(spec: WorkflowSpec, predictions_path: Path) -> None:
    """Refuse a predictions file that lives in another workflow's output directory."""
    resolved = predictions_path.expanduser().resolve()
    for other in config.WORKFLOWS.values():
        if other.name != spec.name and resolved.is_relative_to(other.output_dir.resolve()):
            raise EvaluationInputError(
                f"{spec.name} evaluation cannot use predictions from the {other.name} "
                f"output directory: {resolved}"
            )


def _case_id(value: Any, line_number: int) -> int:
    if value is None:
        raise EvaluationInputError(f"Prediction line {line_number} has no case_id.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise EvaluationInputError(
            f"Prediction line {line_number}: case_id {value!r} cannot be converted to an "
            f"integer: {exc}"
        ) from exc


def load_prediction_records(path: Path) -> PredictionRecords:
    """Read a predictions JSONL file strictly, skipping only unparseable lines."""
    if not path.is_file():
        raise FileNotFoundError(f"Predictions file not found: {path}")

    labels_by_case: dict[int, Mapping[str, str]] = {}
    skipped: list[SkippedLine] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                skipped.append(SkippedLine(
                    line_number,
                    f"not valid JSON ({exc.msg}); ignored as an interrupted or incomplete write",
                ))
                continue
            if not isinstance(record, dict):
                raise EvaluationInputError(
                    f"Prediction line {line_number} is not a JSON object."
                )
            case_id = _case_id(record.get("case_id"), line_number)
            if case_id in labels_by_case:
                raise EvaluationInputError(f"Duplicate prediction CaseID: {case_id}")
            if record.get("status") != STATUS_SUCCESS:
                raise EvaluationInputError(f"Prediction is not successful for CaseID {case_id}")
            labels = record.get("predictions")
            if not isinstance(labels, dict) or set(labels) != set(CONDITION_KEYS):
                raise EvaluationInputError(f"Prediction keys mismatch for CaseID {case_id}")
            if any(value not in VALID_LABELS for value in labels.values()):
                raise EvaluationInputError(f"Invalid prediction label for CaseID {case_id}")
            labels_by_case[case_id] = MappingProxyType(
                {condition: labels[condition] for condition in CONDITION_KEYS}
            )
    if not labels_by_case:
        raise EvaluationInputError(f"No valid prediction records found in {path}")
    return PredictionRecords(MappingProxyType(labels_by_case), tuple(skipped))


def reconcile(
    spec: WorkflowSpec,
    reference: EvaluationReference,
    predictions_path: str | Path,
    *,
    expected_cases: int | None = None,
) -> ReconciledLabels:
    """Align one workflow's predictions with its reference labels.

    ``expected_cases`` (Matrix 1: 100, as in Week 4) is checked after the
    CaseID sets have been shown to match. Matrix 2 uses exact set matching only.
    """
    path = Path(predictions_path)
    check_predictions_location(spec, path)
    records = load_prediction_records(path)

    reference_ids = set(reference.case_ids)
    prediction_ids = set(records.labels)
    if reference_ids != prediction_ids:
        skipped_note = (f"; {len(records.skipped)} unreadable prediction line(s) were skipped"
                        if records.skipped else "")
        raise EvaluationInputError(
            "CaseID mismatch: "
            f"reference-only={sorted(reference_ids - prediction_ids)}; "
            f"prediction-only={sorted(prediction_ids - reference_ids)}{skipped_note}"
        )
    if expected_cases is not None and len(reference.case_ids) != expected_cases:
        raise EvaluationInputError(
            f"{spec.name} evaluation requires exactly {expected_cases} cases; "
            f"found {len(reference.case_ids)}"
        )

    return ReconciledLabels(
        workflow=spec.name,
        case_ids=reference.case_ids,
        reference=reference.labels,
        predictions=MappingProxyType({cid: records.labels[cid] for cid in reference.case_ids}),
        reference_source=reference.source_path,
        predictions_source=path.resolve(),
        skipped_lines=records.skipped,
    )


def sorted_case_ids(case_ids) -> list[Any]:
    """Week 4 lists cases in ``sorted()`` order."""
    return sorted(case_ids)
