"""Offline tests for the Matrix 1 Block 1 data loader; no API calls."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from week_04.matrix_1.matrix1_data_loader import (
    CASE_LIMIT,
    REPORT_COLUMNS,
    load_matrix1_dataset,
)
from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS


class TestMatrix1DataLoader(unittest.TestCase):
    def _make_workbook(self, path: Path, case_count: int = 100) -> None:
        headers = [
            "CaseID",
            *REPORT_COLUMNS,
            "Original Radiologist",
            "Findings (AI report)",
            "Conclusions (AI report)",
            "Recommendations (AI report)",
            *CONDITION_KEYS,
        ]
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(headers)
        for case_id in range(1, case_count + 1):
            row = [
                case_id,
                f"Original findings {case_id}",
                f"Original conclusions {case_id}",
                f"Original recommendations {case_id}",
                "Do not use this field",
                "AI findings must not be sent",
                "AI conclusions must not be sent",
                "AI recommendations must not be sent",
                *[
                    "Positive" if (case_id + i) % 2 else "Negative"
                    for i in range(len(CONDITION_KEYS))
                ],
            ]
            ws.append(row)
        wb.save(path)

    def test_loads_first_100_and_separates_ground_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix1.xlsx"
            self._make_workbook(path, case_count=125)
            dataset = load_matrix1_dataset(path)
            self.assertEqual(len(dataset.cases), CASE_LIMIT)
            self.assertEqual(len(dataset.ground_truth), CASE_LIMIT)
            self.assertEqual(dataset.cases[0].case_id, 1)
            self.assertEqual(dataset.cases[-1].case_id, 100)
            self.assertEqual(len(dataset.ground_truth[1]), 20)

    def test_llm_payload_contains_only_original_report_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix1.xlsx"
            self._make_workbook(path)
            dataset = load_matrix1_dataset(path)
            payload = dataset.cases[0].to_llm_payload()
            self.assertEqual(
                set(payload),
                {"findings", "conclusions", "recommendations"},
            )
            self.assertNotIn("AI findings must not be sent", str(payload))
            self.assertNotIn("CaseID", str(payload))
            self.assertNotIn("Positive", str(payload))
            self.assertNotIn("Negative", str(payload))

    def test_rejects_invalid_ground_truth_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix1.xlsx"
            self._make_workbook(path)
            wb = __import__("openpyxl").load_workbook(path)
            ws = wb["Sheet1"]
            ws.cell(2, 9, "Abnormal")
            wb.save(path)
            with self.assertRaisesRegex(ValueError, "Invalid ground-truth label"):
                load_matrix1_dataset(path)

    def test_rejects_limit_above_100(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix1.xlsx"
            self._make_workbook(path)
            with self.assertRaises(ValueError):
                load_matrix1_dataset(path, limit=101)


if __name__ == "__main__":
    unittest.main(verbosity=2)
