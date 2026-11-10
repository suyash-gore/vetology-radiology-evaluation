"""Offline tests for the Week 4-style evaluation reference loader (synthetic workbooks)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from week_05.conditions import CONDITION_KEYS
from week_05.config import MATRIX1, MATRIX2
from week_05.evaluation.reference_loader import (
    REFERENCE_LOADERS,
    AmbiguousReferenceError,
    ReferenceLoadError,
    ReferenceLoadingPending,
    compare_reference_loaders,
    load_matrix1_reference,
    load_matrix2_reference,
    load_reference_for_evaluation,
    reference_loader_for,
)
from week_05.tests.support import quiet
from week_05.tests.workbook_factory import (
    MATRIX1_HEADERS,
    MATRIX2_HEADERS,
    default_row,
    label_for,
    write_workbook,
)


class RefTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.n = 0
        quiet(self, "week_05.dataset_loader")

    def path(self) -> Path:
        self.n += 1
        return self.dir / f"ref{self.n}.xlsx"

    def rows(self, ids=range(1, 101)):
        return [default_row(i) for i in ids]

    def book(self, rows=None, headers=MATRIX1_HEADERS, first_sheet=None) -> Path:
        path = write_workbook(self.path(), headers, self.rows() if rows is None else rows)
        if first_sheet:
            wb = load_workbook(path)
            wb.create_sheet(first_sheet, 0).append(["notes"])
            wb.save(path)
        return path


class TestWeek4Rules(RefTestCase):
    def test_clean_workbook(self):
        ref = load_matrix1_reference(self.book())
        self.assertEqual(ref.case_ids, tuple(range(1, 101)))
        self.assertEqual(ref.worksheet_name, "Sheet1")
        self.assertEqual(tuple(ref.labels[1]), CONDITION_KEYS)
        self.assertEqual(dict(ref.labels[7]),
                         {c: label_for(7, i) for i, c in enumerate(CONDITION_KEYS)})
        self.assertNotIn("Positive", repr(ref))

    def test_uses_first_worksheet_whatever_its_name(self):
        path = write_workbook(self.path(), MATRIX1_HEADERS, self.rows(), sheet_name="Data")
        self.assertEqual(load_matrix1_reference(path).worksheet_name, "Data")
        with self.assertRaisesRegex(ReferenceLoadError, "Missing ground-truth columns"):
            load_matrix1_reference(self.book(first_sheet="Notes"))

    def test_reads_all_rows_without_limit(self):
        self.assertEqual(len(load_matrix1_reference(self.book(self.rows(range(1, 126))))
                             .case_ids), 125)

    def test_blank_case_id_rows_skipped_but_whitespace_is_an_error(self):
        rows = [*self.rows(), None, {**default_row(500), "CaseID": None}]
        self.assertEqual(len(load_matrix1_reference(self.book(rows)).case_ids), 100)
        rows = [*self.rows(), {**default_row(500), "CaseID": "  "}]
        with self.assertRaisesRegex(ReferenceLoadError, "cannot be converted"):
            load_matrix1_reference(self.book(rows))

    def test_case_ids_converted_with_int(self):
        rows = self.rows()
        rows[2]["CaseID"], rows[3]["CaseID"], rows[4]["CaseID"] = "3", 4.0, 5.7
        ref = load_matrix1_reference(self.book(rows))
        self.assertEqual(ref.case_ids[2:5], (3, 4, 5))      # 5.7 -> 5 (Week 4 quirk)
        rows = self.rows()
        rows[0]["CaseID"] = "A-1"
        with self.assertRaisesRegex(ReferenceLoadError, "'A-1' cannot be converted"):
            load_matrix1_reference(self.book(rows))

    def test_duplicates_after_conversion(self):
        rows = self.rows()
        rows[1]["CaseID"] = "1"
        with self.assertRaisesRegex(ReferenceLoadError, "Duplicate ground-truth CaseID: 1"):
            load_matrix1_reference(self.book(rows))

    def test_labels_and_headers_are_not_trimmed(self):
        rows = self.rows()
        rows[0]["rtm"] = " Positive"
        with self.assertRaisesRegex(ReferenceLoadError, "CaseID=1, rtm= Positive"):
            load_matrix1_reference(self.book(rows))
        headers = [" CaseID" if h == "CaseID" else h for h in MATRIX1_HEADERS]
        with self.assertRaisesRegex(ReferenceLoadError,
                                    r"Missing ground-truth columns: \['CaseID'\]"):
            load_matrix1_reference(self.book(headers=headers))

    def test_invalid_labels(self):
        for bad in ("positive", "Abnormal", "", None, 1):
            with self.subTest(bad=bad):
                rows = self.rows()
                rows[9]["esophagitis"] = bad
                with self.assertRaisesRegex(ReferenceLoadError, "CaseID=10, esophagitis="):
                    load_matrix1_reference(self.book(rows))

    def test_only_case_id_and_conditions_required(self):
        headers = ["CaseID", *CONDITION_KEYS]
        self.assertEqual(len(load_matrix1_reference(self.book(headers=headers)).case_ids), 100)

    def test_first_occurrence_of_a_duplicated_header_is_used(self):
        headers = [*MATRIX1_HEADERS, "rtm"]
        rows = [[*[default_row(i)[h] for h in MATRIX1_HEADERS], "Abnormal"] for i in range(1, 101)]
        ref = load_matrix1_reference(write_workbook(self.path(), headers, rows))
        self.assertEqual(ref.labels[1]["rtm"], label_for(1, CONDITION_KEYS.index("rtm")))

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_matrix1_reference(self.dir / "absent.xlsx")


class TestWeek4LoaderParity(RefTestCase):
    """Same accept/reject decisions and the same labels as Week 4's load_matrix1_inputs."""

    def week4_reference(self, workbook: Path):
        from week_04.matrix_1.matrix1_evaluator import load_matrix1_inputs

        ids = load_matrix1_reference(workbook).case_ids
        predictions = self.dir / f"{workbook.stem}.jsonl"
        predictions.write_text("".join(
            json.dumps({"case_id": i, "status": "success",
                        "predictions": {c: "Negative" for c in CONDITION_KEYS}}) + "\n"
            for i in ids), encoding="utf-8")
        truth, _ = load_matrix1_inputs(workbook, predictions)
        return truth

    def test_accepted_workbooks_match(self):
        mixed = self.rows()
        mixed[2]["CaseID"], mixed[3]["CaseID"], mixed[4]["CaseID"] = "3", 4.0, 5.7
        scenarios = {
            "clean": self.book(),
            "mixed CaseID types": self.book(mixed),
            "blank rows": self.book([None, *self.rows(), None]),
            "unsorted": self.book(self.rows(range(100, 0, -1))),
            "minimal columns": self.book(headers=["CaseID", *CONDITION_KEYS]),
            "alternative column order": self.book(headers=MATRIX2_HEADERS),
        }
        for name, path in scenarios.items():
            with self.subTest(scenario=name):
                week5 = load_matrix1_reference(path)
                week4 = self.week4_reference(path)
                self.assertEqual(list(week5.case_ids), list(week4))
                self.assertEqual({k: dict(v) for k, v in week5.labels.items()}, week4)

    def test_rejected_workbooks_match(self):
        from week_04.matrix_1.matrix1_evaluator import load_matrix1_inputs

        spaced_label = self.rows()
        spaced_label[0]["rtm"] = " Positive"
        duplicate = self.rows()
        duplicate[1]["CaseID"] = 1
        scenarios = {
            "label with whitespace": self.book(spaced_label),
            "header with whitespace": self.book(
                headers=[" CaseID" if h == "CaseID" else h for h in MATRIX1_HEADERS]),
            "duplicate CaseID": self.book(duplicate),
            "whitespace CaseID": self.book([*self.rows(), {**default_row(1), "CaseID": " "}]),
            "notes sheet first": self.book(first_sheet="Notes"),
        }
        dummy = self.dir / "dummy.jsonl"
        dummy.write_text("", encoding="utf-8")
        for name, path in scenarios.items():
            with self.subTest(scenario=name):
                with self.assertRaises(Exception):
                    load_matrix1_inputs(path, dummy)
                with self.assertRaises(ReferenceLoadError):
                    load_matrix1_reference(path)


class TestPerWorkflowLoaders(RefTestCase):
    """Matrix 1 and Matrix 2 evaluation reference loading are independent."""

    def test_each_workflow_has_its_own_loader(self):
        self.assertEqual(set(REFERENCE_LOADERS), {"matrix1", "matrix2"})
        self.assertIs(reference_loader_for(MATRIX1), load_matrix1_reference)
        self.assertIs(reference_loader_for(MATRIX2), load_matrix2_reference)
        self.assertIsNot(load_matrix2_reference, load_matrix1_reference)

    def test_matrix1_dispatch_uses_the_week4_rules(self):
        path = self.book()
        self.assertEqual(load_reference_for_evaluation(MATRIX1, path),
                         load_matrix1_reference(path))

    def test_unknown_workflow_has_no_loader(self):
        import dataclasses

        other = dataclasses.replace(MATRIX1, name="matrix3")
        for call in (lambda: reference_loader_for(other),
                     lambda: load_reference_for_evaluation(other, self.book()),
                     lambda: compare_reference_loaders(other, self.book())):
            with self.subTest(call=call):
                with self.assertRaises(ReferenceLoadingPending):
                    call()

    def test_pending_is_not_an_input_error(self):
        self.assertFalse(issubclass(ReferenceLoadingPending, ValueError))
        self.assertTrue(issubclass(ReferenceLoadingPending, NotImplementedError))


class TestMatrix2Loader(RefTestCase):
    """Decision D3: Week 4 Matrix 2 batch-loader rules plus an ambiguity guardrail."""

    def test_unambiguous_workbook_uses_batch_loader_selection(self):
        from week_05.dataset_loader import load_dataset

        path = self.book(headers=MATRIX2_HEADERS)
        ref = load_matrix2_reference(path)
        batch = load_dataset(MATRIX2, path)
        self.assertEqual(ref.case_ids, batch.case_ids)
        self.assertEqual(ref.worksheet_name, "Sheet1")
        self.assertEqual({k: dict(v) for k, v in ref.labels.items()},
                         {k: dict(v) for k, v in batch.reference_labels.items()})
        self.assertTrue(all(type(c) is int for c in ref.case_ids))

    def test_blank_rows_after_the_cases_are_not_ambiguous(self):
        rows = [*self.rows(), *[None] * 50]
        self.assertEqual(len(load_matrix2_reference(self.book(rows)).case_ids), 100)

    def test_fewer_than_100_cases_is_not_ambiguous(self):
        self.assertEqual(len(load_matrix2_reference(self.book(self.rows(range(1, 61))))
                             .case_ids), 60)

    def test_ambiguous_workbooks_are_rejected(self):
        padded = self.rows()
        padded[0]["rtm"] = " Positive"
        text_id = self.rows()
        text_id[4]["CaseID"] = "5"
        decimal_id = self.rows()
        decimal_id[4]["CaseID"] = 5.7
        cases = {
            "more than 100 populated rows": (self.book(self.rows(range(1, 126))),
                                             "Case count differs"),
            "padded label": (self.book(padded), "Evaluation loader failed"),
            "text CaseID": (self.book(text_id), "CaseID '5' is read as 5"),
            "decimal CaseID": (self.book(decimal_id), "Evaluation loader failed|read as"),
            "different first sheet": (self.book(first_sheet="Notes"),
                                      "Evaluation loader failed"),
        }
        for name, (path, detail) in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(AmbiguousReferenceError) as ctx:
                    load_matrix2_reference(path)
                self.assertIn("ambiguous", str(ctx.exception))
                self.assertRegex(str(ctx.exception), detail)
                self.assertEqual(compare_reference_loaders(MATRIX2, path) != [], True)

    def test_ambiguity_is_an_input_error(self):
        self.assertTrue(issubclass(AmbiguousReferenceError, ReferenceLoadError))

    def test_missing_workbook(self):
        with self.assertRaises(AmbiguousReferenceError):
            load_matrix2_reference(self.dir / "absent.xlsx")


class TestCompareLoaders(RefTestCase):
    def test_clean_workbook_has_no_differences(self):
        for headers in (MATRIX1_HEADERS, MATRIX2_HEADERS):
            with self.subTest(column_order=len(headers)):
                self.assertEqual(compare_reference_loaders(MATRIX1,
                                                           self.book(headers=headers)), [])

    def test_more_than_100_rows_is_reported(self):
        diffs = compare_reference_loaders(MATRIX1, self.book(self.rows(range(1, 126))))
        self.assertIn("Case count differs: batch=100, evaluation=125", diffs)
        self.assertTrue(any("only in the evaluation reference: [101, 102" in d for d in diffs))

    def test_whitespace_label_is_reported_as_loader_failure(self):
        rows = self.rows()
        rows[0]["rtm"] = " Positive"
        diffs = compare_reference_loaders(MATRIX1, self.book(rows))
        self.assertEqual(len(diffs), 1)
        self.assertIn("Evaluation loader failed: ReferenceLoadError", diffs[0])

    def test_case_id_conversion_is_reported(self):
        rows = self.rows()
        rows[2]["CaseID"], rows[4]["CaseID"] = "3", 5.7
        diffs = compare_reference_loaders(MATRIX1, self.book(rows))
        self.assertIn("CaseID '3' is read as 3 by the evaluation loader", diffs)
        self.assertIn("CaseID 5.7 is read as 5 by the evaluation loader", diffs)

    def test_different_first_sheet_is_reported(self):
        diffs = compare_reference_loaders(MATRIX1, self.book(first_sheet="Notes"))
        self.assertTrue(any(d.startswith("Evaluation loader failed") for d in diffs))

    def test_both_loaders_failing(self):
        diffs = compare_reference_loaders(MATRIX1, self.dir / "absent.xlsx")
        self.assertEqual(len(diffs), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
