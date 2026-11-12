"""Model and workflow configuration for the Week 5 application.

Model settings mirror the Week 4 client exactly (same environment variables,
same defaults, same ``.env`` precedence). The API key itself is never read into
a Python object here: LangChain's ``ChatOpenAI`` reads ``OPENAI_API_KEY`` from
the process environment, as in Week 4. This module only checks that it is set.

Approved improvement (P6): configuration is validated up front so that missing
credentials or malformed settings fail before any classification is attempted.
"""
from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Repository paths (anchored to the repository root, not the working directory)
# ---------------------------------------------------------------------------

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
ENV_FILE: Final[Path] = REPO_ROOT / ".env"
DEFAULT_INPUT_DIR: Final[Path] = REPO_ROOT / "data" / "week_04_inputs"
OUTPUT_ROOT: Final[Path] = REPO_ROOT / "outputs" / "week_05"

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

API_KEY_VAR: Final[str] = "OPENAI_API_KEY"
MODEL_VAR: Final[str] = "OPENAI_MODEL"
TEMPERATURE_VAR: Final[str] = "OPENAI_TEMPERATURE"
TIMEOUT_VAR: Final[str] = "OPENAI_TIMEOUT_SECONDS"
MAX_RETRIES_VAR: Final[str] = "OPENAI_MAX_RETRIES"

DEFAULT_MODEL: Final[str] = "gpt-4.1-mini"
DEFAULT_TEMPERATURE: Final[str] = "0"
DEFAULT_TIMEOUT_SECONDS: Final[str] = "90"
DEFAULT_MAX_RETRIES: Final[str] = "2"

# Application-level attempts per case (Week 4 default). Each attempt is one
# classifier call plus validation; LangChain transport retries are separate.
DEFAULT_MAX_ATTEMPTS: Final[int] = 2


class ConfigurationError(RuntimeError):
    """Raised when credentials or settings are missing or invalid."""


@dataclass(frozen=True)
class ModelConfig:
    """OpenAI model settings. Deliberately contains no credential."""

    model: str = DEFAULT_MODEL
    temperature: float = 0.0
    timeout_seconds: float = 90.0
    max_retries: int = 2


def _environment(environ: Mapping[str, str] | None, env_file: Path | None) -> Mapping[str, str]:
    """Return the variable source, loading ``.env`` only for the real environment.

    As in Week 4, ``load_dotenv`` does not override variables that are already
    set in the process environment.
    """
    if environ is not None:
        return environ
    if env_file is not None:
        load_dotenv(env_file, override=False)
    return os.environ


def _parse_float(raw: str, name: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a number; received {raw!r}.") from exc
    if not math.isfinite(value):
        raise ConfigurationError(f"{name} must be a finite number; received {raw!r}.")
    return value


def _parse_int(raw: str, name: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer; received {raw!r}.") from exc


def load_model_config(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> ModelConfig:
    """Read and validate model settings (Week 4 variables and defaults).

    ``environ`` may be supplied (e.g. in tests) to bypass ``os.environ`` and the
    ``.env`` file entirely.
    """
    env = _environment(environ, env_file)

    model = env.get(MODEL_VAR, DEFAULT_MODEL).strip()
    if not model:
        raise ConfigurationError(f"{MODEL_VAR} is empty. Set a valid model name in .env.")

    temperature = _parse_float(env.get(TEMPERATURE_VAR, DEFAULT_TEMPERATURE), TEMPERATURE_VAR)
    if not 0.0 <= temperature <= 2.0:
        raise ConfigurationError(
            f"{TEMPERATURE_VAR} must be between 0 and 2; received {temperature}."
        )

    timeout = _parse_float(env.get(TIMEOUT_VAR, DEFAULT_TIMEOUT_SECONDS), TIMEOUT_VAR)
    if timeout <= 0:
        raise ConfigurationError(f"{TIMEOUT_VAR} must be greater than 0; received {timeout}.")

    max_retries = _parse_int(env.get(MAX_RETRIES_VAR, DEFAULT_MAX_RETRIES), MAX_RETRIES_VAR)
    if max_retries < 0:
        raise ConfigurationError(f"{MAX_RETRIES_VAR} must be 0 or greater; received {max_retries}.")

    return ModelConfig(
        model=model,
        temperature=temperature,
        timeout_seconds=timeout,
        max_retries=max_retries,
    )


def api_key_is_configured(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> bool:
    """Return whether a non-blank API key is available. The value is never returned."""
    env = _environment(environ, env_file)
    return bool(env.get(API_KEY_VAR, "").strip())


def require_api_key(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> None:
    """Fail fast when ``OPENAI_API_KEY`` is missing or blank (approved P6)."""
    if not api_key_is_configured(environ, env_file):
        raise ConfigurationError(
            f"{API_KEY_VAR} was not found. Add it to the repository-root .env file. "
            "Do not paste the key into source code or commit the .env file."
        )


def validate_runtime_configuration(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> ModelConfig:
    """Validate credentials and model settings before any classification starts."""
    require_api_key(environ, env_file)
    return load_model_config(environ, env_file)


# ---------------------------------------------------------------------------
# Workflow configuration (Matrix 1 and Matrix 2 are strictly separate)
# ---------------------------------------------------------------------------

WORKSHEET_NAME: Final[str] = "Sheet1"
CASE_LIMIT: Final[int] = 100

PREDICTIONS_FILENAME: Final[str] = "predictions.jsonl"
ERRORS_FILENAME: Final[str] = "errors.jsonl"
SINGLE_CASE_FILENAME: Final[str] = "single_case_test.json"


@dataclass(frozen=True)
class WorkflowSpec:
    """Everything that distinguishes one evaluation workflow from the other."""

    name: str
    title: str
    reference_description: str
    input_filename: str
    evaluation_workbook_filename: str
    output_dir: Path
    worksheet_name: str = WORKSHEET_NAME
    case_limit: int = CASE_LIMIT
    # Week 4 Matrix 1 loader raises when fewer than ``case_limit`` cases exist;
    # the Week 4 Matrix 2 loader only logs a warning. Both behaviours are kept.
    require_exact_case_count: bool = False
    # Week 4 Matrix 1 loader rejects a limit above 100; Matrix 2 has no cap.
    max_case_limit: int | None = None
    # Week 4's Matrix 1 batch always ran exactly 100 cases (no --limit option);
    # Matrix 2's batch accepted --limit. Applies to batch runs and the CLI.
    configurable_limit: bool = True
    input_dir: Path = DEFAULT_INPUT_DIR

    @property
    def default_input_path(self) -> Path:
        return self.input_dir / self.input_filename

    @property
    def predictions_path(self) -> Path:
        return self.output_dir / PREDICTIONS_FILENAME

    @property
    def errors_path(self) -> Path:
        return self.output_dir / ERRORS_FILENAME

    @property
    def single_case_path(self) -> Path:
        return self.output_dir / SINGLE_CASE_FILENAME

    @property
    def evaluation_workbook_path(self) -> Path:
        return self.output_dir / self.evaluation_workbook_filename


MATRIX1: Final[WorkflowSpec] = WorkflowSpec(
    name="matrix1",
    title="Matrix 1 — Original Vetology scoring vs. LLM",
    reference_description="Original Vetology condition scores",
    input_filename="Vetology_Matrix1_First100_Encoded.xlsx",
    evaluation_workbook_filename="matrix1_evaluation_workbook.xlsx",
    output_dir=OUTPUT_ROOT / "matrix_1",
    require_exact_case_count=True,
    max_case_limit=CASE_LIMIT,
    configurable_limit=False,
)

MATRIX2: Final[WorkflowSpec] = WorkflowSpec(
    name="matrix2",
    title="Matrix 2 — Gold Standard vs. LLM",
    reference_description="Gold Standard condition scores",
    input_filename="1_canine_thorax_gold_standard_score_draft.xlsx",
    evaluation_workbook_filename="Evaluation Workbook v2.xlsx",
    output_dir=OUTPUT_ROOT / "matrix_2",
    require_exact_case_count=False,
)

WORKFLOWS: Final[Mapping[str, WorkflowSpec]] = {MATRIX1.name: MATRIX1, MATRIX2.name: MATRIX2}


def get_workflow(name: str) -> WorkflowSpec:
    """Return a workflow by its exact name (``matrix1`` or ``matrix2``)."""
    try:
        return WORKFLOWS[name]
    except KeyError:
        raise ConfigurationError(
            f"Unknown workflow {name!r}. Expected one of: {', '.join(WORKFLOWS)}."
        ) from None
