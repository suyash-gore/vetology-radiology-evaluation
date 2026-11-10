"""Confusion-matrix metrics — the Week 4 methodology, unchanged.

Per condition (reference label vs. model prediction):

* TP: reference Positive, prediction Positive
* FN: reference Positive, prediction Negative
* TN: reference Negative, prediction Negative
* FP: reference Negative, prediction Positive

Ratios (``None`` = undefined, written as a blank cell; never treated as 0):

* Accuracy    = (TP + TN) / (TP + FN + TN + FP)
* Sensitivity = TP / (TP + FN)        — undefined with no reference positives
* Specificity = TN / (TN + FP)        — undefined with no reference negatives
* Precision   = TP / (TP + FP)        — undefined with no positive predictions
* F1          = 2·P·S / (P + S)       — undefined if P or S is undefined, or if
  P + S = 0. Known Week 4 edge case, preserved deliberately: when TP = 0 with
  FP > 0 and FN > 0, P = S = 0 and F1 is undefined rather than 0.

Aggregation:

* Micro: sum TP, FN, TN, FP over all conditions, then apply the formulas.
* Macro: unweighted mean of the defined condition-level values, in canonical
  condition order; undefined values are excluded, not counted as 0.

Balanced accuracy is not part of the Week 4 methodology and is not computed.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from week_05.conditions import CONDITION_KEYS, NEGATIVE, POSITIVE

LabelTable = Mapping[Any, Mapping[str, str]]  # CaseID -> condition -> label


@dataclass(frozen=True)
class ConfusionMetrics:
    """Counts and ratios for one condition, or the micro total across conditions."""

    tp: int
    fn: int
    tn: int
    fp: int
    total: int
    positive_gt: int
    negative_gt: int
    accuracy: float | None
    sensitivity: float | None
    specificity: float | None
    precision: float | None
    f1: float | None

    def as_dict(self) -> dict[str, Any]:
        """Same keys and order as the Week 4 evaluator's per-condition dict."""
        return asdict(self)


@dataclass(frozen=True)
class MacroMetrics:
    accuracy: float | None
    sensitivity: float | None
    specificity: float | None
    precision: float | None
    f1: float | None


def ratio(numerator: int, denominator: int) -> float | None:
    """``numerator / denominator``, or ``None`` when the denominator is zero."""
    return numerator / denominator if denominator else None


def f1_score(precision: float | None, sensitivity: float | None) -> float | None:
    """Week 4 F1: undefined if either input is undefined or their sum is zero."""
    if precision is not None and sensitivity is not None and precision + sensitivity:
        return 2 * precision * sensitivity / (precision + sensitivity)
    return None


def mean_defined(values: Iterable[float | None]) -> float | None:
    """Mean of the values that are not ``None``; ``None`` if none are defined."""
    defined = [value for value in values if value is not None]
    return sum(defined) / len(defined) if defined else None


def metrics_from_counts(tp: int, fn: int, tn: int, fp: int) -> ConfusionMetrics:
    total = tp + fn + tn + fp
    precision = ratio(tp, tp + fp)
    sensitivity = ratio(tp, tp + fn)
    return ConfusionMetrics(
        tp=tp, fn=fn, tn=tn, fp=fp, total=total,
        positive_gt=tp + fn, negative_gt=tn + fp,
        accuracy=ratio(tp + tn, total),
        sensitivity=sensitivity,
        specificity=ratio(tn, tn + fp),
        precision=precision,
        f1=f1_score(precision, sensitivity),
    )


def count_outcomes(
    reference: LabelTable,
    predictions: LabelTable,
    condition: str,
    case_ids: Sequence[Any],
) -> tuple[int, int, int, int]:
    """Return (TP, FN, TN, FP) for one condition over the given cases.

    Labels must already be validated; anything other than Positive/Negative is
    rejected here rather than silently counted.
    """
    tp = fn = tn = fp = 0
    for case_id in case_ids:
        actual = reference[case_id][condition]
        predicted = predictions[case_id][condition]
        if actual not in (POSITIVE, NEGATIVE) or predicted not in (POSITIVE, NEGATIVE):
            raise ValueError(
                f"Invalid label for CaseID {case_id!r}, condition {condition!r}: "
                f"reference={actual!r}, prediction={predicted!r}"
            )
        if actual == POSITIVE:
            if predicted == POSITIVE:
                tp += 1
            else:
                fn += 1
        elif predicted == NEGATIVE:
            tn += 1
        else:
            fp += 1
    return tp, fn, tn, fp


def condition_metrics(
    reference: LabelTable,
    predictions: LabelTable,
    case_ids: Sequence[Any] | None = None,
    conditions: Sequence[str] = CONDITION_KEYS,
) -> dict[str, ConfusionMetrics]:
    """Per-condition metrics in canonical condition order."""
    ids = list(reference) if case_ids is None else list(case_ids)
    return {
        condition: metrics_from_counts(*count_outcomes(reference, predictions, condition, ids))
        for condition in conditions
    }


def micro_metrics(per_condition: Mapping[str, ConfusionMetrics]) -> ConfusionMetrics:
    """Metrics computed from counts summed across all conditions."""
    values = list(per_condition.values())
    return metrics_from_counts(
        tp=sum(m.tp for m in values),
        fn=sum(m.fn for m in values),
        tn=sum(m.tn for m in values),
        fp=sum(m.fp for m in values),
    )


def macro_metrics(per_condition: Mapping[str, ConfusionMetrics]) -> MacroMetrics:
    """Unweighted means of defined condition-level values (in condition order)."""
    values = list(per_condition.values())
    return MacroMetrics(
        accuracy=mean_defined(m.accuracy for m in values),
        sensitivity=mean_defined(m.sensitivity for m in values),
        specificity=mean_defined(m.specificity for m in values),
        precision=mean_defined(m.precision for m in values),
        f1=mean_defined(m.f1 for m in values),
    )
