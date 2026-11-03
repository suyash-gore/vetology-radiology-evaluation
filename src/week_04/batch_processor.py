"""Vetology Week 4 — Block 5: resumable batch classification."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

from week_04.llm_client import classify_one_case
from week_04.response_validator import validate_model_response, ResponseValidationError

logger = logging.getLogger("vetology_week4.batch")


def _load_successful_case_ids(results_path: Path) -> set[str]:
    """Read valid completed records; malformed lines are reported and ignored."""
    completed: set[str] = set()
    if not results_path.exists():
        return completed
    with results_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if record.get("status") == "success" and record.get("case_id") is not None:
                    # Only count a checkpoint as complete if its predictions
                    # still satisfy the current 20-key output contract.
                    validate_model_response(json.dumps(record.get("predictions")))
                    completed.add(str(record["case_id"]))
            except Exception as exc:
                logger.warning(
                    "Ignoring invalid checkpoint line %d in %s: %s",
                    line_number, results_path, exc
                )
    return completed


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def run_batch(
    cases: tuple,
    results_path: str | Path,
    errors_path: str | Path,
    max_attempts: int = 2,
    classifier: Callable[[dict[str, str]], str] = classify_one_case,
) -> dict[str, int]:
    """Classify cases, validate every response, and checkpoint successes.

    Successful validated cases are skipped on restart. Failed cases are not
    marked complete and will be attempted again on a later run.
    Gold labels are never passed to `classifier` or written to prediction files.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    results_file = Path(results_path)
    errors_file = Path(errors_path)
    results_file.parent.mkdir(parents=True, exist_ok=True)
    errors_file.parent.mkdir(parents=True, exist_ok=True)

    completed = _load_successful_case_ids(results_file)
    counts = {"total": len(cases), "skipped": 0, "succeeded": 0, "failed": 0}

    for index, case in enumerate(cases, start=1):
        case_id = str(case.case_id)
        if case_id in completed:
            counts["skipped"] += 1
            logger.info(
                "Case %s already has a valid checkpoint; skipping (%d/%d).",
                case_id, index, len(cases)
            )
            continue

        logger.info("Processing CaseID %s (%d/%d).", case_id, index, len(cases))
        last_error: str | None = None
        success_record: dict[str, Any] | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                raw_response = classifier(case.to_llm_payload())
                predictions = validate_model_response(raw_response)
                success_record = {
                    "case_id": case.case_id,
                    "status": "success",
                    "attempts": attempt,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "predictions": predictions,
                }
                break
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "CaseID %s attempt %d/%d failed: %s",
                    case_id, attempt, max_attempts, last_error
                )

        if success_record is not None:
            _append_jsonl(results_file, success_record)
            completed.add(case_id)
            counts["succeeded"] += 1
            logger.info("CaseID %s validated and checkpointed.", case_id)
        else:
            error_record = {
                "case_id": case.case_id,
                "status": "failed",
                "attempts": max_attempts,
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                "error": last_error or "Unknown error",
            }
            _append_jsonl(errors_file, error_record)
            counts["failed"] += 1
            logger.error("CaseID %s failed after %d attempts.", case_id, max_attempts)

        logger.info(
            "Progress: %d/%d visited | %d newly successful | %d failed | %d skipped",
            index, len(cases), counts["succeeded"], counts["failed"], counts["skipped"]
        )

    return counts
