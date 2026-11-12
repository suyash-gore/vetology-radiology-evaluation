"""Cell-by-cell comparison of two Excel workbooks (values and formatting).

Used by the offline tests and the baseline parity checks (A5 Matrix 1 and A6
Matrix 2 evaluation workbooks).

Compared: sheet names and order, sheet dimensions, merged ranges, freeze panes,
auto-filter, every column width and row height, and for every cell its value,
number format, font (name, size, bold, italic, underline, colour), fill (type,
colour), alignment (horizontal, vertical, wrap) and all four borders.

Either argument may be a path or an already-loaded ``openpyxl`` workbook, so a
baseline can be adjusted in memory (e.g. an approved, documented row removal)
without ever modifying the baseline file. Floating-point values are compared
exactly unless ``float_tolerance`` is set.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook

Ignore = Iterable[tuple[str, str]]  # (sheet title, cell coordinate)
WorkbookSource = str | Path | Workbook


def _colour(color: Any) -> Any:
    """RGB string for explicit colours; (type, value, tint) for theme/indexed colours."""
    if color is None:
        return None
    if getattr(color, "type", None) == "rgb":
        return color.rgb
    kind = getattr(color, "type", None)
    return (kind, getattr(color, kind, None) if kind else None, getattr(color, "tint", None))


def _side(side: Any) -> tuple:
    if side is None:
        return (None, None)
    return (side.style, _colour(side.color))


def cell_style(cell) -> tuple:
    """Every formatting attribute that is compared, as one hashable tuple."""
    font, fill, align, border = cell.font, cell.fill, cell.alignment, cell.border
    return (
        cell.number_format,
        font.name, font.sz, bool(font.b), bool(font.i), font.u, _colour(font.color),
        fill.fill_type, _colour(fill.fgColor),
        align.horizontal, align.vertical, bool(align.wrap_text),
        _side(border.left), _side(border.right), _side(border.top), _side(border.bottom),
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _values_equal(a: Any, b: Any, tolerance: float) -> bool:
    # Excel has a single numeric type: a stored 1.0 reads back as 1, so int and
    # float compare numerically. Text, booleans and empty cells stay strict.
    if _is_number(a) and _is_number(b):
        return a == b or (tolerance > 0 and math.isclose(a, b, rel_tol=0, abs_tol=tolerance))
    return a == b and type(a) is type(b)


def _load(source: WorkbookSource) -> Workbook:
    return source if isinstance(source, Workbook) else load_workbook(source)


def compare_workbooks(
    expected: WorkbookSource,
    actual: WorkbookSource,
    *,
    ignore_cells: Ignore = (),
    float_tolerance: float = 0.0,
    compare_styles: bool = True,
    max_differences: int = 50,
) -> list[str]:
    """Return human-readable differences (an empty list means identical)."""
    ignored = set(ignore_cells)
    a_book, b_book = _load(expected), _load(actual)
    diffs: list[str] = []

    def add(message: str) -> bool:
        diffs.append(message)
        return len(diffs) >= max_differences

    if a_book.sheetnames != b_book.sheetnames:
        add(f"Sheet names differ: {a_book.sheetnames} != {b_book.sheetnames}")
        return diffs

    for title in a_book.sheetnames:
        a, b = a_book[title], b_book[title]
        if (a.max_row, a.max_column) != (b.max_row, b.max_column):
            if add(f"[{title}] dimensions {a.max_row}x{a.max_column} != "
                   f"{b.max_row}x{b.max_column}"):
                return diffs
        if a.freeze_panes != b.freeze_panes:
            add(f"[{title}] freeze_panes {a.freeze_panes!r} != {b.freeze_panes!r}")
        if a.auto_filter.ref != b.auto_filter.ref:
            add(f"[{title}] auto_filter {a.auto_filter.ref!r} != {b.auto_filter.ref!r}")
        merged_a = sorted(str(r) for r in a.merged_cells.ranges)
        merged_b = sorted(str(r) for r in b.merged_cells.ranges)
        if merged_a != merged_b:
            add(f"[{title}] merged cells {merged_a} != {merged_b}")
        if compare_styles:
            for letter in sorted(set(a.column_dimensions) | set(b.column_dimensions)):
                wa, wb = a.column_dimensions[letter].width, b.column_dimensions[letter].width
                if wa != wb and add(f"[{title}] column {letter} width {wa} != {wb}"):
                    return diffs
            for row in range(1, max(a.max_row, b.max_row) + 1):
                ha, hb = a.row_dimensions[row].height, b.row_dimensions[row].height
                if ha != hb and add(f"[{title}] row {row} height {ha} != {hb}"):
                    return diffs

        for row in range(1, max(a.max_row, b.max_row) + 1):
            for col in range(1, max(a.max_column, b.max_column) + 1):
                ca, cb = a.cell(row, col), b.cell(row, col)
                if (title, ca.coordinate) in ignored:
                    continue
                if not _values_equal(ca.value, cb.value, float_tolerance):
                    if add(f"[{title}!{ca.coordinate}] value {ca.value!r} != {cb.value!r}"):
                        return diffs
                if compare_styles and cell_style(ca) != cell_style(cb):
                    if add(f"[{title}!{ca.coordinate}] style {cell_style(ca)} != "
                           f"{cell_style(cb)}"):
                        return diffs
    return diffs
