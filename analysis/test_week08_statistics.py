"""Focused tests for analysis/week08_statistics.py helper functions.

These use synthetic data only; no confidential inputs are needed.
Run:  python -m unittest analysis/test_week08_statistics.py
"""
import importlib.util
import math
import unittest
from pathlib import Path

import numpy as np

_SPEC = importlib.util.spec_from_file_location(
    "week08_statistics", Path(__file__).with_name("week08_statistics.py"))
st = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(st)


class TestMetrics(unittest.TestCase):
    def test_rates_and_f1_definition(self):
        r = st.rates(127, 31, 1803, 39)  # Week 4 Matrix 2 registered counts
        self.assertAlmostEqual(float(r["accuracy"]), 0.965)
        self.assertAlmostEqual(float(r["f1"]), 254 / 324)

    def test_f1_zero_positive_conditions(self):
        # TP = FN = 0, FP > 0 -> precision 0, F1 0, sensitivity undefined
        r = st.rates(0, 0, 98, 2)
        self.assertTrue(math.isnan(float(r["sensitivity"])))
        self.assertEqual(float(r["precision"]), 0.0)
        self.assertEqual(float(r["f1"]), 0.0)
        # TP = FN = FP = 0 -> precision and F1 undefined
        r = st.rates(0, 0, 100, 0)
        self.assertTrue(math.isnan(float(r["precision"])))
        self.assertTrue(math.isnan(float(r["f1"])))

    def test_wilson(self):
        lo, hi = st.wilson(0, 59)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.0611, places=3)
        self.assertIsNone(st.wilson(0, 0))


class TestAgreement(unittest.TestCase):
    def setUp(self):
        # 2x2: n11=2, n10=3, n01=1, n00=4
        self.a = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
        self.b = np.array([1, 1, 0, 0, 0, 1, 0, 0, 0, 0])

    def test_specific_agreement(self):
        sa = st.specific_agreement(self.a, self.b)
        self.assertEqual((sa["both_pos"], sa["both_neg"], sa["a_pos_b_neg"], sa["a_neg_b_pos"]), (2, 4, 3, 1))
        self.assertAlmostEqual(sa["positive_agreement"], 4 / 8)
        self.assertAlmostEqual(sa["negative_agreement"], 8 / 12)

    def test_specific_agreement_undefined(self):
        sa = st.specific_agreement(np.zeros(5), np.zeros(5))
        self.assertIsNone(sa["positive_agreement"])
        self.assertEqual(sa["negative_agreement"], 1.0)

    def test_kappa(self):
        po, pe = 0.6, 0.5 * 0.3 + 0.5 * 0.7
        self.assertAlmostEqual(st.kappa(self.a, self.b), (po - pe) / (1 - pe))
        self.assertIsNone(st.kappa(np.ones(4), np.ones(4)))


class TestTests(unittest.TestCase):
    def test_mcnemar_exact(self):
        self.assertIsNone(st.mcnemar_exact(0, 0))
        self.assertAlmostEqual(st.mcnemar_exact(0, 5), 2 / 32)
        self.assertEqual(st.mcnemar_exact(3, 3), 1.0)

    def test_holm(self):
        adj = st.holm([0.01, None, 0.04, 0.03])
        self.assertIsNone(adj[1])
        self.assertAlmostEqual(adj[0], 0.03)
        self.assertAlmostEqual(adj[3], 0.06)
        self.assertAlmostEqual(adj[2], 0.06)  # monotone

    def test_percentile_interval_counts_undefined(self):
        ci, und = st.pct_interval([0.1, float("nan"), 0.2, 0.3])
        self.assertEqual(und, 1)
        self.assertLessEqual(ci[0], ci[1])


if __name__ == "__main__":
    unittest.main()
