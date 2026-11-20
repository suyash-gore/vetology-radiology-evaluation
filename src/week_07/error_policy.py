"""Gemini-specific classification of classification-attempt errors (decision O3).

Verified against the installed SDK (langchain-google-genai 4.4.2, google-genai
2.34.0) with an offline mock transport:

* The SDK raises ``google.genai.errors.ClientError`` (4xx) / ``ServerError`` (5xx),
  both subclasses of ``google.genai.errors.APIError`` with an integer ``code``
  attribute (the HTTP status code).
* LangChain re-raises 4xx errors as its own types (``GoogleInvalidRequestError``,
  ``GoogleAuthenticationError``, ``GooglePermissionDeniedError``,
  ``GoogleModelNotFoundError``, ``GoogleRateLimitError`` or
  ``ChatGoogleGenerativeAIError``), which carry NO ``code``; the original
  ``ClientError`` is chained as ``__cause__``. 5xx errors are re-raised as
  ``GoogleAPIError``, itself a ``ServerError`` with ``code``.
* Network timeouts and network errors are not wrapped: they surface as
  ``httpx.TimeoutException`` subclasses (``ReadTimeout``, ``ConnectTimeout``, ...)
  and ``httpx.NetworkError`` subclasses (``ConnectError``, ``ReadError``,
  ``WriteError``, ``CloseError``), or the ``httpx2`` equivalents when the SDK uses
  that backend.

The status code is therefore taken from the first ``APIError`` found by walking
the exception, then its ``__cause__``/``__context__`` chain (bounded depth,
cycle-safe). Classification uses exception classes and the integer ``code``
attribute only — exception messages are never parsed.

=========  =====================================================================
Class      Errors
=========  =====================================================================
FATAL      ``ConfigurationError`` anywhere in the chain; HTTP 400, 401, 403, 404.
           Never retried: the batch stops.
TRANSIENT  HTTP 408, 429, 500, 502, 503, 504; network timeouts and network
           (connection/read/write/close) errors without an HTTP status, treated
           like HTTP 408. Bounded exponential backoff before the next attempt.
RETRYABLE  Everything else, including response validation failures, malformed
           JSON, empty/safety-blocked responses, other HTTP codes, HTTP protocol
           and proxy errors, and programming errors. Week 5 semantics: retried
           immediately, without backoff.
=========  =====================================================================
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

import httpx
from google.genai import errors as genai_errors

from week_07.config import DEFAULT_RETRY_POLICY, ConfigurationError, RetryPolicy

try:  # the SDK may use the httpx2 backend (GOOGLE_GENAI_HTTP_CLIENT)
    import httpx2
except ImportError:  # pragma: no cover - httpx2 is a google-genai dependency
    httpx2 = None

TIMEOUT_EXCEPTIONS: tuple[type[BaseException], ...] = tuple(
    cls for cls in (httpx.TimeoutException,
                    getattr(httpx2, "TimeoutException", None))
    if cls is not None
)
# ConnectError, ReadError, WriteError and CloseError (httpx and httpx2).
NETWORK_EXCEPTIONS: tuple[type[BaseException], ...] = tuple(
    cls for cls in (httpx.NetworkError,
                    getattr(httpx2, "NetworkError", None))
    if cls is not None
)
# Network timeouts and network errors without an HTTP status are handled like HTTP 408.
TIMEOUT_EQUIVALENT_STATUS = 408
MAX_CHAIN_DEPTH = 10


class ErrorClass(Enum):
    FATAL = "fatal"
    TRANSIENT = "transient"
    RETRYABLE = "retryable"


@dataclass(frozen=True)
class ErrorDecision:
    error_class: ErrorClass
    status_code: int | None
    reason: str

    @property
    def is_fatal(self) -> bool:
        return self.error_class is ErrorClass.FATAL

    @property
    def needs_backoff(self) -> bool:
        return self.error_class is ErrorClass.TRANSIENT


class FatalProviderError(RuntimeError):
    """A non-retryable provider error (HTTP 400/401/403/404): the batch must stop."""

    def __init__(self, message: str, decision: ErrorDecision,
                 counts: dict[str, int] | None = None) -> None:
        super().__init__(message)
        self.decision = decision
        self.counts = dict(counts or {})


def exception_chain(exc: BaseException) -> Iterator[BaseException]:
    """``exc`` followed by its causes/contexts (bounded, cycle-safe)."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen and len(seen) < MAX_CHAIN_DEPTH:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def http_status_code(exc: BaseException) -> int | None:
    """HTTP status from the first SDK ``APIError`` in the chain (typed attribute only)."""
    for item in exception_chain(exc):
        if isinstance(item, genai_errors.APIError):
            code = getattr(item, "code", None)
            if isinstance(code, int) and not isinstance(code, bool):
                return code
    return None


def classify_error(exc: BaseException, policy: RetryPolicy = DEFAULT_RETRY_POLICY) -> ErrorDecision:
    """Classify one failed attempt. See the module docstring for the rules."""
    chain = list(exception_chain(exc))

    if any(isinstance(item, ConfigurationError) for item in chain):
        return ErrorDecision(ErrorClass.FATAL, None, "configuration error")

    status = http_status_code(exc)
    if status is not None:
        if status in policy.fatal_status_codes:
            return ErrorDecision(ErrorClass.FATAL, status, f"HTTP {status} (not retryable)")
        if status in policy.transient_status_codes:
            return ErrorDecision(ErrorClass.TRANSIENT, status, f"HTTP {status} (transient)")
        return ErrorDecision(ErrorClass.RETRYABLE, status, f"HTTP {status}")

    for exceptions, label in ((TIMEOUT_EXCEPTIONS, "network timeout"),
                              (NETWORK_EXCEPTIONS, "network error")):
        if any(isinstance(item, exceptions) for item in chain):
            if TIMEOUT_EQUIVALENT_STATUS in policy.transient_status_codes:
                return ErrorDecision(ErrorClass.TRANSIENT, None,
                                     f"{label} (handled like HTTP 408)")
            return ErrorDecision(ErrorClass.RETRYABLE, None, label)

    return ErrorDecision(ErrorClass.RETRYABLE, None, type(exc).__name__)
