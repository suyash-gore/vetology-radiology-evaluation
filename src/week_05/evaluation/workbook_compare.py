"""Cell-by-cell comparison of two Excel workbooks (values and formatting).

Used by the offline tests to compare Week 5 output with the Week 4 evaluator,
and intended for the later parity check against the real baseline workbooks
(A5 ``matrix1_evaluation_workbook.xlsx`` and A6 ``Evaluation Workbook v2.xlsx``).

Compared: sheet names and order, sheet dimensions, every cell's value, number
format, font (bold, colour), fill (type, colour), alignment (vertical, wrap)
and bottom border, column widths, row-1 height, freeze panes and auto-filter.
Floating-point values are compared exactly unless ``float_tolerance`` is set.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

Ignore = Iterable[tuple[str, str]]  # (sheet title, cell coordinate)


def _colour(color: Any) -> Any:
    return getattr(color, "rgb", None) if color is not None else None


def _style(cell) -> tuple:
    return (
        cell.number_format,
        bool(cell.font.bold), _colour(cell.font.color),
        cell.fill.fill_type, _colour(cell.fill.fgColor),
        cell.alignment.vertical, bool(cell.alignment.wrap_text),
        cell.border.bottom.style, _colour(cell.border.bottom.color),
    )


def _values_equal(a: Any, b: Any, tolerance: float) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (tolerance > 0 and math.isclose(a, b, rel_tol=0, abs_tol=tolerance))
    return a == b and type(a) is type(b)


def compare_workbooks(
    expected_path: str | Path,
    actual_path: str | Path,
    *,
    ignore_cells: Ignore = (),
    float_tolerance: float = 0.0,
    compare_styles: bool = True,
    max_differences: int = 50,
) -> list[str]:
    """Return human-readable differences (an empty list means identical)."""
    ignored = set(ignore_cells)
    expected = load_workbook(expected_path)
    actual = load_workbook(actual_path)
    diffs: list[str] = []

    def add(message: str) -> bool:
        diffs.append(message)
        return len(diffs) >= max_differences

    if expected.sheetnames != actual.sheetnames:
        add(f"Sheet names differ: {expected.sheetnames} != {actual.sheetnames}")
        return diffs

    for title in expected.sheetnames:
        a, b = expected[title], actual[title]
        if (a.max_row, a.max_column) != (b.max_row, b.max_column):
            if add(f"[{title}] dimensions {a.max_row}x{a.max_column} != "
                   f"{b.max_row}x{b.max_column}"):
                return diffs
        for attr in ("freeze_panes",):
            if getattr(a, attr) != getattr(b, attr):
                add(f"[{title}] {attr} {getattr(a, attr)!r} != {getattr(b, attr)!r}")
        if a.auto_filter.ref != b.auto_filter.ref:
            add(f"[{title}] auto_filter {a.auto_filter.ref!r} != {b.auto_filter.ref!r}")
        if compare_styles:
            if a.row_dimensions[1].height != b.row_dimensions[1].height:
                add(f"[{title}] row 1 height {a.row_dimensions[1].height} != "
                    f"{b.row_dimensions[1].height}")
            letters = set(a.column_dimensions) | set(b.column_dimensions)
            for letter in sorted(letters):
                wa, wb = a.column_dimensions[letter].width, b.column_dimensions[letter].width
                if wa != wb:
                    add(f"[{title}] column {letter} width {wa} != {wb}")

        rows = max(a.max_row, b.max_row)
        cols = max(a.max_column, b.max_column)
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                ca, cb = a.cell(row, col), b.cell(row, col)
                if (title, ca.coordinate) in ignored:
                    continue
                if not _values_equal(ca.value, cb.value, float_tolerance):
                    if add(f"[{title}!{ca.coordinate}] value {ca.value!r} != {cb.value!r}"):
                        return diffs
                if compare_styles and _style(ca) != _style(cb):
                    if add(f"[{title}!{ca.coordinate}] style {_style(ca)} != {_style(cb)}"):
                        return diffs
    return diffs
