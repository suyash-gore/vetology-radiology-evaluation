"""Strict validation of the raw LLM response against the V1.3 output contract.

Reproduces the Week 4 validator (``src/week_04/response_validator.py``) rule for
rule, including the exact error messages, because those messages are written
to ``errors.jsonl`` as ``"ResponseValidationError: <message>"``.

Contract:

* The response must be a non-blank string whose entire content is one JSON
  object (surrounding whitespace is tolerated by the JSON parser; Markdown
  fences, prose, a BOM or a second value are not).
* Duplicate keys are rejected at any nesting level.
* Exactly the 20 condition keys: none missing, none unexpected.
* Every value must be exactly the string ``Positive`` or ``Negative``
  (case-sensitive, no surrounding whitespace).
* Key order in the response is NOT required to be canonical (Week 4 accepts
  any order); the returned dictionary is always in canonical order.

Validation uses only the response text: it never receives a CaseID or any
reference label.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from week_05.conditions import CONDITION_KEYS, VALID_LABELS


class ResponseValidationError(ValueError):
    """Raised when an LLM response violates the required output contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ResponseValidationError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _parse_json_object(raw_response: Any) -> dict[str, Any]:
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ResponseValidationError("Model response is empty or is not text.")
    try:
        parsed = json.loads(raw_response, object_pairs_hook=_reject_duplicate_keys)
    except ResponseValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ResponseValidationError(
            f"Response is not valid JSON: {exc.msg} at line {exc.lineno}, "
            f"column {exc.colno}."
        ) from exc
    if not isinstance(parsed, dict):
        raise ResponseValidationError(
            f"Expected a JSON object, received {type(parsed).__name__}."
        )
    return parsed


def _check_keys(parsed: Mapping[str, Any]) -> None:
    received = set(parsed)
    missing = [key for key in CONDITION_KEYS if key not in received]
    unexpected = sorted(received - set(CONDITION_KEYS))

    problems: list[str] = []
    if missing:
        problems.append(f"Missing keys ({len(missing)}): {missing}")
    if unexpected:
        problems.append(f"Unexpected keys ({len(unexpected)}): {unexpected}")
    if problems:
        raise ResponseValidationError("; ".join(problems))


def _check_labels(parsed: Mapping[str, Any]) -> None:
    invalid = {
        key: value
        for key, value in parsed.items()
        if not isinstance(value, str) or value not in VALID_LABELS
    }
    if invalid:
        details = ", ".join(f"{key}={value!r}" for key, value in invalid.items())
        raise ResponseValidationError(
            "Invalid labels. Values must be exactly 'Positive' or "
            f"'Negative': {details}"
        )


def validate_model_response(raw_response: str) -> dict[str, str]:
    """Parse and validate one raw response; return labels in canonical order.

    Checks run in the Week 4 order: text -> JSON -> object -> keys -> labels,
    so the first failing stage determines the error message.
    """
    parsed = _parse_json_object(raw_response)
    _check_keys(parsed)
    _check_labels(parsed)
    return {key: parsed[key] for key in CONDITION_KEYS}


def validate_predictions(predictions: Any) -> dict[str, str]:
    """Validate an already-parsed prediction mapping (e.g. from a checkpoint).

    Mirrors Week 4's checkpoint check, which serialises the stored mapping and
    applies the same response contract: ``validate_model_response(json.dumps(x))``.
    """
    try:
        serialised = json.dumps(predictions)
    except (TypeError, ValueError) as exc:
        raise ResponseValidationError(f"Predictions are not JSON-serialisable: {exc}") from exc
    return validate_model_response(serialised)
