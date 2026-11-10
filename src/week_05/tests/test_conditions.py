"""Tests for the canonical condition keys and labels."""
from __future__ import annotations

import unittest

from week_05.conditions import CONDITION_COUNT, CONDITION_KEYS, VALID_LABELS

# Canonical order from the Stage 1 brief and the V1.3 prompt's JSON structure.
EXPECTED_ORDER = (
    "perihilar_infiltrate", "pneumonia", "bronchitis", "interstitial",
    "diseased_lungs", "hypo_plastic_trachea", "cardiomegaly", "pulmonary_nodules",
    "pleural_effusion", "rtm", "focal_caudodorsal_lung", "focal_perihilar",
    "pulmonary_hypoinflation", "right_sided_cardiomegaly", "pericardial_effusion",
    "bronchiectasis", "pulmonary_vessel_enlargement", "left_sided_cardiomegaly",
    "thoracic_lymphadenopathy", "esophagitis",
)


class TestConditions(unittest.TestCase):
    def test_exactly_twenty_unique_keys_in_canonical_order(self):
        self.assertEqual(CONDITION_COUNT, 20)
        self.assertEqual(len(set(CONDITION_KEYS)), 20)
        self.assertEqual(CONDITION_KEYS, EXPECTED_ORDER)

    def test_only_positive_and_negative_labels(self):
        self.assertEqual(VALID_LABELS, ("Positive", "Negative"))

    def test_keys_match_week4_definition(self):
        """Parity check only: Week 5 does not import Week 4 at runtime."""
        from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS as WEEK4_KEYS
        from week_04.prompts.canine_thorax_prompt import VALID_LABELS as WEEK4_LABELS

        self.assertEqual(CONDITION_KEYS, WEEK4_KEYS)
        self.assertEqual(VALID_LABELS, WEEK4_LABELS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
