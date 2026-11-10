"""Prediction checkpoint and error-log JSONL files (exact Week 4 contract).

Success record (one line per validated case, field order as written)::

    {"case_id": <as loaded>, "status": "success", "attempts": <n>,
     "completed_at_utc": "<ISO-8601 UTC>", "predictions": {<20 keys, canonical order>}}

Failure record (one line per case that exhausted its attempts)::

    {"case_id": <as loaded>, "status": "failed", "attempts": <max_attempts>,
     "failed_at_utc": "<ISO-8601 UTC>", "error": "<ExceptionType>: <message>"}

Lines are written with ``json.dumps(record, ensure_ascii=False)`` plus ``"\\n"``,
appended and flushed, exactly as in Week 4. No other fields are written. The one
approved deviation is crash recovery in ``append_jsonl`` (see its docstring).
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from week_05.response_validator import validate_predictions

logger = logging.getLogger("week_05.jsonl_store")

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
UNKNOWN_ERROR = "Unknown error"

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(clock: Clock = utc_now) -> str:
    """ISO-8601 UTC timestamp, e.g. ``2026-11-07T05:10:39.561912+00:00``."""
    return clock().isoformat()


def checkpoint_key(case_id: Any) -> str:
    """Week 4 identifies cases by ``str(case_id)``, so 5 and "5" are the same case."""
    return str(case_id)


def format_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def success_record(
    case_id: Any, attempts: int, predictions: Mapping[str, str], clock: Clock = utc_now
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": STATUS_SUCCESS,
        "attempts": attempts,
        "completed_at_utc": timestamp(clock),
        "predictions": dict(predictions),
    }


def failure_record(
    case_id: Any, attempts: int, error: str | None, clock: Clock = utc_now
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": STATUS_FAILED,
        "attempts": attempts,
        "failed_at_utc": timestamp(clock),
        "error": error or UNKNOWN_ERROR,
    }


def _ends_without_newline(path: Path) -> bool:
    """True when the file exists, is non-empty and its last byte is not ``\\n``."""
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            if handle.tell() == 0:
                return False
            handle.seek(-1, 2)
            return handle.read(1) != b"\n"
    except FileNotFoundError:
        return False


def append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    """Append one record as a JSON line and flush.

    Approved deviation from Week 4 (crash recovery only): if an earlier run was
    interrupted mid-write, the file ends with a partial line and no newline.
    Week 4 would append onto that partial line, corrupting the new record too.
    Here a newline is written first, so the partial line stays an (ignored)
    invalid line and the new record is independently readable. When the file
    ends with a newline — every normal run — the bytes written are identical
    to Week 4.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_separator = _ends_without_newline(path)
    if needs_separator:
        logger.warning(
            "%s does not end with a newline (interrupted write?); starting a new line.", path
        )
    with path.open("a", encoding="utf-8") as handle:
        if needs_separator:
            handle.write("\n")
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def load_successful_case_ids(results_path: Path) -> set[str]:
    """Return checkpoint keys of valid completed records (Week 4 semantics).

    A line counts as completed only if it parses, has ``status == "success"``,
    a non-null ``case_id``, and ``predictions`` that still satisfy the 20-key
    Positive/Negative contract. Blank lines are skipped. Any other line is
    reported and ignored, so that case will be classified again.
    """
    completed: set[str] = set()
    if not results_path.exists():
        return completed
    with results_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if record.get("status") == STATUS_SUCCESS and record.get("case_id") is not None:
                    validate_predictions(record.get("predictions"))
                    completed.add(checkpoint_key(record["case_id"]))
            except Exception as exc:  # noqa: BLE001 — Week 4 ignores any bad line
                logger.warning(
                    "Ignoring invalid checkpoint line %d in %s: %s", line_number, results_path, exc
                )
    return completed
