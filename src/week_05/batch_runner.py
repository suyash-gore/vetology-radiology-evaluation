"""Resumable batch classification with Week 4 retry and checkpoint semantics.

Per case, in input order:

1. If ``str(case_id)`` already has a valid success record in the predictions
   file, the case is skipped (no classifier call).
2. Otherwise up to ``max_attempts`` application-level attempts are made. An
   attempt = one classifier call on ``case.to_llm_payload()`` + strict response
   validation. Any exception (API error, timeout, invalid response) fails the
   attempt; the next attempt starts immediately (no backoff, as in Week 4).
   LangChain's own transport retries (``OPENAI_MAX_RETRIES``) happen inside a
   single classifier call and are not counted here.
3. The first valid attempt appends a success record; if all attempts fail, one
   failure record (``attempts = max_attempts``, last error) is appended to the
   errors file and the batch continues with the next case.
4. Failed cases are not marked complete, so a later run retries them.

Only ``case.to_llm_payload()`` ever reaches the classifier; reference labels
are never passed to this module.

Approved improvement (P6): when the default OpenAI classifier is used and at
least one case needs classifying, credentials and settings are validated once
before the first attempt, so a missing key aborts the run instead of being
recorded as a failure for every case. A ``ConfigurationError`` raised during a
run is likewise fatal rather than retried.
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from week_05 import config
from week_05.config import ConfigurationError, WorkflowSpec
from week_05.dataset_loader import DatasetError, load_dataset
from week_05.jsonl_store import (
    Clock,
    append_jsonl,
    checkpoint_key,
    failure_record,
    format_error,
    load_successful_case_ids,
    success_record,
    utc_now,
)
from week_05.response_validator import validate_model_response

logger = logging.getLogger("week_05.batch_runner")

Classifier = Callable[[Mapping[str, str]], str]


class BatchCase(Protocol):
    """What the batch runner needs from a case (``ReportCase`` satisfies it)."""

    case_id: Any

    def to_llm_payload(self) -> dict[str, str]: ...


def _new_counts(total: int) -> dict[str, int]:
    return {"total": total, "skipped": 0, "succeeded": 0, "failed": 0}


def _default_classifier() -> Classifier:
    from week_05.llm_client import OpenAIClassifier

    return OpenAIClassifier()


def run_batch(
    cases: Sequence[BatchCase],
    results_path: str | Path,
    errors_path: str | Path,
    max_attempts: int = config.DEFAULT_MAX_ATTEMPTS,
    classifier: Classifier | None = None,
    *,
    clock: Clock = utc_now,
) -> dict[str, int]:
    """Classify cases, validate every response and checkpoint successes.

    Returns Week 4's summary: ``{"total", "skipped", "succeeded", "failed"}``.
    """
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    results_file = Path(results_path)
    errors_file = Path(errors_path)
    results_file.parent.mkdir(parents=True, exist_ok=True)
    errors_file.parent.mkdir(parents=True, exist_ok=True)

    completed = load_successful_case_ids(results_file)
    counts = _new_counts(len(cases))

    pending = sum(1 for case in cases if checkpoint_key(case.case_id) not in completed)
    if classifier is None:
        if pending:
            config.validate_runtime_configuration()  # fail fast before any attempt
        classifier = _default_classifier()

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
                predictions = validate_model_response(raw_response)
                record = success_record(case.case_id, attempt, predictions, clock)
                break
            except ConfigurationError:
                raise  # not a per-case problem; retrying cannot help
            except Exception as exc:  # noqa: BLE001 — Week 4 retries on any error
                last_error = format_error(exc)
                logger.warning(
                    "CaseID %s attempt %d/%d failed: %s", key, attempt, max_attempts, last_error
                )

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
# Workflow-level entry point
# ---------------------------------------------------------------------------

WEEK4_OUTPUTS = config.REPO_ROOT / "outputs" / "week_04"


@dataclass(frozen=True)
class BatchOutputs:
    output_dir: Path
    predictions_path: Path
    errors_path: Path


def resolve_outputs(spec: WorkflowSpec, output_dir: str | Path | None = None) -> BatchOutputs:
    """Return the workflow's output files, refusing locations that break isolation.

    The directory may be overridden, but never to another workflow's default
    directory or anywhere inside ``outputs/week_04`` (Week 4 artifacts are
    read-only for Week 5).
    """
    directory = Path(spec.output_dir if output_dir is None else output_dir).expanduser().resolve()
    for other in config.WORKFLOWS.values():
        if other.name == spec.name:
            continue
        other_dir = other.output_dir.resolve()
        if (directory == other_dir or directory.is_relative_to(other_dir)
                or other_dir.is_relative_to(directory)):
            raise ConfigurationError(
                f"{spec.name} cannot write to or around the {other.name} output "
                f"directory: {directory}"
            )
    if directory == WEEK4_OUTPUTS.resolve() or directory.is_relative_to(WEEK4_OUTPUTS.resolve()):
        raise ConfigurationError(f"Week 5 must not write into Week 4 outputs: {directory}")
    return BatchOutputs(
        output_dir=directory,
        predictions_path=directory / config.PREDICTIONS_FILENAME,
        errors_path=directory / config.ERRORS_FILENAME,
    )


def run_workflow_batch(
    spec: WorkflowSpec,
    input_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_attempts: int = config.DEFAULT_MAX_ATTEMPTS,
    limit: int | None = None,
    worksheet_name: str | None = None,
    classifier: Classifier | None = None,
    clock: Clock = utc_now,
) -> dict[str, int]:
    """Load one workflow's cases and run the batch into that workflow's outputs.

    Only ``dataset.cases`` is passed on; ``dataset.reference_labels`` stays here
    and is discarded. Matrix 1 keeps Week 4's exact-100-case requirement and
    rejects any ``limit`` argument; Matrix 2 accepts one.
    """
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")
    if limit is not None and not spec.configurable_limit:
        raise ValueError(
            f"{spec.name} always processes exactly {spec.case_limit} cases; "
            "the case limit is not configurable."
        )
    outputs = resolve_outputs(spec, output_dir)

    dataset = load_dataset(spec, input_path, limit=limit, worksheet_name=worksheet_name)
    expected = spec.case_limit if limit is None else limit
    if spec.require_exact_case_count and len(dataset.cases) != expected:
        raise DatasetError(
            f"{spec.name} batch requires exactly {expected} cases; loaded {len(dataset.cases)}."
        )

    logger.info("%s input: %s", spec.name, dataset.source_path)
    logger.info("%s cases selected: %d", spec.name, len(dataset.cases))
    logger.info("%s predictions/checkpoint: %s", spec.name, outputs.predictions_path)
    logger.info("%s errors: %s", spec.name, outputs.errors_path)

    return run_batch(
        cases=dataset.cases,
        results_path=outputs.predictions_path,
        errors_path=outputs.errors_path,
        max_attempts=max_attempts,
        classifier=classifier,
        clock=clock,
    )
