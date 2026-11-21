"""Gemini model, retry and workflow configuration for the Week 7 application.

Model settings follow the Week 5 pattern (environment variables, defaults,
``.env`` loaded with ``override=False`` so existing variables take precedence,
validation before any classification), with Gemini-specific variables:

=========================  ====================  =============================
Variable                   Default               Rule
=========================  ====================  =============================
``GOOGLE_API_KEY``         (required, live run)  presence check only
``GEMINI_MODEL``           ``gemini-3.8-flash``  non-empty
``GEMINI_TEMPERATURE``     ``0``                 0 to 2
``GEMINI_TIMEOUT_SECONDS`` ``90``                greater than 0
=========================  ====================  =============================

The API key itself is never read into a Python object here: the LangChain
Google client reads ``GOOGLE_API_KEY`` from the process environment. This module
only checks that it is set. The Gemini functions never read OpenAI variables;
the OpenAI settings used by Feline Thorax and Canine Abdomen are defined at the
end of this module.

Retry policy (approved decision O3): the SDK makes exactly ONE transport
attempt per application invocation (``TRANSPORT_MAX_RETRIES = 0`` is a fixed
constant, not an environment setting); the application makes at most two
attempts per case. Bounded exponential backoff is applied between application
attempts only for the transient HTTP status codes 408, 429, 500, 502, 503 and
504, and for network timeouts and network errors without an HTTP status
(handled like 408). HTTP 400, 401, 403 and 404 and configuration errors are
fatal and never retried. Response validation failures keep Week 5's immediate
retry.

Workflows: Matrix 1 and Matrix 2 keep the Week 5 inputs, case-count rules and
workbook names, but every Week 7 output lives under ``outputs/week_07/``. The
Week 5 OpenAI prediction files are referenced only as read-only comparison
sources.
"""
from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Repository paths (anchored to the repository root, not the working directory)
# ---------------------------------------------------------------------------

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
ENV_FILE: Final[Path] = REPO_ROOT / ".env"
DATA_DIR: Final[Path] = REPO_ROOT / "data"
SRC_DIR: Final[Path] = REPO_ROOT / "src"
DEFAULT_INPUT_DIR: Final[Path] = DATA_DIR / "week_04_inputs"
OUTPUTS_DIR: Final[Path] = REPO_ROOT / "outputs"
OUTPUT_ROOT: Final[Path] = OUTPUTS_DIR / "week_07"
COMPARISON_ROOT: Final[Path] = OUTPUT_ROOT / "comparison"
WEEK4_OUTPUTS: Final[Path] = OUTPUTS_DIR / "week_04"
WEEK5_OUTPUTS: Final[Path] = OUTPUTS_DIR / "week_05"

# ---------------------------------------------------------------------------
# Gemini model configuration
# ---------------------------------------------------------------------------

API_KEY_VAR: Final[str] = "GOOGLE_API_KEY"
MODEL_VAR: Final[str] = "GEMINI_MODEL"
TEMPERATURE_VAR: Final[str] = "GEMINI_TEMPERATURE"
TIMEOUT_VAR: Final[str] = "GEMINI_TIMEOUT_SECONDS"
# Deliberately NOT configurable: refused if present (see load_model_config).
FORBIDDEN_RETRY_VAR: Final[str] = "GEMINI_MAX_RETRIES"

DEFAULT_MODEL: Final[str] = "gemini-3.8-flash"
DEFAULT_TEMPERATURE: Final[str] = "0"
DEFAULT_TIMEOUT_SECONDS: Final[str] = "90"

# Gemini structured-output mode without a response schema (approved decision O2).
RESPONSE_MIME_TYPE: Final[str] = "application/json"

# SDK transport: one attempt per application invocation (O3). Fixed constant.
TRANSPORT_MAX_RETRIES: Final[int] = 0
TRANSPORT_ATTEMPTS: Final[int] = TRANSPORT_MAX_RETRIES + 1


class ConfigurationError(RuntimeError):
    """Raised when credentials or settings are missing or invalid."""


@dataclass(frozen=True)
class GeminiModelConfig:
    """Gemini model settings. Deliberately contains no credential."""

    model: str = DEFAULT_MODEL
    temperature: float = 0.0
    timeout_seconds: float = 90.0
    response_mime_type: str = RESPONSE_MIME_TYPE
    transport_max_retries: int = TRANSPORT_MAX_RETRIES

    def __post_init__(self) -> None:
        if self.transport_max_retries != TRANSPORT_MAX_RETRIES:
            raise ConfigurationError(
                "Gemini transport retries are fixed at "
                f"{TRANSPORT_MAX_RETRIES} (one transport attempt per application attempt); "
                f"received {self.transport_max_retries}."
            )
        if self.response_mime_type != RESPONSE_MIME_TYPE:
            raise ConfigurationError(
                f"Gemini response MIME type is fixed at {RESPONSE_MIME_TYPE!r}; "
                f"received {self.response_mime_type!r}."
            )


# ---------------------------------------------------------------------------
# Application retry policy (approved decision O3)
# ---------------------------------------------------------------------------

DEFAULT_MAX_ATTEMPTS: Final[int] = 2
TRANSIENT_HTTP_STATUS_CODES: Final[frozenset[int]] = frozenset({408, 429, 500, 502, 503, 504})
FATAL_HTTP_STATUS_CODES: Final[frozenset[int]] = frozenset({400, 401, 403, 404})
DEFAULT_BACKOFF_BASE_SECONDS: Final[float] = 2.0
DEFAULT_BACKOFF_FACTOR: Final[float] = 2.0
DEFAULT_BACKOFF_MAX_SECONDS: Final[float] = 30.0


@dataclass(frozen=True)
class RetryPolicy:
    """Application-level attempts and backoff. Recorded verbatim in the run manifest."""

    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    transient_status_codes: frozenset[int] = TRANSIENT_HTTP_STATUS_CODES
    fatal_status_codes: frozenset[int] = FATAL_HTTP_STATUS_CODES
    backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    backoff_max_seconds: float = DEFAULT_BACKOFF_MAX_SECONDS

    def __post_init__(self) -> None:
        if (isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int)
                or self.max_attempts < 1):
            raise ConfigurationError(
                f"max_attempts must be an integer of at least 1; received {self.max_attempts!r}."
            )
        overlap = self.transient_status_codes & self.fatal_status_codes
        if overlap:
            raise ConfigurationError(
                f"HTTP status codes cannot be both transient and fatal: {sorted(overlap)}"
            )
        for name in ("backoff_base_seconds", "backoff_factor", "backoff_max_seconds"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) \
                    or not math.isfinite(value) or value < 0:
                raise ConfigurationError(f"{name} must be a finite number >= 0; got {value!r}.")
        if self.backoff_factor < 1:
            raise ConfigurationError("backoff_factor must be at least 1.")

    def backoff_seconds(self, failed_attempt: int) -> float:
        """Delay after a TRANSIENT failure of ``failed_attempt`` (1-based), before the next.

        ``min(base * factor ** (failed_attempt - 1), max)``: with the defaults the
        only delay that can occur (between attempts 1 and 2) is 2 seconds.
        """
        if isinstance(failed_attempt, bool) or not isinstance(failed_attempt, int) \
                or failed_attempt < 1:
            raise ValueError(f"failed_attempt must be an integer >= 1; got {failed_attempt!r}.")
        delay = self.backoff_base_seconds * self.backoff_factor ** (failed_attempt - 1)
        return float(min(delay, self.backoff_max_seconds))

    def as_manifest(self) -> dict[str, object]:
        """JSON-serialisable description for the run manifest."""
        return {
            "transport_attempts_per_application_attempt": TRANSPORT_ATTEMPTS,
            "transport_max_retries": TRANSPORT_MAX_RETRIES,
            "application_max_attempts": self.max_attempts,
            "transient_http_status_codes": sorted(self.transient_status_codes),
            "transient_handling": "bounded exponential backoff between application attempts",
            "network_error_handling": "network timeouts and httpx/httpx2 NetworkError "
                                      "(connect/read/write/close) without an HTTP status: "
                                      "transient, same backoff as HTTP 408",
            "rate_limit_handling": "HTTP 429 uses the same bounded backoff; Retry-After "
                                   "is not used",
            "backoff_base_seconds": self.backoff_base_seconds,
            "backoff_factor": self.backoff_factor,
            "backoff_max_seconds": self.backoff_max_seconds,
            "fatal_http_status_codes": sorted(self.fatal_status_codes),
            "fatal_handling": "not retried; the batch stops and the case stays pending",
            "validation_failure_handling": "retried immediately without backoff (Week 5)",
            "other_error_handling": "retried immediately without backoff (Week 5)",
            "classification_basis": "SDK exception class and HTTP status code attribute; "
                                    "exception messages are never parsed",
        }


DEFAULT_RETRY_POLICY: Final[RetryPolicy] = RetryPolicy()

# ---------------------------------------------------------------------------
# Environment loading and validation
# ---------------------------------------------------------------------------


def _environment(environ: Mapping[str, str] | None, env_file: Path | None) -> Mapping[str, str]:
    """Return the variable source, loading ``.env`` only for the real environment.

    As in Weeks 4 and 5, ``load_dotenv`` does not override variables that are
    already set in the process environment.
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


def load_model_config(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> GeminiModelConfig:
    """Read and validate Gemini settings.

    ``environ`` may be supplied (e.g. in tests) to bypass ``os.environ`` and the
    ``.env`` file entirely.
    """
    env = _environment(environ, env_file)

    if FORBIDDEN_RETRY_VAR in env:
        raise ConfigurationError(
            f"{FORBIDDEN_RETRY_VAR} is not supported: Gemini transport retries are fixed at "
            f"{TRANSPORT_MAX_RETRIES} and application attempts are controlled by the batch "
            "command. Remove the variable from the environment/.env."
        )

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

    return GeminiModelConfig(model=model, temperature=temperature, timeout_seconds=timeout)


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
    """Fail fast when ``GOOGLE_API_KEY`` is missing or blank."""
    if not api_key_is_configured(environ, env_file):
        raise ConfigurationError(
            f"{API_KEY_VAR} was not found. Add it to the repository-root .env file. "
            "Do not paste the key into source code or commit the .env file."
        )


def validate_runtime_configuration(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> GeminiModelConfig:
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
MANIFEST_FILENAME: Final[str] = "run_manifest.json"


@dataclass(frozen=True)
class WorkflowSpec:
    """Everything that distinguishes one evaluation workflow from the other.

    Application-aware fields (Week 7 extension; the Canine Thorax defaults
    reproduce the original Matrix 1 / Matrix 2 specs exactly):

    * ``application`` — the owning application key (``week_07.applications``).
    * ``comparison_dir`` / ``week5_output_dir`` — ``None`` for applications that
      have no OpenAI-vs-Gemini comparison and no Week 5 predecessor.
    * ``shared_predictions_dir`` — when set, the batch outputs (predictions,
      errors, run manifest) live in this application-wide directory, shared by
      both workflows, while the evaluation workbook stays in ``output_dir``.
    """

    name: str
    title: str
    reference_description: str
    input_filename: str
    evaluation_workbook_filename: str
    comparison_workbook_filename: str
    output_dir: Path
    comparison_dir: Path | None = None
    week5_output_dir: Path | None = None
    worksheet_name: str = WORKSHEET_NAME
    case_limit: int = CASE_LIMIT
    # Week 4/5 Matrix 1 loader raises when fewer than ``case_limit`` cases exist;
    # the Matrix 2 loader only logs a warning. Both behaviours are kept.
    require_exact_case_count: bool = False
    # Matrix 1 rejects a limit above 100; Matrix 2 has no cap.
    max_case_limit: int | None = None
    # Matrix 1's batch always runs exactly 100 cases (no --limit); Matrix 2 accepts --limit.
    configurable_limit: bool = True
    input_dir: Path = DEFAULT_INPUT_DIR
    application: str = "canine_thorax"
    shared_predictions_dir: Path | None = None

    @property
    def qualified_name(self) -> str:
        """``<application>/<workflow>``: unique across all applications."""
        return f"{self.application}/{self.name}"

    @property
    def default_input_path(self) -> Path:
        return self.input_dir / self.input_filename

    @property
    def run_dir(self) -> Path:
        """Directory of the batch outputs (predictions, errors, run manifest)."""
        return self.output_dir if self.shared_predictions_dir is None \
            else self.shared_predictions_dir

    @property
    def predictions_path(self) -> Path:
        return self.run_dir / PREDICTIONS_FILENAME

    @property
    def errors_path(self) -> Path:
        return self.run_dir / ERRORS_FILENAME

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / MANIFEST_FILENAME

    @property
    def evaluation_workbook_path(self) -> Path:
        return self.output_dir / self.evaluation_workbook_filename

    @property
    def comparison_workbook_path(self) -> Path:
        return self._require(self.comparison_dir, "comparison") \
            / self.comparison_workbook_filename

    @property
    def week5_predictions_path(self) -> Path:
        """Read-only Week 5 OpenAI predictions for this workflow (comparison source)."""
        return self._require(self.week5_output_dir, "Week 5") / PREDICTIONS_FILENAME

    @property
    def week5_errors_path(self) -> Path:
        """Read-only Week 5 OpenAI error log for this workflow (informational only)."""
        return self._require(self.week5_output_dir, "Week 5") / ERRORS_FILENAME

    def _require(self, directory: Path | None, what: str) -> Path:
        if directory is None:
            raise ConfigurationError(
                f"{self.qualified_name} has no {what} output directory; "
                "this feature is not available for this application."
            )
        return directory


MATRIX1: Final[WorkflowSpec] = WorkflowSpec(
    name="matrix1",
    title="Matrix 1 — Original Vetology scoring vs. LLM",
    reference_description="Original Vetology condition scores",
    input_filename="Vetology_Matrix1_First100_Encoded.xlsx",
    evaluation_workbook_filename="matrix1_evaluation_workbook.xlsx",
    comparison_workbook_filename="matrix1_openai_vs_gemini_comparison.xlsx",
    output_dir=OUTPUT_ROOT / "matrix_1",
    comparison_dir=COMPARISON_ROOT / "matrix_1",
    week5_output_dir=WEEK5_OUTPUTS / "matrix_1",
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
    comparison_workbook_filename="matrix2_openai_vs_gemini_comparison.xlsx",
    output_dir=OUTPUT_ROOT / "matrix_2",
    comparison_dir=COMPARISON_ROOT / "matrix_2",
    week5_output_dir=WEEK5_OUTPUTS / "matrix_2",
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


# ---------------------------------------------------------------------------
# Additional applications (Feline Thorax, Canine Abdomen)
# ---------------------------------------------------------------------------
#
# Each application owns ``outputs/week_07/<application>/``:
#
# * ``predictions/`` — the ONE shared batch run (predictions, errors, manifest),
#   generated from the Matrix 1 workbook and reused by both evaluations;
# * ``matrix_1/`` and ``matrix_2/`` — the two separate evaluation workbooks.
#
# The input workbooks live outside the repository and are normally given with
# ``--input``; ``WEEK7_INPUT_DIR`` is only the fallback location when no path is
# given. Nothing is ever copied there. ``config.WORKFLOWS`` stays Canine Thorax
# only (Week 5 parity); ``ALL_WORKFLOWS`` lists every application's workflows.

WEEK7_INPUT_DIR: Final[Path] = DATA_DIR / "week_07_inputs"
CANINE_THORAX_APPLICATION: Final[str] = "canine_thorax"
FELINE_THORAX_APPLICATION: Final[str] = "feline_thorax"
CANINE_ABDOMEN_APPLICATION: Final[str] = "canine_abdomen"

# Each new application's own output tree. Canine Thorax has none: its outputs
# stay directly under ``outputs/week_07/`` (matrix_1, matrix_2, comparison).
APPLICATION_OUTPUT_ROOTS: Final[Mapping[str, Path]] = MappingProxyType({
    FELINE_THORAX_APPLICATION: OUTPUT_ROOT / FELINE_THORAX_APPLICATION,
    CANINE_ABDOMEN_APPLICATION: OUTPUT_ROOT / CANINE_ABDOMEN_APPLICATION,
})


def _application_workflows(application: str, matrix1_input: str,
                           matrix2_input: str) -> tuple[WorkflowSpec, WorkflowSpec]:
    root = APPLICATION_OUTPUT_ROOTS[application]
    shared = root / "predictions"
    matrix1 = WorkflowSpec(
        name=MATRIX1.name,
        title=MATRIX1.title,
        reference_description=MATRIX1.reference_description,
        input_filename=matrix1_input,
        evaluation_workbook_filename=f"{application}_matrix1_evaluation_workbook.xlsx",
        comparison_workbook_filename="",
        output_dir=root / "matrix_1",
        require_exact_case_count=True,
        max_case_limit=CASE_LIMIT,
        configurable_limit=False,
        input_dir=WEEK7_INPUT_DIR,
        application=application,
        shared_predictions_dir=shared,
    )
    matrix2 = WorkflowSpec(
        name=MATRIX2.name,
        title=MATRIX2.title,
        reference_description=MATRIX2.reference_description,
        input_filename=matrix2_input,
        evaluation_workbook_filename=f"{application}_matrix2_evaluation_workbook.xlsx",
        comparison_workbook_filename="",
        output_dir=root / "matrix_2",
        require_exact_case_count=False,
        input_dir=WEEK7_INPUT_DIR,
        application=application,
        shared_predictions_dir=shared,
    )
    return matrix1, matrix2


FELINE_THORAX_MATRIX1, FELINE_THORAX_MATRIX2 = _application_workflows(
    FELINE_THORAX_APPLICATION,
    "2_feline_thorax_raw_data_encoded.xlsx",
    "2_feline_thorax_gold_standard_score_draft.xlsx",
)
CANINE_ABDOMEN_MATRIX1, CANINE_ABDOMEN_MATRIX2 = _application_workflows(
    CANINE_ABDOMEN_APPLICATION,
    "3_canine_abdomen_raw_data_encoded.xlsx",
    "3_canine_abdomen_gold_standard_score_draft.xlsx",
)

ALL_WORKFLOWS: Final[Mapping[str, WorkflowSpec]] = MappingProxyType({
    spec.qualified_name: spec
    for spec in (MATRIX1, MATRIX2, FELINE_THORAX_MATRIX1, FELINE_THORAX_MATRIX2,
                 CANINE_ABDOMEN_MATRIX1, CANINE_ABDOMEN_MATRIX2)
})


# ---------------------------------------------------------------------------
# OpenAI model configuration (Feline Thorax, Canine Abdomen)
# ---------------------------------------------------------------------------
#
# =========================  ==================  ==================================
# Variable                   Default             Rule
# =========================  ==================  ==================================
# ``OPENAI_API_KEY``         (required, live)    presence check only
# ``OPENAI_MODEL``           ``gpt-4.1-mini``    non-empty
# ``OPENAI_TEMPERATURE``     ``0``               0 to 2
# ``OPENAI_TIMEOUT_SECONDS`` ``90``              greater than 0
# =========================  ==================  ==================================
#
# Same names and defaults as Week 5. The key value is never read into Python:
# LangChain's ``ChatOpenAI`` reads it from the process environment. The OpenAI
# functions never read ``GOOGLE_API_KEY`` and the Gemini functions above never
# read ``OPENAI_*``.
#
# Retries: the SDK transport makes exactly ONE attempt per application attempt
# (``max_retries=0`` is a fixed constant). ``OPENAI_MAX_RETRIES`` (a Week 5
# setting) is deliberately ignored by Week 7 so that the batch retry policy
# (``RetryPolicy``) is the only retry system; ``config`` reports it as ignored.

OPENAI_API_KEY_VAR: Final[str] = "OPENAI_API_KEY"
OPENAI_MODEL_VAR: Final[str] = "OPENAI_MODEL"
OPENAI_TEMPERATURE_VAR: Final[str] = "OPENAI_TEMPERATURE"
OPENAI_TIMEOUT_VAR: Final[str] = "OPENAI_TIMEOUT_SECONDS"
OPENAI_IGNORED_RETRY_VAR: Final[str] = "OPENAI_MAX_RETRIES"

OPENAI_DEFAULT_MODEL: Final[str] = "gpt-4.1-mini"
OPENAI_TRANSPORT_MAX_RETRIES: Final[int] = 0


@dataclass(frozen=True)
class OpenAIModelConfig:
    """OpenAI model settings. Deliberately contains no credential."""

    model: str = OPENAI_DEFAULT_MODEL
    temperature: float = 0.0
    timeout_seconds: float = 90.0
    transport_max_retries: int = OPENAI_TRANSPORT_MAX_RETRIES

    def __post_init__(self) -> None:
        if self.transport_max_retries != OPENAI_TRANSPORT_MAX_RETRIES:
            raise ConfigurationError(
                f"OpenAI transport retries are fixed at {OPENAI_TRANSPORT_MAX_RETRIES} (one "
                "transport attempt per application attempt); received "
                f"{self.transport_max_retries}."
            )
        if not isinstance(self.model, str) or not self.model.strip():
            raise ConfigurationError("The OpenAI model name must not be empty.")
        if not 0.0 <= self.temperature <= 2.0:
            raise ConfigurationError("OpenAI temperature must be between 0 and 2.")
        if not self.timeout_seconds > 0:
            raise ConfigurationError("OpenAI timeout must be greater than 0.")


def load_openai_model_config(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
    *,
    default_model: str = OPENAI_DEFAULT_MODEL,
) -> OpenAIModelConfig:
    """Read and validate OpenAI settings (``environ`` bypasses os.environ and .env)."""
    env = _environment(environ, env_file)
    model = env.get(OPENAI_MODEL_VAR, default_model).strip()
    if not model:
        raise ConfigurationError(
            f"{OPENAI_MODEL_VAR} is empty. Set a valid model name in .env.")
    temperature = _parse_float(env.get(OPENAI_TEMPERATURE_VAR, DEFAULT_TEMPERATURE),
                               OPENAI_TEMPERATURE_VAR)
    if not 0.0 <= temperature <= 2.0:
        raise ConfigurationError(
            f"{OPENAI_TEMPERATURE_VAR} must be between 0 and 2; received {temperature}.")
    timeout = _parse_float(env.get(OPENAI_TIMEOUT_VAR, DEFAULT_TIMEOUT_SECONDS),
                           OPENAI_TIMEOUT_VAR)
    if timeout <= 0:
        raise ConfigurationError(
            f"{OPENAI_TIMEOUT_VAR} must be greater than 0; received {timeout}.")
    return OpenAIModelConfig(model=model, temperature=temperature, timeout_seconds=timeout)


def openai_retry_setting_ignored(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> bool:
    """Whether ``OPENAI_MAX_RETRIES`` is set (it is ignored by Week 7)."""
    return OPENAI_IGNORED_RETRY_VAR in _environment(environ, env_file)


def openai_api_key_is_configured(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> bool:
    """Return whether a non-blank OpenAI key is available. The value is never returned."""
    env = _environment(environ, env_file)
    return bool(env.get(OPENAI_API_KEY_VAR, "").strip())


def require_openai_api_key(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
) -> None:
    """Fail fast when ``OPENAI_API_KEY`` is missing or blank."""
    if not openai_api_key_is_configured(environ, env_file):
        raise ConfigurationError(
            f"{OPENAI_API_KEY_VAR} was not found. Add it to the repository-root .env file. "
            "Do not paste the key into source code or commit the .env file."
        )


def validate_openai_runtime_configuration(
    environ: Mapping[str, str] | None = None,
    env_file: Path | None = ENV_FILE,
    *,
    default_model: str = OPENAI_DEFAULT_MODEL,
) -> OpenAIModelConfig:
    """Validate the OpenAI credential and settings before any classification starts."""
    require_openai_api_key(environ, env_file)
    return load_openai_model_config(environ, env_file, default_model=default_model)
