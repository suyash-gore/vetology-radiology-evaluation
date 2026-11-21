"""Run manifest (``run_manifest.json``): provenance for one workflow's Week 7 predictions.

The prediction and error JSONL files keep the exact Week 4/5 record schema
(D-028), so provenance is recorded here, beside them, instead:

* ``identity`` — everything that determines what the predictions mean: workflow,
  provider, model, temperature, response MIME type (no schema), prompt version
  and digests, input workbook name/digest/worksheet. It is fixed for the life of
  a predictions file: a resumed run with a different identity is refused, so one
  ``predictions.jsonl`` can never mix models, settings, prompts or inputs.
* ``runs`` — one entry per batch invocation: start/end time (UTC), status,
  requested limit and cases selected, timeout, the full retry policy, package
  versions and the summary counts.

The manifest never contains the API key, report text or reference labels.
Writes are atomic (temporary file + ``os.replace``) and pass the Week 7
isolation guard.
"""
from __future__ import annotations

import json
import os
import platform
import tempfile
from collections.abc import Mapping
from importlib import metadata
from pathlib import Path
from typing import Any, Final

from week_07.config import ConfigurationError, GeminiModelConfig, RetryPolicy, WorkflowSpec
from week_07.isolation import DEFAULT_POLICY, IsolationPolicy, OutputArea, sha256_file
from week_07.jsonl_store import Clock, timestamp, utc_now
from week_07.prompts.prompt_loader import (
    PROMPT_FILE_SHA256,
    PROMPT_TEXT_SHA256,
    PROMPT_VERSION,
)

SCHEMA_VERSION: Final[int] = 1
PROVIDER: Final[str] = "Google Gemini via langchain-google-genai ChatGoogleGenerativeAI"
PROMPT_NAME: Final[str] = "Canine Thorax Master Prompt"
PACKAGES: Final[tuple[str, ...]] = (
    "langchain-google-genai", "google-genai", "langchain-core", "httpx", "openpyxl",
)
STATUS_RUNNING: Final[str] = "running"
STATUS_COMPLETED: Final[str] = "completed"
STATUS_FATAL: Final[str] = "stopped: fatal provider error"
STATUS_CONFIGURATION: Final[str] = "stopped: configuration error"
STATUS_INTERRUPTED: Final[str] = "stopped: interrupted or failed"


class ManifestMismatch(ConfigurationError):
    """The existing predictions were produced under a different run identity."""


def package_versions(packages: tuple[str, ...] = PACKAGES) -> dict[str, str | None]:
    versions: dict[str, str | None] = {"python": platform.python_version()}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def run_identity(
    spec: WorkflowSpec,
    settings: GeminiModelConfig,
    input_path: Path,
    worksheet_name: str,
) -> dict[str, Any]:
    """The fields that must stay identical for every run writing one predictions file."""
    return {
        "workflow": spec.name,
        "workflow_title": spec.title,
        "reference_labels": spec.reference_description,
        "provider": PROVIDER,
        "model": settings.model,
        "temperature": settings.temperature,
        "response_mime_type": settings.response_mime_type,
        "response_schema": None,
        "prompt": {
            "name": PROMPT_NAME,
            "version": PROMPT_VERSION,
            "file_sha256": PROMPT_FILE_SHA256,
            "text_sha256": PROMPT_TEXT_SHA256,
        },
        "llm_input_fields": ["Findings (original radiologist report)",
                             "Conclusions (original radiologist report)",
                             "Recommendations (original radiologist report)"],
        "input_workbook": {
            "file_name": input_path.name,
            "sha256": sha256_file(input_path),
            "worksheet": worksheet_name,
        },
    }


def model_record(identity: Mapping[str, Any], workflow_label: str) -> str:
    """Human-readable model description for the evaluation workbooks."""
    return (f"{identity['model']} (Google Gemini, temperature {identity['temperature']}, "
            f"from {workflow_label} batch run manifest)")


def application_run_identity(
    app: Any,
    spec: WorkflowSpec,
    provider_label: str,
    settings: Any,
    input_path: Path,
    worksheet_name: str,
    prompt: Mapping[str, Any],
) -> dict[str, Any]:
    """Run identity of a shared-prediction application batch (Feline Thorax, Canine Abdomen).

    A superset of the Canine Thorax identity fields plus everything that makes the
    predictions application-specific: application, ordered condition keys, the
    human instruction, the reference-label normalisation applied to the source
    workbook, the prediction source workflow and the workflows that reuse the
    predictions, and the fixed transport retry setting. The Canine Thorax
    ``run_identity`` is unchanged (existing manifests keep matching).
    """
    return {
        "application": app.key,
        "application_name": app.display_name,
        "workflow": spec.name,
        "workflow_title": spec.title,
        "prediction_source_workflow": app.prediction_source_workflow,
        "predictions_reused_by_workflows": list(app.workflows),
        "reference_labels": "Not used by the batch run (evaluation only)",
        "provider": provider_label,
        "model": settings.model,
        "temperature": settings.temperature,
        "transport_max_retries": settings.transport_max_retries,
        "response_format": None,
        "prompt": dict(prompt),
        "human_instruction": app.human_instruction,
        "condition_keys": list(app.condition_keys),
        "source_label_normalization": {
            condition: dict(mapping)
            for condition, mapping in app.label_normalization(spec.name).items()
        },
        "llm_input_fields": ["Findings (original radiologist report)",
                             "Conclusions (original radiologist report)",
                             "Recommendations (original radiologist report)"],
        "input_workbook": {
            "file_name": input_path.name,
            "sha256": sha256_file(input_path),
            "worksheet": worksheet_name,
        },
    }


def application_model_record(identity: Mapping[str, Any], provider_short_label: str) -> str:
    """Model description for a shared-prediction application's evaluation workbooks."""
    return (f"{identity['model']} ({provider_short_label}, temperature "
            f"{identity['temperature']}, from {identity['application_name']} shared batch run "
            "manifest)")


def read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestMismatch(f"Run manifest {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION \
            or not isinstance(data.get("identity"), dict) or not isinstance(data.get("runs"), list):
        raise ManifestMismatch(f"Run manifest {path} does not have the expected structure.")
    return data


def _write_atomic(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".run_manifest.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _differences(stored: Mapping[str, Any], current: Mapping[str, Any]) -> list[str]:
    keys = sorted(set(stored) | set(current))
    return [f"{key}: recorded {stored.get(key)!r}, now {current.get(key)!r}"
            for key in keys if stored.get(key) != current.get(key)]


class RunManifest:
    """Start, then finish, one run entry in a workflow's manifest."""

    def __init__(self, path: Path, data: dict[str, Any], clock: Clock) -> None:
        self.path = path
        self.data = data
        self._clock = clock

    @property
    def identity(self) -> dict[str, Any]:
        return self.data["identity"]

    @property
    def current_run(self) -> dict[str, Any]:
        return self.data["runs"][-1]

    @classmethod
    def begin(
        cls,
        manifest_path: str | Path,
        predictions_path: Path,
        identity: dict[str, Any],
        run_details: Mapping[str, Any],
        *,
        spec: WorkflowSpec | None = None,
        isolation: IsolationPolicy = DEFAULT_POLICY,
        clock: Clock = utc_now,
        packages: tuple[str, ...] = PACKAGES,
    ) -> RunManifest:
        """Validate the run identity against existing outputs and record a new run.

        Refused (``ManifestMismatch``) when the recorded identity differs, or when
        predictions already exist without a manifest (unknown provenance).
        """
        path = isolation.assert_writable(manifest_path, spec, OutputArea.RUN)
        stored = read_manifest(path)
        if stored is None:
            if predictions_path.is_file() and predictions_path.stat().st_size > 0:
                raise ManifestMismatch(
                    f"{predictions_path} already exists but has no run manifest, so its "
                    "provenance is unknown. Use a new output directory."
                )
            data: dict[str, Any] = {"schema_version": SCHEMA_VERSION,
                                    "identity": identity, "runs": []}
        else:
            differences = _differences(stored["identity"], identity)
            if differences:
                raise ManifestMismatch(
                    "The existing predictions in this output directory were produced with a "
                    "different run identity; resuming would mix results. Use a new output "
                    "directory. Differences: " + "; ".join(differences)
                )
            data = stored
        data["runs"].append({
            "started_at_utc": timestamp(clock),
            "finished_at_utc": None,
            "status": STATUS_RUNNING,
            **dict(run_details),
            "package_versions": package_versions(packages),
            "summary": None,
        })
        manifest = cls(path, data, clock)
        _write_atomic(path, data)
        return manifest

    def finish(self, status: str, summary: Mapping[str, int] | None,
               error: str | None = None) -> None:
        run = self.current_run
        run["finished_at_utc"] = timestamp(self._clock)
        run["status"] = status
        run["summary"] = dict(summary) if summary is not None else None
        if error is not None:
            run["error"] = error
        _write_atomic(self.path, self.data)


def run_details(limit: int | None, cases_selected: int, settings: GeminiModelConfig,
                retry_policy: RetryPolicy) -> dict[str, Any]:
    """Per-run (non-identity) details recorded in each run entry."""
    return {
        "requested_limit": limit,
        "cases_selected": cases_selected,
        "timeout_seconds": settings.timeout_seconds,
        "retry_policy": retry_policy.as_manifest(),
    }
