"""Matrix 1 — Block 3: fresh, resumable 100-case prediction batch.

Uses the existing Week 4 batch processor, OpenAI client, V1.3 prompt, and
strict response validator. Matrix 1 outputs are stored in their own directory.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from week_04.matrix_1.matrix1_data_loader import load_matrix1_dataset  # noqa: E402


def run_batch(*args, **kwargs):
    """Load the shared batch processor only when a batch is actually run."""
    from week_04.batch_processor import run_batch as shared_run_batch
    return shared_run_batch(*args, **kwargs)

DEFAULT_INPUT = "Vetology_Matrix1_First100_Encoded.xlsx"
DEFAULT_OUTPUT_DIR = Path("outputs/week_04/matrix_1")
CASE_LIMIT = 100


def run_matrix1_batch(
    input_path: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    max_attempts: int = 2,
) -> dict[str, int]:
    """Load Matrix 1 cases and run the existing validated batch processor."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    dataset = load_matrix1_dataset(
        input_path=input_path,
        limit=CASE_LIMIT,
    )
    if len(dataset.cases) != CASE_LIMIT:
        raise ValueError(
            f"Matrix 1 batch requires exactly {CASE_LIMIT} cases; "
            f"loaded {len(dataset.cases)}."
        )

    destination = Path(output_dir)
    results_path = destination / "predictions.jsonl"
    errors_path = destination / "errors.jsonl"
    destination.mkdir(parents=True, exist_ok=True)

    logging.info("Matrix 1 input: %s", Path(input_path).resolve())
    logging.info("Cases selected: %d", len(dataset.cases))
    logging.info("Conditions per case: 20")
    logging.info("Prompt version: V1.3")
    logging.info("Prediction checkpoint: %s", results_path)
    logging.info("Error log: %s", errors_path)
    logging.info(
        "Existing valid checkpoints will be skipped; failed cases can be retried."
    )

    # run_batch sends only case.to_llm_payload() to classify_one_case.
    # Ground-truth labels remain isolated in dataset.ground_truth and are
    # deliberately not passed to the batch processor.
    return run_batch(
        cases=dataset.cases,
        results_path=results_path,
        errors_path=errors_path,
        max_attempts=max_attempts,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the fresh Matrix 1 100-case OpenAI batch using the V1.3 "
            "prompt, response validation, checkpointing, and retry handling."
        )
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=f"Processed Matrix 1 ground-truth workbook (default: {DEFAULT_INPUT}).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Matrix 1 output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=2,
        help="Application-level attempts per case (default: 2).",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    args = parse_args()

    if args.max_attempts < 1:
        raise SystemExit("--max-attempts must be at least 1.")

    print("\nMATRIX 1 — BLOCK 3: 100-CASE OPENAI BATCH")
    print("WARNING: This run can make billable OpenAI API requests.")
    print(f"Input workbook: {args.input}")
    print(f"Cases: {CASE_LIMIT}")
    print("Conditions per case: 20")
    print("Model and prompt: repository .env configuration + V1.3")
    print(f"Maximum application attempts per case: {args.max_attempts}")
    print(f"Output directory: {args.output_dir}")
    print("Ground-truth labels and AI-generated reports will not be sent.")

    summary = run_matrix1_batch(
        input_path=args.input,
        output_dir=args.output_dir,
        max_attempts=args.max_attempts,
    )

    print("\nBLOCK 3 BATCH RUN FINISHED")
    for key, value in summary.items():
        print(f"{key.capitalize()}: {value}")
    print("Prediction and error files are separate from Matrix 2 outputs.")
    print("Ground-truth labels were not passed to the LLM or batch processor.")


if __name__ == "__main__":
    main()
