"""Single source of truth for the 20 canine thorax conditions and labels.

The order below is the canonical V1.3 output order. It is used for LLM output
validation, dataset column validation, prediction records and evaluation
workbooks. Do not reorder, rename, add or remove keys.
"""
from __future__ import annotations

from typing import Final

CONDITION_KEYS: Final[tuple[str, ...]] = (
    "perihilar_infiltrate",
    "pneumonia",
    "bronchitis",
    "interstitial",
    "diseased_lungs",
    "hypo_plastic_trachea",
    "cardiomegaly",
    "pulmonary_nodules",
    "pleural_effusion",
    "rtm",
    "focal_caudodorsal_lung",
    "focal_perihilar",
    "pulmonary_hypoinflation",
    "right_sided_cardiomegaly",
    "pericardial_effusion",
    "bronchiectasis",
    "pulmonary_vessel_enlargement",
    "left_sided_cardiomegaly",
    "thoracic_lymphadenopathy",
    "esophagitis",
)

POSITIVE: Final[str] = "Positive"
NEGATIVE: Final[str] = "Negative"

# Exactly two permitted labels; there is no third class.
VALID_LABELS: Final[tuple[str, ...]] = (POSITIVE, NEGATIVE)

CONDITION_COUNT: Final[int] = len(CONDITION_KEYS)

if CONDITION_COUNT != 20 or len(set(CONDITION_KEYS)) != 20:
    raise AssertionError("The V1.3 configuration must contain 20 unique condition keys.")
