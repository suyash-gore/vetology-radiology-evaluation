"""Offline tests for batch checkpoint/retry behaviour; no API calls."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from week_04.batch_processor import run_batch
from week_04.prompts.canine_thorax_prompt import CONDITION_KEYS

VALID = {key: "Negative" for key in CONDITION_KEYS}


def main() -> None:
    cases = (
        SimpleNamespace(case_id=1, to_llm_payload=lambda: {
            "findings": "sample", "conclusions": "", "recommendations": ""
        }),
        SimpleNamespace(case_id=2, to_llm_payload=lambda: {
            "findings": "sample 2", "conclusions": "", "recommendations": ""
        }),
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        results = root / "predictions.jsonl"
        errors = root / "errors.jsonl"
        calls = []

        def mock_classifier(payload):
            calls.append(payload)
            return json.dumps(VALID)

        first = run_batch(cases, results, errors, max_attempts=2, classifier=mock_classifier)
        assert first == {"total": 2, "skipped": 0, "succeeded": 2, "failed": 0}
        assert len(calls) == 2
        print("PASS — two successful cases checkpointed")

        second = run_batch(cases, results, errors, max_attempts=2, classifier=mock_classifier)
        assert second == {"total": 2, "skipped": 2, "succeeded": 0, "failed": 0}
        assert len(calls) == 2
        print("PASS — successful cases skipped on restart")

        # Verify retry of invalid response, followed by success.
        retry_results = root / "retry_predictions.jsonl"
        retry_errors = root / "retry_errors.jsonl"
        retry_calls = []
        def invalid_then_valid(payload):
            retry_calls.append(payload)
            return "not json" if len(retry_calls) == 1 else json.dumps(VALID)

        retry = run_batch(cases[:1], retry_results, retry_errors,
                          max_attempts=2, classifier=invalid_then_valid)
        assert retry["succeeded"] == 1 and retry["failed"] == 0
        assert len(retry_calls) == 2
        print("PASS — invalid response retried and valid response saved")

        # Verify permanent failure is recorded but not checkpointed as success.
        fail_results = root / "fail_predictions.jsonl"
        fail_errors = root / "fail_errors.jsonl"
        failure = run_batch(cases[:1], fail_results, fail_errors,
                            max_attempts=2, classifier=lambda payload: "bad")
        assert failure["failed"] == 1
        error_record = json.loads(fail_errors.read_text().splitlines()[0])
        assert error_record["status"] == "failed"
        assert not fail_results.exists()
        print("PASS — exhausted attempts logged as failure, not success")

    print("\nBLOCK 5 OFFLINE TESTS PASSED")
    print("No OpenAI API request was made.")


if __name__ == "__main__":
    main()
