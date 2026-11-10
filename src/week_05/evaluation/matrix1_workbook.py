"""Matrix 1 evaluation workbook — layout and wording of the DELIVERED baseline A5.

Parity target (approved decision D1): the delivered Week 4 Matrix 1 workbook
(``Evaluation_Workbook_v1.xlsx``, A5). A5 was produced by a variant of the Week 4
evaluator that is not in the repository; it differs from the committed
``matrix1_evaluator.py`` only in presentation — 10 wording changes, row-1 height
28 (code: 30), Overall Summary column C width 55 (code: 58) and a dark font
colour on the Overall Summary header row. All metric calculations are the Week 4
calculations (``metrics.py``) and are identical to the committed code.

Sheets, row text, column headers, number formats, fills, fonts, widths, freeze
panes and filters reproduce A5, including the existing wording that calls the
Matrix 1 reference labels "Gold Standard" / "GS" (terminology is preserved until
a change is explicitly approved).

Sheets (in order):
1. Overall Summary    — title, header, 17 metric rows (counts, micro, macro)
2. Condition Summary  — 20 conditions + TOTAL (micro) row
3. Case Predictions   — CaseID + (reference, prediction, Match/Mismatch) x 20
4. Confusion Matrix   — Week 2 template-derived columns (+ TOTAL row)
5. Execution Log      — inputs, reconciliation and run metadata
6. Metric Definitions — formulas and undefined-metric handling
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from week_05.conditions import CONDITION_KEYS
from week_05.evaluation.metrics import ConfusionMetrics, MacroMetrics
from week_05.evaluation.reconcile import ReconciledLabels, sorted_case_ids
from week_05.jsonl_store import Clock, utc_now

NAVY, PALE_BLUE, PALE_GREEN, PALE_RED = "1F4E78", "D9EAF7", "E2F0D9", "FCE4D6"
DARK_TEXT = "1F1F1F"          # A5: Overall Summary header-row font colour
HEADER_ROW_HEIGHT = 28        # A5 (committed Week 4 code: 30)
PERCENT = "0.00%"
SUMMARY_TITLE = "VETOLOGY MATRIX 1 - EVALUATION SUMMARY"

# Recorded verbatim from the delivered Week 4 Matrix 1 workbook (A5).
MODEL_RECORD = "gpt-4.1-mini (from Matrix 1 batch execution record)"
PROMPT_RECORD = "Canine Thorax Master Prompt V1.3"
DEFAULT_GROUND_TRUTH_NAME = "Matrix 1 encoded ground-truth workbook"
DEFAULT_PREDICTIONS_NAME = "Matrix 1 predictions.jsonl"

CONDITION_SUMMARY_HEADERS = [
    "Condition", "TP", "FN", "TN", "FP", "Total", "Positive Ground Truth",
    "Negative Ground Truth", "Accuracy", "Sensitivity", "Specificity", "Precision", "F1-score",
]
CONFUSION_HEADERS = [
    "Condition", "True Positive", "False Negative", "True Negative", "False Positive",
    "Sensitivity", "Specificity", "Check", "Positive Ground Truth", "Negative Ground Truth",
    "Accuracy", "Precision", "F1-score", "Total",
]
METRIC_DEFINITIONS = [
    ("TP", "Ground Truth = Positive and Model Prediction = Positive."),
    ("FN", "Ground Truth = Positive and Model Prediction = Negative."),
    ("TN", "Ground Truth = Negative and Model Prediction = Negative."),
    ("FP", "Ground Truth = Negative and Model Prediction = Positive."),
    ("Accuracy", "(TP + TN) / (TP + FN + TN + FP)."),
    ("Sensitivity / Recall",
     "TP / (TP + FN). Undefined when there are no Gold Standard Positive labels."),
    ("Specificity", "TN / (TN + FP). Undefined when there are no Gold Standard Negative labels."),
    ("Precision", "TP / (TP + FP). Undefined when the model makes no Positive predictions."),
    ("F1-score", "2 × Precision × Sensitivity / (Precision + Sensitivity). Undefined when "
                 "precision or sensitivity is undefined, or their sum is zero."),
    ("Micro average", "Metrics calculated after summing TP, FN, TN, and FP across all conditions."),
    ("Macro average", "Unweighted mean of the defined condition-level metric values. Undefined "
                      "condition-level values are excluded and not treated as zero."),
    ("Separation rule", "Matrix 1 results are not combined with Matrix 2 results."),
]


def _summary_rows(cases: int, micro: ConfusionMetrics, macro: MacroMetrics) -> list[tuple]:
    return [
        ("Cases evaluated", cases, "Unique matched CaseIDs",
         "Fresh 100-case Matrix 1 evaluation."),
        ("Conditions evaluated", len(CONDITION_KEYS), "Condition columns",
         "All 20 Matrix 1 conditions evaluated independently."),
        ("Total paired labels", micro.total, "Cases × conditions",
         "Each case-condition pair contributes one label comparison."),
        ("True Positive (TP)", micro.tp, "GS Positive; model Positive",
         "Correctly identified positive labels."),
        ("False Negative (FN)", micro.fn, "GS Positive; model Negative",
         "Positive labels missed by the model."),
        ("True Negative (TN)", micro.tn, "GS Negative; model Negative",
         "Correctly identified negative labels."),
        ("False Positive (FP)", micro.fp, "GS Negative; model Positive",
         "Negative labels incorrectly predicted positive."),
        ("Micro Accuracy", micro.accuracy, "(TP + TN) / all paired labels",
         "Overall agreement across all case-condition pairs."),
        ("Micro Sensitivity (Recall)", micro.sensitivity, "TP / (TP + FN)",
         "Recall across all Gold Standard Positive labels."),
        ("Micro Specificity", micro.specificity, "TN / (TN + FP)",
         "Correct rejection rate across all Gold Standard Negative labels."),
        ("Micro Precision", micro.precision, "TP / (TP + FP)",
         "Proportion of model-positive labels that are Gold Standard Positive."),
        ("Micro F1-score", micro.f1, "2 × Precision × Sensitivity / (Precision + Sensitivity)",
         "Harmonic mean of micro precision and micro sensitivity."),
        ("Macro Accuracy", macro.accuracy, "Mean of condition-level accuracies",
         "Each condition receives equal weight."),
        ("Macro Sensitivity", macro.sensitivity, "Mean of defined condition-level sensitivities",
         "Conditions with no Gold Standard positives are excluded."),
        ("Macro Specificity", macro.specificity, "Mean of defined condition-level specificities",
         "Conditions with no Gold Standard negatives are excluded."),
        ("Macro Precision", macro.precision, "Mean of defined condition-level precisions",
         "Conditions with no predicted positives are excluded."),
        ("Macro F1-score", macro.f1, "Mean of defined condition-level F1-scores",
         "Conditions with undefined F1 are excluded."),
    ]


def _skipped_line_rows(labels: ReconciledLabels) -> list[tuple]:
    """Approved addition (Option B): only present when unreadable lines were skipped.

    With no skipped lines the Execution Log is exactly the Week 4 layout.
    """
    if not labels.skipped_lines:
        return []
    count = len(labels.skipped_lines)
    rows: list[tuple] = [(
        "Skipped prediction lines",
        f"{count} unreadable line(s) in the prediction file were skipped (listed below); "
        f"all {len(labels.case_ids)} CaseIDs still have exactly one valid successful "
        "prediction.",
    )]
    rows.extend(("Skipped prediction line", skipped.describe())
                for skipped in labels.skipped_lines)
    return rows


def _condition_row(name: str, m: ConfusionMetrics) -> list:
    return [name, m.tp, m.fn, m.tn, m.fp, m.total, m.positive_gt, m.negative_gt,
            m.accuracy, m.sensitivity, m.specificity, m.precision, m.f1]


def _confusion_row(name: str, m: ConfusionMetrics) -> list:
    return [name, m.tp, m.fn, m.tn, m.fp, m.sensitivity, m.specificity, m.total,
            m.positive_gt, m.negative_gt, m.accuracy, m.precision, m.f1, m.total]


def build_matrix1_workbook(
    labels: ReconciledLabels,
    per_condition: Mapping[str, ConfusionMetrics],
    micro: ConfusionMetrics,
    macro: MacroMetrics,
    output_path: str | Path,
    *,
    clock: Clock = utc_now,
) -> Path:
    """Write the Matrix 1 evaluation workbook and return its path."""
    if labels.workflow != "matrix1":
        raise ValueError(f"The Matrix 1 workbook cannot be built for {labels.workflow!r}.")

    wb = Workbook()
    summary = wb.active
    summary.title = "Overall Summary"
    summary.append([SUMMARY_TITLE])
    summary.append(["Metric", "Result", "Calculation / Definition", "Interpretation"])
    for row in _summary_rows(len(labels.case_ids), micro, macro):
        summary.append(list(row))

    condition_sheet = wb.create_sheet("Condition Summary")
    condition_sheet.append(CONDITION_SUMMARY_HEADERS)
    for condition in CONDITION_KEYS:
        condition_sheet.append(_condition_row(condition, per_condition[condition]))
    condition_sheet.append(_condition_row("TOTAL", micro))

    case_sheet = wb.create_sheet("Case Predictions")
    columns = ["CaseID"]
    for condition in CONDITION_KEYS:
        columns.extend([f"{condition} - Gold Standard", f"{condition} - Model Prediction",
                        f"{condition} - Agreement"])
    case_sheet.append(columns)
    for case_id in sorted_case_ids(labels.case_ids):
        row = [case_id]
        for condition in CONDITION_KEYS:
            actual = labels.reference[case_id][condition]
            predicted = labels.predictions[case_id][condition]
            row.extend([actual, predicted, "Match" if actual == predicted else "Mismatch"])
        case_sheet.append(row)

    confusion = wb.create_sheet("Confusion Matrix")
    confusion.append(CONFUSION_HEADERS)
    for condition in CONDITION_KEYS:
        confusion.append(_confusion_row(condition, per_condition[condition]))
    confusion.append(_confusion_row("TOTAL", micro))

    reference_name = (labels.reference_source.name if labels.reference_source
                      else DEFAULT_GROUND_TRUTH_NAME)
    predictions_name = (labels.predictions_source.name if labels.predictions_source
                        else DEFAULT_PREDICTIONS_NAME)
    log = wb.create_sheet("Execution Log")
    log.append(["Metric", "Value"])
    for row in [
        ("Evaluation Track", "Matrix 1 only — kept separate from Matrix 2"),
        ("Ground-truth workbook", reference_name),
        ("Prediction file", predictions_name),
        ("Cases in ground truth", len(labels.reference)),
        ("Prediction records", len(labels.predictions)),
        ("Conditions", len(CONDITION_KEYS)),
        ("Expected paired labels", len(labels.reference) * len(CONDITION_KEYS)),
        ("Actual paired labels", micro.total),
        ("CaseID reconciliation",
         "PASS — exact match; no missing, duplicate, or unexpected CaseIDs"),
        ("Prediction validation",
         "PASS — all records successful; exact 20 keys; Positive/Negative labels only"),
        *_skipped_line_rows(labels),
        ("Model", MODEL_RECORD),
        ("Prompt version", PROMPT_RECORD),
        ("Evaluation generated (UTC)", clock().strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Metric scope", "Model predictions compared against Matrix 1 encoded ground truth only"),
        ("Clinical interpretation",
         "Dataset-specific evaluation; not a statement of clinical readiness."),
    ]:
        log.append(list(row))

    definitions = wb.create_sheet("Metric Definitions")
    definitions.append(["Term", "Definition"])
    for row in METRIC_DEFINITIONS:
        definitions.append(list(row))

    _apply_week4_formatting(wb)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destination)
    return destination


def _apply_week4_formatting(wb: Workbook) -> None:
    """Formatting pass in the same order as Week 4 (later steps override earlier); A5 values."""
    thin = Side(style="thin", color="D9E1F2")
    for sheet in wb.worksheets:
        sheet.freeze_panes = "B3" if sheet.title == "Overall Summary" else "B2"
        if sheet.title in ("Condition Summary", "Case Predictions", "Confusion Matrix"):
            sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.fill = PatternFill("solid", fgColor=NAVY)
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        sheet.row_dimensions[1].height = HEADER_ROW_HEIGHT

        if sheet.title == "Overall Summary":
            for cell in sheet[2]:
                cell.fill = PatternFill("solid", fgColor=PALE_BLUE)
                cell.font = Font(bold=True, color=DARK_TEXT)
            for row in range(3, sheet.max_row + 1):
                if row in range(10, 20):  # Micro and Macro ratio rows
                    sheet.cell(row, 2).number_format = PERCENT
            widths = [30, 18, 55, 65]
        elif sheet.title == "Condition Summary":
            for row in range(2, sheet.max_row + 1):
                for col in range(9, 14):
                    sheet.cell(row, col).number_format = PERCENT
            for cell in sheet[sheet.max_row]:
                cell.fill = PatternFill("solid", fgColor=PALE_GREEN)
                cell.font = Font(bold=True)
            widths = [30, 10, 10, 10, 10, 10, 20, 20, 13, 13, 13, 13, 13]
        elif sheet.title == "Confusion Matrix":
            for row in range(2, sheet.max_row + 1):
                for col in (6, 7, 11, 12, 13):
                    sheet.cell(row, col).number_format = PERCENT
            for cell in sheet[sheet.max_row]:
                cell.fill = PatternFill("solid", fgColor=PALE_GREEN)
                cell.font = Font(bold=True)
            widths = [30, 15, 15, 15, 15, 14, 14, 12, 20, 20, 14, 14, 14, 12]
        elif sheet.title == "Case Predictions":
            widths = [12] + [22, 22, 14] * len(CONDITION_KEYS)
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    if cell.value == "Mismatch":
                        cell.fill = PatternFill("solid", fgColor=PALE_RED)
                    elif cell.value == "Match":
                        cell.fill = PatternFill("solid", fgColor=PALE_GREEN)
        elif sheet.title == "Execution Log":
            widths = [32, 90]
        else:
            widths = [32, 100]

        for index, width in enumerate(widths, 1):
            sheet.column_dimensions[get_column_letter(index)].width = width
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                cell.border = Border(bottom=thin)
