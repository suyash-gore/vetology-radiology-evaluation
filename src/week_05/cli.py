"""Command-line interface for the Week 5 application.

Run from the repository root:

    PYTHONPATH=src python -m week_05 config --workflow matrix1

Phase 1 provides only the ``config`` command, which reports the resolved
configuration without making any API request and without displaying the key.
Further commands (data validation, single case, batch, evaluation) are added in
later phases.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from week_05 import config
from week_05.conditions import CONDITION_COUNT


def _add_workflow_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workflow",
        required=True,
        choices=sorted(config.WORKFLOWS),
        help="Evaluation workflow: matrix1 (Original Vetology) or matrix2 (Gold Standard).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m week_05",
        description="Vetology Week 5 canine thorax classification and evaluation.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    show = subcommands.add_parser(
        "config",
        help="Show the resolved model and workflow configuration (no API request).",
    )
    _add_workflow_argument(show)
    return parser


def _command_config(args: argparse.Namespace) -> int:
    workflow = config.get_workflow(args.workflow)
    model = config.load_model_config()
    key_status = "set" if config.api_key_is_configured() else "NOT SET"

    lines = [
        f"Workflow: {workflow.name} ({workflow.title})",
        f"Reference labels: {workflow.reference_description}",
        f"Default input: {workflow.default_input_path}",
        f"Worksheet: {workflow.worksheet_name}",
        f"Case limit: {workflow.case_limit}",
        f"Conditions: {CONDITION_COUNT}",
        f"Output directory: {workflow.output_dir}",
        f"Predictions: {workflow.predictions_path.name}",
        f"Errors: {workflow.errors_path.name}",
        f"Evaluation workbook: {workflow.evaluation_workbook_filename}",
        f"Model: {model.model}",
        f"Temperature: {model.temperature}",
        f"Timeout (seconds): {model.timeout_seconds}",
        f"LangChain max retries: {model.max_retries}",
        f"Application attempts per case (default): {config.DEFAULT_MAX_ATTEMPTS}",
        f"{config.API_KEY_VAR}: {key_status}",
        "No API request was made.",
    ]
    print("\n".join(lines))
    return 0


COMMANDS = {"config": _command_config}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except config.ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 2
