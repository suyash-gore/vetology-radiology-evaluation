"""Pure comparison calculations: hand-computed tables and an independent brute-force check."""
from __future__ import annotations

from week_07.comparison.agreement import (
    Disagreement,
    ModelAgreement,
    ReferenceCorrectness,
    agreement_by_condition,
    correctness_by_condition,
    difference,
    disagreements,
    model_agreement,
    rate_differences,
    reference_correctness,
    total_agreement,
    total_correctness,
)
from week_07.conditions import CONDITION_KEYS
from week_07.evaluation.metrics import MacroMetrics, metrics_from_counts
from week_07.tests.fixtures import (
    GEMINI_FLIPS,
    OPENAI_FLIPS,
    predicted_labels,
    reference_labels,
)
from week_07.tests.support import OfflineTestCase

P, N = "Positive", "Negative"
CONDS = ("pneumonia", "rtm")
REF = {1: {"pneumonia": P, "rtm": N}, 2: {"pneumonia": N, "rtm": P}}
OAI = {1: {"pneumonia": P, "rtm": P}, 2: {"pneumonia": N, "rtm": N}}
GEM = {1: {"pneumonia": N, "rtm": N}, 2: {"pneumonia": N, "rtm": P}}


class TestHandComputed(OfflineTestCase):
    def test_model_agreement_per_condition(self):
        self.assertEqual(model_agreement(OAI, GEM, [1, 2], "pneumonia"), ModelAgreement(0, 1, 0, 1))
        self.assertEqual(model_agreement(OAI, GEM, [1, 2], "rtm"), ModelAgreement(0, 1, 1, 0))

    def test_reference_correctness_per_condition(self):
        self.assertEqual(reference_correctness(REF, OAI, GEM, [1, 2], "pneumonia"),
                         ReferenceCorrectness(1, 1, 0, 0))
        self.assertEqual(reference_correctness(REF, OAI, GEM, [1, 2], "rtm"),
                         ReferenceCorrectness(0, 0, 2, 0))

    def test_totals_and_derived_values(self):
        agreement = total_agreement(agreement_by_condition(OAI, GEM, [1, 2], CONDS))
        self.assertEqual(agreement, ModelAgreement(0, 2, 1, 1))
        self.assertEqual((agreement.total, agreement.agreements, agreement.disagreements),
                         (4, 1, 3))
        self.assertEqual(agreement.agreement_rate, 0.25)
        self.assertEqual((agreement.openai_positive, agreement.gemini_positive), (2, 1))
        correctness = total_correctness(correctness_by_condition(REF, OAI, GEM, [1, 2], CONDS))
        self.assertEqual(correctness, ReferenceCorrectness(1, 1, 2, 0))
        self.assertEqual((correctness.openai_correct, correctness.gemini_correct), (2, 3))

    def test_disagreement_rows_sorted_with_matching_model(self):
        rows = disagreements(REF, OAI, GEM, [2, 1], CONDS)
        self.assertEqual(rows, [Disagreement(1, "pneumonia", P, P, N),
                                Disagreement(1, "rtm", N, P, N),
                                Disagreement(2, "rtm", P, N, P)])
        self.assertEqual([r.model_matching_reference for r in rows],
                         ["OpenAI", "Gemini", "Gemini"])

    def test_agreement_does_not_use_reference(self):
        """Model agreement is a separate analysis: changing the reference cannot affect it."""
        flipped_ref = {c: {k: (N if v == P else P) for k, v in labels.items()}
                       for c, labels in REF.items()}
        import inspect

        for function in (model_agreement, agreement_by_condition):
            self.assertNotIn("reference", inspect.signature(function).parameters)
        self.assertNotEqual(correctness_by_condition(REF, OAI, GEM, [1, 2], CONDS),
                            correctness_by_condition(flipped_ref, OAI, GEM, [1, 2], CONDS))

    def test_empty_case_list(self):
        empty = model_agreement(OAI, GEM, [], "rtm")
        self.assertEqual((empty.total, empty.agreement_rate), (0, None))

    def test_invalid_labels_rejected(self):
        bad = {1: {"pneumonia": "positive", "rtm": N}, 2: OAI[2]}
        with self.assertRaises(ValueError):
            model_agreement(bad, GEM, [1, 2], "pneumonia")
        with self.assertRaises(ValueError):
            reference_correctness(bad, OAI, GEM, [1, 2], "pneumonia")
        with self.assertRaises(ValueError):
            disagreements(REF, OAI, {1: {"pneumonia": "", "rtm": N}, 2: GEM[2]}, [1, 2], CONDS)

    def test_missing_case_raises(self):
        with self.assertRaises(KeyError):
            model_agreement(OAI, {1: GEM[1]}, [1, 2], "rtm")


class TestDifferences(OfflineTestCase):
    def test_gemini_minus_openai_with_undefined(self):
        self.assertEqual(difference(0.75, 0.5), 0.25)
        self.assertIsNone(difference(None, 0.5))
        self.assertIsNone(difference(0.5, None))
        self.assertIsNone(difference(None, None))
        self.assertEqual(difference(0.0, 0.0), 0.0)

    def test_rate_differences(self):
        openai = metrics_from_counts(tp=0, fn=2, tn=8, fp=0)      # precision undefined
        gemini = metrics_from_counts(tp=1, fn=1, tn=7, fp=1)
        diffs = rate_differences(openai, gemini)
        self.assertEqual(set(diffs), {"accuracy", "sensitivity", "specificity", "precision", "f1"})
        self.assertAlmostEqual(diffs["accuracy"], 0.8 - 0.8)
        self.assertAlmostEqual(diffs["sensitivity"], 0.5)
        self.assertIsNone(diffs["precision"])
        self.assertIsNone(diffs["f1"])
        macro = rate_differences(MacroMetrics(0.5, None, 0.9, 0.4, None),
                                 MacroMetrics(0.6, 0.2, 0.8, None, None))
        self.assertAlmostEqual(macro["accuracy"], 0.1)
        self.assertIsNone(macro["sensitivity"])
        self.assertIsNone(macro["precision"])


class TestSyntheticFullScale(OfflineTestCase):
    """100 cases x 20 conditions, checked against an independent brute-force count."""

    def test_matches_brute_force(self):
        ids = list(range(1, 101))
        ref = {c: reference_labels(c, 1) for c in ids}
        oai = {c: predicted_labels(c, 1, OPENAI_FLIPS) for c in ids}
        gem = {c: predicted_labels(c, 1, GEMINI_FLIPS) for c in ids}
        pairs = [(c, k) for c in ids for k in CONDITION_KEYS]
        agreement = total_agreement(agreement_by_condition(oai, gem, ids))
        self.assertEqual(agreement.total, 2000)
        self.assertEqual(agreement.disagreements,
                         sum(oai[c][k] != gem[c][k] for c, k in pairs))
        self.assertEqual(agreement.both_positive,
                         sum(oai[c][k] == gem[c][k] == P for c, k in pairs))
        correctness = total_correctness(correctness_by_condition(ref, oai, gem, ids))
        self.assertEqual(correctness.only_gemini_correct,
                         sum(gem[c][k] == ref[c][k] != oai[c][k] for c, k in pairs))
        self.assertEqual(correctness.both_wrong,
                         sum(gem[c][k] != ref[c][k] and oai[c][k] != ref[c][k]
                             for c, k in pairs))
        rows = disagreements(ref, oai, gem, ids)
        self.assertEqual(len(rows), agreement.disagreements)
        # Flips on the same pair in both models (case 1 pneumonia, case 10 esophagitis) agree.
        self.assertNotIn((1, "pneumonia"), {(r.case_id, r.condition) for r in rows})
        self.assertIn((1, "rtm"), {(r.case_id, r.condition) for r in rows})
        expected = {(1, "rtm"), (2, "cardiomegaly"), (3, "cardiomegaly"), (3, "rtm"),
                    (55, "bronchitis"), (55, "interstitial"), (77, "pleural_effusion")}
        self.assertEqual({(r.case_id, r.condition) for r in rows}, expected)
