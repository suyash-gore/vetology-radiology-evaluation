"""Reference-label loading for EVALUATION, kept independent per workflow.

Each workflow has its own evaluation reference loader, registered in
``REFERENCE_LOADERS``; ``load_reference_for_evaluation`` dispatches to it.

* Matrix 1 — ``load_matrix1_reference`` (below), a reproduction of Week 4's
  ``load_matrix1_inputs``. This is the only Week 4 evaluation loader that
  exists in the repository.
* Matrix 2 — ``load_matrix2_reference`` (approved decision D3, after
  inspecting A2 and A6): the Week 4 Matrix 2 batch loader rules, guarded so
  that any workbook on which the alternative (Matrix 1-style) rules would give
  a different result is rejected as ambiguous. The original Matrix 2 evaluator
  is not in the repository; the Matrix 1 rules are never applied silently.

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


class AmbiguousReferenceError(ReferenceLoadError):
    """The two candidate loading approaches disagree on a workbook (Matrix 2 guardrail)."""


def _loader_differences(spec: WorkflowSpec, path: str | Path) -> tuple[list[str], Any]:
    """Compare the Phase 3 batch loader with the Week 4 evaluator-style rules.

    Batch loader: ``Sheet1``, first ``case_limit`` populated rows, trimmed labels.
    Week 4 evaluator-style rules (``load_matrix1_reference``): first worksheet,
    all rows, ``int()`` CaseIDs, no trimming. Returns the differences (empty when
    both select the same cases, in the same order, with the same labels) and the
    batch loader's dataset (``None`` if it failed). Failures are reported as
    differences, not raised.
    """
    from week_05.dataset_loader import load_dataset

    differences: list[str] = []
    try:
        batch = load_dataset(spec, path)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        batch = None
        differences.append(f"Phase 3 batch loader failed: {type(exc).__name__}: {exc}")
    try:
        evaluation = load_matrix1_reference(path)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        evaluation = None
        differences.append(f"Evaluation loader failed: {type(exc).__name__}: {exc}")
    if batch is None or evaluation is None:
        return differences, batch

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
    return differences, batch


def load_matrix2_reference(path: str | Path) -> EvaluationReference:
    """Matrix 2 evaluation reference labels (approved decision D3).

    Uses the Week 4 Matrix 2 batch loader behaviour — the only Week 4 code known
    to have read the Gold Standard workbook: worksheet ``Sheet1``, the first 100
    populated rows, labels trimmed (Phase 3 ``dataset_loader`` with MATRIX2).

    Guardrail: the inspected baseline (A2/A6) could not distinguish this from the
    Week 4 evaluator-style rules (first sheet, all rows, ``int()`` CaseIDs, no
    trimming), because on A2 both select CaseIDs 1-100 with identical labels. If
    the two approaches produce ANY difference on a workbook — extra populated
    rows, padded labels, non-integer CaseIDs, a different first sheet, either
    approach failing — the workbook is rejected as ambiguous rather than one
    result being chosen silently.
    """
    from week_05.config import MATRIX2

    differences, batch = _loader_differences(MATRIX2, path)
    if differences:
        listed = "\n  - ".join(differences[:20])
        raise AmbiguousReferenceError(
            "Matrix 2 reference workbook is ambiguous: the Week 4 Matrix 2 batch loader rules "
            "and the alternative Week 4 evaluator-style rules give different results, and the "
            f"baseline does not establish which applies. Differences:\n  - {listed}"
        )
    return EvaluationReference(
        source_path=batch.source_path,
        worksheet_name=batch.worksheet_name,
        case_ids=tuple(batch.case_ids),
        labels=batch.reference_labels,
    )


# One evaluation reference loader per workflow (independent rules).
REFERENCE_LOADERS: Mapping[str, ReferenceLoader] = MappingProxyType({
    "matrix1": load_matrix1_reference,
    "matrix2": load_matrix2_reference,
})


def reference_loader_for(spec: WorkflowSpec) -> ReferenceLoader:
    """Return the workflow's own evaluation reference loader, or raise if none exists."""
    try:
        return REFERENCE_LOADERS[spec.name]
    except KeyError:
        raise ReferenceLoadingPending(
            f"No evaluation reference loader has been established for {spec.name!r}."
        ) from None


def load_reference_for_evaluation(spec: WorkflowSpec, path: str | Path) -> EvaluationReference:
    """Load reference labels for evaluation with the workflow's own rules."""
    return reference_loader_for(spec)(path)


def compare_reference_loaders(spec: WorkflowSpec, path: str | Path) -> list[str]:
    """Differences between the batch loader and the Week 4 evaluator-style rules.

    For Matrix 1 the evaluator-style rules ARE its evaluation loader; for Matrix 2
    they are the alternative checked by the ambiguity guardrail, so an empty list
    means the Matrix 2 loader will accept the workbook.
    """
    reference_loader_for(spec)  # raises for a workflow without a loader
    differences, _ = _loader_differences(spec, path)
    return differences
