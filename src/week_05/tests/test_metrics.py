"""Offline tests for the evaluation metric engine (synthetic labels only)."""
from __future__ import annotations

import random
import unittest

from week_05.conditions import CONDITION_KEYS
from week_05.evaluation.metrics import (
    ConfusionMetrics,
    condition_metrics,
    count_outcomes,
    f1_score,
    macro_metrics,
    mean_defined,
    metrics_from_counts,
    micro_metrics,
    ratio,
)

P, N = "Positive", "Negative"


def table(rows: dict) -> dict:
    """{case_id: {condition: label}} with unspecified conditions Negative."""
    return {cid: {c: labels.get(c, N) for c in CONDITION_KEYS} for cid, labels in rows.items()}


def random_tables(seed: int, cases: int = 100, positive_rate: float = 0.2):
    rng = random.Random(seed)
    ref = {i: {c: P if rng.random() < positive_rate else N for c in CONDITION_KEYS}
           for i in range(1, cases + 1)}
    pred = {i: {c: P if rng.random() < positive_rate else N for c in CONDITION_KEYS}
            for i in range(1, cases + 1)}
    return ref, pred


class TestPrimitives(unittest.TestCase):
    def test_ratio_and_zero_denominator(self):
        self.assertEqual(ratio(1, 4), 0.25)
        self.assertEqual(ratio(0, 4), 0.0)
        self.assertIsNone(ratio(0, 0))
        self.assertIsNone(ratio(3, 0))

    def test_f1_rules(self):
        self.assertAlmostEqual(f1_score(0.5, 1.0), 2 * 0.5 / 1.5)
        self.assertEqual(f1_score(1.0, 1.0), 1.0)
        self.assertIsNone(f1_score(None, 0.5))
        self.assertIsNone(f1_score(0.5, None))
        self.assertIsNone(f1_score(None, None))
        self.assertIsNone(f1_score(0.0, 0.0))  # Week 4 edge case: undefined, not 0

    def test_mean_defined(self):
        self.assertIsNone(mean_defined([]))
        self.assertIsNone(mean_defined([None, None]))
        self.assertEqual(mean_defined([None, 0.0, 1.0]), 0.5)
        self.assertEqual(mean_defined([0.0, 0.0, 0.0]), 0.0)  # zeros are values, not gaps


class TestMetricsFromCounts(unittest.TestCase):
    def test_hand_calculated_example(self):
        m = metrics_from_counts(tp=3, fn=1, tn=5, fp=1)
        self.assertEqual((m.tp, m.fn, m.tn, m.fp, m.total), (3, 1, 5, 1, 10))
        self.assertEqual((m.positive_gt, m.negative_gt), (4, 6))
        self.assertEqual(m.accuracy, 0.8)
        self.assertEqual(m.sensitivity, 0.75)
        self.assertEqual(m.specificity, 5 / 6)
        self.assertEqual(m.precision, 0.75)
        self.assertEqual(m.f1, 0.75)

    def test_perfect_and_inverted(self):
        perfect = metrics_from_counts(tp=4, fn=0, tn=6, fp=0)
        self.assertEqual((perfect.accuracy, perfect.sensitivity, perfect.specificity,
                          perfect.precision, perfect.f1), (1.0, 1.0, 1.0, 1.0, 1.0))
        inverted = metrics_from_counts(tp=0, fn=4, tn=0, fp=6)
        self.assertEqual(inverted.accuracy, 0.0)
        self.assertEqual(inverted.sensitivity, 0.0)
        self.assertEqual(inverted.specificity, 0.0)
        self.assertEqual(inverted.precision, 0.0)
        self.assertIsNone(inverted.f1)

    def test_f1_edge_case_tp0_fp_and_fn_positive(self):
        """Preserved Week 4 behaviour: P = S = 0 gives undefined F1, not 0."""
        m = metrics_from_counts(tp=0, fn=3, tn=90, fp=7)
        self.assertEqual(m.precision, 0.0)
        self.assertEqual(m.sensitivity, 0.0)
        self.assertIsNone(m.f1)

    def test_zero_denominator_cases(self):
        cases = {
            # name: (counts, expected (acc, sens, spec, prec, f1))
            "no reference positives, no positive predictions":
                ((0, 0, 100, 0), (1.0, None, 1.0, None, None)),
            "no reference positives, some false positives":
                ((0, 0, 95, 5), (0.95, None, 0.95, 0.0, None)),
            "no reference negatives":
                ((10, 0, 0, 0), (1.0, 1.0, None, 1.0, 1.0)),
            "no positive predictions, some reference positives":
                ((0, 4, 96, 0), (0.96, 0.0, 1.0, None, None)),
            "empty":
                ((0, 0, 0, 0), (None, None, None, None, None)),
        }
        for name, (counts, expected) in cases.items():
            with self.subTest(case=name):
                m = metrics_from_counts(*counts)
                self.assertEqual((m.accuracy, m.sensitivity, m.specificity, m.precision, m.f1),
                                 expected)

    def test_published_baseline_counts_give_published_rates(self):
        """Formula check on the Stage 1 baseline counts (not a real-data parity claim)."""
        m1 = metrics_from_counts(tp=128, fn=921, tn=913, fp=38)
        self.assertEqual(m1.total, 2000)
        self.assertEqual([round(v * 100, 2) for v in
                          (m1.accuracy, m1.sensitivity, m1.specificity, m1.precision, m1.f1)],
                         [52.05, 12.20, 96.00, 77.11, 21.07])
        m2 = metrics_from_counts(tp=127, fn=31, tn=1803, fp=39)
        self.assertEqual([round(v * 100, 2) for v in
                          (m2.accuracy, m2.sensitivity, m2.specificity, m2.precision, m2.f1)],
                         [96.50, 80.38, 97.88, 76.51, 78.40])

    def test_as_dict_matches_week4_keys_and_order(self):
        self.assertEqual(list(metrics_from_counts(1, 1, 1, 1).as_dict()),
                         ["tp", "fn", "tn", "fp", "total", "positive_gt", "negative_gt",
                          "accuracy", "sensitivity", "specificity", "precision", "f1"])


class TestConfusionCounting(unittest.TestCase):
    def test_each_outcome_is_counted(self):
        ref = table({1: {"rtm": P}, 2: {"rtm": P}, 3: {}, 4: {}})
        pred = table({1: {"rtm": P}, 2: {}, 3: {}, 4: {"rtm": P}})
        self.assertEqual(count_outcomes(ref, pred, "rtm", [1, 2, 3, 4]), (1, 1, 1, 1))

    def test_conditions_are_independent(self):
        ref = table({1: {"pneumonia": P}})
        pred = table({1: {"pneumonia": P, "bronchitis": P}})
        metrics = condition_metrics(ref, pred)
        self.assertEqual((metrics["pneumonia"].tp, metrics["pneumonia"].fp), (1, 0))
        self.assertEqual((metrics["bronchitis"].tp, metrics["bronchitis"].fp), (0, 1))
        self.assertEqual(metrics["rtm"].tn, 1)

    def test_condition_order_and_totals(self):
        ref, pred = random_tables(1, cases=37)
        metrics = condition_metrics(ref, pred)
        self.assertEqual(tuple(metrics), CONDITION_KEYS)
        for m in metrics.values():
            self.assertEqual(m.total, 37)
            self.assertEqual(m.tp + m.fn + m.tn + m.fp, 37)

    def test_case_subset(self):
        ref, pred = random_tables(2, cases=10)
        subset = condition_metrics(ref, pred, case_ids=[1, 2, 3])
        self.assertTrue(all(m.total == 3 for m in subset.values()))

    def test_invalid_labels_are_rejected_not_counted(self):
        for bad in ("positive", "", None, "Abnormal"):
            with self.subTest(bad=bad):
                ref = table({1: {}})
                pred = table({1: {}})
                pred[1]["rtm"] = bad
                with self.assertRaises(ValueError):
                    condition_metrics(ref, pred)
                with self.assertRaises(ValueError):
                    condition_metrics(pred, ref)


class TestAggregation(unittest.TestCase):
    def test_micro_sums_counts_then_applies_formulas(self):
        ref, pred = random_tables(3)
        per = condition_metrics(ref, pred)
        micro = micro_metrics(per)
        sums = [sum(getattr(m, f) for m in per.values()) for f in ("tp", "fn", "tn", "fp")]
        self.assertEqual(micro, metrics_from_counts(*sums))
        self.assertEqual(micro.total, 2000)
        self.assertEqual(micro.positive_gt, sum(m.positive_gt for m in per.values()))

    def test_macro_excludes_undefined_values(self):
        per = {c: metrics_from_counts(0, 0, 10, 0) for c in CONDITION_KEYS}   # all undefined
        per["pneumonia"] = metrics_from_counts(tp=1, fn=1, tn=8, fp=0)       # sens 0.5
        per["rtm"] = metrics_from_counts(tp=0, fn=2, tn=7, fp=1)             # F1 edge case
        macro = macro_metrics(per)
        self.assertEqual(macro.sensitivity, (0.5 + 0.0) / 2)  # 18 undefined excluded
        self.assertEqual(macro.precision, (1.0 + 0.0) / 2)
        self.assertEqual(macro.f1, per["pneumonia"].f1)        # rtm F1 undefined -> excluded
        self.assertEqual(macro.accuracy, mean_defined(m.accuracy for m in per.values()))
        self.assertEqual(macro.specificity, mean_defined(m.specificity for m in per.values()))

    def test_macro_is_unweighted(self):
        per = {c: metrics_from_counts(1, 0, 9, 0) for c in CONDITION_KEYS}
        per["rtm"] = metrics_from_counts(tp=1, fn=99, tn=0, fp=0)
        self.assertAlmostEqual(macro_metrics(per).sensitivity, (19 * 1.0 + 0.01) / 20)

    def test_macro_all_undefined(self):
        per = {c: metrics_from_counts(0, 0, 0, 0) for c in CONDITION_KEYS}
        macro = macro_metrics(per)
        self.assertEqual((macro.accuracy, macro.sensitivity, macro.specificity,
                          macro.precision, macro.f1), (None, None, None, None, None))


class TestWeek4Parity(unittest.TestCase):
    """Per-condition, micro and macro values must equal Week 4's to the last bit."""

    @classmethod
    def setUpClass(cls):
        from week_04.matrix_1 import matrix1_evaluator as week4

        cls.week4 = week4

    def week4_micro_and_macro(self, ref, pred):
        per = self.week4.calculate_condition_metrics(ref, pred)
        keys = ("tp", "fn", "tn", "fp", "total", "positive_gt", "negative_gt")
        totals = {k: sum(per[c][k] for c in CONDITION_KEYS) for k in keys}
        r = self.week4._ratio
        totals.update(accuracy=r(totals["tp"] + totals["tn"], totals["total"]),
                      sensitivity=r(totals["tp"], totals["tp"] + totals["fn"]),
                      specificity=r(totals["tn"], totals["tn"] + totals["fp"]),
                      precision=r(totals["tp"], totals["tp"] + totals["fp"]))
        p, s = totals["precision"], totals["sensitivity"]
        totals["f1"] = 2 * p * s / (p + s) if p is not None and s is not None and p + s else None
        macro = {f: self.week4._mean_defined([per[c][f] for c in CONDITION_KEYS])
                 for f in ("accuracy", "sensitivity", "specificity", "precision", "f1")}
        return per, totals, macro

    def test_randomised_tables(self):
        for seed, rate in [(10, 0.05), (11, 0.2), (12, 0.5), (13, 0.9), (14, 0.0), (15, 1.0)]:
            with self.subTest(seed=seed, positive_rate=rate):
                ref, pred = random_tables(seed, positive_rate=rate)
                week4_per, week4_totals, week4_macro = self.week4_micro_and_macro(ref, pred)
                per = condition_metrics(ref, pred)
                self.assertEqual({c: per[c].as_dict() for c in CONDITION_KEYS}, week4_per)
                self.assertEqual(micro_metrics(per).as_dict(), week4_totals)
                macro = macro_metrics(per)
                self.assertEqual({f: getattr(macro, f) for f in week4_macro}, week4_macro)

    def test_edge_case_tables(self):
        ref = table({1: {"rtm": P}, 2: {}})
        pred = table({1: {}, 2: {"rtm": P}})          # rtm: TP0 FN1 TN0 FP1
        week4_per, week4_totals, week4_macro = self.week4_micro_and_macro(ref, pred)
        per = condition_metrics(ref, pred)
        self.assertEqual({c: per[c].as_dict() for c in CONDITION_KEYS}, week4_per)
        self.assertIsNone(per["rtm"].f1)
        self.assertEqual(micro_metrics(per).as_dict(), week4_totals)
        macro = macro_metrics(per)
        self.assertEqual({f: getattr(macro, f) for f in week4_macro}, week4_macro)

    def test_result_type(self):
        self.assertIsInstance(metrics_from_counts(1, 0, 0, 0), ConfusionMetrics)


if __name__ == "__main__":
    unittest.main(verbosity=2)
