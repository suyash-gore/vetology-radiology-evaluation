"""Offline tests for Matrix 1 Block 2; these tests do not call OpenAI."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from week_04.matrix_1.matrix1_data_loader import REPORT_COLUMNS
from week_04.matrix_1.run_matrix1_single_case_test import (
    build_test_record,
    run_single_case_test,
)
from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS


def make_matrix1_workbook(path: Path) -> None:
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
    for case_id in range(1, 101):
        ws.append([
            case_id,
            f"Original findings {case_id}",
            f"Original conclusions {case_id}",
            f"Original recommendations {case_id}",
            "Original Radiologist value",
            "AI-only findings",
            "AI-only conclusions",
            "AI-only recommendations",
            *["Negative" for _ in CONDITION_KEYS],
        ])
    wb.save(path)


class TestMatrix1SingleCaseTest(unittest.TestCase):
    def test_build_record_excludes_ground_truth(self):
        predictions = {key: "Negative" for key in CONDITION_KEYS}
        record = build_test_record(1, "test-model", json.dumps(predictions), predictions)
        self.assertEqual(record["prompt_version"], "V1.3")
        self.assertEqual(record["status"], "success")
        self.assertEqual(set(record["predictions"]), set(CONDITION_KEYS))
        self.assertNotIn("ground_truth", record)
        self.assertNotIn("ai_report", record)

    def test_fake_classifier_receives_only_original_report_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "matrix1.xlsx"
            output = root / "single_case_test.json"
            make_matrix1_workbook(workbook)
            calls = []

            def fake_classifier(payload):
                calls.append(payload)
                return json.dumps({key: "Negative" for key in CONDITION_KEYS})

            record = run_single_case_test(
                workbook,
                case_id="7",
                output_path=output,
                classifier=fake_classifier,
                model_name="offline-test-model",
            )

            self.assertEqual(record["case_id"], 7)
            self.assertEqual(len(calls), 1)
            self.assertEqual(
                set(calls[0]),
                {"findings", "conclusions", "recommendations"},
            )
            self.assertEqual(calls[0]["findings"], "Original findings 7")
            self.assertNotIn("AI-only", str(calls[0]))
            self.assertNotIn("CaseID", str(calls[0]))
            self.assertTrue(output.is_file())

            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["case_id"], 7)
            self.assertEqual(len(saved["predictions"]), 20)
            self.assertNotIn("ground_truth", saved)

    def test_rejects_case_id_outside_first_100(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "matrix1.xlsx"
            make_matrix1_workbook(workbook)
            with self.assertRaisesRegex(ValueError, "not found"):
                run_single_case_test(
                    workbook,
                    case_id="101",
                    output_path=root / "out.json",
                    classifier=lambda payload: "{}",
                    model_name="offline-test-model",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
