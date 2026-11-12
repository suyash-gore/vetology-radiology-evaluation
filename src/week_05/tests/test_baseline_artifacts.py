"""Real-data verification against the Week 4 baseline artifacts A1-A6.

The artifacts are confidential and gitignored (``data/``); these tests are
skipped automatically when they are absent. Workbooks are generated only in a
temporary directory. No API requests are made and the artifacts are never
modified (their SHA-256 digests are checked before and after).

Approved intentional parity differences (reported, not hidden):

* Matrix 1 vs A5: none, apart from run-dependent cells (input file names and
  the generation timestamp; decision D7).
* Matrix 2 vs A6: A6's Overall Summary "Balanced Accuracy" row is not produced
  (decision D2) — compared against an in-memory copy of A6 with that row
  removed; Execution Log C8 carries the failure-count source disclosure
  (decision D6); input file names are run-dependent (D7).
"""
from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from week_05.conditions import CONDITION_KEYS
from week_05.config import MATRIX1, MATRIX2, REPO_ROOT
from week_05.evaluation.evaluate import evaluate_workflow, write_evaluation_workbook
from week_05.evaluation.matrix2_workbook import BALANCED_ACCURACY_ROW, FAILURE_COUNT_SOURCE
from week_05.evaluation.reference_loader import compare_reference_loaders
from week_05.evaluation.workbook_compare import compare_workbooks

DATA = REPO_ROOT / "data"
A1 = DATA / "week_04_inputs" / "Vetology_Matrix1_First100_Encoded.xlsx"
A2 = DATA / "week_04_inputs" / "1_canine_thorax_gold_standard_score_draft.xlsx"
A3 = DATA / "week_04_baseline" / "matrix_1" / "predictions.jsonl"
A4 = DATA / "week_04_baseline" / "matrix_2" / "predictions.jsonl"
A5 = DATA / "week_04_baseline" / "Evaluation_Workbook_v1.xlsx"
A6 = DATA / "week_04_baseline" / "Evaluation Workbook v2.xlsx"
ARTIFACTS = {
    "A1": (A1, "3f1a17b7046b2e1ff7e7d857e24b2f421f56392040a624b90836818b1176ef25"),
    "A2": (A2, "d1fab50ee938f0608d7487f87e6650a28846cc5253dd6f170dce3fa990896fa4"),
    "A3": (A3, "78814024fade03cc1e0a673166efca8cfe473a6977d44f632b20d3583052c8c1"),
    "A4": (A4, "70fe93918f2e941fec32fe065c17841ce325faa6fa40daafbf17b6f3ae092f70"),
    "A5": (A5, "7237d3cf2b5c9c0d040bf2bae682785baf6d279f77963ca4be0e45816fe9636c"),
    "A6": (A6, "2ff2bffa33d4ec74ab29c171d3b548cb3ba74f98f0bf51627f37e0ab0893f82a"),
}
AVAILABLE = all(path.is_file() for path, _ in ARTIFACTS.values())
M1_DYNAMIC = [("Execution Log", "B3"), ("Execution Log", "B4"), ("Execution Log", "B14")]
M2_DYNAMIC = [("Execution Log", "B3"), ("Execution Log", "B4")]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(AVAILABLE, "baseline artifacts A1-A6 are not present in data/")
class TestBaselineArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("week_05").setLevel(logging.ERROR)
        for name, (path, digest) in ARTIFACTS.items():
            if sha256(path) != digest:
                raise AssertionError(f"{name} is not the transferred baseline artifact")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.m1 = evaluate_workflow(MATRIX1, A1, A3)
        cls.m2 = evaluate_workflow(MATRIX2, A2, A4)
        cls.m1_book = write_evaluation_workbook(MATRIX1, cls.m1, cls.out / "m1.xlsx")
        cls.m2_book = write_evaluation_workbook(MATRIX2, cls.m2, cls.out / "m2.xlsx")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
        for name, (path, digest) in ARTIFACTS.items():
            assert sha256(path) == digest, f"{name} was modified"

    # -- reference loading ---------------------------------------------------
    def test_reference_loaders_agree_on_both_inputs(self):
        self.assertEqual(compare_reference_loaders(MATRIX1, A1), [])
        self.assertEqual(compare_reference_loaders(MATRIX2, A2), [])

    # -- metric reproduction ---------------------------------------------------
    def test_matrix1_baseline_counts_and_rates(self):
        m = self.m1.micro
        self.assertEqual((m.tp, m.fn, m.tn, m.fp, m.total), (128, 921, 913, 38, 2000))
        self.assertEqual([round(v * 100, 2) for v in
                          (m.accuracy, m.sensitivity, m.specificity, m.precision, m.f1)],
                         [52.05, 12.20, 96.00, 77.11, 21.07])

    def test_matrix1_metrics_equal_week4_code(self):
        from week_04.matrix_1.matrix1_evaluator import (
            calculate_condition_metrics,
            load_matrix1_inputs,
        )

        truth, preds = load_matrix1_inputs(A1, A3)
        self.assertEqual({c: self.m1.per_condition[c].as_dict() for c in CONDITION_KEYS},
                         calculate_condition_metrics(truth, preds))

    def test_matrix2_baseline_counts_and_rates(self):
        m = self.m2.micro
        self.assertEqual((m.tp, m.fn, m.tn, m.fp, m.total), (127, 31, 1803, 39, 2000))
        self.assertEqual([round(v * 100, 2) for v in
                          (m.accuracy, m.sensitivity, m.specificity, m.precision, m.f1)],
                         [96.50, 80.38, 97.88, 76.51, 78.40])

    def test_matrix2_f1_edge_case_observed_in_a6(self):
        rows = self.m2.per_condition["perihilar_infiltrate"]
        self.assertEqual((rows.tp, rows.fn, rows.fp), (0, 2, 2))
        self.assertIsNone(rows.f1)

    # -- workbook parity -------------------------------------------------------
    def test_matrix1_workbook_matches_a5(self):
        diffs = compare_workbooks(A5, self.m1_book, ignore_cells=M1_DYNAMIC,
                                  float_tolerance=1e-12)
        self.assertEqual(diffs, [])

    def test_matrix2_workbook_matches_a6_except_approved_differences(self):
        baseline = load_workbook(A6)
        removed = [c.value for c in baseline["Overall Summary"][BALANCED_ACCURACY_ROW]]
        self.assertEqual(removed[0], "Balanced Accuracy")
        baseline["Overall Summary"].delete_rows(BALANCED_ACCURACY_ROW)   # in memory only
        diffs = compare_workbooks(baseline, self.m2_book, ignore_cells=M2_DYNAMIC,
                                  float_tolerance=1e-12)
        self.assertEqual(diffs, [f"[Execution Log!C8] value None != {FAILURE_COUNT_SOURCE!r}"])

    def test_dynamic_cells_hold_the_actual_input_names(self):
        m1 = load_workbook(self.m1_book)["Execution Log"]
        self.assertEqual((m1["B3"].value, m1["B4"].value), (A1.name, A3.name))
        m2 = load_workbook(self.m2_book)["Execution Log"]
        self.assertEqual((m2["B3"].value, m2["B4"].value), (A4.name, A2.name))

    # -- documented run-to-run variation ---------------------------------------
    def test_a3_a4_run_to_run_variation_is_documented_not_altered(self):
        def load(path):
            return {json.loads(line)["case_id"]: json.loads(line)["predictions"]
                    for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}

        a3, a4 = load(A3), load(A4)
        diffs = [(c, k) for c in a3 for k in CONDITION_KEYS if a3[c][k] != a4[c][k]]
        self.assertEqual(len(diffs), 8)
        self.assertEqual(len({c for c, _ in diffs}), 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
