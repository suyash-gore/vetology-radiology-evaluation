"""Matrix 2 evaluation workbook — structure of the DELIVERED baseline A6.

Structural reference: ``Evaluation Workbook v2.xlsx`` (A6), the delivered Week 4
Matrix 2 workbook. No Matrix 2 evaluator source exists in the repository; this
layout was reconstructed from A6 cell by cell (values, fonts, fills, borders,
alignment, widths, heights, merges, freeze panes, filters) and is independent of
the Matrix 1 layout.

Approved decisions applied:

* D2 — A6's "Balanced Accuracy" row is intentionally NOT reproduced: balanced
  accuracy is never computed. The Overall Summary is laid out exactly as in A6
  and that one row is then removed, so every other row keeps A6's content and
  formatting (shifted up by one row from row 8).
* D4 — no macro metrics (A6 has none).
* D5 — run-specific narrative (case counts, attempt notes, validation summary)
  is generated from the actual results; A6's exact wording is produced for A6's
  numbers.
* D6 — batch details (status, attempts, timestamps, successes, failures) come
  from the prediction records. The Execution Log states the failure-count
  source and that no errors.jsonl was supplied (column C of "Failed records";
  A6 has no text there).
* D8 — Case Predictions and the per-case log are sorted by CaseID.

Undefined metrics are blank cells (Week 4 rules, including the F1 edge case).
A6 formatting quirks are reproduced, e.g. the Overall Summary section styling on
the blank row before "Dataset / Scope".
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from week_05.conditions import CONDITION_COUNT, CONDITION_KEYS
from week_05.evaluation.metrics import ConfusionMetrics
from week_05.evaluation.reconcile import ReconciledLabels, sorted_case_ids
from week_05.jsonl_store import STATUS_SUCCESS

NAVY, PALE_BLUE, BAND, CASE_ID_FILL = "1F4E78", "D9EAF7", "F7FAFC", "F3F6F9"
MATCH_FILL, MISMATCH_FILL, WHITE, DARK_TEXT = "E2F0D9", "FCE4D6", "FFFFFF", "1F1F1F"
GRID = "D9E1F2"
PERCENT = "0.00%"

SUMMARY_TITLE = "VETOLOGY WEEK 4 - OVERALL EVALUATION SUMMARY"
DATASET_NAME = "Canine thorax Gold Standard pilot"
NOT_APPLICABLE = "N/A - no separate radiologist-agreement reference supplied"
NOT_CALCULATED = "Not calculated - separate radiologist-agreement reference not supplied"
FAILURE_COUNT_SOURCE = (
    "Source: prediction records only. No errors.jsonl was supplied, so failures recorded "
    "only in an errors file are not counted."
)
DEFAULT_GOLD_STANDARD_NAME = "Matrix 2 Gold Standard workbook"
DEFAULT_PREDICTIONS_NAME = "Matrix 2 predictions.jsonl"

# Row of A6's Overall Summary that holds "Balanced Accuracy" (removed, decision D2).
BALANCED_ACCURACY_ROW = 8

CONDITION_SUMMARY_HEADERS = [
    "Condition", "TP", "FN", "TN", "FP", "Total", "Positive Ground Truth",
    "Negative Ground Truth", "Accuracy", "Sensitivity", "Specificity", "Precision", "F1 Score",
]
CONFUSION_HEADERS = [
    "Condition", "True Positive", "False Negative", "True Negative", "False Positive",
    "Sensitivity", "Specificity", "Check", "Positive Ground Truth", "Negative Ground Truth",
    "Ground Truth Check", None, "Radiologist Agreement Rate", None,
]
LOG_HEADERS = ["CaseID", "Status", "Attempts", "Completed At (UTC)"]


# ---------------------------------------------------------------------------
# Style helpers (A6 values)
# ---------------------------------------------------------------------------

def _fill(colour: str) -> PatternFill:
    return PatternFill("solid", fgColor=colour)


THIN_BOTTOM = Border(bottom=Side(style="thin", color=GRID))
MEDIUM_BOTTOM = Border(bottom=Side(style="medium", color=NAVY))
MEDIUM_TOP = Border(top=Side(style="medium", color=NAVY))
HEADER_FONT = Font(bold=True, color=WHITE)
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
TOP_WRAP = Alignment(vertical="top", wrap_text=True)
CENTER_WRAP = Alignment(vertical="center", wrap_text=True)


def _style(cell, *, font=None, fill=None, alignment=None, border=None, number_format=None):
    if font is not None:
        cell.font = font
    if fill is not None:
        cell.fill = fill
    if alignment is not None:
        cell.alignment = alignment
    if border is not None:
        cell.border = border
    if number_format is not None:
        cell.number_format = number_format


def _widths(sheet, widths: list[float]) -> None:
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width


# ---------------------------------------------------------------------------
# Run-specific narrative (decision D5)
# ---------------------------------------------------------------------------

def _attempt_counts(labels: ReconciledLabels) -> Counter:
    return Counter(meta.attempts for meta in labels.prediction_metadata.values())


def _retry_rows(attempts: Counter) -> list[tuple[str, int]]:
    """One "Cases requiring k attempts" row per k >= 2 present (A6: k = 2)."""
    ks = sorted(k for k in attempts if isinstance(k, int) and k >= 2) or [2]
    return [(f"Cases requiring {k} attempts", attempts.get(k, 0)) for k in ks]


def _first_attempt_note(attempts: Counter, cases: int) -> str:
    first = attempts.get(1, 0)
    retried = cases - first
    if retried == 0:
        return "No case required a second application-level attempt."
    if retried == 1:
        if attempts.get(2, 0) == 1:
            return "One case required a second application-level attempt."
        return "One case required more than one application-level attempt."
    return f"{retried} cases required more than one application-level attempt."


def _failed_note(failed: int) -> str:
    if failed == 0:
        return "No final failed records in the completed batch."
    return f"{failed} final failed record(s) in the completed batch."


def _case_range(case_ids) -> str:
    ordered = sorted_case_ids(case_ids)
    if ordered and ordered == list(range(ordered[0], ordered[-1] + 1)):
        return f"CaseIDs {ordered[0]}–{ordered[-1]} matched."
    return f"{len(ordered)} CaseIDs matched."


def _validation_note(labels: ReconciledLabels) -> str:
    return (f"All {len(labels.predictions)} records successful; exact {CONDITION_COUNT} "
            "condition keys; valid Positive/Negative labels; " + _case_range(labels.case_ids))


# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------

def _overall_summary(wb: Workbook, labels: ReconciledLabels, micro: ConfusionMetrics) -> None:
    sheet = wb.active
    sheet.title = "Overall Summary"
    cases = len(labels.case_ids)
    attempts = _attempt_counts(labels)
    statuses = Counter(meta.status for meta in labels.prediction_metadata.values())
    failed = sum(n for status, n in statuses.items() if status != STATUS_SUCCESS)

    metric_rows = [
        ("Accuracy", micro.accuracy, "(TP + TN) / Total labels",
         "Overall proportion of labels matching the approved Gold Standard."),
        ("Sensitivity (Recall)", micro.sensitivity, "TP / (TP + FN)",
         "Proportion of Gold Standard Positive labels correctly identified."),
        ("Specificity", micro.specificity, "TN / (TN + FP)",
         "Proportion of Gold Standard Negative labels correctly identified."),
        ("Precision (Positive Predictive Value)", micro.precision, "TP / (TP + FP)",
         "Proportion of model Positive predictions that are Gold Standard Positive."),
        ("F1 Score", micro.f1, "2 × (Precision × Sensitivity) / (Precision + Sensitivity)",
         "Harmonic mean of precision and sensitivity."),
        (None, None, None, None),  # A6 "Balanced Accuracy" position — removed (D2)
    ]
    count_rows = [
        ("True Positives (TP)", micro.tp, "Gold Standard Positive and model Positive", None),
        ("False Negatives (FN)", micro.fn, "Gold Standard Positive and model Negative", None),
        ("True Negatives (TN)", micro.tn, "Gold Standard Negative and model Negative", None),
        ("False Positives (FP)", micro.fp, "Gold Standard Negative and model Positive", None),
        ("Total evaluated labels", micro.total, f"{cases} cases × {CONDITION_COUNT} conditions",
         None),
        ("Positive Gold Standard labels", micro.positive_gt, "TP + FN", None),
        ("Negative Gold Standard labels", micro.negative_gt, "TN + FP", None),
    ]
    scope_rows = [
        ("Cases evaluated", cases, f"All {cases} cases had successful validated predictions.",
         None),
        ("Conditions evaluated", CONDITION_COUNT,
         "Each condition independently evaluated as Positive or Negative.", None),
        ("Prediction records", len(labels.predictions),
         "One validated prediction record per case.", None),
        ("Failed prediction records", failed, _failed_note(failed), None),
        ("First-attempt completions", attempts.get(1, 0),
         _first_attempt_note(attempts, cases), None),
        *[(label, count, "Transport-level retries may be additional.", None)
          for label, count in _retry_rows(attempts)],
    ]
    note_rows = [
        ("Important interpretation note", "Pilot evaluation only",
         "High overall accuracy should be interpreted alongside class imbalance and "
         "sensitivity. Conditions with zero positive Gold Standard examples have undefined "
         "sensitivity.", None),
        ("Radiologist agreement", "Not calculated",
         "A separate radiologist-agreement reference dataset was not supplied. This is not the "
         "same as LLM-vs-Gold-Standard agreement.", None),
    ]
    blank = (None, None, None, None)

    sheet.append([SUMMARY_TITLE, None, None, None])
    sheet.append(["Metric", "Result", "Calculation / Definition", "Interpretation"])
    metric_start = sheet.max_row + 1
    for row in metric_rows:
        sheet.append(list(row))
    metric_end = sheet.max_row
    sheet.append(list(blank))
    counts_header = sheet.max_row + 1
    sheet.append(["Evaluation Counts", "Count", "Description", None])
    for row in count_rows:
        sheet.append(list(row))
    scope_gap = sheet.max_row + 1
    sheet.append(list(blank))
    sheet.append(["Dataset / Scope", "Value", "Notes", None])
    for row in scope_rows:
        sheet.append(list(row))
    sheet.append(list(blank))
    note_header = sheet.max_row + 1
    for row in note_rows:
        sheet.append(list(row))

    # Formatting (A6). Section styling falls on the counts header, on the blank
    # row before "Dataset / Scope" and on the interpretation-note row, as in A6.
    sheet.merge_cells("A1:D1")
    _style(sheet["A1"], font=Font(bold=True, color=WHITE, size=14), fill=_fill(NAVY),
           alignment=Alignment(horizontal="center", vertical="center"))
    for cell in sheet[2]:
        _style(cell, font=HEADER_FONT, fill=_fill(NAVY), alignment=HEADER_ALIGN,
               border=MEDIUM_BOTTOM)
    section_rows = {counts_header, scope_gap, note_header}
    for row in range(3, sheet.max_row + 1):
        for col in range(1, 5):
            cell = sheet.cell(row, col)
            if row in section_rows:
                _style(cell, font=Font(bold=True, color=NAVY), fill=_fill(PALE_BLUE),
                       alignment=TOP_WRAP, border=THIN_BOTTOM)
                continue
            is_metric = metric_start <= row <= metric_end
            _style(cell, fill=_fill(BAND) if row % 2 else None, alignment=TOP_WRAP,
                   border=THIN_BOTTOM)
            if is_metric and col == 1:
                cell.font = Font(bold=True)
            if is_metric and col == 2:
                cell.number_format = PERCENT
    sheet.row_dimensions[1].height = 30
    sheet.row_dimensions[2].height = 32
    sheet.freeze_panes = "A3"
    _widths(sheet, [34, 24, 62, 62])

    # Decision D2: remove the Balanced Accuracy position; later rows move up.
    assert BALANCED_ACCURACY_ROW == metric_end, "layout drifted from A6"
    sheet.delete_rows(BALANCED_ACCURACY_ROW)


def _condition_row(name: str, m: ConfusionMetrics) -> list:
    return [name, m.tp, m.fn, m.tn, m.fp, m.total, m.positive_gt, m.negative_gt,
            m.accuracy, m.sensitivity, m.specificity, m.precision, m.f1]


def _condition_summary(wb: Workbook, per_condition: Mapping[str, ConfusionMetrics],
                       micro: ConfusionMetrics) -> None:
    sheet = wb.create_sheet("Condition Summary")
    sheet.append(CONDITION_SUMMARY_HEADERS)
    for condition in CONDITION_KEYS:
        sheet.append(_condition_row(condition, per_condition[condition]))
    sheet.append(_condition_row("MICRO TOTAL", micro))
    _table_formatting(sheet, percent_columns=range(9, 14), total_font=Font(bold=True))
    _widths(sheet, [31, 10, 10, 10, 10, 12, 22, 22, 13, 14, 14, 13, 13])


def _confusion_row(name: str, m: ConfusionMetrics, agreement: str) -> list:
    return [name, m.tp, m.fn, m.tn, m.fp, m.sensitivity, m.specificity, m.total,
            m.positive_gt, m.negative_gt, m.positive_gt + m.negative_gt, None, agreement, None]


def _confusion_matrix(wb: Workbook, per_condition: Mapping[str, ConfusionMetrics],
                      micro: ConfusionMetrics) -> None:
    sheet = wb.create_sheet("Confusion Matrix")
    sheet.append(CONFUSION_HEADERS)
    for condition in CONDITION_KEYS:
        sheet.append(_confusion_row(condition, per_condition[condition], NOT_APPLICABLE))
    sheet.append(_confusion_row("TOTAL", micro, NOT_CALCULATED))
    _table_formatting(sheet, percent_columns=(6, 7),
                      total_font=Font(bold=True, color=DARK_TEXT))
    _widths(sheet, [31, 14, 16, 14, 16, 15, 15, 12, 22, 22, 20, 4, 58, 4])


def _table_formatting(sheet, *, percent_columns, total_font: Font) -> None:
    """Shared A6 table style: navy header, banded body, pale-blue total row."""
    percent = set(percent_columns)
    last = sheet.max_row
    for cell in sheet[1]:
        _style(cell, font=HEADER_FONT, fill=_fill(NAVY), alignment=HEADER_ALIGN,
               border=MEDIUM_BOTTOM)
    for row in range(2, last + 1):
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(row, col)
            if row == last:
                _style(cell, font=total_font, fill=_fill(PALE_BLUE), alignment=CENTER_WRAP,
                       border=MEDIUM_TOP)
            else:
                _style(cell, fill=_fill(BAND) if row % 2 == 0 else None,
                       alignment=CENTER_WRAP, border=THIN_BOTTOM)
            if col in percent:
                cell.number_format = PERCENT
    sheet.row_dimensions[1].height = 32
    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = sheet.dimensions


def _case_predictions(wb: Workbook, labels: ReconciledLabels) -> None:
    sheet = wb.create_sheet("Case Predictions")
    header = ["CaseID"]
    for condition in CONDITION_KEYS:
        header.extend([f"{condition} - Gold Standard", f"{condition} - Model Prediction",
                       f"{condition} - Agreement"])
    sheet.append(header)
    for case_id in sorted_case_ids(labels.case_ids):
        row: list[Any] = [case_id]
        for condition in CONDITION_KEYS:
            actual = labels.reference[case_id][condition]
            predicted = labels.predictions[case_id][condition]
            row.extend([actual, predicted, "Match" if actual == predicted else "Mismatch"])
        sheet.append(row)

    for cell in sheet[1]:
        _style(cell, font=Font(bold=True, color=WHITE, size=9), fill=_fill(NAVY),
               alignment=HEADER_ALIGN)
    for row in range(2, sheet.max_row + 1):
        _style(sheet.cell(row, 1), font=Font(bold=True), fill=_fill(CASE_ID_FILL))
        for col in range(4, sheet.max_column + 1, 3):
            cell = sheet.cell(row, col)
            colour = MATCH_FILL if cell.value == "Match" else MISMATCH_FILL
            _style(cell, fill=_fill(colour), alignment=Alignment(horizontal="center"))
    sheet.row_dimensions[1].height = 36
    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = sheet.dimensions
    _widths(sheet, [10] + [18, 18, 13] * len(CONDITION_KEYS))


def _execution_log(wb: Workbook, labels: ReconciledLabels, micro: ConfusionMetrics) -> None:
    sheet = wb.create_sheet("Execution Log")
    meta = labels.prediction_metadata
    attempts = _attempt_counts(labels)
    statuses = Counter(m.status for m in meta.values())
    successes = statuses.get(STATUS_SUCCESS, 0)
    failed = sum(n for status, n in statuses.items() if status != STATUS_SUCCESS)
    gold_name = (labels.reference_source.name if labels.reference_source
                 else DEFAULT_GOLD_STANDARD_NAME)
    pred_name = (labels.predictions_source.name if labels.predictions_source
                 else DEFAULT_PREDICTIONS_NAME)

    rows: list[list[Any]] = [
        ["Metric", "Value", None, None],
        ["Dataset", DATASET_NAME, None, None],
        ["Prediction file", pred_name, None, None],
        ["Gold Standard file", gold_name, None, None],
        ["Cases in Gold Standard", len(labels.reference), None, None],
        ["Prediction records", len(labels.predictions), None, None],
        ["Successful records", successes, None, None],
        ["Failed records", failed, FAILURE_COUNT_SOURCE, None],
        ["Unique CaseIDs", len(set(labels.case_ids)), None, None],
        ["Conditions per case", CONDITION_COUNT, None, None],
        ["Total evaluated labels", micro.total, None, None],
        ["First-attempt completions", attempts.get(1, 0), None, None],
        *[[label, count, None, None] for label, count in _retry_rows(attempts)],
        ["Overall label agreement", micro.accuracy, None, None],
        ["Evaluation note", "Agreement is not the same as clinical validity; interpret "
                            "per-condition metrics alongside support counts.", None, None],
        ["Radiologist agreement", "Not calculated: a separate radiologist-agreement reference "
                                  "was not provided.", None, None],
        ["Validation", _validation_note(labels), None, None],
    ]
    if labels.skipped_lines:
        rows.append(["Skipped prediction lines",
                     f"{len(labels.skipped_lines)} unreadable line(s) in the prediction file "
                     f"were skipped (listed below); all {len(labels.case_ids)} CaseIDs still "
                     "have exactly one valid successful prediction.", None, None])
        rows.extend(["Skipped prediction line", skipped.describe(), None, None]
                    for skipped in labels.skipped_lines)
    rows.append([None, None, None, None])
    rows.append(LOG_HEADERS)
    for case_id in sorted_case_ids(labels.case_ids):
        record = meta[case_id]
        rows.append([case_id, record.status, record.attempts, record.completed_at_utc])
    for row in rows:
        sheet.append(row)

    for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, max_col=4):
        for cell in row:
            _style(cell, alignment=TOP_WRAP, border=THIN_BOTTOM)
            if cell.row == 1:
                _style(cell, font=HEADER_FONT, fill=_fill(NAVY))
    sheet.freeze_panes = "A2"
    _widths(sheet, [34, 100, 14, 34])


def build_matrix2_workbook(
    labels: ReconciledLabels,
    per_condition: Mapping[str, ConfusionMetrics],
    micro: ConfusionMetrics,
    output_path: str | Path,
) -> Path:
    """Write the Matrix 2 evaluation workbook and return its path."""
    if labels.workflow != "matrix2":
        raise ValueError(f"The Matrix 2 workbook cannot be built for {labels.workflow!r}.")
    wb = Workbook()
    _overall_summary(wb, labels, micro)
    _condition_summary(wb, per_condition, micro)
    _case_predictions(wb, labels)
    _confusion_matrix(wb, per_condition, micro)
    _execution_log(wb, labels, micro)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destination)
    return destination
