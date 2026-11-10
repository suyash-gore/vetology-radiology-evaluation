"""Offline tests for the unified dataset loader using synthetic workbooks only."""
from __future__ import annotations

import dataclasses
import logging
import re
import tempfile
import unittest
from pathlib import Path

from week_05.conditions import CONDITION_KEYS
from week_05.config import MATRIX1, MATRIX2
from week_05.dataset_loader import (
    REPORT_COLUMNS,
    REQUIRED_COLUMNS,
    DatasetError,
    ReportCase,
    load_dataset,
)
from week_05.llm_client import build_human_content, build_messages
from week_05.tests.workbook_factory import (
    AI_COLUMNS,
    LEAK_MARKER,
    MATRIX1_HEADERS,
    MATRIX2_HEADERS,
    default_row,
    label_for,
    make_workbook,
    write_workbook,
)

WORKFLOWS = ((MATRIX1, MATRIX1_HEADERS), (MATRIX2, MATRIX2_HEADERS))
LOGGER = "week_05.dataset_loader"


class LoaderTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self._count = 0
        # Keep loader log lines out of test output without depending on them.
        logger = logging.getLogger(LOGGER)
        handler = logging.NullHandler()
        previous = logger.propagate
        logger.addHandler(handler)
        logger.propagate = False
        self.addCleanup(logger.removeHandler, handler)
        self.addCleanup(setattr, logger, "propagate", previous)

    def path(self) -> Path:
        self._count += 1
        return self.dir / f"book{self._count}.xlsx"

    def load(self, spec, path, **kwargs):
        return load_dataset(spec, path, **kwargs)


class TestBothWorkflowConfigurations(LoaderTestCase):
    def test_each_workflow_loads_its_schema(self):
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                dataset = self.load(spec, make_workbook(self.path(), headers))
                self.assertEqual(dataset.workflow, spec.name)
                self.assertEqual(dataset.reference_description, spec.reference_description)
                self.assertEqual(len(dataset.cases), 100)
                self.assertEqual(len(dataset.reference_labels), 100)
                self.assertEqual(dataset.worksheet_name, "Sheet1")

    def test_matrix1_reference_is_vetology_and_matrix2_is_gold_standard(self):
        self.assertIn("Original Vetology", MATRIX1.reference_description)
        self.assertIn("Gold Standard", MATRIX2.reference_description)

    def test_loader_is_schema_driven_not_position_driven(self):
        """Same cases and labels whatever the column order (M1 vs M2 layout)."""
        m1 = self.load(MATRIX1, make_workbook(self.path(), MATRIX1_HEADERS))
        m2 = self.load(MATRIX2, make_workbook(self.path(), MATRIX2_HEADERS))
        self.assertEqual(m1.cases, m2.cases)
        self.assertEqual({k: dict(v) for k, v in m1.reference_labels.items()},
                         {k: dict(v) for k, v in m2.reference_labels.items()})

    def test_minimal_schema_without_optional_columns(self):
        for spec, _ in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                path = make_workbook(self.path(), REQUIRED_COLUMNS)
                self.assertEqual(len(self.load(spec, path).cases), 100)

    def test_explicit_path_accepts_str_and_path(self):
        path = make_workbook(self.path())
        self.assertEqual(self.load(MATRIX1, str(path)).source_path, path.resolve())
        self.assertEqual(self.load(MATRIX1, path).source_path, path.resolve())

    def test_default_path_comes_from_workflow(self):
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                self.assertEqual(spec.default_input_path.name, spec.input_filename)
                target = self.dir / spec.input_filename
                make_workbook(target, headers)
                relocated = dataclasses.replace(spec, input_dir=self.dir)
                dataset = self.load(relocated, None)
                self.assertEqual(dataset.source_path, target.resolve())

    def test_missing_file(self):
        for spec, _ in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                with self.assertRaisesRegex(FileNotFoundError, spec.name):
                    load_dataset(spec, self.dir / "absent.xlsx")


class TestColumns(LoaderTestCase):
    def test_every_required_column_is_enforced(self):
        self.assertEqual(REQUIRED_COLUMNS[:4], ("CaseID", *REPORT_COLUMNS))
        self.assertEqual(REQUIRED_COLUMNS[4:], CONDITION_KEYS)
        for missing in REQUIRED_COLUMNS:
            headers = [h for h in MATRIX1_HEADERS if h != missing]
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(DatasetError, f"missing: .*{re.escape(missing)}"):
                    load_dataset(MATRIX1, make_workbook(self.path(), headers))

    def test_all_missing_columns_are_listed(self):
        headers = [h for h in MATRIX2_HEADERS if h not in ("pneumonia", "rtm", "CaseID")]
        with self.assertRaises(DatasetError) as ctx:
            load_dataset(MATRIX2, make_workbook(self.path(), headers))
        for name in ("CaseID", "pneumonia", "rtm"):
            self.assertIn(name, str(ctx.exception))

    def test_misspelled_condition_column_is_missing(self):
        headers = ["rtm_" if h == "rtm" else h for h in MATRIX1_HEADERS]
        with self.assertRaisesRegex(DatasetError, "missing: rtm"):
            load_dataset(MATRIX1, make_workbook(self.path(), headers))

    def test_duplicate_header_rejected(self):
        headers = [*MATRIX1_HEADERS, "pneumonia"]
        with self.assertRaisesRegex(DatasetError, "Duplicate column header found: 'pneumonia'"):
            load_dataset(MATRIX1, make_workbook(self.path(), headers))

    def test_duplicate_after_stripping_rejected(self):
        headers = [*MATRIX1_HEADERS, " CaseID "]
        with self.assertRaisesRegex(DatasetError, "Duplicate column header"):
            load_dataset(MATRIX1, make_workbook(self.path(), headers))

    def test_headers_are_stripped_and_blank_headers_ignored(self):
        headers = [f"  {h}  " for h in MATRIX1_HEADERS]
        rows = [[*[default_row(i)[h] for h in MATRIX1_HEADERS], "stray"] for i in range(1, 101)]
        path = write_workbook(self.path(), [*headers, None], rows)
        self.assertEqual(len(self.load(MATRIX1, path).cases), 100)

    def test_worksheet_selection(self):
        path = make_workbook(self.path(), sheet_name="Data", extra_sheets=["Sheet2"])
        with self.assertRaisesRegex(DatasetError, "Worksheet 'Sheet1' not found"):
            load_dataset(MATRIX1, path)
        self.assertEqual(len(self.load(MATRIX1, path, worksheet_name="Data").cases), 100)

    def test_empty_worksheet(self):
        from openpyxl import Workbook

        path = self.path()
        workbook = Workbook()
        workbook.active.title = "Sheet1"
        workbook.save(path)
        with self.assertRaisesRegex(DatasetError, "empty"):
            load_dataset(MATRIX1, path)

    def test_header_only_worksheet_has_no_cases(self):
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                path = write_workbook(self.path(), headers, [])
                with self.assertRaisesRegex(DatasetError, "no populated cases"):
                    load_dataset(spec, path)


class TestLabels(LoaderTestCase):
    def test_exact_twenty_keys_in_canonical_order(self):
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                dataset = self.load(spec, make_workbook(self.path(), headers))
                for case_id, labels in dataset.reference_labels.items():
                    self.assertEqual(tuple(labels), CONDITION_KEYS)
                    self.assertEqual(
                        dict(labels),
                        {c: label_for(case_id, i) for i, c in enumerate(CONDITION_KEYS)},
                    )

    def test_label_whitespace_is_stripped(self):
        def edit(case_id, row):
            row["pneumonia"] = "  Positive \n"
            row["rtm"] = " Negative"
            return row

        dataset = self.load(MATRIX2, make_workbook(self.path(), MATRIX2_HEADERS, edit=edit))
        self.assertEqual(dataset.reference_labels[1]["pneumonia"], "Positive")
        self.assertEqual(dataset.reference_labels[1]["rtm"], "Negative")

    def test_invalid_labels_rejected(self):
        for bad in ("positive", "NEGATIVE", "Abnormal", "Normal", "Uncertain", "Pos", "",
                    None, 1, 0, True):
            for spec, headers in WORKFLOWS:
                with self.subTest(label=bad, workflow=spec.name):
                    def edit(case_id, row, bad=bad):
                        if case_id == 37:
                            row["esophagitis"] = bad
                        return row

                    path = make_workbook(self.path(), headers, edit=edit)
                    with self.assertRaisesRegex(
                        DatasetError, "invalid reference label for CaseID 37, condition "
                                      "'esophagitis'"):
                        load_dataset(spec, path)

    def test_rows_after_the_limit_are_not_validated(self):
        """Week 4 stops reading at the limit; an invalid label in row 101 is ignored."""
        def edit(case_id, row):
            if case_id == 101:
                row["pneumonia"] = "Abnormal"
            return row

        path = make_workbook(self.path(), case_ids=range(1, 102), edit=edit)
        self.assertEqual(len(self.load(MATRIX1, path).cases), 100)

    def test_reference_labels_are_read_only(self):
        dataset = self.load(MATRIX1, make_workbook(self.path()))
        with self.assertRaises(TypeError):
            dataset.reference_labels[1]["pneumonia"] = "Positive"
        with self.assertRaises(TypeError):
            dataset.reference_labels[999] = {}


class TestCaseIds(LoaderTestCase):
    def test_blank_case_ids_are_skipped_and_not_counted(self):
        rows = [None, {**default_row(1), "CaseID": None}, {**default_row(2), "CaseID": "   "}]
        rows += [default_row(i) for i in range(3, 103)]
        dataset = self.load(MATRIX1, write_workbook(self.path(), MATRIX1_HEADERS, rows))
        self.assertEqual(dataset.case_ids, tuple(range(3, 103)))

    def test_duplicate_case_id_rejected(self):
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                ids = [*range(1, 50), 7, *range(50, 101)]
                with self.assertRaisesRegex(DatasetError, "duplicate CaseID found: 7"):
                    load_dataset(spec, make_workbook(self.path(), headers, case_ids=ids))

    def test_whole_float_and_int_duplicate_detected(self):
        ids = [1, 2, 3.0, 3, *range(4, 98)]
        with self.assertRaisesRegex(DatasetError, "duplicate CaseID found: 3"):
            load_dataset(MATRIX1, make_workbook(self.path(), case_ids=ids))

    def test_duplicate_after_the_limit_not_detected(self):
        """Week 4 behaviour: rows after the 100th case are never read."""
        path = make_workbook(self.path(), case_ids=[*range(1, 101), 5])
        self.assertEqual(len(self.load(MATRIX1, path).cases), 100)

    def test_case_id_normalisation(self):
        ids = [1.0, 2, "A-3", "004", 5.5, *range(6, 101)]
        dataset = self.load(MATRIX1, make_workbook(self.path(), case_ids=ids))
        self.assertEqual(dataset.case_ids[:5], (1, 2, "A-3", "004", 5.5))
        self.assertIsInstance(dataset.case_ids[0], int)
        self.assertEqual(set(dataset.reference_labels), set(dataset.case_ids))


class TestFirst100Selection(LoaderTestCase):
    def test_first_100_in_worksheet_order_not_sorted(self):
        ids = [*range(150, 100, -1), *range(1, 76)]  # 125 rows, deliberately unsorted
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                dataset = self.load(spec, make_workbook(self.path(), headers, case_ids=ids))
                self.assertEqual(dataset.case_ids, tuple(ids[:100]))
                self.assertEqual(tuple(dataset.reference_labels), tuple(ids[:100]))

    def test_matrix1_requires_exactly_the_limit(self):
        path = make_workbook(self.path(), case_ids=range(1, 100))
        with self.assertRaisesRegex(DatasetError, "expected 100 populated cases, but loaded 99"):
            load_dataset(MATRIX1, path)

    def test_matrix2_warns_when_fewer_than_limit(self):
        path = make_workbook(self.path(), MATRIX2_HEADERS, case_ids=range(1, 100))
        with self.assertLogs(LOGGER, level="WARNING") as logs:
            dataset = load_dataset(MATRIX2, path)
        self.assertEqual(len(dataset.cases), 99)
        self.assertTrue(any("only 99 populated cases" in m for m in logs.output))

    def test_limit_ranges(self):
        path = make_workbook(self.path(), case_ids=range(1, 151))
        for bad in (0, -1, 101):
            with self.subTest(workflow="matrix1", limit=bad):
                with self.assertRaisesRegex(DatasetError, "between 1 and 100"):
                    load_dataset(MATRIX1, path, limit=bad)
        with self.assertRaisesRegex(DatasetError, "at least 1"):
            load_dataset(MATRIX2, path, limit=0)
        self.assertEqual(len(self.load(MATRIX2, path, limit=150).cases), 150)
        self.assertEqual(self.load(MATRIX1, path, limit=10).case_ids, tuple(range(1, 11)))
        for bad in ("100", 10.0, True):
            with self.subTest(limit=bad):
                with self.assertRaisesRegex(DatasetError, "must be an integer"):
                    load_dataset(MATRIX1, path, limit=bad)


class TestReportFields(LoaderTestCase):
    def test_empty_report_fields(self):
        def edit(case_id, row):
            if case_id == 1:
                row["Findings (original radiologist report)"] = None
                row["Conclusions (original radiologist report)"] = "   "
                row["Recommendations (original radiologist report)"] = ""
            return row

        dataset = self.load(MATRIX1, make_workbook(self.path(), edit=edit))
        first = dataset.cases[0]
        self.assertEqual((first.findings, first.conclusions, first.recommendations), ("", "", ""))
        content = build_human_content(first.to_llm_payload())
        self.assertEqual(content.count("[Not provided]"), 3)

    def test_text_is_stripped_and_values_stringified(self):
        def edit(case_id, row):
            row["Findings (original radiologist report)"] = "  Mild\ncardiomegaly.  \n"
            row["Recommendations (original radiologist report)"] = 42
            return row

        case = self.load(MATRIX2, make_workbook(self.path(), MATRIX2_HEADERS, edit=edit)).cases[0]
        self.assertEqual(case.findings, "Mild\ncardiomegaly.")
        self.assertEqual(case.recommendations, "42")


class TestReferenceLabelSeparation(LoaderTestCase):
    def test_report_case_has_no_label_or_extra_fields(self):
        names = {field.name for field in dataclasses.fields(ReportCase)}
        self.assertEqual(names, {"case_id", "findings", "conclusions", "recommendations"})

    def test_payload_contains_only_original_report_text(self):
        for spec, headers in WORKFLOWS:
            with self.subTest(workflow=spec.name):
                dataset = self.load(spec, make_workbook(self.path(), headers))
                for case in dataset.cases:
                    payload = case.to_llm_payload()
                    self.assertEqual(tuple(payload),
                                     ("findings", "conclusions", "recommendations"))
                    self.assertEqual(payload["findings"], f"Original findings {case.case_id}")
                    text = repr(payload)
                    self.assertNotIn(LEAK_MARKER, text)          # AI, radiologist, legacy
                    self.assertNotIn("CaseID", text)
                    self.assertNotIn("Positive", text)
                    self.assertNotIn("Negative", text)
                    for condition in CONDITION_KEYS:
                        self.assertNotIn(condition, payload)

    def test_messages_built_from_cases_exclude_everything_else(self):
        dataset = self.load(MATRIX1, make_workbook(self.path(), case_ids=range(9001, 9101)))
        for case in dataset.cases:
            human = build_messages(case.to_llm_payload())[1].content
            self.assertNotIn(LEAK_MARKER, human)
            self.assertNotIn(str(case.case_id), human.replace(
                f"Original findings {case.case_id}", "").replace(
                f"Original conclusions {case.case_id}", "").replace(
                f"Original recommendations {case.case_id}", ""))
            for column in AI_COLUMNS:
                self.assertNotIn(column, human)

    def test_labels_are_stored_separately_and_keyed_by_case(self):
        dataset = self.load(MATRIX2, make_workbook(self.path(), MATRIX2_HEADERS))
        self.assertEqual(tuple(dataset.reference_labels), dataset.case_ids)
        self.assertNotIn("Positive", repr(dataset))  # repr never dumps labels
        for case in dataset.cases:
            self.assertFalse(hasattr(case, "labels"))
            self.assertFalse(hasattr(case, "reference_labels"))


class TestWeek4Parity(LoaderTestCase):
    """Same synthetic workbooks through the Week 4 loaders must give identical data."""

    @classmethod
    def setUpClass(cls):
        logging.getLogger("vetology_week4").setLevel(logging.ERROR)
        from week_04.matrix_1.matrix1_data_loader import load_matrix1_dataset
        from week_04.week4_block1_data_loader import load_canine_thorax_dataset

        cls.week4_m1 = staticmethod(load_matrix1_dataset)
        cls.week4_m2 = staticmethod(load_canine_thorax_dataset)

    def _compare(self, spec, week4_cases, week4_labels, week5):
        self.assertEqual(
            [(c.case_id, c.findings, c.conclusions, c.recommendations) for c in week4_cases],
            [(c.case_id, c.findings, c.conclusions, c.recommendations) for c in week5.cases],
        )
        self.assertEqual([c.to_llm_payload() for c in week4_cases],
                         [c.to_llm_payload() for c in week5.cases])
        self.assertEqual(list(week4_labels), list(week5.reference_labels))
        self.assertEqual({k: dict(v) for k, v in week4_labels.items()},
                         {k: dict(v) for k, v in week5.reference_labels.items()})

    def _scenarios(self):
        def messy(case_id, row):
            number = case_id if isinstance(case_id, (int, float)) else 0
            if number % 9 == 0:
                row["Findings (original radiologist report)"] = None
            if number % 11 == 0:
                row["pneumonia"] = " Positive "
            return row

        ids = [*range(130, 100, -1), 4.0, "X-1", *range(5, 100)]
        return {
            "plain 125 rows": dict(case_ids=range(1, 126)),
            "unsorted, mixed ids, messy cells": dict(case_ids=ids, edit=messy),
        }

    def test_matrix1_parity(self):
        for name, options in self._scenarios().items():
            with self.subTest(scenario=name):
                path = make_workbook(self.path(), MATRIX1_HEADERS, **options)
                week4 = self.week4_m1(path)
                self._compare(MATRIX1, week4.cases, week4.ground_truth, self.load(MATRIX1, path))

    def test_matrix2_parity(self):
        for name, options in self._scenarios().items():
            with self.subTest(scenario=name):
                path = make_workbook(self.path(), MATRIX2_HEADERS, **options)
                week4 = self.week4_m2(path)
                self._compare(MATRIX2, week4.cases, week4.gold_labels, self.load(MATRIX2, path))

    def test_matrix2_short_dataset_parity(self):
        path = make_workbook(self.path(), MATRIX2_HEADERS, case_ids=range(1, 61))
        week4 = self.week4_m2(path)
        self._compare(MATRIX2, week4.cases, week4.gold_labels, self.load(MATRIX2, path))

    def test_both_reject_the_same_invalid_inputs(self):
        def bad_label(case_id, row):
            if case_id == 3:
                row["rtm"] = "Normal"
            return row

        invalid = {
            "invalid label": dict(edit=bad_label),
            "duplicate id": dict(case_ids=[1, 2, 2, *range(3, 100)]),
            "missing column": dict(headers=[h for h in MATRIX1_HEADERS if h != "bronchitis"]),
        }
        for name, options in invalid.items():
            with self.subTest(scenario=name):
                path = make_workbook(self.path(), **options)
                for loader in (self.week4_m1, self.week4_m2):
                    with self.assertRaises(ValueError):
                        loader(path)
                for spec in (MATRIX1, MATRIX2):
                    with self.assertRaises(ValueError):
                        load_dataset(spec, path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
