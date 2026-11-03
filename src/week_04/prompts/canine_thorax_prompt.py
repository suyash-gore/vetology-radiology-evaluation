"""Runtime prompt loader for Vetology Week 4 — Canine Thorax (V1.3)."""
from pathlib import Path

PROMPT_PATH = Path(__file__).with_name("canine_thorax_master_prompt_v1_3.txt")

CONDITION_KEYS = (
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
VALID_LABELS = ("Positive", "Negative")


def load_system_prompt() -> str:
    """Load the operational V1.3 canine thorax prompt from the adjacent text file."""
    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(
            f"Canine thorax prompt file not found: {PROMPT_PATH}"
        )
    return PROMPT_PATH.read_text(encoding="utf-8").strip()
