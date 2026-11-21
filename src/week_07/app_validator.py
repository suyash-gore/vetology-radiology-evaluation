"""Strict, application-aware validation of raw LLM responses.

The contract and the error messages are those of ``response_validator`` (the
verbatim Week 5 copy, used unchanged for Canine Thorax), with the required
condition keys supplied by the application:

* text -> one JSON object (duplicate keys rejected at any depth, no Markdown
  fences, no prose, no repair);
* exactly the application's condition keys: none missing, none unexpected;
* every value exactly ``Positive`` or ``Negative``;
* the returned mapping is in the application's canonical order.

The parsing and label stages are the verbatim functions themselves; only the
key check is parameterised. With the Canine Thorax keys every outcome and
message equals ``response_validator`` (asserted by tests).
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

from week_07.jsonl_store import STATUS_SUCCESS, checkpoint_key
from week_07.response_validator import (
    ResponseValidationError,
    _check_labels,
    _parse_json_object,
)

__all__ = ["ResponseValidationError", "load_successful_case_ids_for", "validate_model_response",
           "validate_predictions", "validator_for"]

logger = logging.getLogger("week_07.jsonl_store")


def _check_keys(parsed: Mapping[str, Any], condition_keys: Sequence[str]) -> None:
    received = set(parsed)
    missing = [key for key in condition_keys if key not in received]
    unexpected = sorted(received - set(condition_keys))

    problems: list[str] = []
    if missing:
        problems.append(f"Missing keys ({len(missing)}): {missing}")
    if unexpected:
        problems.append(f"Unexpected keys ({len(unexpected)}): {unexpected}")
    if problems:
        raise ResponseValidationError("; ".join(problems))


def _require_keys(condition_keys: Sequence[str]) -> tuple[str, ...]:
    keys = tuple(condition_keys)
    if not keys or len(set(keys)) != len(keys):
        raise ValueError("condition_keys must be a non-empty sequence of unique keys.")
    return keys


def validate_model_response(raw_response: str, condition_keys: Sequence[str]) -> dict[str, str]:
    """Parse and validate one raw response; return labels in the application's order."""
    keys = _require_keys(condition_keys)
    parsed = _parse_json_object(raw_response)
    _check_keys(parsed, keys)
    _check_labels(parsed)
    return {key: parsed[key] for key in keys}


def validate_predictions(predictions: Any, condition_keys: Sequence[str]) -> dict[str, str]:
    """Validate an already-parsed prediction mapping (e.g. from a checkpoint)."""
    try:
        serialised = json.dumps(predictions)
    except (TypeError, ValueError) as exc:
        raise ResponseValidationError(f"Predictions are not JSON-serialisable: {exc}") from exc
    return validate_model_response(serialised, condition_keys)


def validator_for(condition_keys: Sequence[str]) -> Callable[[str], dict[str, str]]:
    """A one-argument validator bound to an application's condition keys."""
    return partial(validate_model_response, condition_keys=_require_keys(condition_keys))


def load_successful_case_ids_for(results_path: str | Path,
                                 condition_keys: Sequence[str]) -> set[str]:
    """Checkpoint keys of valid completed records, against an application's keys.

    Same semantics as ``jsonl_store.load_successful_case_ids`` (verbatim Week 5,
    still used for Canine Thorax): a line counts only if it parses, has
    ``status == "success"``, a non-null ``case_id`` and predictions that satisfy
    the application's exact key / Positive-Negative contract. Any other line is
    reported and ignored, so that case is classified again.
    """
    keys = _require_keys(condition_keys)
    completed: set[str] = set()
    path = Path(results_path)
    if not path.exists():
        return completed
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if record.get("status") == STATUS_SUCCESS and record.get("case_id") is not None:
                    validate_predictions(record.get("predictions"), keys)
                    completed.add(checkpoint_key(record["case_id"]))
            except Exception as exc:  # noqa: BLE001 — Week 4 ignores any bad line
                logger.warning("Ignoring invalid checkpoint line %d in %s: %s",
                               line_number, path, exc)
    return completed
