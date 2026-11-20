"""Dataset loading: Week 5 input-data and reference-label semantics (synthetic workbooks)."""
from __future__ import annotations

from week_07.dataset_loader import (
    CASE_ID_COLUMN,
    FINDINGS_COLUMN,
    DatasetError,
    load_dataset,
)
from week_07.tests.fixtures import (
    LEAK_MARKER,
    MATRIX1_HEADERS,
    MATRIX2_HEADERS,
    SyntheticRepo,
    make_workbook,
    reference_labels,
)
from week_07.tests.support import OfflineTestCase, quiet


class LoaderTestCase(OfflineTestCase):
    def setUp(self):
        super().setUp()
        quiet(self, "week_07")
        self.repo = SyntheticRepo()
        self.addCleanup(self.repo.cleanup)
        self.m1, self.m2 = self.repo.m1, self.repo.m2


class TestMatrix1(LoaderTestCase):
    def test_first_100_of_more_rows(self):
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, range(1, 106))
        dataset = load_dataset(self.m1)
        self.assertEqual(dataset.case_ids, tuple(range(1, 101)))
        self.assertEqual(dataset.workflow, "matrix1")
        self.assertEqual(dataset.reference_description, "Original Vetology condition scores")

    def test_requires_exactly_100(self):
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, range(1, 100))
        with self.assertRaises(DatasetError):
            load_dataset(self.m1)

    def test_limit_range(self):
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, range(1, 101))
        for bad in (0, 101, True, 1.0):
            with self.subTest(limit=bad), self.assertRaises(DatasetError):
                load_dataset(self.m1, limit=bad)

    def test_reference_labels_are_held_separately_and_read_only(self):
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, range(1, 101))
        dataset = load_dataset(self.m1)
        self.assertEqual(dict(dataset.reference_labels[7]), reference_labels(7, 0))
        with self.assertRaises(TypeError):
            dataset.reference_labels[7]["pneumonia"] = "Positive"  # type: ignore[index]
        self.assertNotIn("Positive", repr(dataset))


class TestMatrix2(LoaderTestCase):
    def test_columns_located_by_name_in_any_order(self):
        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, range(1, 101), variant=1)
        dataset = load_dataset(self.m2)
        self.assertEqual(len(dataset.cases), 100)
        self.assertEqual(dataset.reference_description, "Gold Standard condition scores")
        self.assertEqual(dict(dataset.reference_labels[3]), reference_labels(3, 1))
        self.assertEqual(dataset.cases[2].findings, "Synthetic findings for report 3.")

    def test_limit_and_short_workbook_warning(self):
        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, range(1, 11))
        self.assertEqual(len(load_dataset(self.m2, limit=5).cases), 5)
        with self.assertLogs("week_07.dataset_loader", "WARNING"):
            self.assertEqual(len(load_dataset(self.m2).cases), 10)


class TestSemantics(LoaderTestCase):
    def test_payload_contains_only_three_original_report_fields(self):
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, range(1, 101))
        for case in load_dataset(self.m1).cases:
            payload = case.to_llm_payload()
            self.assertEqual(set(payload), {"findings", "conclusions", "recommendations"})
            text = " ".join(payload.values())
            self.assertNotIn(LEAK_MARKER, text)
            self.assertNotIn("Positive", text)
            self.assertNotIn("Negative", text)

    def test_case_id_handling(self):
        ids = [1.0, 2, "A-3", 4]

        def edit(case_id, row):
            return row

        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, ids, edit=edit)
        dataset = load_dataset(self.m2, limit=4)
        self.assertEqual(dataset.case_ids, (1, 2, "A-3", 4))
        self.assertIsInstance(dataset.case_ids[0], int)

    def test_blank_case_ids_skipped_and_not_counted(self):
        def edit(case_id, row):
            if case_id in (2, 5):
                row[CASE_ID_COLUMN] = "   " if case_id == 2 else None
            return row

        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, range(1, 8), edit=edit)
        self.assertEqual(load_dataset(self.m2, limit=4).case_ids, (1, 3, 4, 6))

    def test_duplicate_case_id_rejected(self):
        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, [1, 2, 2])
        with self.assertRaises(DatasetError):
            load_dataset(self.m2, limit=3)

    def test_labels_trimmed_but_otherwise_exact(self):
        def padded(case_id, row):
            row["pneumonia"] = f"  {row['pneumonia']} "
            return row

        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, range(1, 4), edit=padded)
        dataset = load_dataset(self.m2, limit=3)
        self.assertIn(dataset.reference_labels[1]["pneumonia"], ("Positive", "Negative"))

        def lower(case_id, row):
            row["pneumonia"] = "positive"
            return row

        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, range(1, 4), edit=lower)
        with self.assertRaises(DatasetError):
            load_dataset(self.m2, limit=3)

    def test_missing_required_column(self):
        headers = tuple(h for h in MATRIX1_HEADERS if h != FINDINGS_COLUMN)
        make_workbook(self.m1.default_input_path, headers, range(1, 101))
        with self.assertRaisesRegex(DatasetError, "missing"):
            load_dataset(self.m1)

    def test_text_cleaning(self):
        def edit(case_id, row):
            row[FINDINGS_COLUMN] = None if case_id == 1 else "  padded text  "
            return row

        make_workbook(self.m2.default_input_path, MATRIX2_HEADERS, range(1, 3), edit=edit)
        cases = load_dataset(self.m2, limit=2).cases
        self.assertEqual((cases[0].findings, cases[1].findings), ("", "padded text"))

    def test_missing_workbook_and_sheet(self):
        with self.assertRaises(FileNotFoundError):
            load_dataset(self.m1)
        make_workbook(self.m1.default_input_path, MATRIX1_HEADERS, range(1, 101),
                      sheet_name="Other")
        with self.assertRaisesRegex(DatasetError, "Worksheet"):
            load_dataset(self.m1)
