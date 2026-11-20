"""Six-sheet OpenAI vs Gemini comparison workbook for ONE workflow.

Sheets (in order):

1. Overall Comparison   — reference-based metrics for each model (counts, micro
   rates; Matrix 1 also macro rates, as in its evaluation workbook) and the
   Gemini − OpenAI difference, plus reference-based correctness totals.
2. Condition Comparison — per condition (+ MICRO TOTAL): reference support, each
   model's TP/FN/TN/FP and rates, rate differences, and reference-based
   correctness (both correct / only OpenAI / only Gemini / both wrong).
3. Model Agreement      — per condition (+ TOTAL): OpenAI vs Gemini only
   (reference labels NOT used): both Positive, OpenAI-only Positive,
   Gemini-only Positive, both Negative, agreements, agreement rate.
4. Case Disagreements   — every case-condition pair where the models differ,
   with the reference label and the model that matches it.
5. Execution Log        — workflow, sources with SHA-256 digests, record counts,
   skipped lines, error-log reconciliation (superseded / unresolved / final
   failures), model and prompt provenance, read-only verification.
6. Metric Definitions   — formulas and interpretation notes.

Model agreement and reference-based accuracy are reported as separate analyses.
Undefined values are blank cells (never 0). Styling follows the Week 5
workbooks (navy header row, percent formats, frozen headers, filters).
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from week_07.comparison.agreement import RATE_FIELDS, rate_differences
from week_07.comparison.compare import ComparisonResult
from week_07.comparison.sources import PredictionSource
from week_07.conditions import CONDITION_COUNT, CONDITION_KEYS
from week_07.config import WorkflowSpec
from week_07.evaluation.evaluate import WORKFLOW_LABELS
from week_07.evaluation.metrics import ConfusionMetrics
from week_07.isolation import DEFAULT_POLICY, IsolationPolicy, OutputArea
from week_07.jsonl_store import Clock, utc_now
from week_07.prompts.prompt_loader import PROMPT_FILE_SHA256, PROMPT_TEXT_SHA256, PROMPT_VERSION

SHEETS = ("Overall Comparison", "Condition Comparison", "Model Agreement",
          "Case Disagreements", "Execution Log", "Metric Definitions")
NAVY, PALE_BLUE, PALE_GREEN, PALE_RED, WHITE = "1F4E78", "D9EAF7", "E2F0D9", "FCE4D6", "FFFFFF"
PERCENT = "0.00%"
RATE_NAMES = {"accuracy": "Accuracy", "sensitivity": "Sensitivity", "specificity": "Specificity",
              "precision": "Precision", "f1": "F1-score"}
OPENAI_LABEL, GEMINI_LABEL = "Week 5 OpenAI", "Week 7 Gemini"
DIFF_LABEL = "Difference (Gemini − OpenAI)"
NO_DISAGREEMENTS = "No disagreements: the two models agree on every case-condition pair."

OVERALL_HEADERS = ["Metric", OPENAI_LABEL, GEMINI_LABEL, DIFF_LABEL, "Definition"]
CONDITION_HEADERS = (
    ["Condition", "Positive Reference", "Negative Reference"]
    + [f"{OPENAI_LABEL} {m}" for m in ("TP", "FN", "TN", "FP")]
    + [f"{GEMINI_LABEL} {m}" for m in ("TP", "FN", "TN", "FP")]
    + [f"{OPENAI_LABEL} {RATE_NAMES[r]}" for r in RATE_FIELDS]
    + [f"{GEMINI_LABEL} {RATE_NAMES[r]}" for r in RATE_FIELDS]
    + [f"Difference {RATE_NAMES[r]}" for r in RATE_FIELDS]
    + ["Both Correct", "Only OpenAI Correct", "Only Gemini Correct", "Both Wrong"]
)
CONDITION_PERCENT_COLUMNS = range(12, 27)            # 15 rate / difference columns
AGREEMENT_HEADERS = ["Condition", "Both Positive", "OpenAI-only Positive",
                     "Gemini-only Positive", "Both Negative", "Total Pairs", "Agreements",
                     "Disagreements", "Agreement Rate", "OpenAI Positive", "Gemini Positive"]
DISAGREEMENT_HEADERS = ["CaseID", "Condition", "Reference Label", OPENAI_LABEL, GEMINI_LABEL,
                        "Model Matching Reference"]
LOG_HEADERS = ["Item", "Value", "Detail"]

METRIC_DEFINITIONS = [
    ("Reference labels", "The workflow's own reference labels: Matrix 1 = original Vetology "
                         "scores; Matrix 2 = Gold Standard. Matrix 1 and Matrix 2 are never "
                         "combined."),
    ("TP / FN / TN / FP", "Reference Positive & model Positive / reference Positive & model "
                          "Negative / reference Negative & model Negative / reference Negative "
                          "& model Positive (Week 5 methodology)."),
    ("Accuracy", "(TP + TN) / (TP + FN + TN + FP)."),
    ("Sensitivity", "TP / (TP + FN). Undefined when there are no reference Positive labels."),
    ("Specificity", "TN / (TN + FP). Undefined when there are no reference Negative labels."),
    ("Precision", "TP / (TP + FP). Undefined when the model makes no Positive predictions."),
    ("F1-score", "2 × Precision × Sensitivity / (Precision + Sensitivity). Undefined when "
                 "precision or sensitivity is undefined, or their sum is zero."),
    ("Micro / Macro", "Micro: counts summed over all conditions, then the formulas. Macro "
                      "(Matrix 1 only, as in its evaluation workbook): unweighted mean of the "
                      "defined condition-level values; undefined values are excluded."),
    ("Difference", "Gemini value minus OpenAI value. Blank when either value is undefined."),
    ("Both / Only OpenAI / Only Gemini Correct, Both Wrong",
     "Reference-based correctness of the two models on the same case-condition pair."),
    ("Both Positive / OpenAI-only / Gemini-only Positive / Both Negative",
     "Model agreement: the two models' labels compared with each other. Reference labels are "
     "NOT used; agreement is not accuracy."),
    ("Agreement Rate", "(Both Positive + Both Negative) / Total Pairs."),
    ("Case disagreement", "A case-condition pair where the two models give different labels; "
                          "with binary labels exactly one of them matches the reference."),
    ("Superseded failure record", "A failure record in an error log whose CaseID also has a "
                                  "valid success record (a later attempt succeeded). Reported "
                                  "for transparency; not a final failure."),
    ("Unresolved failure record", "A failure record without a valid success record (a final "
                                  "failure). The comparison is refused when any exists."),
    ("Skipped prediction line", "A line that is not valid JSON (interrupted write); listed in "
                                "the Execution Log. Exact CaseID matching is still enforced."),
    ("Interpretation", "Pilot comparison on the same reports; not evidence of clinical "
                       "readiness. Matrix 1 and Matrix 2 results use different reference labels "
                       "and are not a like-for-like comparison of each other."),
]

_THIN = Side(style="thin", color="D9E1F2")
_HEADER_FILL = PatternFill("solid", fgColor=NAVY)
_HEADER_FONT = Font(bold=True, color=WHITE)
_TOTAL_FILL = PatternFill("solid", fgColor=PALE_BLUE)


def display_path(path: Path) -> str:
    """Last three path components, e.g. ``week_05/matrix_1/predictions.jsonl``.

    Distinguishes same-named files (Week 5 vs Week 7 ``predictions.jsonl``)
    without exposing the full local path.
    """
    return "/".join(Path(path).parts[-3:])


def _case_ranges(case_ids: Iterable[int]) -> str:
    ids = sorted(case_ids)
    if not ids:
        return "none"
    parts, start, prev = [], ids[0], ids[0]
    for cid in ids[1:] + [None]:
        if cid is not None and cid == prev + 1:
            prev = cid
            continue
        parts.append(str(start) if start == prev else f"{start}–{prev}")
        if cid is not None:
            start = prev = cid
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Sheet builders
# ---------------------------------------------------------------------------

def _overall(ws, result: ComparisonResult, macro: bool) -> None:
    label = WORKFLOW_LABELS.get(result.workflow, result.workflow)
    o, g = result.openai_evaluation, result.gemini_evaluation
    ws.append([f"VETOLOGY WEEK 7 - {label.upper()} MODEL COMPARISON "
               "(WEEK 5 OPENAI VS WEEK 7 GEMINI)", None, None, None, None])
    ws.append([f"{result.title}. Reference labels: {result.reference_description}. Both models "
               "are scored against the same reference labels on the same cases.",
               None, None, None, None])
    ws.append(OVERALL_HEADERS)
    cases = len(result.case_ids)
    rows: list[list[Any]] = [
        ["Cases compared", cases, cases, None, "Identical CaseID sets in reference, OpenAI "
                                               "and Gemini predictions."],
        ["Conditions", CONDITION_COUNT, CONDITION_COUNT, None, "All 20 conditions."],
        ["Paired labels", o.micro.total, g.micro.total, None, "Cases × conditions."],
    ]
    for name, field in (("True Positive (TP)", "tp"), ("False Negative (FN)", "fn"),
                        ("True Negative (TN)", "tn"), ("False Positive (FP)", "fp")):
        a, b = getattr(o.micro, field), getattr(g.micro, field)
        rows.append([name, a, b, b - a, "Count against the reference labels."])
    percent_rows = []
    diffs = rate_differences(o.micro, g.micro)
    for field in RATE_FIELDS:
        percent_rows.append(len(rows))
        rows.append([f"Micro {RATE_NAMES[field]}", getattr(o.micro, field),
                     getattr(g.micro, field), diffs[field], "Counts summed over conditions."])
    if macro:
        diffs = rate_differences(o.macro, g.macro)
        for field in RATE_FIELDS:
            percent_rows.append(len(rows))
            rows.append([f"Macro {RATE_NAMES[field]}", getattr(o.macro, field),
                         getattr(g.macro, field), diffs[field],
                         "Mean of defined condition-level values."])
    c = result.correctness_total
    rows.append(["Correct labels", c.openai_correct, c.gemini_correct,
                 c.gemini_correct - c.openai_correct, "Labels equal to the reference label."])
    for name, value, note in (
            ("Both models correct", c.both_correct, "Reference-based; same pair."),
            ("Only OpenAI correct", c.only_openai_correct, "Reference-based; same pair."),
            ("Only Gemini correct", c.only_gemini_correct, "Reference-based; same pair."),
            ("Both models wrong", c.both_wrong, "Reference-based; same pair.")):
        rows.append([name, value, None, None, note])  # one shared value (B:C merged)
    first = ws.max_row + 1
    for row in rows:
        ws.append(row)
    for offset in percent_rows:
        for col in (2, 3, 4):
            ws.cell(first + offset, col).number_format = PERCENT
    for row in range(first + len(rows) - 4, first + len(rows)):  # shared cross-tab rows
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    ws.merge_cells("A1:E1")
    ws.merge_cells("A2:E2")
    ws["A1"].font = Font(bold=True, color=WHITE, size=13)
    ws["A1"].fill = _HEADER_FILL
    ws["A2"].font = Font(italic=True)
    _header_row(ws, 3)
    ws.freeze_panes = "B4"
    _widths(ws, [34, 22, 22, 26, 60])
    _grid(ws, start_row=3)


def _condition_row(name: str, o: ConfusionMetrics, g: ConfusionMetrics, corr: Any) -> list:
    diffs = rate_differences(o, g)
    return ([name, o.positive_gt, o.negative_gt, o.tp, o.fn, o.tn, o.fp, g.tp, g.fn, g.tn, g.fp]
            + [getattr(o, r) for r in RATE_FIELDS] + [getattr(g, r) for r in RATE_FIELDS]
            + [diffs[r] for r in RATE_FIELDS]
            + [corr.both_correct, corr.only_openai_correct, corr.only_gemini_correct,
               corr.both_wrong])


def _conditions(ws, result: ComparisonResult) -> None:
    o, g = result.openai_evaluation, result.gemini_evaluation
    ws.append(CONDITION_HEADERS)
    for condition in CONDITION_KEYS:
        ws.append(_condition_row(condition, o.per_condition[condition],
                                 g.per_condition[condition], result.correctness[condition]))
    ws.append(_condition_row("MICRO TOTAL", o.micro, g.micro, result.correctness_total))
    _table(ws, CONDITION_PERCENT_COLUMNS, [30, 12, 12] + [10] * 8 + [14] * 15 + [12] * 4)


def _agreement_row(name: str, a: Any) -> list:
    return [name, a.both_positive, a.openai_only_positive, a.gemini_only_positive,
            a.both_negative, a.total, a.agreements, a.disagreements, a.agreement_rate,
            a.openai_positive, a.gemini_positive]


def _agreement(ws, result: ComparisonResult) -> None:
    ws.append(AGREEMENT_HEADERS)
    for condition in CONDITION_KEYS:
        ws.append(_agreement_row(condition, result.agreement[condition]))
    ws.append(_agreement_row("TOTAL", result.agreement_total))
    _table(ws, (9,), [30, 14, 18, 18, 14, 12, 12, 14, 14, 14, 14])


def _disagreements(ws, result: ComparisonResult) -> None:
    ws.append(DISAGREEMENT_HEADERS)
    if not result.disagreements:
        ws.append([NO_DISAGREEMENTS, None, None, None, None, None])
    for row in result.disagreements:
        ws.append([row.case_id, row.condition, row.reference, row.openai, row.gemini,
                   row.model_matching_reference])
    _header_row(ws, 1)
    ws.freeze_panes = "A2"
    if result.disagreements:
        ws.auto_filter.ref = ws.dimensions
        for cells in ws.iter_rows(min_row=2, min_col=4, max_col=5):
            for cell in cells:
                reference = ws.cell(cell.row, 3).value
                colour = PALE_GREEN if cell.value == reference else PALE_RED
                cell.fill = PatternFill("solid", fgColor=colour)
    _widths(ws, [12, 30, 16, 16, 16, 24])
    _grid(ws)


def _source_rows(source: PredictionSource) -> list[list[Any]]:
    p, errors, records = source.provenance, source.errors, source.records
    name = source.label
    rows = [
        [f"{name} predictions", p.path.name, f"sha256 {p.sha256}; {p.size_bytes} bytes"],
        [f"{name} prediction records", len(records.labels),
         "Valid success records (strict Week 5 rules)."],
        [f"{name} skipped prediction lines", len(records.skipped),
         "; ".join(s.describe() for s in records.skipped) or "None."],
        [f"{name} model", source.model_record, None],
    ]
    if source.manifest_provenance is not None:
        m = source.manifest_provenance
        identity = source.manifest_identity or {}
        prompt = identity.get("prompt", {})
        rows += [
            [f"{name} run manifest", m.path.name, f"sha256 {m.sha256}"],
            [f"{name} prompt", f"{prompt.get('name', '')} {prompt.get('version', '')}".strip(),
             f"file sha256 {prompt.get('file_sha256')}; text sha256 {prompt.get('text_sha256')}"],
            [f"{name} response format",
             identity.get("response_mime_type"), "No response schema."],
        ]
    else:
        rows.append([f"{name} prompt", f"Canine Thorax Master Prompt {PROMPT_VERSION}",
                     "Week 5 configuration (pinned digests identical to Week 7); not embedded "
                     "in the prediction file."])
    if errors.provenance is None:
        rows.append([f"{name} error log", "None", errors.describe()])
    else:
        e = errors.provenance
        rows += [
            [f"{name} error log", e.path.name, f"sha256 {e.sha256}; {errors.origin}"],
            [f"{name} error records", errors.records, errors.describe()],
            [f"{name} superseded failures", errors.superseded_records,
             f"CaseIDs: {_case_ranges(errors.superseded)}. A later attempt succeeded; "
             "not final failures."],
        ]
    rows.append([f"{name} final failures", errors.unresolved_records,
                 "Unresolved failure records (the comparison requires none)."])
    return rows


def _execution_log(ws, result: ComparisonResult, clock: Clock) -> None:
    label = WORKFLOW_LABELS.get(result.workflow, result.workflow)
    ref = result.reference
    ws.append(LOG_HEADERS)
    rows: list[list[Any]] = [
        ["Comparison", f"{label} — Week 5 OpenAI vs Week 7 Gemini",
         "Matrix 1 and Matrix 2 are kept separate and never combined."],
        ["Workflow", result.title, None],
        ["Reference labels", result.reference_description, None],
        ["Reference workbook", ref.path.name, f"sha256 {ref.sha256}; {ref.size_bytes} bytes"],
        ["Reference worksheet", result.reference_worksheet, None],
        ["Cases compared", len(result.case_ids), f"CaseIDs {_case_ranges(result.case_ids)}"],
        ["Conditions", CONDITION_COUNT, None],
        ["Paired labels per model", len(result.case_ids) * CONDITION_COUNT, None],
        ["CaseID reconciliation", "PASS",
         "Reference, OpenAI and Gemini CaseID sets are identical; no missing, extra or "
         "duplicate CaseIDs."],
        ["Prediction validation", "PASS",
         "All records successful; exactly 20 condition keys; Positive/Negative labels only."],
        *_source_rows(result.openai),
        *_source_rows(result.gemini),
        ["Week 7 pinned prompt digests", PROMPT_VERSION,
         f"file sha256 {PROMPT_FILE_SHA256}; text sha256 {PROMPT_TEXT_SHA256}"],
        ["Model disagreements", len(result.disagreements), "Listed in Case Disagreements."],
        ["Read-only verification", "PASS",
         f"{len(result.source_digests)} source file(s) hashed before and after reading; "
         "none changed."],
        *[["Source file SHA-256", display_path(path), digest]
          for path, digest in result.source_digests.items()],
        ["Comparison generated (UTC)", clock().strftime("%Y-%m-%d %H:%M:%S UTC"), None],
        ["API requests", "None", "Offline comparison of saved predictions; no model client "
                                 "was loaded."],
        ["Interpretation", "Pilot comparison only",
         "Model agreement is not accuracy; reference-based metrics use the workflow's own "
         "reference labels. Not evidence of clinical readiness."],
    ]
    for row in rows:
        ws.append(row)
    _header_row(ws, 1)
    ws.freeze_panes = "A2"
    _widths(ws, [36, 58, 100])
    _grid(ws)


def _definitions(ws) -> None:
    ws.append(["Term", "Definition"])
    for row in METRIC_DEFINITIONS:
        ws.append(list(row))
    _header_row(ws, 1)
    ws.freeze_panes = "A2"
    _widths(ws, [42, 110])
    _grid(ws)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _header_row(ws, row: int) -> None:
    for cell in ws[row]:
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32


def _widths(ws, widths: Sequence[float]) -> None:
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width


def _grid(ws, start_row: int = 1) -> None:
    for row in ws.iter_rows(min_row=start_row + 1):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=_THIN)


def _table(ws, percent_columns: Iterable[int], widths: Sequence[float]) -> None:
    percent = set(percent_columns)
    _header_row(ws, 1)
    _widths(ws, widths)
    _grid(ws)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if cell.column in percent:
                cell.number_format = PERCENT
    for cell in ws[ws.max_row]:
        cell.fill = _TOTAL_FILL
        cell.font = Font(bold=True)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def build_comparison_workbook(result: ComparisonResult, *, clock: Clock = utc_now) -> Workbook:
    """Build (in memory) the six-sheet workbook for one workflow's comparison."""
    wb = Workbook()
    overall = wb.active
    overall.title = SHEETS[0]
    _overall(overall, result, macro=result.workflow == "matrix1")
    _conditions(wb.create_sheet(SHEETS[1]), result)
    _agreement(wb.create_sheet(SHEETS[2]), result)
    _disagreements(wb.create_sheet(SHEETS[3]), result)
    _execution_log(wb.create_sheet(SHEETS[4]), result, clock)
    _definitions(wb.create_sheet(SHEETS[5]))
    return wb


def write_comparison_workbook(
    spec: WorkflowSpec,
    result: ComparisonResult,
    output_path: str | Path | None = None,
    *,
    isolation: IsolationPolicy = DEFAULT_POLICY,
    clock: Clock = utc_now,
) -> Path:
    """Write the workbook to the workflow's comparison directory (isolation-guarded)."""
    if result.workflow != spec.name:
        raise ValueError(
            f"A {result.workflow!r} comparison cannot be written as a {spec.name} workbook."
        )
    target = spec.comparison_workbook_path if output_path is None else output_path
    path = isolation.assert_writable(target, spec, OutputArea.COMPARISON)
    workbook = build_comparison_workbook(result, clock=clock)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return path


def summary_lines(result: ComparisonResult) -> list[str]:
    """Short console summary (no report text, no labels per case)."""
    o, g, a = result.openai_evaluation.micro, result.gemini_evaluation.micro, result.agreement_total

    def pct(value: float | None) -> str:
        return "undefined" if value is None else f"{value:.2%}"

    return [
        f"Workflow: {result.workflow} ({result.title})",
        f"Reference labels: {result.reference_description}",
        f"Cases: {len(result.case_ids)} | Paired labels per model: {o.total}",
        f"{OPENAI_LABEL}: {result.openai.model_record}",
        f"  TP={o.tp} FN={o.fn} TN={o.tn} FP={o.fp} | accuracy={pct(o.accuracy)} "
        f"sensitivity={pct(o.sensitivity)} specificity={pct(o.specificity)} "
        f"precision={pct(o.precision)} F1={pct(o.f1)}",
        f"{GEMINI_LABEL}: {result.gemini.model_record}",
        f"  TP={g.tp} FN={g.fn} TN={g.tn} FP={g.fp} | accuracy={pct(g.accuracy)} "
        f"sensitivity={pct(g.sensitivity)} specificity={pct(g.specificity)} "
        f"precision={pct(g.precision)} F1={pct(g.f1)}",
        f"Model agreement (reference not used): {a.agreements}/{a.total} "
        f"({pct(a.agreement_rate)}); disagreements: {a.disagreements}",
        f"{OPENAI_LABEL} error log: {result.openai.errors.describe()}",
        f"{GEMINI_LABEL} error log: {result.gemini.errors.describe()}",
    ]
