"""Run the canine thorax 100-case pilot batch."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from week_04.week4_block1_data_loader import load_canine_thorax_dataset  # noqa: E402
from week_04.batch_processor import run_batch  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify the canine-thorax pilot cases with validated, resumable output."
    )
    parser.add_argument("--input", required=True, help="Authoritative Gold Standard workbook")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sheet", default="Sheet1")
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--output-dir", default="outputs/week_04/canine_thorax")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    dataset = load_canine_thorax_dataset(
        input_path=args.input,
        limit=args.limit,
        worksheet_name=args.sheet,
    )

    output_dir = Path(args.output_dir)
    results_path = output_dir / "predictions.jsonl"
    errors_path = output_dir / "errors.jsonl"

    print("\nIMPORTANT: This run makes billable OpenAI API requests for cases "
          "without valid saved predictions.")
    print(f"Cases selected: {len(dataset.cases)}")
    print(f"Maximum attempts per case: {args.max_attempts}")
    print(f"Predictions/checkpoint: {results_path}")
    print(f"Errors: {errors_path}")

    summary = run_batch(
        cases=dataset.cases,
        results_path=results_path,
        errors_path=errors_path,
        max_attempts=args.max_attempts,
    )

    print("\nBLOCK 5 BATCH RUN FINISHED")
    for key, value in summary.items():
        print(f"{key.capitalize()}: {value}")
    print("Gold Standard labels were not sent to the model or written to predictions.")


if __name__ == "__main__":
    main()
