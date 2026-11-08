"""Matrix 1 — Block 1: load the Vetology first-100 ground-truth workbook.

This loader keeps report text and evaluation labels separate. Only the three
original radiologist report fields are exposed through ``to_llm_payload()``.
AI-generated report fields and all 20 ground-truth labels are evaluation-only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS

WORKSHEET_NAME = "Sheet1"
CASE_LIMIT = 100
CASE_ID_COLUMN = "CaseID"
REPORT_COLUMNS = (
    "Findings (original radiologist report)",
    "Conclusions (original radiologist report)",
    "Recommendations (original radiologist report)",
)
ALLOWED_LABELS = {"Positive", "Negative"}


@dataclass(frozen=True)
class Matrix1Case:
    """One case; only original radiologist text is eligible for LLM input."""

    case_id: Any
    findings: str
    conclusions: str
    recommendations: str

    def to_llm_payload(self) -> dict[str, str]:
        """Return exactly the three original report fields; no ID or labels."""
        return {
            "findings": self.findings,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
        }


@dataclass(frozen=True)
class Matrix1Dataset:
    """LLM cases and ground truth stored in separate structures."""

    cases: tuple[Matrix1Case, ...]
    ground_truth: dict[Any, dict[str, str]]


def _normalise_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalise_case_id(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def load_matrix1_dataset(
    input_path: str | Path,
    worksheet_name: str = WORKSHEET_NAME,
    limit: int = CASE_LIMIT,
) -> Matrix1Dataset:
    """Load up to the first 100 populated cases and validate all 20 labels.

    The source workbook is expected to be the processed Matrix 1 workbook:
    first 100 records retained, condition labels encoded as Positive/Negative.
    Records are taken in worksheet order. Rows without CaseID are ignored.
    """
    if limit < 1 or limit > CASE_LIMIT:
        raise ValueError(f"limit must be between 1 and {CASE_LIMIT}.")

    path = Path(input_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Matrix 1 input workbook not found: {path}")

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if worksheet_name not in workbook.sheetnames:
            raise ValueError(
                f"Worksheet {worksheet_name!r} not found. "
                f"Available worksheets: {workbook.sheetnames}"
            )

        worksheet = workbook[worksheet_name]
        rows = worksheet.iter_rows(values_only=True)
        header_row = next(rows, None)
        if header_row is None:
            raise ValueError("The selected worksheet is empty.")

        header_map: dict[str, int] = {}
        for index, value in enumerate(header_row):
            if value is None:
                continue
            header = str(value).strip()
            if header in header_map:
                raise ValueError(f"Duplicate column header found: {header!r}")
            header_map[header] = index

        required = (CASE_ID_COLUMN, *REPORT_COLUMNS, *CONDITION_KEYS)
        missing = [column for column in required if column not in header_map]
        if missing:
            raise ValueError("Required columns are missing: " + ", ".join(missing))

        cases: list[Matrix1Case] = []
        ground_truth: dict[Any, dict[str, str]] = {}
        seen_ids: set[Any] = set()

        for row in rows:
            raw_id = row[header_map[CASE_ID_COLUMN]]
            if raw_id is None or _normalise_text(raw_id) == "":
                continue

            case_id = _normalise_case_id(raw_id)
            if case_id in seen_ids:
                raise ValueError(f"Duplicate CaseID found: {case_id!r}")
            seen_ids.add(case_id)

            report = [
                _normalise_text(row[header_map[column]])
                for column in REPORT_COLUMNS
            ]
            labels: dict[str, str] = {}
            for condition in CONDITION_KEYS:
                label = _normalise_text(row[header_map[condition]])
                if label not in ALLOWED_LABELS:
                    raise ValueError(
                        f"Invalid ground-truth label for CaseID {case_id!r}, "
                        f"condition {condition!r}: {label!r}. "
                        "Expected exactly 'Positive' or 'Negative'."
                    )
                labels[condition] = label

            cases.append(
                Matrix1Case(
                    case_id=case_id,
                    findings=report[0],
                    conclusions=report[1],
                    recommendations=report[2],
                )
            )
            ground_truth[case_id] = labels

            if len(cases) >= limit:
                break

        if len(cases) != limit:
            raise ValueError(
                f"Expected {limit} populated cases, but loaded {len(cases)}."
            )

        return Matrix1Dataset(
            cases=tuple(cases),
            ground_truth=ground_truth,
        )
    finally:
        workbook.close()
