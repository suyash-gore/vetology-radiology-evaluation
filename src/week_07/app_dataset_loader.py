"""Application-aware workbook loading: report input and reference labels kept apart.

The loading rules are exactly those of ``dataset_loader`` (verbatim Week 5 copy,
still used unchanged for Canine Thorax); this module supplies the application's
condition columns and reference-label normalisation:

* header row 1, stripped; blank headers ignored; duplicate headers rejected;
  columns located by name; required: ``CaseID``, the three ORIGINAL radiologist
  report columns and the application's condition columns. Nothing else
  (Original Radiologist, AI-generated report fields, ...) is ever read.
* rows in worksheet order; rows with an empty/whitespace CaseID are skipped and
  do not count; whole-number float CaseIDs become ``int``; duplicates rejected.
* report text: ``None`` -> ``""``, otherwise ``str(value).strip()``.
* labels: ``str(value).strip()``, then — only for the columns the application
  declares for this workflow (Feline Thorax Matrix 1: ``pulmonary_nodules``,
  ``esophagitis``, ``pneumonia``) — ``Normal`` -> ``Negative`` and
  ``Abnormal`` -> ``Positive``; then the value must be exactly ``Positive`` or
  ``Negative``. Any other value, in any column, is an error.
* loading stops after ``limit`` cases; Matrix 1 requires exactly ``limit``.

``ApplicationDataset.cases`` (``ReportCase``: CaseID + the three report fields)
is the only object that may reach a classifier; ``to_llm_payload()`` returns
exactly findings, conclusions and recommendations. Reference labels are held
separately and read-only and never appear in ``repr``.

``check_cross_matrix`` proves that an application's Matrix 1 and Matrix 2
workbooks describe the same cases (same unique CaseIDs, in the same order, with
identical report payloads) so that ONE prediction run can serve both reference
tracks. Labels are never compared, merged or substituted.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from openpyxl import load_workbook

from week_07.applications import ApplicationSpec, LabelNormalization
from week_07.conditions import VALID_LABELS
from week_07.config import WorkflowSpec
from week_07.dataset_loader import (
    CASE_ID_COLUMN,
    REPORT_COLUMNS,
    CaseId,
    DatasetError,
    ReportCase,
    _cell,
    _validate_limit,
    build_header_map,
    is_blank_case_id,
    normalise_case_id,
    normalise_text,
)

logger = logging.getLogger("week_07.app_dataset_loader")

__all__ = ["ApplicationDataset", "CrossMatrixCheck", "DatasetError", "ReportCase",
           "check_cross_matrix", "load_application_dataset", "required_columns"]


@dataclass(frozen=True)
class ApplicationDataset:
    """Report cases and reference labels of one application workflow, held separately."""

    application: str
    workflow: str
    reference_description: str
    source_path: Path
    worksheet_name: str
    condition_keys: tuple[str, ...]
    cases: tuple[ReportCase, ...]
    reference_labels: Mapping[CaseId, Mapping[str, str]]
    normalized_label_counts: Mapping[str, Mapping[str, int]]

    @property
    def case_ids(self) -> tuple[CaseId, ...]:
        return tuple(case.case_id for case in self.cases)

    def __repr__(self) -> str:  # keep labels and report text out of logs and tracebacks
        return (f"ApplicationDataset(application={self.application!r}, "
                f"workflow={self.workflow!r}, cases={len(self.cases)}, "
                f"reference_labels={len(self.reference_labels)} cases x "
                f"{len(self.condition_keys)}, source={self.source_path.name!r})")


def required_columns(app: ApplicationSpec) -> tuple[str, ...]:
    return (CASE_ID_COLUMN, *REPORT_COLUMNS, *app.condition_keys)


def resolve_spec(app: ApplicationSpec, workflow: str | WorkflowSpec) -> WorkflowSpec:
    """The application's own spec for a workflow; refuses a spec of another application."""
    if not isinstance(app, ApplicationSpec):
        raise TypeError("app must be an ApplicationSpec.")
    if isinstance(workflow, WorkflowSpec):
        spec = workflow
        if spec.application != app.key or app.workflow(spec.name) != spec:
            raise DatasetError(
                f"Workflow spec {spec.qualified_name!r} is not a workflow of {app.key!r}."
            )
        return spec
    if not isinstance(workflow, str):
        raise TypeError("workflow must be a workflow name or a WorkflowSpec.")
    return app.workflow(workflow)


def _iter_selected_rows(
    rows: Iterator[Sequence[Any]],
    header_map: Mapping[str, int],
    app: ApplicationSpec,
    spec: WorkflowSpec,
    normalization: LabelNormalization,
    limit: int,
    normalized: dict[str, dict[str, int]],
) -> Iterator[tuple[ReportCase, dict[str, str]]]:
    seen_ids: set[CaseId] = set()
    selected = 0
    case_index = header_map[CASE_ID_COLUMN]
    report_index = [header_map[column] for column in REPORT_COLUMNS]
    label_index = [(condition, header_map[condition]) for condition in app.condition_keys]
    label = f"{spec.qualified_name}"

    for row in rows:
        raw_id = _cell(row, case_index)
        if is_blank_case_id(raw_id):
            continue  # formatted but unpopulated Excel row

        case_id = normalise_case_id(raw_id)
        if case_id in seen_ids:
            raise DatasetError(f"{label}: duplicate CaseID found: {case_id!r}")
        seen_ids.add(case_id)

        findings, conclusions, recommendations = (
            normalise_text(_cell(row, index)) for index in report_index
        )

        labels: dict[str, str] = {}
        for condition, index in label_index:
            value = normalise_text(_cell(row, index))
            mapping = normalization.get(condition)
            if mapping is not None and value in mapping:
                normalized[condition][value] = normalized[condition].get(value, 0) + 1
                value = mapping[value]
            if value not in VALID_LABELS:
                raise DatasetError(
                    f"{label}: invalid reference label for CaseID {case_id!r}, "
                    f"condition {condition!r}: {value!r}. "
                    "Expected exactly 'Positive' or 'Negative'."
                )
            labels[condition] = value

        yield ReportCase(case_id, findings, conclusions, recommendations), labels

        selected += 1
        if selected >= limit:
            return


def load_application_dataset(
    app: ApplicationSpec,
    workflow: str | WorkflowSpec,
    input_path: str | Path | None = None,
    *,
    limit: int | None = None,
    worksheet_name: str | None = None,
) -> ApplicationDataset:
    """Load the first ``limit`` eligible cases of one application workflow's workbook."""
    spec = resolve_spec(app, workflow)
    limit = spec.case_limit if limit is None else limit
    worksheet_name = spec.worksheet_name if worksheet_name is None else worksheet_name
    _validate_limit(spec, limit)
    normalization = app.label_normalization(spec.name)

    path = Path(spec.default_input_path if input_path is None else input_path)
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{spec.qualified_name} input workbook not found: {path}")

    normalized: dict[str, dict[str, int]] = {condition: {} for condition in normalization}
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if worksheet_name not in workbook.sheetnames:
            raise DatasetError(
                f"Worksheet {worksheet_name!r} not found. "
                f"Available worksheets: {workbook.sheetnames}"
            )
        rows = workbook[worksheet_name].iter_rows(values_only=True)
        header_row = next(rows, None)
        if header_row is None:
            raise DatasetError("The selected worksheet is empty.")

        header_map = build_header_map(header_row)
        missing = [column for column in required_columns(app) if column not in header_map]
        if missing:
            raise DatasetError("Required workbook columns are missing: " + ", ".join(missing))

        cases: list[ReportCase] = []
        labels_by_case: dict[CaseId, Mapping[str, str]] = {}
        for case, labels in _iter_selected_rows(rows, header_map, app, spec, normalization,
                                                limit, normalized):
            cases.append(case)
            labels_by_case[case.case_id] = MappingProxyType(labels)
    finally:
        workbook.close()

    if not cases:
        raise DatasetError(
            f"{spec.qualified_name}: no populated cases with CaseID values were found."
        )
    if len(cases) < limit:
        if spec.require_exact_case_count:
            raise DatasetError(
                f"{spec.qualified_name}: expected {limit} populated cases, but loaded "
                f"{len(cases)}."
            )
        logger.warning("%s: requested %d cases, but only %d populated cases were found.",
                       spec.qualified_name, limit, len(cases))

    logger.info("%s: workbook %s, worksheet %s", spec.qualified_name, path.name, worksheet_name)
    logger.info("%s: %d cases loaded; %d reference labels validated (%s)", spec.qualified_name,
                len(cases), len(cases) * app.condition_count, spec.reference_description)
    for condition, counts in normalized.items():
        logger.info("%s: reference column %s normalised %s", spec.qualified_name, condition,
                    ", ".join(f"{source}->{normalization[condition][source]} x{count}"
                              for source, count in sorted(counts.items())) or "nothing")

    return ApplicationDataset(
        application=app.key,
        workflow=spec.name,
        reference_description=spec.reference_description,
        source_path=path,
        worksheet_name=worksheet_name,
        condition_keys=app.condition_keys,
        cases=tuple(cases),
        reference_labels=MappingProxyType(labels_by_case),
        normalized_label_counts=MappingProxyType(
            {condition: MappingProxyType(counts) for condition, counts in normalized.items()}),
    )


@dataclass(frozen=True)
class CrossMatrixCheck:
    """Result of a successful Matrix 1 / Matrix 2 case-identity check (no labels)."""

    application: str
    matrix1_path: Path
    matrix2_path: Path
    case_ids: tuple[CaseId, ...]


def check_cross_matrix(
    app: ApplicationSpec,
    matrix1_path: str | Path | None = None,
    matrix2_path: str | Path | None = None,
) -> CrossMatrixCheck:
    """Require identical cases in both workbooks so one prediction run serves both.

    Both workbooks are loaded with their own workflow rules (Matrix 1: exactly
    100 cases; Matrix 2: first 100 populated cases). Then: same number of cases,
    same CaseIDs (unique by construction) in the same order, and identical
    findings/conclusions/recommendations per CaseID. Reference labels are not
    compared.
    """
    first = load_application_dataset(app, "matrix1", matrix1_path)
    second = load_application_dataset(app, "matrix2", matrix2_path)
    prefix = f"{app.key}: Matrix 1 and Matrix 2 workbooks"
    if len(first.cases) != len(second.cases):
        raise DatasetError(f"{prefix} have different case counts: {len(first.cases)} vs "
                           f"{len(second.cases)}.")
    ids1, ids2 = first.case_ids, second.case_ids
    if set(ids1) != set(ids2):
        raise DatasetError(
            f"{prefix} do not contain the same CaseIDs: "
            f"matrix1-only={sorted(set(ids1) - set(ids2), key=str)[:20]}; "
            f"matrix2-only={sorted(set(ids2) - set(ids1), key=str)[:20]}"
        )
    if ids1 != ids2:
        raise DatasetError(f"{prefix} list the same CaseIDs in a different order.")
    different = [a.case_id for a, b in zip(first.cases, second.cases)
                 if a.to_llm_payload() != b.to_llm_payload()]
    if different:
        raise DatasetError(
            f"{prefix} have different original report text for CaseIDs "
            f"{different[:20]}; the shared predictions cannot serve both reference tracks."
        )
    return CrossMatrixCheck(app.key, first.source_path, second.source_path, ids1)
