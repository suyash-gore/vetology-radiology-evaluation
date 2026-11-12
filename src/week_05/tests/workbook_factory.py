"""Synthetic workbooks for offline tests. Contains no real Vetology data.

Two schemas approximate the two real inputs described in Stage 1:

* Matrix 1 (original Vetology-scored): CaseID, original report fields,
  ``Original Radiologist``, AI-generated report fields, 20 condition columns.
* Matrix 2 (Gold Standard): CaseID, original report fields, AI-generated
  report fields, a legacy Abnormal/Normal column, 20 condition columns, in a
  different column order (columns are located by header name).

Every non-eligible cell contains a unique marker string so tests can prove
that none of it reaches an LLM payload.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from week_05.conditions import CONDITION_KEYS
from week_05.dataset_loader import (
    CASE_ID_COLUMN,
    CONCLUSIONS_COLUMN,
    FINDINGS_COLUMN,
    RECOMMENDATIONS_COLUMN,
)

ORIGINAL_RADIOLOGIST = "Original Radiologist"
AI_COLUMNS = ("Findings (AI report)", "Conclusions (AI report)", "Recommendations (AI report)")
LEGACY_CLASS_COLUMN = "Abnormal/Normal"

MATRIX1_HEADERS: tuple[str, ...] = (
    CASE_ID_COLUMN, FINDINGS_COLUMN, CONCLUSIONS_COLUMN, RECOMMENDATIONS_COLUMN,
    ORIGINAL_RADIOLOGIST, *AI_COLUMNS, *CONDITION_KEYS,
)
MATRIX2_HEADERS: tuple[str, ...] = (
    *AI_COLUMNS, CASE_ID_COLUMN, *reversed(CONDITION_KEYS), LEGACY_CLASS_COLUMN,
    RECOMMENDATIONS_COLUMN, CONCLUSIONS_COLUMN, FINDINGS_COLUMN,
)

LEAK_MARKER = "LEAK"


def label_for(case_id: Any, index: int) -> str:
    """Deterministic, varied label pattern for a case/condition pair."""
    seed = case_id if isinstance(case_id, int) else len(str(case_id))
    return "Positive" if (seed * 7 + index * 3) % 5 == 0 else "Negative"


def default_row(case_id: Any) -> dict[str, Any]:
    """Cell values for one case, keyed by header."""
    row: dict[str, Any] = {
        CASE_ID_COLUMN: case_id,
        FINDINGS_COLUMN: f"Original findings {case_id}",
        CONCLUSIONS_COLUMN: f"Original conclusions {case_id}",
        RECOMMENDATIONS_COLUMN: f"Original recommendations {case_id}",
        ORIGINAL_RADIOLOGIST: f"{LEAK_MARKER}-radiologist-{case_id}",
        LEGACY_CLASS_COLUMN: f"{LEAK_MARKER}-Abnormal-{case_id}",
    }
    for column in AI_COLUMNS:
        row[column] = f"{LEAK_MARKER}-ai-{column}-{case_id}"
    for index, condition in enumerate(CONDITION_KEYS):
        row[condition] = label_for(case_id, index)
    return row


def write_workbook(
    path: Path,
    headers: Sequence[Any],
    rows: Iterable[dict[str, Any] | Sequence[Any] | None],
    sheet_name: str = "Sheet1",
    extra_sheets: Sequence[str] = (),
) -> Path:
    """Write a workbook. A dict row is laid out by header; ``None`` is an empty row."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    for name in extra_sheets:
        workbook.create_sheet(name)
    sheet.append(list(headers))
    for row in rows:
        if row is None:
            sheet.append([None] * len(headers))
        elif isinstance(row, dict):
            sheet.append([row.get(header) for header in headers])
        else:
            sheet.append(list(row))
    try:
        workbook.save(path)
    finally:
        workbook.close()
    return path


def make_workbook(
    path: Path,
    headers: Sequence[Any] = MATRIX1_HEADERS,
    case_ids: Iterable[Any] = range(1, 101),
    edit: Callable[[Any, dict[str, Any]], dict[str, Any] | None] | None = None,
    **kwargs: Any,
) -> Path:
    """Write one row per case ID; ``edit`` may modify or drop (return None) a row."""
    rows = []
    for case_id in case_ids:
        row = default_row(case_id)
        if edit is not None:
            row = edit(case_id, row)
        rows.append(row)
    return write_workbook(path, headers, rows, **kwargs)
