"""Synthetic fixtures for the Feline Thorax and Canine Abdomen applications.

Contains NO real Vetology data and makes NO network request. ``SyntheticAppRepo``
builds a throwaway ``data/`` + ``outputs/week_07`` tree with:

* the real application with, by default, a TEMPORARY pinned stand-in prompt
  (not clinical; keeps the synthetic tests independent of the approved text),
  or the real approved prompt, or a pending prompt; its workflows rebased into
  the temporary tree;
* an isolation policy holding all six workflows (Canine Thorax rebased too)
  and both application roots, exactly like ``DEFAULT_POLICY``;
* Matrix 1 / Matrix 2 workbooks in the real column layout (CaseID, original
  report fields, ``Original Radiologist``, AI report fields, condition columns)
  plus trailing blank rows in Matrix 2, like the real Gold Standard drafts.
  Feline Thorax Matrix 1 writes ``Normal``/``Abnormal`` in its three
  normalised columns. Every cell that must never reach the model contains the
  ``LEAK`` marker.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from week_07 import applications, config
from week_07.applications import ApplicationSpec
from week_07.dataset_loader import (
    CASE_ID_COLUMN,
    CONCLUSIONS_COLUMN,
    FINDINGS_COLUMN,
    RECOMMENDATIONS_COLUMN,
)
from week_07.isolation import IsolationPolicy
from week_07.tests.fixtures import (
    AI_COLUMNS,
    LEAK_MARKER,
    ORIGINAL_RADIOLOGIST,
    case_from_payload,
    write_workbook,
)

STAND_IN_PROMPT = "SYNTHETIC TEST PROMPT - stand-in for an approved prompt; not clinical.\n"
TO_SOURCE = {"Negative": "Normal", "Positive": "Abnormal"}


def app_label(case_id: int, index: int, variant: int) -> str:
    return "Positive" if (case_id * 5 + index * 3 + variant) % 7 == 0 else "Negative"


def app_reference(app: ApplicationSpec, case_id: int, variant: int) -> dict[str, str]:
    return {condition: app_label(case_id, index, variant)
            for index, condition in enumerate(app.condition_keys)}


def headers(app: ApplicationSpec) -> tuple[str, ...]:
    return (CASE_ID_COLUMN, FINDINGS_COLUMN, CONCLUSIONS_COLUMN, RECOMMENDATIONS_COLUMN,
            ORIGINAL_RADIOLOGIST, *AI_COLUMNS, *app.condition_keys)


def app_row(app: ApplicationSpec, case_id: Any, variant: int,
            source_labels: bool) -> dict[str, Any]:
    row: dict[str, Any] = {
        CASE_ID_COLUMN: case_id,
        FINDINGS_COLUMN: f"Synthetic findings for report {case_id}.",
        CONCLUSIONS_COLUMN: f"Synthetic conclusions {case_id}",
        RECOMMENDATIONS_COLUMN: f"Synthetic recommendations {case_id}",
        ORIGINAL_RADIOLOGIST: f"{LEAK_MARKER}-radiologist-{case_id}",
    }
    for column in AI_COLUMNS:
        row[column] = f"{LEAK_MARKER}-ai-{column}-{case_id}"
    normalised = app.label_normalization("matrix1") if source_labels else {}
    for index, condition in enumerate(app.condition_keys):
        label = app_label(case_id, index, variant)
        row[condition] = TO_SOURCE[label] if condition in normalised else label
    return row


class AppEchoClassifier:
    """Fake model: answers with a case's reference labels (variant), with optional flips."""

    def __init__(self, app: ApplicationSpec, variant: int = 0,
                 flips: dict[int, Sequence[str]] | None = None) -> None:
        self.app = app
        self.variant = variant
        self.flips = flips or {}
        self.calls: list[dict[str, str]] = []

    def __call__(self, payload: dict[str, str]) -> str:
        self.calls.append(dict(payload))
        case_id = case_from_payload(payload)
        labels = app_reference(self.app, case_id, self.variant)
        for condition in self.flips.get(case_id, ()):
            labels[condition] = "Negative" if labels[condition] == "Positive" else "Positive"
        return json.dumps(labels)


def pinned_prompt(base: ApplicationSpec, directory: Path, text: str = STAND_IN_PROMPT):
    path = directory / base.prompt.filename
    path.write_text(text, encoding="utf-8")
    stripped = path.read_text(encoding="utf-8").strip()
    return replace(base.prompt, directory=directory,
                   file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   text_sha256=hashlib.sha256(stripped.encode("utf-8")).hexdigest(),
                   text_length=len(stripped))


class SyntheticAppRepo:
    """Temporary tree with one application ready to run offline."""

    def __init__(self, key: str, *, prompt: str = "stand-in") -> None:
        """``prompt``: "stand-in" (temporary pinned test prompt, default), "approved"
        (the real registered prompt, read-only) or "pending" (no pins: refused)."""
        if prompt not in ("stand-in", "approved", "pending"):
            raise ValueError(f"unknown prompt mode {prompt!r}")
        self.root = Path(tempfile.mkdtemp(prefix=f"week07_{key}_")).resolve()
        self.inputs = self.root / "data" / "week_07_inputs"
        self.week7 = self.root / "outputs" / "week_07"
        self.prompts = self.root / "prompts"
        self.prompts.mkdir(parents=True)
        base = applications.get_application(key)

        def rebase(path: Path | None) -> Path | None:
            return None if path is None else self.week7 / path.relative_to(config.OUTPUT_ROOT)

        def move(spec: config.WorkflowSpec) -> config.WorkflowSpec:
            week5 = spec.week5_output_dir
            return replace(spec, output_dir=rebase(spec.output_dir),
                           comparison_dir=rebase(spec.comparison_dir),
                           shared_predictions_dir=rebase(spec.shared_predictions_dir),
                           input_dir=self.inputs,
                           week5_output_dir=None if week5 is None
                           else self.root / "outputs" / "week_05" / week5.name)

        self.specs = {name: move(spec) for name, spec in config.ALL_WORKFLOWS.items()}
        workflows = MappingProxyType({name: self.specs[f"{key}/{name}"]
                                      for name in base.workflows})
        if prompt == "stand-in":
            spec = pinned_prompt(base, self.prompts)
        elif prompt == "approved":
            spec = base.prompt
        else:
            spec = replace(base.prompt, file_sha256=None, text_sha256=None, text_length=None)
        self.app = replace(base, prompt=spec, workflows=workflows)
        self.base = base
        self.policy = IsolationPolicy(
            output_root=self.week7,
            protected_roots=(self.root / "outputs" / "week_05", self.root / "data",
                             self.root / "src"),
            workflows=self.specs,
            application_roots={name: self.week7 / name
                               for name in config.APPLICATION_OUTPUT_ROOTS},
        )

    @property
    def m1(self) -> config.WorkflowSpec:
        return self.app.workflow("matrix1")

    @property
    def m2(self) -> config.WorkflowSpec:
        return self.app.workflow("matrix2")

    def write_inputs(self, m1_cases: Iterable[Any] = range(1, 101),
                     m2_cases: Iterable[Any] = range(1, 101), *, m2_blank_rows: int = 25,
                     edit_m1: Callable[[Any, dict], dict] | None = None,
                     edit_m2: Callable[[Any, dict], dict] | None = None) -> None:
        """Matrix 1 (variant 0, source labels) and Matrix 2 (variant 1) workbooks."""
        rows1 = [app_row(self.app, cid, 0, source_labels=True) for cid in m1_cases]
        rows2 = [app_row(self.app, cid, 1, source_labels=False) for cid in m2_cases]
        if edit_m1:
            rows1 = [edit_m1(row[CASE_ID_COLUMN], row) for row in rows1]
        if edit_m2:
            rows2 = [edit_m2(row[CASE_ID_COLUMN], row) for row in rows2]
        write_workbook(self.m1.default_input_path, headers(self.app), rows1)
        write_workbook(self.m2.default_input_path, headers(self.app),
                       rows2 + [None] * m2_blank_rows)

    def run_batch(self, classifier: Callable | None = None, **kwargs: Any) -> dict[str, int]:
        from week_07.batch_runner import run_application_batch
        from week_07.tests.gemini_fakes import RecordingSleep, StepClock

        kwargs.setdefault("settings", config.OpenAIModelConfig())
        kwargs.setdefault("clock", StepClock())
        kwargs.setdefault("sleep", RecordingSleep())
        return run_application_batch(
            self.app, "matrix1", self.m1.default_input_path,
            classifier=AppEchoClassifier(self.app) if classifier is None else classifier,
            isolation=self.policy, **kwargs)

    def all_output_text(self) -> str:
        return "\n".join(path.read_text(encoding="utf-8")
                         for path in sorted(self.week7.rglob("*"))
                         if path.is_file() and path.suffix in (".json", ".jsonl"))

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
