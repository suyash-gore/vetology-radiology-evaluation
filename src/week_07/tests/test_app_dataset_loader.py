"""Application-aware dataset and reference loading (synthetic workbooks only)."""
from __future__ import annotations

import logging

from week_07 import dataset_loader
from week_07.app_dataset_loader import (
    ApplicationDataset,
    DatasetError,
    check_cross_matrix,
    load_application_dataset,
    required_columns,
)
from week_07.applications import CANINE_THORAX
from week_07.evaluation.app_reference_loader import (
    AmbiguousReferenceError,
    ReferenceLoadError,
    compare_application_reference_loaders,
    load_application_reference,
    load_matrix1_style_reference,
)
from week_07.tests.app_fixtures import SyntheticAppRepo, app_reference, headers
from week_07.tests.fixtures import LEAK_MARKER, write_workbook
from week_07.tests.support import OfflineTestCase

NORMALISED = ("pulmonary_nodules", "esophagitis", "pneumonia")


class AppRepoCase(OfflineTestCase):
    key = "feline_thorax"

    def setUp(self):
        super().setUp()
        for name in ("week_07",):
            logging.getLogger(name).setLevel(logging.CRITICAL)
            self.addCleanup(logging.getLogger(name).setLevel, logging.NOTSET)
        self.repo = SyntheticAppRepo(self.key)
        self.addCleanup(self.repo.cleanup)
        self.app = self.repo.app


class TestFelineMatrix1Normalisation(AppRepoCase):
    def setUp(self):
        super().setUp()
        self.repo.write_inputs()

    def test_three_columns_normalised_and_counted(self):
        dataset = load_application_dataset(self.app, "matrix1")
        for case_id in dataset.case_ids:
            self.assertEqual(dict(dataset.reference_labels[case_id]),
                             app_reference(self.app, case_id, 0))
        self.assertEqual(set(dataset.normalized_label_counts), set(NORMALISED))
        for condition in NORMALISED:
            counts = dataset.normalized_label_counts[condition]
            self.assertEqual(sum(counts.values()), 100)
            self.assertLessEqual(set(counts), {"Normal", "Abnormal"})

    def test_normal_in_any_other_column_rejected(self):
        def edit(case_id, row):
            if case_id == 7:
                row["bronchitis"] = "Normal"
            return row
        self.repo.write_inputs(edit_m1=edit)
        with self.assertRaisesRegex(DatasetError, "'bronchitis': 'Normal'"):
            load_application_dataset(self.app, "matrix1")

    def test_positive_negative_still_accepted_in_normalised_columns(self):
        def edit(case_id, row):
            row["pneumonia"] = "Positive"
            return row
        self.repo.write_inputs(edit_m1=edit)
        dataset = load_application_dataset(self.app, "matrix1")
        self.assertTrue(all(labels["pneumonia"] == "Positive"
                            for labels in dataset.reference_labels.values()))

    def test_unknown_source_label_rejected(self):
        def edit(case_id, row):
            if case_id == 3:
                row["esophagitis"] = "Equivocal"
            return row
        self.repo.write_inputs(edit_m1=edit)
        with self.assertRaisesRegex(DatasetError, "Equivocal"):
            load_application_dataset(self.app, "matrix1")

    def test_trimmed_source_label_normalised_by_batch_but_not_week4_rules(self):
        def edit(case_id, row):
            if case_id == 4:
                row["pneumonia"] = " Normal "
            return row
        self.repo.write_inputs(edit_m1=edit)
        self.assertEqual(load_application_dataset(self.app, "matrix1")
                         .reference_labels[4]["pneumonia"], "Negative")
        with self.assertRaises(ReferenceLoadError):
            load_matrix1_style_reference(self.app, "matrix1", self.repo.m1.default_input_path)

    def test_evaluation_loader_applies_the_same_normalisation(self):
        reference = load_application_reference(self.app, "matrix1",
                                               self.repo.m1.default_input_path)
        for case_id in reference.case_ids:
            self.assertEqual(dict(reference.labels[case_id]),
                             app_reference(self.app, case_id, 0))
        self.assertEqual(compare_application_reference_loaders(
            self.app, "matrix1", self.repo.m1.default_input_path), [])


class TestNoNormalisationElsewhere(AppRepoCase):
    def test_feline_matrix2_not_normalised(self):
        def edit(case_id, row):
            if case_id == 5:
                row["pneumonia"] = "Normal"
            return row
        self.repo.write_inputs(edit_m2=edit)
        with self.assertRaisesRegex(DatasetError, "'pneumonia': 'Normal'"):
            load_application_dataset(self.app, "matrix2")
        with self.assertRaises(AmbiguousReferenceError):
            load_application_reference(self.app, "matrix2", self.repo.m2.default_input_path)

    def test_canine_abdomen_not_normalised(self):
        repo = SyntheticAppRepo("canine_abdomen")
        self.addCleanup(repo.cleanup)

        def edit(case_id, row):
            if case_id == 2:
                row["gastritis"] = "Abnormal"
            return row
        repo.write_inputs(edit_m1=edit)
        self.assertEqual(dict(repo.app.label_normalization("matrix1")), {})
        with self.assertRaisesRegex(DatasetError, "'gastritis': 'Abnormal'"):
            load_application_dataset(repo.app, "matrix1")
        with self.assertRaises(ReferenceLoadError):
            load_application_reference(repo.app, "matrix1", repo.m1.default_input_path)

    def test_canine_thorax_loader_unchanged(self):
        self.assertEqual(dict(CANINE_THORAX.label_normalization("matrix1")), {})
        self.assertEqual(dataset_loader.REQUIRED_COLUMNS, required_columns(CANINE_THORAX))


class TestSchemaAndCases(AppRepoCase):
    key = "canine_abdomen"

    def test_exact_case_counts_and_blank_rows(self):
        self.repo.write_inputs(m2_blank_rows=300)
        self.assertEqual(len(load_application_dataset(self.app, "matrix1").cases), 100)
        m2 = load_application_dataset(self.app, "matrix2")
        self.assertEqual(m2.case_ids, tuple(range(1, 101)))
        self.assertEqual(len(load_application_reference(
            self.app, "matrix2", self.repo.m2.default_input_path).case_ids), 100)

    def test_matrix1_requires_exactly_100(self):
        self.repo.write_inputs(m1_cases=range(1, 100))
        with self.assertRaisesRegex(DatasetError, "expected 100"):
            load_application_dataset(self.app, "matrix1")
        with self.assertRaises(DatasetError):
            load_application_dataset(self.app, "matrix1", limit=101)

    def test_duplicate_case_ids_rejected(self):
        self.repo.write_inputs(m1_cases=[1, 2, 2, *range(3, 99)])
        with self.assertRaisesRegex(DatasetError, "duplicate CaseID"):
            load_application_dataset(self.app, "matrix1")

    def test_missing_condition_column_rejected(self):
        cols = [h for h in headers(self.app) if h != "hepatomegaly"]
        write_workbook(self.repo.m1.default_input_path, cols, [])
        with self.assertRaisesRegex(DatasetError, "hepatomegaly"):
            load_application_dataset(self.app, "matrix1")

    def test_wrong_application_columns_rejected(self):
        feline = SyntheticAppRepo("feline_thorax")
        self.addCleanup(feline.cleanup)
        feline.write_inputs()
        with self.assertRaisesRegex(DatasetError, "missing"):
            load_application_dataset(self.app, "matrix1", feline.m1.default_input_path)

    def test_worksheet_must_exist(self):
        self.repo.write_inputs()
        with self.assertRaisesRegex(DatasetError, "Worksheet"):
            load_application_dataset(self.app, "matrix1", worksheet_name="Data")

    def test_spec_of_another_application_refused(self):
        self.repo.write_inputs()
        feline = SyntheticAppRepo("feline_thorax")
        self.addCleanup(feline.cleanup)
        with self.assertRaises(DatasetError):
            load_application_dataset(self.app, feline.m1)


class TestPayloadBoundary(AppRepoCase):
    def test_payload_has_only_three_original_report_fields(self):
        self.repo.write_inputs()
        dataset = load_application_dataset(self.app, "matrix1")
        for case in dataset.cases:
            payload = case.to_llm_payload()
            self.assertEqual(set(payload), {"findings", "conclusions", "recommendations"})
            text = " ".join(payload.values())
            self.assertNotIn(LEAK_MARKER, text)
            self.assertNotIn("Positive", text)
            self.assertNotIn("Negative", text)
            self.assertNotIn("Abnormal", text)

    def test_repr_has_no_labels_or_text(self):
        self.repo.write_inputs()
        dataset = load_application_dataset(self.app, "matrix1")
        self.assertIsInstance(dataset, ApplicationDataset)
        text = repr(dataset)
        for forbidden in ("Positive", "Negative", "Synthetic", "pneumonia"):
            self.assertNotIn(forbidden, text)

    def test_reference_labels_read_only(self):
        self.repo.write_inputs()
        dataset = load_application_dataset(self.app, "matrix1")
        with self.assertRaises(TypeError):
            dataset.reference_labels[1]["pneumonia"] = "Positive"  # type: ignore[index]


class TestCrossMatrix(AppRepoCase):
    def test_identical_cases_accepted(self):
        self.repo.write_inputs()
        result = check_cross_matrix(self.app, self.repo.m1.default_input_path,
                                    self.repo.m2.default_input_path)
        self.assertEqual(result.case_ids, tuple(range(1, 101)))

    def test_different_case_ids_rejected(self):
        self.repo.write_inputs(m2_cases=[*range(1, 100), 101])
        with self.assertRaisesRegex(DatasetError, "same CaseIDs"):
            check_cross_matrix(self.app, self.repo.m1.default_input_path,
                               self.repo.m2.default_input_path)

    def test_different_order_rejected(self):
        self.repo.write_inputs(m2_cases=[2, 1, *range(3, 101)])
        with self.assertRaisesRegex(DatasetError, "different order"):
            check_cross_matrix(self.app, self.repo.m1.default_input_path,
                               self.repo.m2.default_input_path)

    def test_different_report_text_rejected(self):
        def edit(case_id, row):
            if case_id == 42:
                row["Conclusions (original radiologist report)"] = "Edited conclusions"
            return row
        self.repo.write_inputs(edit_m2=edit)
        with self.assertRaisesRegex(DatasetError, r"report text for CaseIDs \[42\]"):
            check_cross_matrix(self.app, self.repo.m1.default_input_path,
                               self.repo.m2.default_input_path)

    def test_matrix2_with_fewer_cases_rejected(self):
        self.repo.write_inputs(m2_cases=range(1, 90))
        with self.assertRaisesRegex(DatasetError, "case counts"):
            check_cross_matrix(self.app, self.repo.m1.default_input_path,
                               self.repo.m2.default_input_path)

    def test_labels_are_not_compared(self):
        self.repo.write_inputs()  # Matrix 1 and Matrix 2 labels differ (variant 0 vs 1)
        m1 = load_application_dataset(self.app, "matrix1")
        m2 = load_application_dataset(self.app, "matrix2")
        self.assertNotEqual(dict(m1.reference_labels[1]), dict(m2.reference_labels[1]))
        check_cross_matrix(self.app, self.repo.m1.default_input_path,
                           self.repo.m2.default_input_path)
