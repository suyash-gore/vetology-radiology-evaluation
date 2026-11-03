"""Local Block 4 tests. Does not call the OpenAI API."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from week_04.response_validator import (  # noqa: E402
    ResponseValidationError,
    validate_model_response,
)
from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS  # noqa: E402


def expect_invalid(label: str, raw: str) -> None:
    try:
        validate_model_response(raw)
    except ResponseValidationError as exc:
        print(f"PASS — rejected {label}: {exc}")
    else:
        raise AssertionError(f"Expected validator to reject {label}.")


def main() -> None:
    fixture = Path(__file__).with_name("case1_raw_response.json")
    raw = fixture.read_text(encoding="utf-8")
    validated = validate_model_response(raw)
    assert len(validated) == 20
    assert tuple(validated) == CONDITION_KEYS
    assert all(value in {"Positive", "Negative"} for value in validated.values())
    print("PASS — CaseID 1 response is valid")
    print(f"PASS — exactly {len(validated)} expected keys")
    print("PASS — all values are Positive/Negative")
    print("PASS — output follows canonical condition order")

    data = json.loads(raw)
    missing = dict(data)
    missing.pop("pneumonia")
    expect_invalid("missing key", json.dumps(missing))

    extra = dict(data)
    extra["unknown_condition"] = "Negative"
    expect_invalid("unexpected key", json.dumps(extra))

    invalid_value = dict(data)
    invalid_value["pneumonia"] = "positive"
    expect_invalid("wrong-case label", json.dumps(invalid_value))

    expect_invalid("Markdown code fence", f"```json\n{raw}\n```")
    expect_invalid("non-object JSON", json.dumps(["Positive", "Negative"]))

    duplicate = raw[:-1] + ', "pneumonia": "Positive"}'
    expect_invalid("duplicate key", duplicate)

    print("\nBLOCK 4 VALIDATION TESTS PASSED")
    print("No OpenAI API request was made.")


if __name__ == "__main__":
    main()
