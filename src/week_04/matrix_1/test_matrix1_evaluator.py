import unittest
from week_04.matrix_1.matrix1_evaluator import CONDITIONS, calculate_condition_metrics

class Matrix1EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.gt = {1: {c: "Positive" for c in CONDITIONS}, 2: {c: "Negative" for c in CONDITIONS}}
        self.pred = {1: {c: "Positive" for c in CONDITIONS}, 2: {c: "Negative" for c in CONDITIONS}}

    def test_perfect_predictions(self):
        metrics = calculate_condition_metrics(self.gt, self.pred)
        for condition in CONDITIONS:
            self.assertEqual(metrics[condition]["tp"], 1)
            self.assertEqual(metrics[condition]["tn"], 1)
            self.assertEqual(metrics[condition]["fn"], 0)
            self.assertEqual(metrics[condition]["fp"], 0)
            self.assertEqual(metrics[condition]["accuracy"], 1.0)
            self.assertEqual(metrics[condition]["sensitivity"], 1.0)
            self.assertEqual(metrics[condition]["specificity"], 1.0)
            self.assertEqual(metrics[condition]["precision"], 1.0)
            self.assertEqual(metrics[condition]["f1"], 1.0)

    def test_mismatch_counts(self):
        for c in CONDITIONS:
            self.pred[1][c] = "Negative"
            self.pred[2][c] = "Positive"
        metrics = calculate_condition_metrics(self.gt, self.pred)
        for condition in CONDITIONS:
            self.assertEqual(metrics[condition]["fn"], 1)
            self.assertEqual(metrics[condition]["fp"], 1)
            self.assertEqual(metrics[condition]["tp"], 0)
            self.assertEqual(metrics[condition]["tn"], 0)
            self.assertEqual(metrics[condition]["accuracy"], 0.0)

    def test_condition_totals_equal_case_count(self):
        metrics = calculate_condition_metrics(self.gt, self.pred)
        for condition in CONDITIONS:
            self.assertEqual(metrics[condition]["total"], 2)

if __name__ == "__main__":
    unittest.main()
