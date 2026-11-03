"""Vetology Week 4 — Block 4: strict model-response validation."""
from __future__ import annotations

import json
from typing import Any

from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS, VALID_LABELS


class ResponseValidationError(ValueError):
    """Raised when an LLM response violates the required output contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ResponseValidationError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def validate_model_response(raw_response: str) -> dict[str, str]:
    """Parse and validate a raw model response against the V1.3 output contract.

    Requirements:
    - The entire response must be a JSON object (no Markdown fences/prose).
    - Exactly the 20 expected condition keys must be present.
    - No duplicate or unexpected keys are allowed.
    - Each value must be exactly 'Positive' or 'Negative'.
    - The returned dictionary follows CONDITION_KEYS order.
    """
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ResponseValidationError("Model response is empty or is not text.")

    try:
        parsed = json.loads(
            raw_response,
            object_pairs_hook=_reject_duplicate_keys,
        )
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

    expected = set(CONDITION_KEYS)
    received = set(parsed.keys())
    missing = [key for key in CONDITION_KEYS if key not in received]
    unexpected = sorted(received - expected)

    problems: list[str] = []
    if missing:
        problems.append(f"Missing keys ({len(missing)}): {missing}")
    if unexpected:
        problems.append(f"Unexpected keys ({len(unexpected)}): {unexpected}")
    if problems:
        raise ResponseValidationError("; ".join(problems))

    invalid_values = {
        key: value
        for key, value in parsed.items()
        if not isinstance(value, str) or value not in VALID_LABELS
    }
    if invalid_values:
        details = ", ".join(
            f"{key}={value!r}" for key, value in invalid_values.items()
        )
        raise ResponseValidationError(
            "Invalid labels. Values must be exactly 'Positive' or "
            f"'Negative': {details}"
        )

    return {key: parsed[key] for key in CONDITION_KEYS}
