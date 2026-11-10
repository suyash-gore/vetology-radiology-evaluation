"""Reference-label loading for EVALUATION, kept independent per workflow.

Each workflow has its own evaluation reference loader, registered in
``REFERENCE_LOADERS``; ``load_reference_for_evaluation`` dispatches to it.

* Matrix 1 — ``load_matrix1_reference`` (below), a reproduction of Week 4's
  ``load_matrix1_inputs``. This is the only Week 4 evaluation loader that
  exists in the repository.
* Matrix 2 — PENDING. The original Week 4 Matrix 2 evaluator is not in the
  repository, so its reference-loading rules are unknown. They are not
  assumed to match Matrix 1; ``ReferenceLoadingPending`` is raised until
  ``1_canine_thorax_gold_standard_score_draft.xlsx`` (A2) and
  ``Evaluation Workbook v2.xlsx`` (A6) have been inspected and a Matrix 2
  loader is approved and registered.

These loaders are deliberately separate from the Phase 3 ``dataset_loader``
used for batch execution.

Matrix 1 rules (``load_matrix1_inputs`` in
``src/week_04/matrix_1/matrix1_evaluator.py``), reproduced exactly:

* the FIRST worksheet is used, whatever its name;
* headers are row 1, taken as-is (not stripped); a column is located at the
  first occurrence of its header; only ``CaseID`` and the 20 condition
  columns are required;
* ALL data rows are read (no case limit); a row whose CaseID cell is empty
  (``None``) is skipped;
* CaseIDs are converted with ``int()`` (``"3"`` -> 3, ``4.0`` -> 4, and —
  Week 4 quirk, preserved — ``5.7`` -> 5); a value ``int()`` rejects is an error;
* duplicate CaseIDs are errors;
* labels must be exactly ``Positive`` or ``Negative`` with NO whitespace
  trimming.

``compare_reference_loaders`` reports any difference between a workflow's
evaluation loader and the Phase 3 loader on the same workbook, so differences
are surfaced rather than silently normalised.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from openpyxl import load_workbook

from week_05.conditions import CONDITION_KEYS, VALID_LABELS
from week_05.config import WorkflowSpec

CASE_ID_COLUMN = "CaseID"


class ReferenceLoadError(ValueError):
    """Raised when a reference workbook cannot be used for evaluation."""


class ReferenceLoadingPending(NotImplementedError):
    """The workflow's original evaluation reference-loading rules are not yet established."""


@dataclass(frozen=True)
class EvaluationReference:
    source_path: Path
    worksheet_name: str
    case_ids: tuple[int, ...]                        # worksheet order
    labels: Mapping[int, Mapping[str, str]]

    def __repr__(self) -> str:
        return (f"EvaluationReference(source={self.source_path.name!r}, "
                f"worksheet={self.worksheet_name!r}, cases={len(self.case_ids)})")


def to_week4_case_id(value: Any) -> int:
    """Week 4 evaluator CaseID conversion: ``int(value)``."""
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ReferenceLoadError(f"CaseID {value!r} cannot be converted to an integer: {exc}") \
            from exc


def load_matrix1_reference(path: str | Path) -> EvaluationReference:
    """Load reference labels for evaluation with the Week 4 evaluator's rules."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Reference workbook not found: {source}")

    workbook = load_workbook(source, data_only=True, read_only=True)
    try:
        worksheet_name = workbook.sheetnames[0]
        sheet = workbook[worksheet_name]
        rows = sheet.iter_rows(values_only=True)
        headers = list(next(rows, None) or [])
        required = [CASE_ID_COLUMN, *CONDITION_KEYS]
        missing = [name for name in required if name not in headers]
        if missing:
            raise ReferenceLoadError(f"Missing ground-truth columns: {missing}")
        positions = {name: headers.index(name) for name in required}

        labels: dict[int, Mapping[str, str]] = {}
        for row in rows:
            raw_id = row[positions[CASE_ID_COLUMN]] if positions[CASE_ID_COLUMN] < len(row) \
                else None
            if raw_id is None:
                continue
            case_id = to_week4_case_id(raw_id)
            if case_id in labels:
                raise ReferenceLoadError(f"Duplicate ground-truth CaseID: {case_id}")
            case_labels: dict[str, str] = {}
            for condition in CONDITION_KEYS:
                index = positions[condition]
                label = row[index] if index < len(row) else None
                if label not in VALID_LABELS:
                    raise ReferenceLoadError(
                        f"Invalid ground-truth label: CaseID={case_id}, {condition}={label}"
                    )
                case_labels[condition] = label
            labels[case_id] = MappingProxyType(case_labels)
    finally:
        workbook.close()

    return EvaluationReference(
        source_path=source,
        worksheet_name=worksheet_name,
        case_ids=tuple(labels),
        labels=MappingProxyType(labels),
    )


ReferenceLoader = Callable[[str | Path], EvaluationReference]

# One evaluation reference loader per workflow. Matrix 2 is intentionally absent
# until its original Week 4 behaviour has been established from A2 and A6.
REFERENCE_LOADERS: Mapping[str, ReferenceLoader] = MappingProxyType({
    "matrix1": load_matrix1_reference,
})


def reference_loader_for(spec: WorkflowSpec) -> ReferenceLoader:
    """Return the workflow's own evaluation reference loader, or raise if pending."""
    try:
        return REFERENCE_LOADERS[spec.name]
    except KeyError:
        raise ReferenceLoadingPending(
            f"The {spec.name} evaluation reference-loading rules have not been established. "
            f"The original Week 4 {spec.name} evaluator is not in the repository, and the "
            "Matrix 1 rules are not assumed to apply. A loader will be defined after "
            f"'{spec.input_filename}' and '{spec.evaluation_workbook_filename}' have been "
            "inspected."
        ) from None


def load_reference_for_evaluation(spec: WorkflowSpec, path: str | Path) -> EvaluationReference:
    """Load reference labels for evaluation with the workflow's own rules."""
    return reference_loader_for(spec)(path)


def compare_reference_loaders(spec: WorkflowSpec, path: str | Path) -> list[str]:
    """Differences between the Phase 3 batch loader and the workflow's evaluation loader.

    An empty list means both loaders select the same cases (in the same order,
    after the evaluation loader's CaseID conversion) with the same labels. A
    loader that fails on the workbook is reported as a difference. A workflow
    whose evaluation loader is pending raises ``ReferenceLoadingPending``.
    """
    from week_05.dataset_loader import load_dataset

    evaluation_loader = reference_loader_for(spec)  # raises if pending
    differences: list[str] = []
    try:
        batch = load_dataset(spec, path)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        batch = None
        differences.append(f"Phase 3 batch loader failed: {type(exc).__name__}: {exc}")
    try:
        evaluation = evaluation_loader(path)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        evaluation = None
        differences.append(f"Evaluation loader failed: {type(exc).__name__}: {exc}")
    if batch is None or evaluation is None:
        return differences

    if batch.worksheet_name != evaluation.worksheet_name:
        differences.append(f"Worksheet differs: batch={batch.worksheet_name!r}, "
                           f"evaluation (first sheet)={evaluation.worksheet_name!r}")

    batch_raw_ids = list(batch.case_ids)
    converted: list[Any] = []
    for raw in batch_raw_ids:
        try:
            converted_id = int(raw)
        except (TypeError, ValueError):
            converted_id = raw
        if converted_id != raw or type(converted_id) is not type(raw):
            differences.append(f"CaseID {raw!r} is read as {converted_id!r} by the evaluation "
                               "loader")
        converted.append(converted_id)

    if len(batch.cases) != len(evaluation.case_ids):
        differences.append(f"Case count differs: batch={len(batch.cases)}, "
                           f"evaluation={len(evaluation.case_ids)}")
    only_batch = [c for c in converted if c not in evaluation.labels]
    only_eval = [c for c in evaluation.case_ids if c not in set(converted)]
    if only_batch:
        differences.append(f"CaseIDs only in the batch selection: {only_batch[:20]}")
    if only_eval:
        differences.append(f"CaseIDs only in the evaluation reference: {only_eval[:20]}")
    common = [c for c in converted if c in evaluation.labels]
    if [c for c in evaluation.case_ids if c in set(common)] != common:
        differences.append("Case order differs between the two loaders.")
    for raw, case_id in zip(batch_raw_ids, converted):
        if case_id not in evaluation.labels:
            continue
        for condition in CONDITION_KEYS:
            a = batch.reference_labels[raw][condition]
            b = evaluation.labels[case_id][condition]
            if a != b:
                differences.append(f"Label differs for CaseID {case_id}, {condition}: "
                                   f"batch={a!r}, evaluation={b!r}")
    return differences
