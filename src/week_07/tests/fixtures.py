"""Synthetic workbooks and a temporary repository layout for offline Week 7 tests.

Contains NO real Vetology data. Adapted from ``src/week_05/tests/workbook_factory.py``
(not imported). Two schemas approximate the two real inputs:

* Matrix 1 (Vetology-scored): CaseID, original report fields,
  ``Original Radiologist``, AI-generated report fields, 20 condition columns.
* Matrix 2 (Gold Standard): AI-generated fields first, CaseID, 20 condition
  columns in reverse order, a legacy Abnormal/Normal column, then the original
  report fields in reverse order (columns are located by header name).

Every cell that must never reach the model contains the ``LEAK`` marker.
``SyntheticRepo`` builds a throwaway ``data/`` + ``outputs/`` tree with its own
workflow specs and isolation policy, so nothing is written into the repository.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from week_07 import config
from week_07.conditions import CONDITION_KEYS
from week_07.dataset_loader import (
    CASE_ID_COLUMN,
    CONCLUSIONS_COLUMN,
    FINDINGS_COLUMN,
    RECOMMENDATIONS_COLUMN,
)
from week_07.isolation import IsolationPolicy

ORIGINAL_RADIOLOGIST = "Original Radiologist"
AI_COLUMNS = ("Findings (AI report)", "Conclusions (AI report)", "Recommendations (AI report)")
LEGACY_CLASS_COLUMN = "Abnormal/Normal"
LEAK_MARKER = "LEAK"

MATRIX1_HEADERS: tuple[str, ...] = (
    CASE_ID_COLUMN, FINDINGS_COLUMN, CONCLUSIONS_COLUMN, RECOMMENDATIONS_COLUMN,
    ORIGINAL_RADIOLOGIST, *AI_COLUMNS, *CONDITION_KEYS,
)
MATRIX2_HEADERS: tuple[str, ...] = (
    *AI_COLUMNS, CASE_ID_COLUMN, *reversed(CONDITION_KEYS), LEGACY_CLASS_COLUMN,
    RECOMMENDATIONS_COLUMN, CONCLUSIONS_COLUMN, FINDINGS_COLUMN,
)
_FINDINGS_ID = re.compile(r"^Synthetic findings for report (\d+)\.$")


def label_for(case_id: Any, index: int, variant: int = 0) -> str:
    """Deterministic, varied label pattern for a case/condition pair."""
    seed = case_id if isinstance(case_id, int) else len(str(case_id))
    return "Positive" if (seed * 7 + index * 3 + variant) % 5 == 0 else "Negative"


def default_row(case_id: Any, variant: int = 0) -> dict[str, Any]:
    row: dict[str, Any] = {
        CASE_ID_COLUMN: case_id,
        FINDINGS_COLUMN: f"Synthetic findings for report {case_id}.",
        CONCLUSIONS_COLUMN: f"Synthetic conclusions {case_id}",
        RECOMMENDATIONS_COLUMN: f"Synthetic recommendations {case_id}",
        ORIGINAL_RADIOLOGIST: f"{LEAK_MARKER}-radiologist-{case_id}",
        LEGACY_CLASS_COLUMN: f"{LEAK_MARKER}-Abnormal-{case_id}",
    }
    for column in AI_COLUMNS:
        row[column] = f"{LEAK_MARKER}-ai-{column}-{case_id}"
    for index, condition in enumerate(CONDITION_KEYS):
        row[condition] = label_for(case_id, index, variant)
    return row


def write_workbook(path: Path, headers: Sequence[Any],
                   rows: Iterable[dict[str, Any] | Sequence[Any] | None],
                   sheet_name: str = "Sheet1", extra_sheets: Sequence[str] = ()) -> Path:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        workbook.save(path)
    finally:
        workbook.close()
    return path


def make_workbook(path: Path, headers: Sequence[Any] = MATRIX1_HEADERS,
                  case_ids: Iterable[Any] = range(1, 101),
                  edit: Callable[[Any, dict[str, Any]], dict[str, Any] | None] | None = None,
                  variant: int = 0, **kwargs: Any) -> Path:
    rows = []
    for case_id in case_ids:
        row = default_row(case_id, variant)
        if edit is not None:
            row = edit(case_id, row)
        rows.append(row)
    return write_workbook(path, headers, rows, **kwargs)


def reference_labels(case_id: int, variant: int = 0) -> dict[str, str]:
    return {condition: label_for(case_id, index, variant)
            for index, condition in enumerate(CONDITION_KEYS)}


def case_from_payload(payload: dict[str, str]) -> int:
    """Recover the synthetic report number from the findings TEXT (never a CaseID field)."""
    match = _FINDINGS_ID.match(payload["findings"])
    if match is None:
        raise AssertionError(f"unexpected synthetic findings text: {payload['findings']!r}")
    return int(match.group(1))


class EchoClassifier:
    """Fake Gemini: answers with the reference labels of the report, with optional flips.

    ``flips`` maps report number -> conditions whose label is inverted, so the
    expected TP/FN/TN/FP are known exactly. Records every payload it receives.
    """

    def __init__(self, variant: int = 0, flips: dict[int, Sequence[str]] | None = None) -> None:
        self.variant = variant
        self.flips = {k: set(v) for k, v in (flips or {}).items()}
        self.calls: list[dict[str, str]] = []

    def __call__(self, payload: dict[str, str]) -> str:
        self.calls.append(dict(payload))
        report = case_from_payload(payload)
        labels = reference_labels(report, self.variant)
        for condition in self.flips.get(report, ()):
            labels[condition] = "Negative" if labels[condition] == "Positive" else "Positive"
        return json.dumps(labels)


class SyntheticRepo:
    """Temporary repository-like tree with Week 7 specs and an isolation policy."""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="week07_synthetic_")).resolve()
        self.inputs = self.root / "data" / "week_04_inputs"
        out = self.root / "outputs"
        self.week7 = out / "week_07"
        self.week5 = out / "week_05"
        self.m1 = replace(config.MATRIX1, input_dir=self.inputs,
                          output_dir=self.week7 / "matrix_1",
                          comparison_dir=self.week7 / "comparison" / "matrix_1",
                          week5_output_dir=self.week5 / "matrix_1")
        self.m2 = replace(config.MATRIX2, input_dir=self.inputs,
                          output_dir=self.week7 / "matrix_2",
                          comparison_dir=self.week7 / "comparison" / "matrix_2",
                          week5_output_dir=self.week5 / "matrix_2")
        self.policy = IsolationPolicy(
            output_root=self.week7,
            protected_roots=(out / "week_04", self.week5, self.root / "data", self.root / "src"),
            workflows={"matrix1": self.m1, "matrix2": self.m2},
        )

    def spec(self, name: str):
        return {"matrix1": self.m1, "matrix2": self.m2}[name]

    def write_inputs(self, m1_cases: Iterable[Any] = range(1, 101),
                     m2_cases: Iterable[Any] = range(1, 101)) -> None:
        """Matrix 1 and Matrix 2 inputs with DIFFERENT labels (variant 0 vs 1)."""
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, m1_cases, variant=0)
        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, m2_cases, variant=1)

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def all_output_text(self) -> str:
        """Concatenated text of every JSON/JSONL file under outputs/week_07."""
        texts = []
        for path in sorted(self.week7.rglob("*")):
            if path.is_file() and path.suffix in (".json", ".jsonl"):
                texts.append(path.read_text(encoding="utf-8"))
        return "\n".join(texts)


# ---------------------------------------------------------------------------
# Comparison fixtures (Phase 4): two synthetic "models" with known disagreements
# ---------------------------------------------------------------------------

# Synthetic Week 5 "OpenAI" and Week 7 "Gemini" flips (report number -> conditions).
OPENAI_FLIPS: dict[int, tuple[str, ...]] = {
    1: ("pneumonia", "rtm"), 2: ("cardiomegaly",), 10: ("esophagitis",),
    55: ("bronchitis", "interstitial"),
}
GEMINI_FLIPS: dict[int, tuple[str, ...]] = {
    1: ("pneumonia",), 3: ("cardiomegaly", "rtm"), 10: ("esophagitis",),
    77: ("pleural_effusion",),
}


def predicted_labels(case_id: int, variant: int, flips: dict[int, Sequence[str]]
                     ) -> dict[str, str]:
    labels = reference_labels(case_id, variant)
    for condition in flips.get(case_id, ()):
        labels[condition] = "Negative" if labels[condition] == "Positive" else "Positive"
    return labels


def write_week5_openai(repo: SyntheticRepo, name: str, variant: int,
                       flips: dict[int, Sequence[str]] = OPENAI_FLIPS,
                       case_ids: Iterable[int] = range(1, 101),
                       error_case_ids: Iterable[int] = (),
                       extra_lines: Sequence[str] = ()) -> Path:
    """Week 5-format OpenAI predictions (+ optional errors.jsonl) in the temporary Week 5 tree.

    Simulates pre-existing Week 5 artifacts: written directly by the test, never by
    Week 7 code (which refuses to write there). No run manifest is created.
    """
    from week_07.jsonl_store import failure_record, success_record
    from week_07.tests.gemini_fakes import StepClock

    spec = repo.spec(name)
    spec.week5_output_dir.mkdir(parents=True, exist_ok=True)
    clock = StepClock()
    lines = [json.dumps(success_record(cid, 1, predicted_labels(cid, variant, flips), clock),
                        ensure_ascii=False) for cid in case_ids]
    lines.extend(extra_lines)
    path = spec.week5_predictions_path
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    errors = [json.dumps(failure_record(cid, 2, "ResponseValidationError: synthetic", clock))
              for cid in error_case_ids]
    if errors:
        spec.week5_errors_path.write_text("\n".join(errors) + "\n", encoding="utf-8")
    return path


def run_week7_gemini(repo: SyntheticRepo, name: str, variant: int,
                     flips: dict[int, Sequence[str]] = GEMINI_FLIPS, **kwargs: Any) -> Path:
    """Week 7 predictions + run manifest produced by the real batch with a fake model."""
    from week_07.batch_runner import run_workflow_batch
    from week_07.config import GeminiModelConfig
    from week_07.tests.gemini_fakes import RecordingSleep, StepClock

    run_workflow_batch(repo.spec(name), classifier=EchoClassifier(variant, flips),
                       settings=GeminiModelConfig(), isolation=repo.policy,
                       clock=StepClock(), sleep=RecordingSleep(), **kwargs)
    return repo.spec(name).predictions_path
