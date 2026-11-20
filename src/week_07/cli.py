"""Command-line interface for the Week 7 Gemini application.

Run from the repository root (``src`` on ``PYTHONPATH``)::

    python -m week_07 config             --workflow matrix1
    python -m week_07 validate-data      --workflow matrix1 [--input PATH]
    python -m week_07 batch              --workflow matrix2 [--input PATH] [--limit N]
    python -m week_07 evaluate           --workflow matrix1 [--input PATH] [--predictions PATH]
    python -m week_07 compare-references --workflow matrix1 [--input PATH]
    python -m week_07 compare            --workflow matrix1 [--openai PATH] [--gemini PATH]

Only ``batch`` contacts Google Gemini: it makes billable requests for every case
without a valid saved prediction. All other commands are offline.

Exit codes: 0 success; 1 compare-references found differences; 2 configuration
or isolation error; 3 input error; 4 invalid argument; 5 not available;
6 fatal provider error (HTTP 400/401/403/404); 7 a read-only source changed.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from week_07 import config
from week_07.conditions import CONDITION_COUNT
from week_07.dataset_loader import DatasetError
from week_07.error_policy import FatalProviderError
from week_07.evaluation.reconcile import EvaluationInputError
from week_07.evaluation.reference_loader import ReferenceLoadError, ReferenceLoadingPending
from week_07.isolation import ProtectedFileModified
from week_07.prompts.prompt_loader import PROMPT_VERSION


def _add_workflow_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workflow",
        required=True,
        choices=sorted(config.WORKFLOWS),
        help="Evaluation workflow: matrix1 (Vetology reference labels) or matrix2 "
             "(Gold Standard reference labels).",
    )


def _add_input_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", help="Input workbook (default: the workflow's default path).")
    parser.add_argument("--sheet", help="Worksheet name (default: Sheet1).")
    parser.add_argument("--limit", type=int,
                        help="matrix2 only: number of cases (default: 100). "
                             "matrix1 always uses exactly 100 cases.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m week_07",
        description="Vetology Week 7 canine thorax classification with Google Gemini.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    show = subcommands.add_parser(
        "config", help="Show the resolved model, retry and workflow configuration (offline)."
    )
    _add_workflow_argument(show)

    validate = subcommands.add_parser(
        "validate-data", help="Load and validate a workflow's input workbook (offline)."
    )
    _add_workflow_argument(validate)
    _add_input_arguments(validate)

    batch = subcommands.add_parser(
        "batch", help="Classify a workflow's cases with Gemini (BILLABLE API requests)."
    )
    _add_workflow_argument(batch)
    _add_input_arguments(batch)
    batch.add_argument("--output-dir",
                       help="Output directory inside outputs/week_07 (default: the workflow's).")
    batch.add_argument("--max-attempts", type=int, default=config.DEFAULT_MAX_ATTEMPTS,
                       help="Application-level attempts per case (default: 2).")

    evaluate = subcommands.add_parser(
        "evaluate", help="Compare saved predictions with reference labels (offline)."
    )
    _add_workflow_argument(evaluate)
    evaluate.add_argument("--input",
                          help="Reference workbook (default: the workflow's input).")
    evaluate.add_argument("--predictions",
                          help="Predictions JSONL (default: the workflow's Week 7 "
                               "predictions.jsonl). Read-only.")
    evaluate.add_argument("--output",
                          help="Evaluation workbook path inside outputs/week_07 "
                               "(default: the workflow's workbook).")
    evaluate.add_argument("--model-record",
                          help="Model description for the workbook when the predictions have "
                               "no Week 7 run manifest (e.g. a Week 5 replay).")

    models = subcommands.add_parser(
        "compare",
        help="Compare saved Week 5 OpenAI and Week 7 Gemini predictions for one workflow "
             "and write the six-sheet comparison workbook (offline).",
    )
    _add_workflow_argument(models)
    models.add_argument("--openai", help="Week 5 OpenAI predictions JSONL (default: "
                                         "outputs/week_05/<matrix>/predictions.jsonl). Read-only.")
    models.add_argument("--gemini", help="Week 7 Gemini predictions JSONL (default: "
                                         "outputs/week_07/<matrix>/predictions.jsonl). Read-only.")
    models.add_argument("--reference", help="Reference workbook (default: the workflow's input).")
    models.add_argument("--openai-errors", help="Week 5 errors.jsonl (default: the one beside "
                                                "the OpenAI predictions, if present).")
    models.add_argument("--gemini-errors", help="Week 7 errors.jsonl (default: the one beside "
                                                "the Gemini predictions, if present).")
    models.add_argument("--output", help="Comparison workbook path inside "
                                         "outputs/week_07/comparison/<matrix> (default: the "
                                         "workflow's comparison workbook).")

    compare = subcommands.add_parser(
        "compare-references",
        help="Report differences between the batch loader and the evaluation reference "
             "loader on one workbook (offline).",
    )
    _add_workflow_argument(compare)
    compare.add_argument("--input", help="Workbook (default: the workflow's input).")
    return parser


def _command_config(args: argparse.Namespace) -> int:
    workflow = config.get_workflow(args.workflow)
    model = config.load_model_config(None, config.ENV_FILE)
    key_status = "set" if config.api_key_is_configured(None, config.ENV_FILE) else "NOT SET"
    policy = config.DEFAULT_RETRY_POLICY

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
        f"Run manifest: {workflow.manifest_path.name}",
        f"Evaluation workbook: {workflow.evaluation_workbook_filename}",
        "Provider: Google Gemini (langchain-google-genai)",
        f"Model: {model.model}",
        f"Temperature: {model.temperature}",
        f"Timeout (seconds): {model.timeout_seconds}",
        f"Response MIME type: {model.response_mime_type} (no response schema)",
        f"Prompt: Canine Thorax Master Prompt {PROMPT_VERSION}",
        f"SDK transport attempts per application attempt: {config.TRANSPORT_ATTEMPTS}",
        f"Application attempts per case (default): {policy.max_attempts}",
        f"Transient HTTP codes (backoff): {sorted(policy.transient_status_codes)} "
        "+ network timeouts/errors",
        f"Fatal HTTP codes (not retried): {sorted(policy.fatal_status_codes)}",
        f"Backoff: {policy.backoff_base_seconds} s x {policy.backoff_factor}^n, "
        f"max {policy.backoff_max_seconds} s",
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
    from week_07.dataset_loader import load_dataset

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
    from week_07.batch_runner import resolve_outputs, run_workflow_batch

    workflow = _workflow_with_limit_check(args)
    policy = config.RetryPolicy(max_attempts=args.max_attempts)
    outputs = resolve_outputs(workflow, args.output_dir)
    print(f"\n{workflow.title}")
    print("IMPORTANT: This run makes billable Google Gemini API requests for cases "
          "without valid saved predictions.")
    print(f"Prompt: Canine Thorax Master Prompt {PROMPT_VERSION}")
    print(f"Maximum application attempts per case: {policy.max_attempts}")
    print(f"Predictions/checkpoint: {outputs.predictions_path}")
    print(f"Errors: {outputs.errors_path}")
    print(f"Run manifest: {outputs.manifest_path}")

    summary = run_workflow_batch(
        workflow,
        args.input,
        output_dir=outputs.output_dir,
        retry_policy=policy,
        limit=args.limit,
        worksheet_name=args.sheet,
    )
    print("\nBATCH RUN FINISHED")
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').capitalize()}: {value}")
    print("Reference labels were not sent to the model or written to predictions.")
    return 0


def _percent(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.2%}"


def _command_evaluate(args: argparse.Namespace) -> int:
    from week_07.evaluation.evaluate import evaluate_workflow, write_evaluation_workbook

    workflow = config.get_workflow(args.workflow)
    result = evaluate_workflow(workflow, args.input, args.predictions,
                               model_record=args.model_record)
    micro = result.micro
    for skipped in result.labels.skipped_lines:
        print(f"WARNING: skipped prediction {skipped.describe()}")
    print(f"Workflow: {workflow.name} ({workflow.title})")
    print(f"Model: {result.model_record}")
    print(f"Cases: {len(result.labels.case_ids)} | Conditions: {CONDITION_COUNT} | "
          f"Paired labels: {micro.total}")
    print(f"TP={micro.tp} FN={micro.fn} TN={micro.tn} FP={micro.fp}")
    print(f"Micro accuracy={_percent(micro.accuracy)} | sensitivity={_percent(micro.sensitivity)}"
          f" | specificity={_percent(micro.specificity)} | precision={_percent(micro.precision)}"
          f" | F1={_percent(micro.f1)}")
    for path, digest in result.source_digests.items():
        print(f"Read-only source unchanged: {path.name} (sha256 {digest})")
    path = write_evaluation_workbook(workflow, result, args.output)
    print(f"Evaluation workbook created: {path}")
    print("No API request was made.")
    return 0


def _command_compare_references(args: argparse.Namespace) -> int:
    from week_07.evaluation.reference_loader import compare_reference_loaders

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


def _command_compare(args: argparse.Namespace) -> int:
    from week_07.comparison.compare import compare_workflow
    from week_07.comparison.comparison_workbook import summary_lines, write_comparison_workbook

    workflow = config.get_workflow(args.workflow)
    result = compare_workflow(
        workflow,
        openai_path=args.openai,
        gemini_path=args.gemini,
        reference_path=args.reference,
        openai_errors_path=args.openai_errors,
        gemini_errors_path=args.gemini_errors,
    )
    print("\n".join(summary_lines(result)))
    for path, digest in result.source_digests.items():
        print(f"Read-only source unchanged: {path.name} (sha256 {digest})")
    path = write_comparison_workbook(workflow, result, args.output)
    print(f"Comparison workbook created: {path}")
    print("No API request was made.")
    return 0


COMMANDS = {
    "config": _command_config,
    "validate-data": _command_validate_data,
    "batch": _command_batch,
    "evaluate": _command_evaluate,
    "compare-references": _command_compare_references,
    "compare": _command_compare,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except FatalProviderError as exc:
        print(f"Fatal provider error (not retried): {exc}")
        return 6
    except ProtectedFileModified as exc:
        print(f"Read-only source changed: {exc}")
        return 7
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
