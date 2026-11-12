"""Workbook loading with strict separation of report input and reference labels.

One loader serves both workflows; the ``WorkflowSpec`` decides which dataset
it represents:

* Matrix 1 — ``Vetology_Matrix1_First100_Encoded.xlsx``; the 20 condition
  columns are the original Vetology scores.
* Matrix 2 — ``1_canine_thorax_gold_standard_score_draft.xlsx``; the 20
  condition columns are the Gold Standard scores.

Behaviour reproduced from the two Week 4 loaders (which share identical
cleaning and validation logic):

* Header row = first worksheet row; headers are stripped, blank headers are
  ignored, duplicate headers are rejected, columns are located by name.
* Required columns: ``CaseID``, the three original radiologist report columns
  and the 20 condition columns. Every other column (Original Radiologist,
  AI-generated report fields, Abnormal/Normal, ...) is never read.
* Rows are taken in worksheet order. A row whose CaseID is empty or
  whitespace is skipped and does not count towards the limit.
* Whole-number float CaseIDs become ``int``; other CaseID values are kept as
  read (strings are not stripped). Duplicate CaseIDs are rejected.
* Report text: ``None`` -> ``""``, otherwise ``str(value).strip()``.
* Labels: ``str(value).strip()`` must be exactly ``Positive`` or ``Negative``.
* Loading stops once ``limit`` cases are collected; later rows are not read
  or validated.

The two behaviours that differed between the Week 4 loaders are kept per
workflow through ``WorkflowSpec``:

* Limit range — Matrix 1: 1..100; Matrix 2: >= 1 (no upper cap).
* Fewer cases than the limit — Matrix 1 raises; Matrix 2 logs a warning
  (and raises only when no case is found).
"""
from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from openpyxl import load_workbook

from week_05.conditions import CONDITION_COUNT, CONDITION_KEYS, VALID_LABELS
from week_05.config import WorkflowSpec

logger = logging.getLogger("week_05.dataset_loader")

CASE_ID_COLUMN: Final[str] = "CaseID"
FINDINGS_COLUMN: Final[str] = "Findings (original radiologist report)"
CONCLUSIONS_COLUMN: Final[str] = "Conclusions (original radiologist report)"
RECOMMENDATIONS_COLUMN: Final[str] = "Recommendations (original radiologist report)"
REPORT_COLUMNS: Final[tuple[str, ...]] = (
    FINDINGS_COLUMN,
    CONCLUSIONS_COLUMN,
    RECOMMENDATIONS_COLUMN,
)
REQUIRED_COLUMNS: Final[tuple[str, ...]] = (CASE_ID_COLUMN, *REPORT_COLUMNS, *CONDITION_KEYS)

CaseId = Any  # int for whole-number Excel IDs; otherwise the value as read


class DatasetError(ValueError):
    """Raised when an input workbook violates the expected schema or content."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReportCase:
    """One case. Only the three original report fields are eligible for the LLM."""

    case_id: CaseId
    findings: str
    conclusions: str
    recommendations: str

    def to_llm_payload(self) -> dict[str, str]:
        """Return exactly the three original report fields — never CaseID or labels."""
        return {
            "findings": self.findings,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
        }


@dataclass(frozen=True)
class WorkflowDataset:
    """Report cases and reference labels, held in separate structures.

    ``cases`` is the only object that may be handed to a batch runner or
    classifier. ``reference_labels`` (CaseID -> condition -> label, canonical
    condition order) is for evaluation only and is read-only.
    """

    workflow: str
    reference_description: str
    source_path: Path
    worksheet_name: str
    cases: tuple[ReportCase, ...]
    reference_labels: Mapping[CaseId, Mapping[str, str]]

    @property
    def case_ids(self) -> tuple[CaseId, ...]:
        return tuple(case.case_id for case in self.cases)

    def __repr__(self) -> str:  # keep labels out of logs and tracebacks
        return (
            f"WorkflowDataset(workflow={self.workflow!r}, cases={len(self.cases)}, "
            f"reference_labels={len(self.reference_labels)} cases x {CONDITION_COUNT}, "
            f"source={self.source_path.name!r})"
        )


# ---------------------------------------------------------------------------
# Cleaning helpers (Week 4 semantics)
# ---------------------------------------------------------------------------

def normalise_text(value: Any) -> str:
    """Excel cell -> clean text, without inventing missing content."""
    return "" if value is None else str(value).strip()


def normalise_case_id(value: Any) -> CaseId:
    """Keep whole-number numeric IDs as integers; leave other values as read."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def is_blank_case_id(value: Any) -> bool:
    return value is None or normalise_text(value) == ""


def build_header_map(header_row: Sequence[Any]) -> dict[str, int]:
    """Map stripped header names to column positions; reject duplicates."""
    header_map: dict[str, int] = {}
    for index, value in enumerate(header_row):
        if value is None:
            continue
        header = str(value).strip()
        if header in header_map:
            raise DatasetError(f"Duplicate column header found: {header!r}")
        header_map[header] = index
    return header_map


def _cell(row: Sequence[Any], index: int) -> Any:
    """Return a cell value; a cell beyond the row's end is treated as empty."""
    return row[index] if index < len(row) else None


def _validate_limit(spec: WorkflowSpec, limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise DatasetError(f"The case limit must be an integer; received {limit!r}.")
    if spec.max_case_limit is not None and not 1 <= limit <= spec.max_case_limit:
        raise DatasetError(
            f"{spec.name}: limit must be between 1 and {spec.max_case_limit}; received {limit}."
        )
    if limit < 1:
        raise DatasetError(f"{spec.name}: the case limit must be at least 1; received {limit}.")


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _iter_selected_rows(
    rows: Iterator[Sequence[Any]],
    header_map: Mapping[str, int],
    spec: WorkflowSpec,
    limit: int,
) -> Iterator[tuple[ReportCase, dict[str, str]]]:
    seen_ids: set[CaseId] = set()
    selected = 0
    case_index = header_map[CASE_ID_COLUMN]
    report_index = [header_map[column] for column in REPORT_COLUMNS]
    label_index = [(condition, header_map[condition]) for condition in CONDITION_KEYS]

    for row in rows:
        raw_id = _cell(row, case_index)
        if is_blank_case_id(raw_id):
            continue  # formatted but unpopulated Excel row

        case_id = normalise_case_id(raw_id)
        if case_id in seen_ids:
            raise DatasetError(f"{spec.name}: duplicate CaseID found: {case_id!r}")
        seen_ids.add(case_id)

        findings, conclusions, recommendations = (
            normalise_text(_cell(row, index)) for index in report_index
        )

        labels: dict[str, str] = {}
        for condition, index in label_index:
            label = normalise_text(_cell(row, index))
            if label not in VALID_LABELS:
                raise DatasetError(
                    f"{spec.name}: invalid reference label for CaseID {case_id!r}, "
                    f"condition {condition!r}: {label!r}. "
                    "Expected exactly 'Positive' or 'Negative'."
                )
            labels[condition] = label

        yield ReportCase(case_id, findings, conclusions, recommendations), labels

        selected += 1
        if selected >= limit:
            return


def load_dataset(
    spec: WorkflowSpec,
    input_path: str | Path | None = None,
    *,
    limit: int | None = None,
    worksheet_name: str | None = None,
) -> WorkflowDataset:
    """Load the first ``limit`` eligible cases of a workflow's input workbook.

    ``input_path``, ``limit`` and ``worksheet_name`` default to the workflow's
    configuration, so the CLI can pass explicit values or rely on defaults.
    """
    limit = spec.case_limit if limit is None else limit
    worksheet_name = spec.worksheet_name if worksheet_name is None else worksheet_name
    _validate_limit(spec, limit)

    path = Path(spec.default_input_path if input_path is None else input_path)
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{spec.name} input workbook not found: {path}")

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
        missing = [column for column in REQUIRED_COLUMNS if column not in header_map]
        if missing:
            raise DatasetError("Required workbook columns are missing: " + ", ".join(missing))

        cases: list[ReportCase] = []
        labels_by_case: dict[CaseId, Mapping[str, str]] = {}
        for case, labels in _iter_selected_rows(rows, header_map, spec, limit):
            cases.append(case)
            labels_by_case[case.case_id] = MappingProxyType(labels)
    finally:
        workbook.close()

    if not cases:
        raise DatasetError(f"{spec.name}: no populated cases with CaseID values were found.")
    if len(cases) < limit:
        if spec.require_exact_case_count:
            raise DatasetError(
                f"{spec.name}: expected {limit} populated cases, but loaded {len(cases)}."
            )
        logger.warning(
            "%s: requested %d cases, but only %d populated cases were found.",
            spec.name, limit, len(cases),
        )

    logger.info("%s: workbook %s, worksheet %s", spec.name, path.name, worksheet_name)
    logger.info(
        "%s: %d cases loaded; %d reference labels validated (%s)",
        spec.name, len(cases), len(cases) * CONDITION_COUNT, spec.reference_description,
    )
    logger.info(
        "%s: LLM input limited to original Findings, Conclusions and Recommendations",
        spec.name,
    )

    return WorkflowDataset(
        workflow=spec.name,
        reference_description=spec.reference_description,
        source_path=path,
        worksheet_name=worksheet_name,
        cases=tuple(cases),
        reference_labels=MappingProxyType(labels_by_case),
    )
