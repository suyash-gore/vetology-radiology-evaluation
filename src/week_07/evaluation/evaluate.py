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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    application: str = config.CANINE_THORAX_APPLICATION


# Week 4/5: Matrix 1 evaluation requires exactly 100 cases; Matrix 2 uses exact
# CaseID-set matching only.
EXPECTED_CASES = {"matrix1": 100}


def compute_evaluation(labels: ReconciledLabels, model_record: str = "Not recorded",
                       source_digests: Mapping[Path, str] | None = None,
                       *, condition_keys: Sequence[str] | None = None,
                       application: str = config.CANINE_THORAX_APPLICATION) -> EvaluationResult:
    if condition_keys is None:
        per_condition = condition_metrics(labels.reference, labels.predictions, labels.case_ids)
    else:
        per_condition = condition_metrics(labels.reference, labels.predictions, labels.case_ids,
                                          conditions=tuple(condition_keys))
    return EvaluationResult(
        workflow=labels.workflow,
        labels=labels,
        per_condition=per_condition,
        micro=micro_metrics(per_condition),
        macro=macro_metrics(per_condition),
        model_record=model_record,
        source_digests=dict(source_digests or {}),
        application=application,
    )


def check_prediction_source(spec: WorkflowSpec, predictions_path: Path,
                            isolation: IsolationPolicy = DEFAULT_POLICY) -> None:
    """Refuse predictions stored in any directory that belongs to another workflow.

    Workflows are identified as ``<application>/<workflow>`` (Stage 2.1). An
    application's shared predictions directory is never foreign to its own
    workflows; directories a workflow does not have (``None``) are skipped.

    Application trees (Stage 2.2), checked first:

    * Predictions anywhere inside ANOTHER application's output root
      (``isolation.application_roots``) are refused, including custom or
      unregistered subdirectories.
    * A workflow of an application that has its own root may only read
      predictions inside ``outputs/week_07/`` when they are inside that root:
      the rest of ``outputs/week_07/`` is Canine Thorax's tree.
    """
    resolved = predictions_path.expanduser().resolve()
    own_root = isolation.application_roots.get(spec.application)
    for application, app_root in isolation.application_roots.items():
        app_root = app_root.resolve()
        if application != spec.application and resolved.is_relative_to(app_root):
            raise EvaluationInputError(
                f"{spec.name} evaluation cannot use predictions from the {application} "
                f"application output directory {app_root}: {resolved}"
            )
    if own_root is not None and resolved.is_relative_to(isolation.output_root.resolve()) \
            and not resolved.is_relative_to(own_root.resolve()):
        raise EvaluationInputError(
            f"{spec.qualified_name} evaluation cannot use predictions from outside its own "
            f"application output directory {own_root.resolve()}: {resolved}"
        )
    for other in isolation.workflows.values():
        if other.qualified_name == spec.qualified_name:
            continue
        directories = [other.output_dir, other.comparison_dir, other.week5_output_dir]
        if other.shared_predictions_dir is not None and not (
                other.application == spec.application
                and other.shared_predictions_dir == spec.shared_predictions_dir):
            directories.append(other.shared_predictions_dir)
        for directory in directories:
            if directory is None:
                continue
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
        recorded_application = identity.get("application", config.CANINE_THORAX_APPLICATION)
        if recorded_application != spec.application:
            raise EvaluationInputError(
                f"The run manifest beside {predictions_path.name} belongs to application "
                f"{recorded_application!r}, not {spec.application!r}."
            )
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


# ---------------------------------------------------------------------------
# Shared-prediction applications (Feline Thorax, Canine Abdomen)
# ---------------------------------------------------------------------------

def _require_application(app: Any, workflow: Any) -> tuple[Any, WorkflowSpec]:
    from week_07.applications import ApplicationSpec

    if not isinstance(app, ApplicationSpec):
        raise config.ConfigurationError(
            "An explicit application specification (ApplicationSpec) is required.")
    if not app.shared_predictions:
        raise config.ConfigurationError(
            f"{app.key} is evaluated per workflow; use evaluate_workflow for it.")
    if not isinstance(workflow, str) or not workflow:
        raise config.ConfigurationError(f"An explicit workflow name is required for {app.key}.")
    return app, app.workflow(workflow)


def check_application_manifest(app: Any, identity: Mapping[str, Any],
                               source_workbook: Path, provider_label: str) -> None:
    """The shared run manifest must belong to this application and its source workbook."""
    expected = {
        "application": app.key,
        "prediction_source_workflow": app.prediction_source_workflow,
        "workflow": app.prediction_source_workflow,
        "provider": provider_label,
        "condition_keys": list(app.condition_keys),
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise EvaluationInputError(
                f"The run manifest {key!r} is {identity.get(key)!r}; expected {value!r} for "
                f"{app.key}. These predictions were not produced by this application's shared "
                "batch run."
            )
    prompt = identity.get("prompt") or {}
    if (prompt.get("name"), prompt.get("version")) != (app.prompt.name, app.prompt.version):
        raise EvaluationInputError(
            f"The run manifest prompt {prompt.get('name')!r} {prompt.get('version')!r} is not "
            f"{app.prompt.label!r}."
        )
    recorded = identity.get("input_workbook", {}).get("sha256")
    actual = sha256_file(source_workbook)
    if recorded != actual:
        raise EvaluationInputError(
            f"The predictions were produced from a different input workbook than "
            f"{source_workbook.name} (run manifest digest {recorded}, workbook digest {actual})."
        )


def evaluate_application(
    app: Any,
    workflow: str,
    input_path: str | Path | None = None,
    predictions_path: str | Path | None = None,
    *,
    prediction_source_input: str | Path | None = None,
    isolation: IsolationPolicy = DEFAULT_POLICY,
) -> EvaluationResult:
    """Evaluate a shared-prediction application's predictions against ONE reference matrix.

    * The predictions (default: the application's shared ``predictions/``) must
      pass the application-qualified source check and have a run manifest of
      THIS application (provider, condition keys, prompt, prediction source
      workflow) produced from the Matrix 1 workbook (SHA-256 verified).
    * Matrix 1: references from the Matrix 1 workbook itself (Week 4 evaluator
      rules + the declared normalisation); exactly 100 cases.
    * Matrix 2: references from the Gold Standard workbook (batch-loader rules +
      ambiguity guardrail, no normalisation). The Matrix 1 workbook
      (``prediction_source_input``, default its configured path) must hold the
      same CaseIDs in the same order with identical report text.
    * All workbooks, the predictions file and the manifest are read-only
      (SHA-256 checked before and after). The two reference tracks are never
      merged: each call evaluates one matrix.
    """
    from week_07.app_dataset_loader import check_cross_matrix
    from week_07.evaluation.app_reconcile import reconcile_application
    from week_07.evaluation.app_reference_loader import load_application_reference
    from week_07.providers import provider_for

    app, spec = _require_application(app, workflow)
    provider = provider_for(app)
    source_spec = app.workflow(app.prediction_source_workflow)
    reference_path = Path(spec.default_input_path if input_path is None else input_path)
    reference_path = reference_path.expanduser().resolve()
    if spec.name == source_spec.name:
        if prediction_source_input is not None and \
                Path(prediction_source_input).expanduser().resolve() != reference_path:
            raise ValueError(
                f"For {spec.qualified_name} the reference workbook IS the prediction source; "
                "--prediction-source-input must be omitted or equal to --input.")
        source_path = reference_path
    else:
        source_path = Path(source_spec.default_input_path if prediction_source_input is None
                           else prediction_source_input).expanduser().resolve()
    predictions = Path(spec.predictions_path if predictions_path is None else predictions_path)
    predictions = predictions.expanduser().resolve()
    check_prediction_source(spec, predictions, isolation)
    manifest_path = predictions.parent / config.MANIFEST_FILENAME
    for label, path in (("Reference workbook", reference_path),
                        ("Prediction source (Matrix 1) workbook", source_path),
                        ("Predictions file", predictions)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} not found: {path}")
    if not manifest_path.is_file():
        raise EvaluationInputError(
            f"No run manifest beside {predictions.name}: {app.key} predictions must come from "
            "this application's shared batch run.")

    with ReadOnlyGuard([reference_path, source_path, predictions, manifest_path]) as guard:
        manifest = run_manifest.read_manifest(manifest_path)
        identity = manifest["identity"]
        check_application_manifest(app, identity, source_path, provider.label)
        if spec.name != source_spec.name:
            check_cross_matrix(app, source_path, reference_path)
        reference = load_application_reference(app, spec, reference_path)
        labels = reconcile_application(spec, app.condition_keys, reference, predictions,
                                       expected_cases=EXPECTED_CASES.get(spec.name))
    record = run_manifest.application_model_record(identity, provider.short_label)
    return compute_evaluation(labels, record, guard.digests, condition_keys=app.condition_keys,
                              application=app.key)


def write_application_workbook(
    app: Any,
    workflow: str,
    result: EvaluationResult,
    output_path: str | Path | None = None,
    *,
    isolation: IsolationPolicy = DEFAULT_POLICY,
    clock: Clock = utc_now,
) -> Path:
    """Write one shared-prediction application's Matrix 1 or Matrix 2 workbook."""
    app, spec = _require_application(app, workflow)
    if result.application != app.key or result.workflow != spec.name:
        raise ValueError(
            f"Result for {result.application}/{result.workflow} cannot be written as a "
            f"{spec.qualified_name} workbook."
        )
    path = resolve_workbook_path(spec, output_path, isolation)
    if spec.name == "matrix1":
        return build_matrix1_workbook(result.labels, result.per_condition, result.micro,
                                      result.macro, path, model_record=result.model_record,
                                      clock=clock, application=app)
    return build_matrix2_workbook(result.labels, result.per_condition, result.micro, path,
                                  model_record=result.model_record, application=app)
