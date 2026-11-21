"""Application-aware reconciliation of saved predictions with reference labels.

Same strict rules as ``reconcile`` (verbatim Week 5 copy, still used unchanged
for Canine Thorax), with the application's condition keys:

* Unparseable JSON lines (interrupted writes) are skipped and reported; every
  other problem is an error: non-object record, missing/non-integer CaseID,
  duplicate CaseID, non-success status, predictions whose keys are not EXACTLY
  the application's condition keys, any label other than Positive/Negative.
* The prediction CaseID set must equal the reference CaseID set exactly; Matrix
  1 additionally requires exactly 100 cases.

The result is the verbatim ``ReconciledLabels`` type: reference labels and
predictions held separately, in reference (worksheet) order.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType

from week_07.conditions import VALID_LABELS
from week_07.config import WorkflowSpec
from week_07.evaluation.reconcile import (
    EvaluationInputError,
    PredictionRecords,
    ReconciledLabels,
    RecordMetadata,
    SkippedLine,
    _case_id,
)
from week_07.evaluation.reference_loader import EvaluationReference
from week_07.jsonl_store import STATUS_SUCCESS


def load_application_prediction_records(path: Path,
                                        condition_keys: Sequence[str]) -> PredictionRecords:
    """Read a predictions JSONL file strictly against an application's condition keys."""
    keys = tuple(condition_keys)
    if not path.is_file():
        raise FileNotFoundError(f"Predictions file not found: {path}")

    labels_by_case: dict[int, Mapping[str, str]] = {}
    metadata: dict[int, RecordMetadata] = {}
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
                raise EvaluationInputError(f"Prediction line {line_number} is not a JSON object.")
            case_id = _case_id(record.get("case_id"), line_number)
            if case_id in labels_by_case:
                raise EvaluationInputError(f"Duplicate prediction CaseID: {case_id}")
            if record.get("status") != STATUS_SUCCESS:
                raise EvaluationInputError(f"Prediction is not successful for CaseID {case_id}")
            labels = record.get("predictions")
            if not isinstance(labels, dict) or set(labels) != set(keys):
                raise EvaluationInputError(f"Prediction keys mismatch for CaseID {case_id}")
            if any(value not in VALID_LABELS for value in labels.values()):
                raise EvaluationInputError(f"Invalid prediction label for CaseID {case_id}")
            labels_by_case[case_id] = MappingProxyType({key: labels[key] for key in keys})
            metadata[case_id] = RecordMetadata(status=record["status"],
                                               attempts=record.get("attempts"),
                                               completed_at_utc=record.get("completed_at_utc"))
    if not labels_by_case:
        raise EvaluationInputError(f"No valid prediction records found in {path}")
    return PredictionRecords(MappingProxyType(labels_by_case), tuple(skipped),
                             MappingProxyType(metadata))


def reconcile_application(
    spec: WorkflowSpec,
    condition_keys: Sequence[str],
    reference: EvaluationReference,
    predictions_path: str | Path,
    *,
    expected_cases: int | None = None,
) -> ReconciledLabels:
    """Align one application workflow's predictions with its reference labels.

    The predictions location must already have been checked with
    ``evaluate.check_prediction_source`` (application-qualified isolation).
    """
    path = Path(predictions_path)
    records = load_application_prediction_records(path, condition_keys)
    reference_ids, prediction_ids = set(reference.case_ids), set(records.labels)
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
            f"{spec.qualified_name} evaluation requires exactly {expected_cases} cases; "
            f"found {len(reference.case_ids)}"
        )
    for case_id in reference.case_ids:
        if set(reference.labels[case_id]) != set(condition_keys):
            raise EvaluationInputError(f"Reference keys mismatch for CaseID {case_id}")
    return ReconciledLabels(
        workflow=spec.name,
        case_ids=reference.case_ids,
        reference=reference.labels,
        predictions=MappingProxyType({cid: records.labels[cid] for cid in reference.case_ids}),
        reference_source=reference.source_path,
        predictions_source=path.resolve(),
        skipped_lines=records.skipped,
        prediction_metadata=MappingProxyType(
            {cid: records.metadata[cid] for cid in reference.case_ids}),
    )
