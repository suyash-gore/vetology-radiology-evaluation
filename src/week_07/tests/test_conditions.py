"""The 20-condition contract and the two permitted labels."""
from __future__ import annotations

from week_07.conditions import (
    CONDITION_COUNT,
    CONDITION_KEYS,
    NEGATIVE,
    POSITIVE,
    VALID_LABELS,
)
from week_07.tests.support import OfflineTestCase

EXPECTED_ORDER = (
    "perihilar_infiltrate", "pneumonia", "bronchitis", "interstitial", "diseased_lungs",
    "hypo_plastic_trachea", "cardiomegaly", "pulmonary_nodules", "pleural_effusion", "rtm",
    "focal_caudodorsal_lung", "focal_perihilar", "pulmonary_hypoinflation",
    "right_sided_cardiomegaly", "pericardial_effusion", "bronchiectasis",
    "pulmonary_vessel_enlargement", "left_sided_cardiomegaly", "thoracic_lymphadenopathy",
    "esophagitis",
)


class TestConditions(OfflineTestCase):
    def test_exact_canonical_order(self):
        self.assertEqual(CONDITION_KEYS, EXPECTED_ORDER)

    def test_twenty_unique_keys(self):
        self.assertEqual(CONDITION_COUNT, 20)
        self.assertEqual(len(set(CONDITION_KEYS)), 20)

    def test_exactly_two_case_sensitive_labels(self):
        self.assertEqual(VALID_LABELS, ("Positive", "Negative"))
        self.assertEqual((POSITIVE, NEGATIVE), ("Positive", "Negative"))
        self.assertNotIn("positive", VALID_LABELS)
        self.assertNotIn("Abnormal", VALID_LABELS)

    def test_keys_are_immutable_tuple(self):
        self.assertIsInstance(CONDITION_KEYS, tuple)
