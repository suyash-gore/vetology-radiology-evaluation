"""Per-workflow comparison of Week 5 OpenAI and Week 7 Gemini predictions (offline).

``compare_workflow(spec, ...)``:

1. Resolves the reference workbook (the workflow's own input) and both
   prediction sources (defaults: ``outputs/week_05/<matrix>/predictions.jsonl``
   and ``outputs/week_07/<matrix>/predictions.jsonl``). The two sources must be
   different files with different content.
2. Under one ``ReadOnlyGuard`` covering EVERY file read (reference workbook,
   both prediction files, error logs, Gemini run manifest), loads both sources
   with their provenance checks (``sources``), refuses any UNRESOLVED failure
   record, loads the reference labels with the workflow's own evaluation
   reference loader, and reconciles each prediction file with the strict
   Week 5 rules (exact CaseID-set match; Matrix 1 exactly 100 cases).
3. Computes, as separate analyses: each model's metrics against the reference
   (Week 5 metric engine), model-vs-model agreement (reference not used),
   reference-based correctness, and every disagreement.

Matrix 1 and Matrix 2 are never combined: one call handles one workflow, and
every source is checked to belong to it. No model client is imported and no
API request is made.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from week_07.comparison import agreement as calc
from week_07.comparison.sources import (
    GEMINI,
    OPENAI,
    ComparisonInputError,
    FileProvenance,
    PredictionSource,
    load_prediction_source,
    source_files,
)
from week_07.config import WorkflowSpec
from week_07.evaluation.evaluate import EXPECTED_CASES, EvaluationResult, compute_evaluation
from week_07.evaluation.reconcile import reconcile
from week_07.evaluation.reference_loader import reference_loader_for
from week_07.isolation import DEFAULT_POLICY, IsolationPolicy, ReadOnlyGuard


@dataclass(frozen=True)
class ComparisonResult:
    workflow: str
    title: str
    reference_description: str
    reference: FileProvenance
    reference_worksheet: str
    case_ids: tuple[Any, ...]
    openai: PredictionSource
    gemini: PredictionSource
    openai_evaluation: EvaluationResult
    gemini_evaluation: EvaluationResult
    agreement: Mapping[str, calc.ModelAgreement]
    agreement_total: calc.ModelAgreement
    correctness: Mapping[str, calc.ReferenceCorrectness]
    correctness_total: calc.ReferenceCorrectness
    disagreements: Sequence[calc.Disagreement]
    source_digests: Mapping[Path, str]

    def __repr__(self) -> str:
        return (f"ComparisonResult(workflow={self.workflow!r}, cases={len(self.case_ids)}, "
                f"disagreements={len(self.disagreements)})")


def _resolve(path: str | Path | None, default: Path) -> Path:
    return Path(default if path is None else path).expanduser().resolve()


def _refuse_unresolved(source: PredictionSource) -> None:
    errors = source.errors
    if errors.unresolved:
        ids = sorted(errors.unresolved)
        raise ComparisonInputError(
            f"{source.label}: {len(ids)} case(s) have failure records without a later success "
            f"(final failures) in {errors.provenance.path.name}: {ids[:20]}. The comparison "
            "requires a valid prediction for every case."
        )


def compare_workflow(
    spec: WorkflowSpec,
    *,
    openai_path: str | Path | None = None,
    gemini_path: str | Path | None = None,
    reference_path: str | Path | None = None,
    openai_errors_path: str | Path | None = None,
    gemini_errors_path: str | Path | None = None,
    isolation: IsolationPolicy = DEFAULT_POLICY,
) -> ComparisonResult:
    """Compare one workflow's Week 5 OpenAI and Week 7 Gemini predictions."""
    reference_file = _resolve(reference_path, spec.default_input_path)
    openai_file = _resolve(openai_path, spec.week5_predictions_path)
    gemini_file = _resolve(gemini_path, spec.predictions_path)
    if not reference_file.is_file():
        raise FileNotFoundError(f"Reference workbook not found: {reference_file}")
    for label, path in (("Week 5 OpenAI", openai_file), ("Week 7 Gemini", gemini_file)):
        if not path.is_file():
            raise FileNotFoundError(f"{label} predictions file not found: {path}")
    if openai_file == gemini_file:
        raise ComparisonInputError(
            f"The OpenAI and Gemini sources are the same file: {openai_file}")

    files = [reference_file, *source_files(openai_file, openai_errors_path),
             *source_files(gemini_file, gemini_errors_path)]
    with ReadOnlyGuard(files) as guard:
        openai = load_prediction_source(OPENAI, spec, openai_file, reference_file,
                                        openai_errors_path, isolation=isolation)
        gemini = load_prediction_source(GEMINI, spec, gemini_file, reference_file,
                                        gemini_errors_path, isolation=isolation)
        if openai.provenance.sha256 == gemini.provenance.sha256:
            raise ComparisonInputError(
                "The OpenAI and Gemini prediction files have identical content "
                f"(sha256 {openai.provenance.sha256}); one appears to be a copy of the other."
            )
        _refuse_unresolved(openai)
        _refuse_unresolved(gemini)

        reference = reference_loader_for(spec)(reference_file)
        expected = EXPECTED_CASES.get(spec.name)
        openai_labels = reconcile(spec, reference, openai_file, expected_cases=expected)
        gemini_labels = reconcile(spec, reference, gemini_file, expected_cases=expected)

    case_ids = reference.case_ids
    ref, o_pred, g_pred = reference.labels, openai_labels.predictions, gemini_labels.predictions
    agreement = calc.agreement_by_condition(o_pred, g_pred, case_ids)
    correctness = calc.correctness_by_condition(ref, o_pred, g_pred, case_ids)
    return ComparisonResult(
        workflow=spec.name,
        title=spec.title,
        reference_description=spec.reference_description,
        reference=FileProvenance.of(reference_file),
        reference_worksheet=reference.worksheet_name,
        case_ids=case_ids,
        openai=openai,
        gemini=gemini,
        openai_evaluation=compute_evaluation(openai_labels, openai.model_record),
        gemini_evaluation=compute_evaluation(gemini_labels, gemini.model_record),
        agreement=agreement,
        agreement_total=calc.total_agreement(agreement),
        correctness=correctness,
        correctness_total=calc.total_correctness(correctness),
        disagreements=tuple(calc.disagreements(ref, o_pred, g_pred, case_ids)),
        source_digests=dict(guard.digests),
    )
