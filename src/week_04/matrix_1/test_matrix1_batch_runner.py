"""Offline tests for the Matrix 1 batch runner; no OpenAI API calls."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from week_04.matrix_1 import run_matrix1_batch as runner_module


class FakeCase:
    def __init__(self, case_id):
        self.case_id = case_id

    def to_llm_payload(self):
        return {
            "findings": f"findings {self.case_id}",
            "conclusions": "",
            "recommendations": "",
        }


class FakeDataset:
    def __init__(self):
        self.cases = tuple(FakeCase(i) for i in range(1, 101))
        # Ground truth exists on the loaded dataset but is not passed to run_batch.
        self.ground_truth = {i: {"condition": "Negative"} for i in range(1, 101)}


class TestMatrix1BatchRunner(unittest.TestCase):
    def test_uses_matrix1_output_paths_and_100_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "matrix_1"
            fake_dataset = FakeDataset()
            expected = {"total": 100, "skipped": 0, "succeeded": 100, "failed": 0}

            with patch.object(
                runner_module, "load_matrix1_dataset", return_value=fake_dataset
            ) as loader, patch.object(
                runner_module, "run_batch", return_value=expected
            ) as batch:
                result = runner_module.run_matrix1_batch(
                    input_path="matrix1.xlsx",
                    output_dir=output_dir,
                    max_attempts=2,
                )

            self.assertEqual(result, expected)
            loader.assert_called_once_with(
                input_path="matrix1.xlsx",
                limit=100,
            )
            args = batch.call_args.kwargs
            self.assertEqual(len(args["cases"]), 100)
            self.assertEqual(args["results_path"], output_dir / "predictions.jsonl")
            self.assertEqual(args["errors_path"], output_dir / "errors.jsonl")
            self.assertEqual(args["max_attempts"], 2)
            self.assertFalse((output_dir / "predictions.jsonl").exists())

    def test_rejects_invalid_attempt_count(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            runner_module.run_matrix1_batch(
                input_path="not-read.xlsx",
                max_attempts=0,
            )

    def test_rejects_dataset_not_containing_100_cases(self):
        class ShortDataset:
            cases = tuple(FakeCase(i) for i in range(1, 100))
            ground_truth = {}

        with patch.object(
            runner_module, "load_matrix1_dataset", return_value=ShortDataset()
        ):
            with self.assertRaisesRegex(ValueError, "exactly 100"):
                runner_module.run_matrix1_batch(
                    input_path="matrix1.xlsx",
                    output_dir="unused",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
