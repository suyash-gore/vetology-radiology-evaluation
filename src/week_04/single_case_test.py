"""Run one canine-thorax case through LangChain/OpenAI (Block 3 test)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make src/ importable when this script is run from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from week_04.llm_client import classify_one_case  # noqa: E402
from week_04.week4_block1_data_loader import load_canine_thorax_dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send exactly one original canine-thorax report to OpenAI."
    )
    parser.add_argument("--input", required=True, help="Gold Standard Excel workbook")
    parser.add_argument("--case-id", type=str, default="1", help="CaseID to test")
    args = parser.parse_args()

    dataset = load_canine_thorax_dataset(args.input, limit=100)
    selected = next(
        (case for case in dataset.cases if str(case.case_id) == args.case_id),
        None,
    )
    if selected is None:
        raise SystemExit(f"CaseID {args.case_id!r} was not found in the loaded cases.")

    print(f"Sending CaseID {selected.case_id} to the configured OpenAI model...")
    raw_output = classify_one_case(selected.to_llm_payload())
    print("\n----- RAW MODEL RESPONSE (not yet validated) -----")
    print(raw_output)
    print("----- END RAW MODEL RESPONSE -----")
    print("\nNote: Block 4 will validate the response structure and labels.")


if __name__ == "__main__":
    main()
