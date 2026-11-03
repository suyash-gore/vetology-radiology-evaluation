"""Vetology Week 4 - Block 1: Canine Thorax data loading and validation.

This block deliberately does NOT call the OpenAI API. It establishes a clean,
validated separation between radiologist report text (LLM input) and Gold
Standard labels (evaluation-only reference).

Run:
    python week4_block1_data_loader.py \
        --input "1_canine_thorax_gold_standard_score_draft(1).xlsx" \
        --limit 100
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


# ---------------------------------------------------------------------------
# 1. Project configuration
# ---------------------------------------------------------------------------

DEFAULT_INPUT_FILE = "1_canine_thorax_gold_standard_score_draft.xlsx"
WORKSHEET_NAME = "Sheet1"
PILOT_CASE_LIMIT = 100

CASE_ID_COLUMN = "CaseID"
REPORT_COLUMNS = (
    "Findings (original radiologist report)",
    "Conclusions (original radiologist report)",
    "Recommendations (original radiologist report)",
)

# Keep this order aligned with the 20 condition columns in the Gold Standard
# workbook and the Week 2 confusion-matrix template.
CONDITION_COLUMNS = (
    "perihilar_infiltrate",
    "pneumonia",
    "bronchitis",
    "interstitial",
    "diseased_lungs",
    "hypo_plastic_trachea",
    "cardiomegaly",
    "pulmonary_nodules",
    "pleural_effusion",
    "rtm",
    "focal_caudodorsal_lung",
    "focal_perihilar",
    "pulmonary_hypoinflation",
    "right_sided_cardiomegaly",
    "pericardial_effusion",
    "bronchiectasis",
    "pulmonary_vessel_enlargement",
    "left_sided_cardiomegaly",
    "thoracic_lymphadenopathy",
    "esophagitis",
)

ALLOWED_LABELS = {"Positive", "Negative"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vetology_week4")


# ---------------------------------------------------------------------------
# 2. Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CaseReport:
    """Only these fields are eligible to be sent to the LLM."""

    case_id: Any
    findings: str
    conclusions: str
    recommendations: str

    def to_llm_payload(self) -> dict[str, str]:
        """Return report text only; never include Gold Standard labels."""
        return {
            "findings": self.findings,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
        }


@dataclass(frozen=True)
class LoadedDataset:
    """Report inputs and evaluation labels are stored separately."""

    cases: tuple[CaseReport, ...]
    gold_labels: dict[Any, dict[str, str]]


# ---------------------------------------------------------------------------
# 3. Excel loading and validation helpers
# ---------------------------------------------------------------------------

def _normalise_cell(value: Any) -> str:
    """Convert an Excel cell to clean text without inventing missing content."""
    if value is None:
        return ""
    return str(value).strip()


def _normalise_case_id(value: Any) -> Any:
    """Preserve numeric IDs as integers where Excel provides whole numbers."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _build_header_map(header_row: tuple[Any, ...]) -> dict[str, int]:
    header_map: dict[str, int] = {}
    for index, value in enumerate(header_row):
        if value is None:
            continue
        header = str(value).strip()
        if header in header_map:
            raise ValueError(f"Duplicate column header found: {header!r}")
        header_map[header] = index
    return header_map


def load_canine_thorax_dataset(
    input_path: str | Path,
    limit: int = PILOT_CASE_LIMIT,
    worksheet_name: str = WORKSHEET_NAME,
) -> LoadedDataset:
    """Load the first `limit` populated cases and validate Gold Standard labels.

    Important separation:
      * `cases` contains CaseID and the three ORIGINAL radiologist report fields.
      * `gold_labels` contains the 20 authoritative reference labels and is for
        evaluation only. It must never be included in an LLM request.

    AI-generated report columns and the Original Radiologist field are
    intentionally ignored by this loader.
    """
    path = Path(input_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input workbook not found: {path}")
    if limit < 1:
        raise ValueError("The case limit must be at least 1.")

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

        header_map = _build_header_map(header_row)
        required_columns = (CASE_ID_COLUMN, *REPORT_COLUMNS, *CONDITION_COLUMNS)
        missing_columns = [name for name in required_columns if name not in header_map]
        if missing_columns:
            raise ValueError(
                "Required workbook columns are missing: " + ", ".join(missing_columns)
            )

        cases: list[CaseReport] = []
        gold_labels: dict[Any, dict[str, str]] = {}
        seen_case_ids: set[Any] = set()

        for row in rows:
            raw_case_id = row[header_map[CASE_ID_COLUMN]]
            if raw_case_id is None or _normalise_cell(raw_case_id) == "":
                continue  # Ignore formatted but unpopulated Excel rows.

            case_id = _normalise_case_id(raw_case_id)
            if case_id in seen_case_ids:
                raise ValueError(f"Duplicate CaseID found: {case_id!r}")
            seen_case_ids.add(case_id)

            report_values = [
                _normalise_cell(row[header_map[column]]) for column in REPORT_COLUMNS
            ]
            labels: dict[str, str] = {}
            for condition in CONDITION_COLUMNS:
                label = _normalise_cell(row[header_map[condition]])
                if label not in ALLOWED_LABELS:
                    raise ValueError(
                        f"Invalid Gold Standard label for CaseID {case_id!r}, "
                        f"condition {condition!r}: {label!r}. "
                        f"Expected exactly 'Positive' or 'Negative'."
                    )
                labels[condition] = label

            cases.append(
                CaseReport(
                    case_id=case_id,
                    findings=report_values[0],
                    conclusions=report_values[1],
                    recommendations=report_values[2],
                )
            )
            gold_labels[case_id] = labels

            if len(cases) >= limit:
                break

        if not cases:
            raise ValueError("No populated cases with CaseID values were found.")

        if len(cases) < limit:
            logger.warning(
                "Requested %d cases, but only %d populated cases were found.",
                limit,
                len(cases),
            )

        if len(CONDITION_COLUMNS) != 20:
            raise AssertionError("The condition configuration must contain 20 labels.")

        logger.info("Workbook: %s", path.name)
        logger.info("Worksheet: %s", worksheet_name)
        logger.info("Cases loaded: %d", len(cases))
        logger.info("Conditions per case: %d", len(CONDITION_COLUMNS))
        logger.info("Gold Standard labels validated: %d", len(gold_labels) * 20)
        logger.info(
            "LLM input fields: CaseID for tracking + original Findings, Conclusions, Recommendations"
        )
        logger.info(
            "Excluded from LLM input: Original Radiologist, all AI report fields, and all Gold Standard labels"
        )

        return LoadedDataset(cases=tuple(cases), gold_labels=gold_labels)
    finally:
        workbook.close()


# ---------------------------------------------------------------------------
# 4. Command-line smoke test (no API call)
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and load the Vetology canine thorax pilot workbook."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_FILE,
        help=f"Path to the authoritative Gold Standard workbook (default: {DEFAULT_INPUT_FILE})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=PILOT_CASE_LIMIT,
        help="Maximum number of populated cases to load (default: 100).",
    )
    parser.add_argument(
        "--sheet",
        default=WORKSHEET_NAME,
        help=f"Worksheet name (default: {WORKSHEET_NAME}).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = load_canine_thorax_dataset(
        input_path=args.input,
        limit=args.limit,
        worksheet_name=args.sheet,
    )

    # Deliberately demonstrate the boundary: this is the only object that
    # should later be passed to the prompt-building / LLM function.
    first_case = dataset.cases[0]
    llm_payload = first_case.to_llm_payload()

    print("\nBLOCK 1 VALIDATION PASSED")
    print(f"Loaded cases: {len(dataset.cases)}")
    print(f"Conditions: {len(CONDITION_COLUMNS)}")
    print(f"First CaseID: {first_case.case_id}")
    print(f"First-case report fields prepared for LLM: {list(llm_payload.keys())}")
    print(
        "Gold Standard labels stored separately for evaluation: "
        f"{len(dataset.gold_labels)} cases"
    )
    print("No OpenAI API request was made.")


if __name__ == "__main__":
    main()
