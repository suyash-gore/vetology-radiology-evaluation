"""Command-line interface for the Week 5 application.

Run from the repository root (``src`` on ``PYTHONPATH``)::

    python -m week_05 config         --workflow matrix1
    python -m week_05 validate-data  --workflow matrix1 [--input PATH]
    python -m week_05 batch          --workflow matrix2 [--input PATH] [--output-dir DIR]
    python -m week_05 evaluate       --workflow matrix1 [--input PATH] [--predictions PATH]
    python -m week_05 compare-references --workflow matrix1 [--input PATH]

Only ``batch`` contacts OpenAI: it makes billable requests for every case
without a valid saved prediction. All other commands are offline.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from week_05 import config
from week_05.conditions import CONDITION_COUNT
from week_05.dataset_loader import DatasetError
from week_05.evaluation.reconcile import EvaluationInputError
from week_05.evaluation.reference_loader import ReferenceLoadError, ReferenceLoadingPending
from week_05.prompts.prompt_loader import PROMPT_VERSION


def _add_workflow_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workflow",
        required=True,
        choices=sorted(config.WORKFLOWS),
        help="Evaluation workflow: matrix1 (Original Vetology) or matrix2 (Gold Standard).",
    )


def _add_input_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", help="Input workbook (default: the workflow's default path).")
    parser.add_argument("--sheet", help="Worksheet name (default: Sheet1).")
    parser.add_argument("--limit", type=int,
                        help="matrix2 only: number of cases (default: 100). "
                             "matrix1 always uses exactly 100 cases.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m week_05",
        description="Vetology Week 5 canine thorax classification and evaluation.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    show = subcommands.add_parser(
        "config", help="Show the resolved model and workflow configuration (no API request)."
    )
    _add_workflow_argument(show)

    validate = subcommands.add_parser(
        "validate-data", help="Load and validate a workflow's input workbook (no API request)."
    )
    _add_workflow_argument(validate)
    _add_input_arguments(validate)

    batch = subcommands.add_parser(
        "batch", help="Classify a workflow's cases with OpenAI (BILLABLE API requests)."
    )
    _add_workflow_argument(batch)
    _add_input_arguments(batch)
    batch.add_argument("--output-dir", help="Output directory (default: the workflow's own).")
    batch.add_argument("--max-attempts", type=int, default=config.DEFAULT_MAX_ATTEMPTS,
                       help="Application-level attempts per case (default: 2).")

    evaluate = subcommands.add_parser(
        "evaluate", help="Compare saved predictions with reference labels (no API request)."
    )
    _add_workflow_argument(evaluate)
    evaluate.add_argument("--input",
                          help="Reference workbook (default: the workflow's input). The first "
                               "worksheet is used, as in Week 4.")
    evaluate.add_argument("--predictions",
                          help="Predictions JSONL (default: the workflow's predictions.jsonl).")
    evaluate.add_argument("--output",
                          help="Evaluation workbook path (default: the workflow's workbook).")

    compare = subcommands.add_parser(
        "compare-references",
        help="Report differences between the batch loader and the evaluation reference "
             "loader on one workbook (no API request).",
    )
    _add_workflow_argument(compare)
    compare.add_argument("--input", help="Workbook (default: the workflow's input).")
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


def _workflow_with_limit_check(args: argparse.Namespace) -> config.WorkflowSpec:
    """Resolve the workflow; refuse ``--limit`` where it is not configurable (matrix1)."""
    workflow = config.get_workflow(args.workflow)
    if args.limit is not None and not workflow.configurable_limit:
        raise ValueError(
            f"--limit is not available for {workflow.name}; it always processes exactly "
            f"{workflow.case_limit} cases."
        )
    return workflow


def _command_validate_data(args: argparse.Namespace) -> int:
    from week_05.dataset_loader import load_dataset

    workflow = _workflow_with_limit_check(args)
    dataset = load_dataset(workflow, args.input, limit=args.limit, worksheet_name=args.sheet)
    print(f"Workflow: {workflow.name} ({workflow.title})")
    print(f"Workbook: {dataset.source_path}")
    print(f"Worksheet: {dataset.worksheet_name}")
    print(f"Cases loaded: {len(dataset.cases)}")
    print(f"First / last CaseID: {dataset.case_ids[0]} / {dataset.case_ids[-1]}")
    print(f"Reference labels validated: {len(dataset.reference_labels) * CONDITION_COUNT} "
          f"({dataset.reference_description})")
    print("LLM input fields: Findings, Conclusions, Recommendations (original radiologist report)")
    print("No API request was made.")
    return 0


def _command_batch(args: argparse.Namespace) -> int:
    from week_05.batch_runner import resolve_outputs, run_workflow_batch

    workflow = _workflow_with_limit_check(args)
    outputs = resolve_outputs(workflow, args.output_dir)
    print(f"\n{workflow.title}")
    print("IMPORTANT: This run makes billable OpenAI API requests for cases "
          "without valid saved predictions.")
    print(f"Prompt: Canine Thorax Master Prompt {PROMPT_VERSION}")
    print(f"Maximum application attempts per case: {args.max_attempts}")
    print(f"Predictions/checkpoint: {outputs.predictions_path}")
    print(f"Errors: {outputs.errors_path}")

    summary = run_workflow_batch(
        workflow,
        args.input,
        output_dir=outputs.output_dir,
        max_attempts=args.max_attempts,
        limit=args.limit,
        worksheet_name=args.sheet,
    )
    print("\nBATCH RUN FINISHED")
    for key, value in summary.items():
        print(f"{key.capitalize()}: {value}")
    print("Reference labels were not sent to the model or written to predictions.")
    return 0


def _percent(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.2%}"


def _command_evaluate(args: argparse.Namespace) -> int:
    from week_05.evaluation.evaluate import (
        WorkbookLayoutPending,
        evaluate_workflow,
        write_evaluation_workbook,
    )

    workflow = config.get_workflow(args.workflow)
    result = evaluate_workflow(workflow, args.input, args.predictions)
    micro = result.micro
    for skipped in result.labels.skipped_lines:
        print(f"WARNING: skipped prediction {skipped.describe()}")
    print(f"Workflow: {workflow.name} ({workflow.title})")
    print(f"Cases: {len(result.labels.case_ids)} | Conditions: {CONDITION_COUNT} | "
          f"Paired labels: {micro.total}")
    print(f"TP={micro.tp} FN={micro.fn} TN={micro.tn} FP={micro.fp}")
    print(f"Micro accuracy={_percent(micro.accuracy)} | sensitivity={_percent(micro.sensitivity)}"
          f" | specificity={_percent(micro.specificity)} | precision={_percent(micro.precision)}"
          f" | F1={_percent(micro.f1)}")
    try:
        path = write_evaluation_workbook(workflow, result, args.output)
    except WorkbookLayoutPending as exc:
        print(f"Evaluation workbook NOT generated: {exc}")
    else:
        print(f"Evaluation workbook created: {path}")
    print("No API request was made.")
    return 0


def _command_compare_references(args: argparse.Namespace) -> int:
    from week_05.evaluation.reference_loader import compare_reference_loaders

    workflow = config.get_workflow(args.workflow)
    path = workflow.default_input_path if args.input is None else args.input
    differences = compare_reference_loaders(workflow, path)
    print(f"Workflow: {workflow.name} ({workflow.title})")
    print(f"Workbook: {path}")
    if not differences:
        print("No differences: the batch loader and the evaluation loader select the same "
              "cases, in the same order, with the same labels.")
    else:
        print(f"{len(differences)} difference(s) between the batch loader and the "
              "evaluation loader:")
        for difference in differences:
            print(f"  - {difference}")
    print("No API request was made.")
    return 0 if not differences else 1


COMMANDS = {
    "config": _command_config,
    "validate-data": _command_validate_data,
    "batch": _command_batch,
    "evaluate": _command_evaluate,
    "compare-references": _command_compare_references,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except config.ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 2
    except (DatasetError, FileNotFoundError, EvaluationInputError, ReferenceLoadError) as exc:
        print(f"Input error: {exc}")
        return 3
    except ValueError as exc:
        print(f"Invalid argument: {exc}")
        return 4
    except ReferenceLoadingPending as exc:
        print(f"Not available yet: {exc}")
        return 5
