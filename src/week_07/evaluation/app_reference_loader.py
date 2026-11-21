"""Application-aware reference-label loading for EVALUATION.

The rules are those of ``reference_loader`` (verbatim Week 5 copy, still used
unchanged for Canine Thorax), parameterised by the application's condition
columns and its per-workflow reference-label normalisation:

* Matrix 1 — Week 4 evaluator rules (``load_matrix1_inputs``): FIRST worksheet;
  headers taken as-is; first occurrence of a header; only ``CaseID`` and the
  condition columns required; ALL rows read; rows with a ``None`` CaseID
  skipped; ``int()`` CaseIDs; duplicates rejected; labels must be exactly
  ``Positive``/``Negative`` with NO trimming. Feline Thorax Matrix 1 maps the
  exact values ``Normal``/``Abnormal`` of its three declared columns first.
* Matrix 2 — the batch-loader rules (``Sheet1``, first 100 populated rows,
  trimmed labels) guarded by the ambiguity check: if the Week 4
  evaluator-style rules would give ANY different result (cases, order, labels,
  worksheet, failure), the workbook is rejected instead of one result being
  chosen silently. Matrix 2 labels are never normalised.

Reference labels are returned in an ``EvaluationReference`` (the verbatim
type); they are never passed to a batch runner or classifier.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from openpyxl import load_workbook

from week_07.app_dataset_loader import load_application_dataset, resolve_spec
from week_07.applications import ApplicationSpec
from week_07.conditions import VALID_LABELS
from week_07.config import WorkflowSpec
from week_07.evaluation.reference_loader import (
    CASE_ID_COLUMN,
    AmbiguousReferenceError,
    EvaluationReference,
    ReferenceLoadError,
    to_week4_case_id,
)

__all__ = ["AmbiguousReferenceError", "EvaluationReference", "ReferenceLoadError",
           "compare_application_reference_loaders", "load_application_reference",
           "load_matrix1_style_reference"]


def load_matrix1_style_reference(app: ApplicationSpec, workflow: str | WorkflowSpec,
                                 path: str | Path) -> EvaluationReference:
    """Week 4 evaluator rules for one application workflow (normalisation per workflow)."""
    spec = resolve_spec(app, workflow)
    normalization = app.label_normalization(spec.name)
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Reference workbook not found: {source}")

    workbook = load_workbook(source, data_only=True, read_only=True)
    try:
        worksheet_name = workbook.sheetnames[0]
        rows = workbook[worksheet_name].iter_rows(values_only=True)
        headers = list(next(rows, None) or [])
        required = [CASE_ID_COLUMN, *app.condition_keys]
        missing = [name for name in required if name not in headers]
        if missing:
            raise ReferenceLoadError(f"Missing ground-truth columns: {missing}")
        positions = {name: headers.index(name) for name in required}

        labels: dict[int, Mapping[str, str]] = {}
        for row in rows:
            index = positions[CASE_ID_COLUMN]
            raw_id = row[index] if index < len(row) else None
            if raw_id is None:
                continue
            case_id = to_week4_case_id(raw_id)
            if case_id in labels:
                raise ReferenceLoadError(f"Duplicate ground-truth CaseID: {case_id}")
            case_labels: dict[str, str] = {}
            for condition in app.condition_keys:
                column = positions[condition]
                label = row[column] if column < len(row) else None
                mapping = normalization.get(condition)
                if mapping is not None and isinstance(label, str) and label in mapping:
                    label = mapping[label]
                if label not in VALID_LABELS:
                    raise ReferenceLoadError(
                        f"Invalid ground-truth label: CaseID={case_id}, {condition}={label}"
                    )
                case_labels[condition] = label
            labels[case_id] = MappingProxyType(case_labels)
    finally:
        workbook.close()

    return EvaluationReference(source_path=source, worksheet_name=worksheet_name,
                               case_ids=tuple(labels), labels=MappingProxyType(labels))


def _differences(app: ApplicationSpec, spec: WorkflowSpec,
                 path: str | Path) -> tuple[list[str], Any]:
    """Batch-loader rules vs Week 4 evaluator-style rules on one workbook."""
    differences: list[str] = []
    try:
        batch = load_application_dataset(app, spec, path)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        batch = None
        differences.append(f"Batch loader failed: {type(exc).__name__}: {exc}")
    try:
        evaluation = load_matrix1_style_reference(app, spec, path)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        evaluation = None
        differences.append(f"Evaluation loader failed: {type(exc).__name__}: {exc}")
    if batch is None or evaluation is None:
        return differences, batch

    if batch.worksheet_name != evaluation.worksheet_name:
        differences.append(f"Worksheet differs: batch={batch.worksheet_name!r}, "
                           f"evaluation (first sheet)={evaluation.worksheet_name!r}")
    raw_ids = list(batch.case_ids)
    converted: list[Any] = []
    for raw in raw_ids:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = raw
        if value != raw or type(value) is not type(raw):
            differences.append(f"CaseID {raw!r} is read as {value!r} by the evaluation loader")
        converted.append(value)
    if len(batch.cases) != len(evaluation.case_ids):
        differences.append(f"Case count differs: batch={len(batch.cases)}, "
                           f"evaluation={len(evaluation.case_ids)}")
    converted_set = set(converted)
    only_batch = [c for c in converted if c not in evaluation.labels]
    only_eval = [c for c in evaluation.case_ids if c not in converted_set]
    if only_batch:
        differences.append(f"CaseIDs only in the batch selection: {only_batch[:20]}")
    if only_eval:
        differences.append(f"CaseIDs only in the evaluation reference: {only_eval[:20]}")
    common = [c for c in converted if c in evaluation.labels]
    if [c for c in evaluation.case_ids if c in set(common)] != common:
        differences.append("Case order differs between the two loaders.")
    for raw, case_id in zip(raw_ids, converted):
        if case_id not in evaluation.labels:
            continue
        for condition in app.condition_keys:
            a = batch.reference_labels[raw][condition]
            b = evaluation.labels[case_id][condition]
            if a != b:
                differences.append(f"Label differs for CaseID {case_id}, {condition}: "
                                   f"batch={a!r}, evaluation={b!r}")
    return differences, batch


def compare_application_reference_loaders(app: ApplicationSpec, workflow: str | WorkflowSpec,
                                          path: str | Path) -> list[str]:
    """Differences between the batch loader and the evaluator-style rules (empty = agree)."""
    differences, _ = _differences(app, resolve_spec(app, workflow), path)
    return differences


def load_application_reference(app: ApplicationSpec, workflow: str | WorkflowSpec,
                               path: str | Path) -> EvaluationReference:
    """Reference labels for evaluating one application workflow, with its own rules."""
    spec = resolve_spec(app, workflow)
    if spec.name == "matrix1":
        return load_matrix1_style_reference(app, spec, path)
    if spec.name == "matrix2":
        differences, batch = _differences(app, spec, path)
        if differences:
            listed = "\n  - ".join(differences[:20])
            raise AmbiguousReferenceError(
                f"{spec.qualified_name} reference workbook is ambiguous: the batch-loader rules "
                "and the Week 4 evaluator-style rules give different results. "
                f"Differences:\n  - {listed}"
            )
        return EvaluationReference(source_path=batch.source_path,
                                   worksheet_name=batch.worksheet_name,
                                   case_ids=tuple(batch.case_ids),
                                   labels=batch.reference_labels)
    raise ReferenceLoadError(f"No evaluation reference rules for {spec.qualified_name!r}.")
