"""Workflow-level evaluation entry point (Week 7 adaptation of Week 5 ``evaluate``).

``evaluate_workflow`` loads the workflow's reference labels with that
workflow's OWN evaluation reference loader (copied unchanged from Week 5),
loads its own predictions file strictly, reconciles them and computes the
metrics — exactly as Week 5:

* Matrix 1 — Vetology reference labels; Week 4 ``load_matrix1_inputs`` rules;
  exactly 100 cases; A5 workbook layout.
* Matrix 2 — Gold Standard reference labels; Week 4 Matrix 2 batch-loader rules
  with the ambiguity guardrail; exact CaseID-set matching; A6 workbook layout
  minus the Balanced Accuracy row.

Week 7 additions (no change to any calculation):

* Read-only sources: the reference workbook and the predictions file are
  SHA-256-checked before and after evaluation (``ReadOnlyGuard``).
* Source separation: predictions are refused if they live in ANY directory of
  the other workflow — its Week 7 run or comparison outputs, or its Week 5
  outputs (so Week 5 Matrix 2 predictions cannot be evaluated as Matrix 1).
* Model identification: the model record comes from the Week 7 run manifest
  beside the predictions file. If that manifest belongs to another workflow, or
  was produced from a different input workbook (digest mismatch), evaluation is
  refused. Without a manifest (e.g. replaying Week 5 OpenAI predictions) the
  workbook says the model was not recorded, unless ``model_record`` is given.
* Workbooks are written only where the Week 7 isolation guard allows.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from week_07 import config, run_manifest
from week_07.config import WorkflowSpec
from week_07.evaluation.matrix1_workbook import build_matrix1_workbook
from week_07.evaluation.matrix2_workbook import build_matrix2_workbook
from week_07.evaluation.metrics import (
    ConfusionMetrics,
    MacroMetrics,
    condition_metrics,
    macro_metrics,
    micro_metrics,
)
from week_07.evaluation.reconcile import EvaluationInputError, ReconciledLabels, reconcile
from week_07.evaluation.reference_loader import reference_loader_for
from week_07.isolation import (
    DEFAULT_POLICY,
    IsolationPolicy,
    OutputArea,
    ReadOnlyGuard,
    sha256_file,
)
from week_07.jsonl_store import Clock, utc_now

WORKFLOW_LABELS = {"matrix1": "Matrix 1", "matrix2": "Matrix 2"}


class WorkbookLayoutPending(NotImplementedError):
    """The workflow's workbook layout has not been reconstructed yet."""


@dataclass(frozen=True)
class EvaluationResult:
    workflow: str
    labels: ReconciledLabels
    per_condition: dict[str, ConfusionMetrics]
    micro: ConfusionMetrics
    macro: MacroMetrics
    model_record: str = "Not recorded"
    source_digests: Mapping[Path, str] = field(default_factory=dict)


# Week 4/5: Matrix 1 evaluation requires exactly 100 cases; Matrix 2 uses exact
# CaseID-set matching only.
EXPECTED_CASES = {"matrix1": 100}


def compute_evaluation(labels: ReconciledLabels, model_record: str = "Not recorded",
                       source_digests: Mapping[Path, str] | None = None) -> EvaluationResult:
    per_condition = condition_metrics(labels.reference, labels.predictions, labels.case_ids)
    return EvaluationResult(
        workflow=labels.workflow,
        labels=labels,
        per_condition=per_condition,
        micro=micro_metrics(per_condition),
        macro=macro_metrics(per_condition),
        model_record=model_record,
        source_digests=dict(source_digests or {}),
    )


def check_prediction_source(spec: WorkflowSpec, predictions_path: Path,
                            isolation: IsolationPolicy = DEFAULT_POLICY) -> None:
    """Refuse predictions stored in any directory that belongs to another workflow."""
    resolved = predictions_path.expanduser().resolve()
    for other in isolation.workflows.values():
        if other.name == spec.name:
            continue
        for directory in (other.output_dir, other.comparison_dir, other.week5_output_dir):
            if resolved.is_relative_to(directory.resolve()):
                raise EvaluationInputError(
                    f"{spec.name} evaluation cannot use predictions from the {other.name} "
                    f"directory {directory.resolve()}: {resolved}"
                )


def resolve_model_record(spec: WorkflowSpec, predictions_path: Path, reference_path: Path,
                         model_record: str | None = None) -> str:
    """Model description for the workbook, checked against the run manifest."""
    manifest = run_manifest.read_manifest(predictions_path.parent / config.MANIFEST_FILENAME)
    label = WORKFLOW_LABELS.get(spec.name, spec.name)
    if manifest is not None:
        identity = manifest["identity"]
        if identity.get("workflow") != spec.name:
            raise EvaluationInputError(
                f"The run manifest beside {predictions_path.name} belongs to workflow "
                f"{identity.get('workflow')!r}, not {spec.name!r}."
            )
        recorded = identity.get("input_workbook", {}).get("sha256")
        actual = sha256_file(reference_path)
        if recorded != actual:
            raise EvaluationInputError(
                f"The predictions were produced from a different input workbook than "
                f"{reference_path.name} (run manifest digest {recorded}, reference digest "
                f"{actual})."
            )
        if model_record is None:
            return run_manifest.model_record(identity, label)
    if model_record is not None:
        if not model_record.strip():
            raise ValueError("model_record must not be blank.")
        return model_record
    return (f"Not recorded: no Week 7 run manifest beside {predictions_path.name} "
            f"({label} predictions)")


def evaluate_workflow(
    spec: WorkflowSpec,
    input_path: str | Path | None = None,
    predictions_path: str | Path | None = None,
    *,
    model_record: str | None = None,
    isolation: IsolationPolicy = DEFAULT_POLICY,
) -> EvaluationResult:
    """Evaluate one workflow's predictions against that workflow's reference labels."""
    load_reference = reference_loader_for(spec)
    reference_path = Path(spec.default_input_path if input_path is None else input_path)
    reference_path = reference_path.expanduser().resolve()
    predictions = Path(spec.predictions_path if predictions_path is None else predictions_path)
    predictions = predictions.expanduser().resolve()
    check_prediction_source(spec, predictions, isolation)
    if not reference_path.is_file():
        raise FileNotFoundError(f"Reference workbook not found: {reference_path}")
    if not predictions.is_file():
        raise FileNotFoundError(f"Predictions file not found: {predictions}")

    with ReadOnlyGuard([reference_path, predictions]) as guard:
        record = resolve_model_record(spec, predictions, reference_path, model_record)
        reference = load_reference(reference_path)
        labels = reconcile(spec, reference, predictions,
                           expected_cases=EXPECTED_CASES.get(spec.name))
    return compute_evaluation(labels, record, guard.digests)


def resolve_workbook_path(spec: WorkflowSpec, output_path: str | Path | None,
                          isolation: IsolationPolicy = DEFAULT_POLICY) -> Path:
    """Default to the workflow's own workbook path; must pass the isolation guard."""
    path = spec.evaluation_workbook_path if output_path is None else output_path
    return isolation.assert_writable(path, spec, OutputArea.RUN)


def write_evaluation_workbook(
    spec: WorkflowSpec,
    result: EvaluationResult,
    output_path: str | Path | None = None,
    *,
    isolation: IsolationPolicy = DEFAULT_POLICY,
    clock: Clock = utc_now,
) -> Path:
    if result.workflow != spec.name:
        raise ValueError(
            f"Result for {result.workflow!r} cannot be written as a {spec.name} workbook."
        )
    path = resolve_workbook_path(spec, output_path, isolation)
    if spec.name == "matrix1":
        return build_matrix1_workbook(result.labels, result.per_condition, result.micro,
                                      result.macro, path, model_record=result.model_record,
                                      clock=clock)
    if spec.name == "matrix2":
        return build_matrix2_workbook(result.labels, result.per_condition, result.micro, path,
                                      model_record=result.model_record)
    raise WorkbookLayoutPending(
        f"No Week 7 workbook layout exists for {spec.name!r}."
    )
