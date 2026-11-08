"""Matrix 1 — Block 2: one-case OpenAI integration smoke test.

This makes one billable OpenAI API request, validates the V1.3 response, and
writes a separate test artifact. It does not write to the batch predictions
or errors JSONL files and does not compare against ground truth.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from week_04.matrix_1.matrix1_data_loader import load_matrix1_dataset  # noqa: E402
from week_04.response_validator import validate_model_response  # noqa: E402


DEFAULT_OUTPUT = Path("outputs/week_04/matrix_1/single_case_test.json")


def build_test_record(
    case_id: object,
    model_name: str,
    raw_response: str,
    predictions: dict[str, str],
) -> dict:
    """Build a traceable test record without including ground-truth labels."""
    return {
        "run_type": "matrix_1_single_case_test",
        "prompt_version": "V1.3",
        "case_id": case_id,
        "model": model_name,
        "status": "success",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_response": raw_response,
        "predictions": predictions,
    }


def run_single_case_test(
    input_path: str | Path,
    case_id: str,
    output_path: str | Path = DEFAULT_OUTPUT,
    classifier: Callable[[dict[str, str]], str] | None = None,
    model_name: str | None = None,
) -> dict:
    """Classify one Matrix 1 case, validate it, and save a separate artifact."""
    dataset = load_matrix1_dataset(input_path)
    selected = next(
        (case for case in dataset.cases if str(case.case_id) == str(case_id)),
        None,
    )
    if selected is None:
        raise ValueError(
            f"CaseID {case_id!r} was not found among the first "
            f"{len(dataset.cases)} Matrix 1 cases."
        )

    # Deliberately pass only the three original report fields to the classifier.
    if classifier is None:
        # Import the live API client only for an actual API run. This keeps
        # offline unit tests independent of API-client initialization.
        from week_04.llm_client import classify_one_case  # noqa: E402
        classify = classify_one_case
    else:
        classify = classifier
    raw_response = classify(selected.to_llm_payload())
    predictions = validate_model_response(raw_response)

    if model_name is None:
        from week_04.llm_client import load_model_config  # noqa: E402
        model_name = load_model_config().model

    record = build_test_record(
        case_id=selected.case_id,
        model_name=model_name,
        raw_response=raw_response,
        predictions=predictions,
    )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one fresh Matrix 1 case through OpenAI using the V1.3 prompt "
            "and validate its 20-condition JSON response."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to Vetology_Matrix1_First100_Encoded.xlsx",
    )
    parser.add_argument(
        "--case-id",
        default="1",
        help="CaseID from the first 100 records (default: 1).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Separate single-case test artifact (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    args = parse_args()

    from week_04.llm_client import load_model_config  # noqa: E402
    model_name = load_model_config().model
    print("\nMATRIX 1 — BLOCK 2: SINGLE-CASE OPENAI TEST")
    print("WARNING: This will make one billable OpenAI API request.")
    print(f"Input workbook: {args.input}")
    print(f"CaseID: {args.case_id}")
    print(f"Model: {model_name}")
    print("Prompt: V1.3")
    print("LLM input: original Findings, Conclusions, Recommendations only.")
    print("Ground-truth labels and AI-generated report fields will not be sent.")
    print(f"Test artifact: {args.output}")

    record = run_single_case_test(
        input_path=args.input,
        case_id=args.case_id,
        output_path=args.output,
        model_name=model_name,
    )

    print("\nBLOCK 2 SINGLE-CASE TEST PASSED")
    print(f"CaseID: {record['case_id']}")
    print(f"Model: {record['model']}")
    print(f"Validated condition count: {len(record['predictions'])}")
    print("Response labels: Positive / Negative only")
    print(f"Saved test artifact: {args.output}")
    print("\nValidated predictions:")
    print(json.dumps(record["predictions"], indent=2))


if __name__ == "__main__":
    main()
