"""Application registry: one shared engine, three strictly configured applications.

* ``canine_thorax``  — gemini, ``gemini-3.8-flash``, 20 conditions, Canine Thorax Master
  Prompt V1.3 (existing application).
* ``feline_thorax``  — openai, ``gpt-4.1-mini``, 21 conditions, Feline Thorax Master
  Prompt V1.2 (supersedes V1.1).
* ``canine_abdomen`` — openai, ``gpt-4.1-mini``, 10 conditions, Canine Abdomen Master
  Prompt V1.4 (supersedes V1.2 and V1.3).

Canine Thorax is the existing application. Its entry reuses the original
objects (``conditions.CONDITION_KEYS``, ``config.MATRIX1``/``MATRIX2``, the
V1.3 prompt constants) so nothing about it changes; it keeps one batch run per
workflow.

Feline Thorax and Canine Abdomen generate predictions ONCE per application,
from the Matrix 1 workbook (``prediction_source_workflow``), and both the
Matrix 1 and Matrix 2 evaluations reuse those predictions. The two reference
tracks stay independent.

Reference-label normalisation is declared per application AND per workflow.
The only entry is Feline Thorax Matrix 1, for exactly three columns
(``pulmonary_nodules``, ``esophagitis``, ``pneumonia``): ``Normal`` ->
``Negative``, ``Abnormal`` -> ``Positive``. It applies to reference labels
before strict Positive/Negative validation and never to any other column,
workflow or application, nor to model responses.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from week_07 import config, conditions
from week_07.conditions import NEGATIVE, POSITIVE, VALID_LABELS
from week_07.config import ConfigurationError, WorkflowSpec
from week_07.prompts.registry import (
    CANINE_ABDOMEN_PROMPT,
    CANINE_THORAX_PROMPT,
    FELINE_THORAX_PROMPT,
    PromptSpec,
)

GEMINI: Final[str] = "gemini"
OPENAI: Final[str] = "openai"
PROVIDERS: Final[tuple[str, ...]] = (GEMINI, OPENAI)
OPENAI_DEFAULT_MODEL: Final[str] = "gpt-4.1-mini"

# Canonical output order. Do not reorder, rename, add or remove keys.
FELINE_THORAX_CONDITION_KEYS: Final[tuple[str, ...]] = (
    "pulmonary_nodules",
    "esophagitis",
    "pneumonia",
    "bronchitis",
    "interstitial",
    "diseased_lungs",
    "hypo_plastic_trachea",
    "cardiomegaly",
    "pleural_effusion",
    "perihilar_infiltrate",
    "rtm",
    "focal_caudodorsal_lung",
    "right_sided_cardiomegaly",
    "focal_perihilar",
    "left_sided_cardiomegaly",
    "bronchiectasis",
    "pulmonary_vessel_enlargement",
    "thoracic_lymphadenopathy",
    "pulmonary_hypoinflation",
    "pericardial_effusion",
    "Fe_Alveolar",
)

CANINE_ABDOMEN_CONDITION_KEYS: Final[tuple[str, ...]] = (
    "gastritis",
    "ascites",
    "colitis",
    "liver_mass",
    "pancreatitis",
    "microhepatia",
    "small_intestinal_obstruction",
    "splenic_mass",
    "splenomegaly",
    "hepatomegaly",
)

NORMAL_ABNORMAL_TO_LABEL: Final[Mapping[str, str]] = MappingProxyType({
    "Normal": NEGATIVE,
    "Abnormal": POSITIVE,
})
FELINE_MATRIX1_NORMALIZED_CONDITIONS: Final[tuple[str, ...]] = (
    "pulmonary_nodules", "esophagitis", "pneumonia",
)

LabelNormalization = Mapping[str, Mapping[str, str]]   # condition -> source label -> label
_NO_NORMALIZATION: Final[LabelNormalization] = MappingProxyType({})


def _frozen_normalization(
    raw: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> Mapping[str, LabelNormalization]:
    return MappingProxyType({
        workflow: MappingProxyType({
            condition: MappingProxyType(dict(mapping))
            for condition, mapping in by_condition.items()
        })
        for workflow, by_condition in raw.items()
    })


@dataclass(frozen=True)
class ApplicationSpec:
    """Everything that makes one application distinct. Validated on creation."""

    key: str
    display_name: str
    region_phrase: str          # used in the human instruction ("feline thorax")
    provider: str
    default_model: str
    condition_keys: tuple[str, ...]
    expected_condition_count: int
    prompt: PromptSpec
    workflows: Mapping[str, WorkflowSpec]
    shared_predictions: bool
    prediction_source_workflow: str | None = None
    reference_label_normalization: Mapping[str, LabelNormalization] = field(
        default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        keys = self.condition_keys
        if not isinstance(keys, tuple) or not all(isinstance(k, str) and k for k in keys):
            raise ConfigurationError(f"{self.key}: condition keys must be a tuple of names.")
        if len(keys) != self.expected_condition_count or len(set(keys)) != len(keys):
            raise ConfigurationError(
                f"{self.key}: expected {self.expected_condition_count} unique condition keys; "
                f"got {len(keys)} ({len(set(keys))} unique)."
            )
        if self.provider not in PROVIDERS:
            raise ConfigurationError(f"{self.key}: unknown provider {self.provider!r}.")
        if not self.default_model.strip():
            raise ConfigurationError(f"{self.key}: a default model is required.")
        if set(self.workflows) != {config.MATRIX1.name, config.MATRIX2.name}:
            raise ConfigurationError(f"{self.key}: workflows must be exactly matrix1 and matrix2.")
        for name, spec in self.workflows.items():
            if spec.name != name or spec.application != self.key:
                raise ConfigurationError(
                    f"{self.key}: workflow {name!r} belongs to {spec.qualified_name!r}."
                )
            if self.shared_predictions != (spec.shared_predictions_dir is not None):
                raise ConfigurationError(
                    f"{spec.qualified_name}: shared_predictions_dir does not match the "
                    "application's shared-prediction setting."
                )
        if self.shared_predictions:
            if self.prediction_source_workflow not in self.workflows:
                raise ConfigurationError(
                    f"{self.key}: shared predictions need a prediction source workflow."
                )
            if len({spec.shared_predictions_dir for spec in self.workflows.values()}) != 1:
                raise ConfigurationError(f"{self.key}: workflows must share one predictions dir.")
        elif self.prediction_source_workflow is not None:
            raise ConfigurationError(
                f"{self.key}: a prediction source workflow requires shared predictions."
            )
        for workflow, by_condition in self.reference_label_normalization.items():
            if workflow not in self.workflows:
                raise ConfigurationError(f"{self.key}: normalisation for unknown {workflow!r}.")
            for condition, mapping in by_condition.items():
                if condition not in keys:
                    raise ConfigurationError(
                        f"{self.key}/{workflow}: normalisation for unknown condition "
                        f"{condition!r}."
                    )
                for source, target in mapping.items():
                    if source in VALID_LABELS or target not in VALID_LABELS:
                        raise ConfigurationError(
                            f"{self.key}/{workflow}/{condition}: invalid normalisation "
                            f"{source!r} -> {target!r}."
                        )

    @property
    def condition_count(self) -> int:
        return len(self.condition_keys)

    @property
    def human_instruction(self) -> str:
        """Fixed human-message instruction; Canine Thorax's is the Week 4/5 sentence."""
        return (f"Classify the following {self.region_phrase} radiology report according "
                "to the system instructions.")

    def workflow(self, name: str) -> WorkflowSpec:
        try:
            return self.workflows[name]
        except KeyError:
            raise ConfigurationError(
                f"Unknown workflow {name!r} for {self.key}. Expected one of: "
                f"{', '.join(self.workflows)}."
            ) from None

    def label_normalization(self, workflow: str) -> LabelNormalization:
        """Reference-label normalisation for one workflow (empty for almost all)."""
        self.workflow(workflow)
        return self.reference_label_normalization.get(workflow, _NO_NORMALIZATION)

    def __repr__(self) -> str:
        return (f"ApplicationSpec(key={self.key!r}, provider={self.provider!r}, "
                f"conditions={self.condition_count}, prompt={self.prompt.label!r})")


CANINE_THORAX: Final[ApplicationSpec] = ApplicationSpec(
    key="canine_thorax",
    display_name="Canine Thorax",
    region_phrase="canine thorax",
    provider=GEMINI,
    default_model=config.DEFAULT_MODEL,
    condition_keys=conditions.CONDITION_KEYS,
    expected_condition_count=20,
    prompt=CANINE_THORAX_PROMPT,
    workflows=MappingProxyType({config.MATRIX1.name: config.MATRIX1,
                                config.MATRIX2.name: config.MATRIX2}),
    shared_predictions=False,
)

FELINE_THORAX: Final[ApplicationSpec] = ApplicationSpec(
    key="feline_thorax",
    display_name="Feline Thorax",
    region_phrase="feline thorax",
    provider=OPENAI,
    default_model=OPENAI_DEFAULT_MODEL,
    condition_keys=FELINE_THORAX_CONDITION_KEYS,
    expected_condition_count=21,
    prompt=FELINE_THORAX_PROMPT,
    workflows=MappingProxyType({config.MATRIX1.name: config.FELINE_THORAX_MATRIX1,
                                config.MATRIX2.name: config.FELINE_THORAX_MATRIX2}),
    shared_predictions=True,
    prediction_source_workflow=config.MATRIX1.name,
    reference_label_normalization=_frozen_normalization({
        config.MATRIX1.name: {condition: NORMAL_ABNORMAL_TO_LABEL
                              for condition in FELINE_MATRIX1_NORMALIZED_CONDITIONS},
    }),
)

CANINE_ABDOMEN: Final[ApplicationSpec] = ApplicationSpec(
    key="canine_abdomen",
    display_name="Canine Abdomen",
    region_phrase="canine abdomen",
    provider=OPENAI,
    default_model=OPENAI_DEFAULT_MODEL,
    condition_keys=CANINE_ABDOMEN_CONDITION_KEYS,
    expected_condition_count=10,
    prompt=CANINE_ABDOMEN_PROMPT,
    workflows=MappingProxyType({config.MATRIX1.name: config.CANINE_ABDOMEN_MATRIX1,
                                config.MATRIX2.name: config.CANINE_ABDOMEN_MATRIX2}),
    shared_predictions=True,
    prediction_source_workflow=config.MATRIX1.name,
)

DEFAULT_APPLICATION: Final[str] = CANINE_THORAX.key

APPLICATIONS: Final[Mapping[str, ApplicationSpec]] = MappingProxyType({
    app.key: app for app in (CANINE_THORAX, FELINE_THORAX, CANINE_ABDOMEN)
})

if {spec.qualified_name for app in APPLICATIONS.values() for spec in app.workflows.values()} \
        != set(config.ALL_WORKFLOWS):
    raise AssertionError("config.ALL_WORKFLOWS must list exactly the registered workflows.")


def get_application(key: str = DEFAULT_APPLICATION) -> ApplicationSpec:
    """Return an application by its exact key."""
    try:
        return APPLICATIONS[key]
    except KeyError:
        raise ConfigurationError(
            f"Unknown application {key!r}. Expected one of: {', '.join(APPLICATIONS)}."
        ) from None


def application_for(spec: WorkflowSpec) -> ApplicationSpec:
    """The application that owns a workflow spec (also for ``dataclasses.replace`` copies)."""
    return get_application(spec.application)
