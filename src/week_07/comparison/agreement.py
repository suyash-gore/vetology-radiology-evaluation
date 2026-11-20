"""Pure comparison calculations (no file access, no model access).

Two SEPARATE analyses, never merged:

1. Model agreement (OpenAI vs Gemini, reference labels NOT used):
   both Positive, OpenAI-only Positive, Gemini-only Positive, both Negative;
   agreement = both Positive + both Negative.
2. Reference-based correctness (each model vs the workflow's reference labels):
   both correct, only OpenAI correct, only Gemini correct, both wrong.

Per-model confusion metrics come from the Week 5 metric engine
(``week_07.evaluation.metrics``). Differences are Gemini − OpenAI; an undefined
value on either side gives an undefined difference (``None``), never 0.

All inputs must already be validated and aligned (same CaseIDs, 20 keys,
Positive/Negative only); any other label raises ``ValueError``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from typing import Any

from week_07.conditions import CONDITION_KEYS, NEGATIVE, POSITIVE
from week_07.evaluation.metrics import ratio

LabelTable = Mapping[Any, Mapping[str, str]]
RATE_FIELDS = ("accuracy", "sensitivity", "specificity", "precision", "f1")


@dataclass(frozen=True)
class ModelAgreement:
    """OpenAI vs Gemini on the same case-condition pairs (reference not used)."""

    both_positive: int
    openai_only_positive: int
    gemini_only_positive: int
    both_negative: int

    @property
    def total(self) -> int:
        return (self.both_positive + self.openai_only_positive + self.gemini_only_positive
                + self.both_negative)

    @property
    def agreements(self) -> int:
        return self.both_positive + self.both_negative

    @property
    def disagreements(self) -> int:
        return self.openai_only_positive + self.gemini_only_positive

    @property
    def agreement_rate(self) -> float | None:
        return ratio(self.agreements, self.total)

    @property
    def openai_positive(self) -> int:
        return self.both_positive + self.openai_only_positive

    @property
    def gemini_positive(self) -> int:
        return self.both_positive + self.gemini_only_positive


@dataclass(frozen=True)
class ReferenceCorrectness:
    """Each model's correctness against the reference labels, cross-tabulated."""

    both_correct: int
    only_openai_correct: int
    only_gemini_correct: int
    both_wrong: int

    @property
    def total(self) -> int:
        return (self.both_correct + self.only_openai_correct + self.only_gemini_correct
                + self.both_wrong)

    @property
    def openai_correct(self) -> int:
        return self.both_correct + self.only_openai_correct

    @property
    def gemini_correct(self) -> int:
        return self.both_correct + self.only_gemini_correct


@dataclass(frozen=True)
class Disagreement:
    """One case-condition pair where the two models disagree."""

    case_id: Any
    condition: str
    reference: str
    openai: str
    gemini: str

    @property
    def model_matching_reference(self) -> str:
        """With binary labels and differing predictions, exactly one model matches."""
        return "OpenAI" if self.openai == self.reference else "Gemini"


def _check(label: str, case_id: Any, condition: str, source: str) -> None:
    if label not in (POSITIVE, NEGATIVE):
        raise ValueError(
            f"Invalid {source} label for CaseID {case_id!r}, condition {condition!r}: {label!r}"
        )


def _sum(items: Sequence[Any], cls: type) -> Any:
    return cls(**{f.name: sum(getattr(item, f.name) for item in items) for f in fields(cls)})


def model_agreement(openai: LabelTable, gemini: LabelTable, case_ids: Sequence[Any],
                    condition: str) -> ModelAgreement:
    both_pos = openai_only = gemini_only = both_neg = 0
    for case_id in case_ids:
        a, b = openai[case_id][condition], gemini[case_id][condition]
        _check(a, case_id, condition, "OpenAI")
        _check(b, case_id, condition, "Gemini")
        if a == POSITIVE and b == POSITIVE:
            both_pos += 1
        elif a == POSITIVE:
            openai_only += 1
        elif b == POSITIVE:
            gemini_only += 1
        else:
            both_neg += 1
    return ModelAgreement(both_pos, openai_only, gemini_only, both_neg)


def reference_correctness(reference: LabelTable, openai: LabelTable, gemini: LabelTable,
                          case_ids: Sequence[Any], condition: str) -> ReferenceCorrectness:
    both = only_openai = only_gemini = neither = 0
    for case_id in case_ids:
        truth = reference[case_id][condition]
        a, b = openai[case_id][condition], gemini[case_id][condition]
        _check(truth, case_id, condition, "reference")
        _check(a, case_id, condition, "OpenAI")
        _check(b, case_id, condition, "Gemini")
        a_ok, b_ok = a == truth, b == truth
        if a_ok and b_ok:
            both += 1
        elif a_ok:
            only_openai += 1
        elif b_ok:
            only_gemini += 1
        else:
            neither += 1
    return ReferenceCorrectness(both, only_openai, only_gemini, neither)


def agreement_by_condition(openai: LabelTable, gemini: LabelTable, case_ids: Sequence[Any],
                           conditions: Sequence[str] = CONDITION_KEYS
                           ) -> dict[str, ModelAgreement]:
    return {c: model_agreement(openai, gemini, case_ids, c) for c in conditions}


def correctness_by_condition(reference: LabelTable, openai: LabelTable, gemini: LabelTable,
                             case_ids: Sequence[Any],
                             conditions: Sequence[str] = CONDITION_KEYS
                             ) -> dict[str, ReferenceCorrectness]:
    return {c: reference_correctness(reference, openai, gemini, case_ids, c)
            for c in conditions}


def total_agreement(per_condition: Mapping[str, ModelAgreement]) -> ModelAgreement:
    return _sum(list(per_condition.values()), ModelAgreement)


def total_correctness(per_condition: Mapping[str, ReferenceCorrectness]
                      ) -> ReferenceCorrectness:
    return _sum(list(per_condition.values()), ReferenceCorrectness)


def disagreements(reference: LabelTable, openai: LabelTable, gemini: LabelTable,
                  case_ids: Sequence[Any],
                  conditions: Sequence[str] = CONDITION_KEYS) -> list[Disagreement]:
    """Every disagreement, sorted by CaseID then canonical condition order."""
    rows = []
    for case_id in sorted(case_ids):
        for condition in conditions:
            a, b = openai[case_id][condition], gemini[case_id][condition]
            _check(a, case_id, condition, "OpenAI")
            _check(b, case_id, condition, "Gemini")
            if a != b:
                truth = reference[case_id][condition]
                _check(truth, case_id, condition, "reference")
                rows.append(Disagreement(case_id, condition, truth, a, b))
    return rows


def difference(gemini: float | None, openai: float | None) -> float | None:
    """Gemini − OpenAI; undefined (``None``) if either side is undefined."""
    if gemini is None or openai is None:
        return None
    return gemini - openai


def rate_differences(openai: Any, gemini: Any) -> dict[str, float | None]:
    """Differences of the five rate fields of two ConfusionMetrics/MacroMetrics."""
    return {name: difference(getattr(gemini, name), getattr(openai, name))
            for name in RATE_FIELDS}
