"""Resumable batch classification: Week 5 semantics plus the approved Gemini retry policy.

Per case, in input order (unchanged from Week 5 unless noted):

1. If ``str(case_id)`` already has a valid success record in the predictions
   file, the case is skipped (no classifier call).
2. Otherwise up to ``retry_policy.max_attempts`` (default 2) application-level
   attempts are made. An attempt = one classifier call on
   ``case.to_llm_payload()`` (one SDK transport attempt) + strict response
   validation.
3. Each failed attempt is classified by ``error_policy.classify_error``
   (Week 7, decision O3):

   * FATAL (HTTP 400/401/403/404, configuration errors): not retried. The batch
     stops at once by raising (``ConfigurationError`` itself, or
     ``FatalProviderError``); nothing is written for that case, so it stays
     pending and is retried by a later run once the cause is fixed.
   * TRANSIENT (HTTP 408/429/500/502/503/504, network timeouts): if another
     attempt remains, wait ``retry_policy.backoff_seconds(attempt)`` first
     (bounded exponential backoff; 2 s with the defaults).
   * RETRYABLE (invalid JSON, validation failures, empty responses, any other
     error): the next attempt starts immediately, as in Week 5.

4. The first valid attempt appends a success record; if all attempts fail, one
   failure record (``attempts = max_attempts``, last error) is appended to the
   errors file and the batch continues with the next case. Record schemas are
   exactly Week 4/5 (``jsonl_store``).
5. Failed cases are not marked complete, so a later run retries them.

Only ``case.to_llm_payload()`` ever reaches the classifier; reference labels
are never passed to this module. Both output files must pass the Week 7
isolation guard before anything is read or written.

``run_workflow_batch`` runs one workflow (Matrix 1 or Matrix 2) end to end:
it loads that workflow's input workbook with the Week 5 loader rules, passes
ONLY ``dataset.cases`` on (reference labels are discarded here), writes into
that workflow's own Week 7 output directory, and records the run in the
directory's ``run_manifest.json`` (identity checked on every resume).
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from week_07 import config, run_manifest
from week_07.app_validator import load_successful_case_ids_for, validator_for
from week_07.config import (
    DEFAULT_RETRY_POLICY,
    ConfigurationError,
    GeminiModelConfig,
    RetryPolicy,
    WorkflowSpec,
)
from week_07.dataset_loader import DatasetError, load_dataset
from week_07.error_policy import ErrorClass, FatalProviderError, classify_error
from week_07.isolation import DEFAULT_POLICY, IsolationPolicy, OutputArea
from week_07.jsonl_store import (
    Clock,
    append_jsonl,
    checkpoint_key,
    failure_record,
    format_error,
    load_successful_case_ids,
    success_record,
    utc_now,
)
from week_07.response_validator import validate_model_response

logger = logging.getLogger("week_07.batch_runner")

Classifier = Callable[[Mapping[str, str]], str]
ErrorClassifier = Callable[[BaseException, RetryPolicy], Any]
Sleep = Callable[[float], None]


class BatchCase(Protocol):
    """What the batch runner needs from a case (``ReportCase`` satisfies it)."""

    case_id: Any

    def to_llm_payload(self) -> dict[str, str]: ...


def _new_counts(total: int) -> dict[str, int]:
    return {"total": total, "skipped": 0, "succeeded": 0, "failed": 0, "transient_backoffs": 0}


def _default_classifier(settings: GeminiModelConfig | None = None) -> Classifier:
    from week_07.llm_client import GeminiClassifier

    return GeminiClassifier(settings)


def run_batch(
    cases: Sequence[BatchCase],
    results_path: str | Path,
    errors_path: str | Path,
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    classifier: Classifier | None = None,
    *,
    spec: WorkflowSpec | None = None,
    isolation: IsolationPolicy = DEFAULT_POLICY,
    clock: Clock = utc_now,
    sleep: Sleep = time.sleep,
    settings: GeminiModelConfig | None = None,
    condition_keys: Sequence[str] | None = None,
    error_classifier: ErrorClassifier | None = None,
) -> dict[str, int]:
    """Classify cases, validate every response and checkpoint successes.

    ``condition_keys`` and ``error_classifier`` default to Canine Thorax
    (``response_validator`` / ``jsonl_store`` checkpoint contract and the Gemini
    ``error_policy``) — the Week 5/7 behaviour. ``run_application_batch`` passes
    the application's keys and its provider's error policy.

    Returns ``{"total", "skipped", "succeeded", "failed", "transient_backoffs"}``
    (Week 5's summary plus the number of backoff waits). On a fatal error the
    raised ``FatalProviderError`` carries the counts reached so far.
    """
    if not isinstance(retry_policy, RetryPolicy):
        raise TypeError("retry_policy must be a RetryPolicy.")
    max_attempts = retry_policy.max_attempts

    results_file = isolation.assert_writable(results_path, spec, OutputArea.RUN)
    errors_file = isolation.assert_writable(errors_path, spec, OutputArea.RUN)
    results_file.parent.mkdir(parents=True, exist_ok=True)
    errors_file.parent.mkdir(parents=True, exist_ok=True)

    if condition_keys is None:
        validate = validate_model_response
        completed = load_successful_case_ids(results_file)
    else:
        validate = validator_for(condition_keys)
        completed = load_successful_case_ids_for(results_file, condition_keys)
    classify = classify_error if error_classifier is None else error_classifier
    counts = _new_counts(len(cases))

    pending = sum(1 for case in cases if checkpoint_key(case.case_id) not in completed)
    if classifier is None:
        if pending:
            config.validate_runtime_configuration(None, config.ENV_FILE)  # fail fast
        classifier = _default_classifier(settings)

    for index, case in enumerate(cases, start=1):
        key = checkpoint_key(case.case_id)
        if key in completed:
            counts["skipped"] += 1
            logger.info(
                "Case %s already has a valid checkpoint; skipping (%d/%d).",
                key, index, len(cases),
            )
            continue

        logger.info("Processing CaseID %s (%d/%d).", key, index, len(cases))
        last_error: str | None = None
        record: dict[str, Any] | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                raw_response = classifier(case.to_llm_payload())
                predictions = validate(raw_response)
                record = success_record(case.case_id, attempt, predictions, clock)
                break
            except Exception as exc:  # noqa: BLE001 — classified below
                decision = classify(exc, retry_policy)
                last_error = format_error(exc)
                if decision.error_class is ErrorClass.FATAL:
                    logger.error("CaseID %s attempt %d/%d fatal (%s): %s",
                                 key, attempt, max_attempts, decision.reason, last_error)
                    if isinstance(exc, ConfigurationError):
                        raise  # as in Week 5: not a per-case problem
                    raise FatalProviderError(
                        f"Fatal provider error for CaseID {key} ({decision.reason}); the batch "
                        f"was stopped and this case remains pending. {last_error}",
                        decision,
                        counts,
                    ) from exc
                logger.warning("CaseID %s attempt %d/%d failed (%s): %s",
                               key, attempt, max_attempts, decision.reason, last_error)
                if decision.needs_backoff and attempt < max_attempts:
                    delay = retry_policy.backoff_seconds(attempt)
                    counts["transient_backoffs"] += 1
                    logger.info("CaseID %s: waiting %.1f s before attempt %d.",
                                key, delay, attempt + 1)
                    sleep(delay)

        if record is not None:
            append_jsonl(results_file, record)
            completed.add(key)
            counts["succeeded"] += 1
            logger.info("CaseID %s validated and checkpointed.", key)
        else:
            append_jsonl(errors_file, failure_record(case.case_id, max_attempts, last_error, clock))
            counts["failed"] += 1
            logger.error("CaseID %s failed after %d attempts.", key, max_attempts)

        logger.info(
            "Progress: %d/%d visited | %d newly successful | %d failed | %d skipped",
            index, len(cases), counts["succeeded"], counts["failed"], counts["skipped"],
        )

    return counts


# ---------------------------------------------------------------------------
# Workflow-level entry point (Matrix 1 and Matrix 2 are strictly separate)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BatchOutputs:
    output_dir: Path
    predictions_path: Path
    errors_path: Path
    manifest_path: Path


def resolve_outputs(
    spec: WorkflowSpec,
    output_dir: str | Path | None = None,
    *,
    isolation: IsolationPolicy = DEFAULT_POLICY,
) -> BatchOutputs:
    """The workflow's output files; the directory must pass the Week 7 isolation guard.

    The directory may be overridden, but only to a location inside
    ``outputs/week_07/`` that belongs to no other workflow or output area.
    """
    directory = isolation.assert_writable(
        spec.output_dir if output_dir is None else output_dir, spec, OutputArea.RUN)
    return BatchOutputs(
        output_dir=directory,
        predictions_path=directory / config.PREDICTIONS_FILENAME,
        errors_path=directory / config.ERRORS_FILENAME,
        manifest_path=directory / config.MANIFEST_FILENAME,
    )


def run_workflow_batch(
    spec: WorkflowSpec,
    input_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    limit: int | None = None,
    worksheet_name: str | None = None,
    classifier: Classifier | None = None,
    settings: GeminiModelConfig | None = None,
    isolation: IsolationPolicy = DEFAULT_POLICY,
    clock: Clock = utc_now,
    sleep: Sleep = time.sleep,
) -> dict[str, int]:
    """Load one workflow's cases and run the batch into that workflow's Week 7 outputs.

    * Matrix 1 keeps the exact-100-case requirement and rejects any ``limit``;
      Matrix 2 accepts one (Week 5 behaviour).
    * Only ``dataset.cases`` is passed on; ``dataset.reference_labels`` stays here
      and is discarded — labels are never sent to Gemini or written to outputs.
    * With the default (Gemini) classifier, credentials and settings are
      validated before anything is written whenever a case still needs
      classifying. ``settings`` (the model identity recorded in the manifest)
      defaults to the environment configuration.
    """
    if limit is not None and not spec.configurable_limit:
        raise ValueError(
            f"{spec.name} always processes exactly {spec.case_limit} cases; "
            "the case limit is not configurable."
        )
    outputs = resolve_outputs(spec, output_dir, isolation=isolation)

    dataset = load_dataset(spec, input_path, limit=limit, worksheet_name=worksheet_name)
    expected = spec.case_limit if limit is None else limit
    if spec.require_exact_case_count and len(dataset.cases) != expected:
        raise DatasetError(
            f"{spec.name} batch requires exactly {expected} cases; loaded {len(dataset.cases)}."
        )
    cases = dataset.cases  # reference labels are deliberately not kept

    completed = load_successful_case_ids(outputs.predictions_path)
    pending = sum(1 for case in cases if checkpoint_key(case.case_id) not in completed)
    if settings is None:
        if classifier is None and pending:
            settings = config.validate_runtime_configuration(None, config.ENV_FILE)
        else:
            settings = config.load_model_config(None, config.ENV_FILE)

    identity = run_manifest.run_identity(spec, settings, dataset.source_path,
                                         dataset.worksheet_name)
    manifest = run_manifest.RunManifest.begin(
        outputs.manifest_path, outputs.predictions_path, identity,
        run_manifest.run_details(limit, len(cases), settings, retry_policy),
        spec=spec, isolation=isolation, clock=clock,
    )

    logger.info("%s input: %s (worksheet %s)", spec.name, dataset.source_path.name,
                dataset.worksheet_name)
    logger.info("%s cases selected: %d (%d pending)", spec.name, len(cases), pending)
    logger.info("%s model: %s, temperature %s", spec.name, settings.model, settings.temperature)
    logger.info("%s predictions/checkpoint: %s", spec.name, outputs.predictions_path)
    logger.info("%s errors: %s", spec.name, outputs.errors_path)

    try:
        counts = run_batch(
            cases=cases,
            results_path=outputs.predictions_path,
            errors_path=outputs.errors_path,
            retry_policy=retry_policy,
            classifier=classifier,
            spec=spec,
            isolation=isolation,
            clock=clock,
            sleep=sleep,
            settings=settings,
        )
    except FatalProviderError as exc:
        manifest.finish(run_manifest.STATUS_FATAL, exc.counts, str(exc))
        raise
    except ConfigurationError as exc:
        manifest.finish(run_manifest.STATUS_CONFIGURATION, None, format_error(exc))
        raise
    except BaseException as exc:
        manifest.finish(run_manifest.STATUS_INTERRUPTED, None, type(exc).__name__)
        raise
    manifest.finish(run_manifest.STATUS_COMPLETED, counts)
    return counts


# ---------------------------------------------------------------------------
# Shared-prediction applications (Feline Thorax, Canine Abdomen)
# ---------------------------------------------------------------------------

def _require_application_workflow(app: Any, workflow: Any) -> tuple[Any, WorkflowSpec]:
    """Explicit, valid application + workflow, or a ConfigurationError/ValueError."""
    from week_07.applications import ApplicationSpec

    if not isinstance(app, ApplicationSpec):
        raise ConfigurationError(
            "An explicit application specification (ApplicationSpec) is required.")
    if not app.shared_predictions:
        raise ConfigurationError(
            f"{app.key} keeps one batch run per workflow; use run_workflow_batch for it.")
    if not isinstance(workflow, str) or not workflow:
        raise ConfigurationError(
            f"An explicit workflow name is required for {app.key} "
            f"(expected {app.prediction_source_workflow!r}).")
    spec = app.workflow(workflow)  # unknown names raise ConfigurationError
    if spec.name != app.prediction_source_workflow:
        raise ValueError(
            f"{app.key} generates its predictions once, from the "
            f"{app.prediction_source_workflow} workbook, and reuses them for every "
            f"reference matrix; a {spec.name} batch run is not available."
        )
    return app, spec


def resolve_application_outputs(
    spec: WorkflowSpec,
    output_dir: str | Path | None = None,
    *,
    isolation: IsolationPolicy = DEFAULT_POLICY,
) -> BatchOutputs:
    """The application's shared batch outputs (default ``<app>/predictions/``), guarded."""
    directory = isolation.assert_writable(
        spec.run_dir if output_dir is None else output_dir, spec, OutputArea.RUN)
    return BatchOutputs(
        output_dir=directory,
        predictions_path=directory / config.PREDICTIONS_FILENAME,
        errors_path=directory / config.ERRORS_FILENAME,
        manifest_path=directory / config.MANIFEST_FILENAME,
    )


def run_application_batch(
    app: Any,
    workflow: str,
    input_path: str | Path | None = None,
    *,
    provider: str | None = None,
    output_dir: str | Path | None = None,
    retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    worksheet_name: str | None = None,
    matrix2_input: str | Path | None = None,
    classifier: Classifier | None = None,
    settings: Any = None,
    isolation: IsolationPolicy = DEFAULT_POLICY,
    clock: Clock = utc_now,
    sleep: Sleep = time.sleep,
) -> dict[str, int]:
    """Run the ONE shared prediction batch of a Feline Thorax / Canine Abdomen application.

    * ``app`` and ``workflow`` are mandatory and must be a shared-prediction
      application and its prediction source workflow (``matrix1``). Matrix 2
      never has its own batch run: it reuses these predictions.
    * Cases come from the Matrix 1 workbook (application loader; exactly 100
      cases). Only ``case.to_llm_payload()`` reaches the classifier; reference
      labels are validated, then discarded here.
    * ``matrix2_input``, when given, is checked against the Matrix 1 workbook
      (same CaseIDs in the same order, identical report text) before any write.
    * The application's prompt must be pinned (a pending prompt stops the run
      before anything is written) and is recorded in the run manifest identity
      together with the application, provider, model, condition keys and input
      digest. Resuming with a different identity is refused.
    * Credentials: only the application's provider key is required, and only
      when a case still needs classifying with the real client.
    """
    from week_07.app_dataset_loader import check_cross_matrix, load_application_dataset
    from week_07.prompts.prompt_loader import PromptIntegrityError
    from week_07.prompts.registry import prompt_identity
    from week_07.providers import provider_for

    app, spec = _require_application_workflow(app, workflow)
    provider_spec = provider_for(app, provider)
    outputs = resolve_application_outputs(spec, output_dir, isolation=isolation)

    dataset = load_application_dataset(app, spec, input_path, worksheet_name=worksheet_name)
    if len(dataset.cases) != spec.case_limit:
        raise DatasetError(f"{spec.qualified_name} batch requires exactly {spec.case_limit} "
                           f"cases; loaded {len(dataset.cases)}.")
    if matrix2_input is not None:
        check_cross_matrix(app, dataset.source_path, matrix2_input)
    cases = dataset.cases  # reference labels are deliberately not kept

    try:
        prompt = prompt_identity(app.prompt)
    except PromptIntegrityError as exc:
        raise ConfigurationError(str(exc)) from exc

    completed = load_successful_case_ids_for(outputs.predictions_path, app.condition_keys)
    pending = sum(1 for case in cases if checkpoint_key(case.case_id) not in completed)
    if settings is None:
        if classifier is None and pending:
            settings = provider_spec.validate_runtime(app)
        else:
            settings = provider_spec.load_settings(app)
    elif classifier is None and pending and not provider_spec.api_key_is_configured():
        raise ConfigurationError(
            f"{provider_spec.api_key_var} was not found. Add it to the repository-root .env "
            "file. Do not paste the key into source code or commit the .env file.")
    if classifier is None:
        classifier = provider_spec.make_classifier(app, settings)

    identity = run_manifest.application_run_identity(
        app, spec, provider_spec.label, settings, dataset.source_path, dataset.worksheet_name,
        prompt)
    manifest = run_manifest.RunManifest.begin(
        outputs.manifest_path, outputs.predictions_path, identity,
        run_manifest.run_details(None, len(cases), settings, retry_policy),
        spec=spec, isolation=isolation, clock=clock, packages=provider_spec.packages,
    )

    logger.info("%s input: %s (worksheet %s)", spec.qualified_name, dataset.source_path.name,
                dataset.worksheet_name)
    logger.info("%s cases selected: %d (%d pending)", spec.qualified_name, len(cases), pending)
    logger.info("%s provider: %s; model: %s, temperature %s", spec.qualified_name,
                provider_spec.name, settings.model, settings.temperature)
    logger.info("%s shared predictions/checkpoint: %s", spec.qualified_name,
                outputs.predictions_path)

    try:
        counts = run_batch(
            cases=cases,
            results_path=outputs.predictions_path,
            errors_path=outputs.errors_path,
            retry_policy=retry_policy,
            classifier=classifier,
            spec=spec,
            isolation=isolation,
            clock=clock,
            sleep=sleep,
            condition_keys=app.condition_keys,
            error_classifier=provider_spec.error_classifier(),
        )
    except FatalProviderError as exc:
        manifest.finish(run_manifest.STATUS_FATAL, exc.counts, str(exc))
        raise
    except ConfigurationError as exc:
        manifest.finish(run_manifest.STATUS_CONFIGURATION, None, format_error(exc))
        raise
    except BaseException as exc:
        manifest.finish(run_manifest.STATUS_INTERRUPTED, None, type(exc).__name__)
        raise
    manifest.finish(run_manifest.STATUS_COMPLETED, counts)
    return counts
