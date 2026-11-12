"""Workflow-level evaluation entry point.

``evaluate_workflow`` loads the workflow's reference labels with that
workflow's OWN evaluation reference loader (``reference_loader``; deliberately
not the Phase 3 batch loader), loads its own predictions file, reconciles them
and computes the metrics. ``write_evaluation_workbook`` then writes the
workflow's workbook.

* Matrix 1 — Week 4 ``load_matrix1_inputs`` loading rules; exactly 100 cases;
  workbook with the delivered A5 layout (``matrix1_workbook``).
* Matrix 2 — Week 4 Matrix 2 batch-loader rules with an ambiguity guardrail
  (``load_matrix2_reference``); exact CaseID-set matching, no case-count rule;
  workbook with the delivered A6 structure minus the Balanced Accuracy row
  (``matrix2_workbook``).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from week_05 import config
from week_05.config import ConfigurationError, WorkflowSpec
from week_05.evaluation.matrix1_workbook import build_matrix1_workbook
from week_05.evaluation.matrix2_workbook import build_matrix2_workbook
from week_05.evaluation.metrics import (
    ConfusionMetrics,
    MacroMetrics,
    condition_metrics,
    macro_metrics,
    micro_metrics,
)
from week_05.evaluation.reconcile import ReconciledLabels, reconcile
from week_05.evaluation.reference_loader import reference_loader_for
from week_05.jsonl_store import Clock, utc_now


class WorkbookLayoutPending(NotImplementedError):
    """The workflow's workbook layout has not been reconstructed yet."""


@dataclass(frozen=True)
class EvaluationResult:
    workflow: str
    labels: ReconciledLabels
    per_condition: dict[str, ConfusionMetrics]
    micro: ConfusionMetrics
    macro: MacroMetrics


# Week 4's Matrix 1 evaluator requires exactly 100 cases. Matrix 2 uses exact
# CaseID-set matching only; no case count is imposed until A6 is inspected.
EXPECTED_CASES = {"matrix1": 100}


def compute_evaluation(labels: ReconciledLabels) -> EvaluationResult:
    per_condition = condition_metrics(labels.reference, labels.predictions, labels.case_ids)
    return EvaluationResult(
        workflow=labels.workflow,
        labels=labels,
        per_condition=per_condition,
        micro=micro_metrics(per_condition),
        macro=macro_metrics(per_condition),
    )


def evaluate_workflow(
    spec: WorkflowSpec,
    input_path: str | Path | None = None,
    predictions_path: str | Path | None = None,
) -> EvaluationResult:
    """Evaluate one workflow's predictions against that workflow's reference labels.

    Raises ``ReferenceLoadingPending`` (before reading any file) for a workflow
    without an established evaluation reference loader.
    """
    load_reference = reference_loader_for(spec)
    reference = load_reference(spec.default_input_path if input_path is None else input_path)
    labels = reconcile(
        spec,
        reference,
        spec.predictions_path if predictions_path is None else predictions_path,
        expected_cases=EXPECTED_CASES.get(spec.name),
    )
    return compute_evaluation(labels)


def resolve_workbook_path(spec: WorkflowSpec, output_path: str | Path | None) -> Path:
    """Default to the workflow's own workbook path; refuse Week 4 / other-workflow dirs."""
    path = Path(spec.evaluation_workbook_path if output_path is None else output_path)
    path = path.expanduser().resolve()
    week4 = (config.REPO_ROOT / "outputs" / "week_04").resolve()
    if path.is_relative_to(week4):
        raise ConfigurationError(f"Week 5 must not write into Week 4 outputs: {path}")
    for other in config.WORKFLOWS.values():
        if other.name != spec.name and path.is_relative_to(other.output_dir.resolve()):
            raise ConfigurationError(
                f"{spec.name} workbook cannot be written to the {other.name} "
                f"output directory: {path}"
            )
    return path


def write_evaluation_workbook(
    spec: WorkflowSpec,
    result: EvaluationResult,
    output_path: str | Path | None = None,
    *,
    clock: Clock = utc_now,
) -> Path:
    if result.workflow != spec.name:
        raise ValueError(
            f"Result for {result.workflow!r} cannot be written as a {spec.name} workbook."
        )
    path = resolve_workbook_path(spec, output_path)
    if spec.name == "matrix1":
        return build_matrix1_workbook(result.labels, result.per_condition, result.micro,
                                      result.macro, path, clock=clock)
    if spec.name == "matrix2":
        return build_matrix2_workbook(result.labels, result.per_condition, result.micro, path)
    raise WorkbookLayoutPending(
        f"The {spec.name} workbook layout will be reconstructed from "
        f"'{spec.evaluation_workbook_filename}' once that file is available for inspection."
    )
