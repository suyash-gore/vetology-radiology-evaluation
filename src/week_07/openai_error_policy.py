"""OpenAI-specific classification of classification-attempt errors.

Same three classes, same ``RetryPolicy`` and same ``ErrorDecision`` as the Gemini
policy (``error_policy``, unchanged and still used for Canine Thorax), so the
batch runner handles both providers identically:

=========  =====================================================================
Class      Errors
=========  =====================================================================
FATAL      ``ConfigurationError`` anywhere in the chain; HTTP 400, 401, 403, 404
           (``openai.APIStatusError.status_code``). Never retried: the batch
           stops and the case stays pending.
TRANSIENT  HTTP 408, 429, 500, 502, 503, 504; ``openai.APITimeoutError`` and
           ``openai.APIConnectionError`` (no HTTP status: handled like HTTP 408);
           httpx/httpx2 timeouts and network errors. Bounded backoff.
RETRYABLE  Everything else (response validation failures, malformed JSON, other
           HTTP codes, programming errors): retried immediately (Week 5).
=========  =====================================================================

Classification uses exception classes and the integer ``status_code`` attribute
found by walking the exception and its ``__cause__``/``__context__`` chain;
messages are never parsed. ``openai`` is imported lazily, so the Gemini
application never needs it.
"""
from __future__ import annotations

from week_07.config import DEFAULT_RETRY_POLICY, ConfigurationError, RetryPolicy
from week_07.error_policy import (
    NETWORK_EXCEPTIONS,
    TIMEOUT_EQUIVALENT_STATUS,
    TIMEOUT_EXCEPTIONS,
    ErrorClass,
    ErrorDecision,
    exception_chain,
)


def _openai():
    import openai  # imported only when an OpenAI error has to be classified

    return openai


def openai_status_code(exc: BaseException) -> int | None:
    """HTTP status from the first ``openai.APIStatusError`` in the chain (typed attribute)."""
    openai = _openai()
    for item in exception_chain(exc):
        if isinstance(item, openai.APIStatusError):
            code = getattr(item, "status_code", None)
            if isinstance(code, int) and not isinstance(code, bool):
                return code
    return None


def classify_openai_error(exc: BaseException,
                          policy: RetryPolicy = DEFAULT_RETRY_POLICY) -> ErrorDecision:
    """Classify one failed OpenAI attempt. See the module docstring for the rules."""
    chain = list(exception_chain(exc))
    if any(isinstance(item, ConfigurationError) for item in chain):
        return ErrorDecision(ErrorClass.FATAL, None, "configuration error")

    status = openai_status_code(exc)
    if status is not None:
        if status in policy.fatal_status_codes:
            return ErrorDecision(ErrorClass.FATAL, status, f"HTTP {status} (not retryable)")
        if status in policy.transient_status_codes:
            return ErrorDecision(ErrorClass.TRANSIENT, status, f"HTTP {status} (transient)")
        return ErrorDecision(ErrorClass.RETRYABLE, status, f"HTTP {status}")

    openai = _openai()
    timeouts = (openai.APITimeoutError, *TIMEOUT_EXCEPTIONS)
    network = (openai.APIConnectionError, *NETWORK_EXCEPTIONS)
    for exceptions, label in ((timeouts, "network timeout"), (network, "network error")):
        if any(isinstance(item, exceptions) for item in chain):
            if TIMEOUT_EQUIVALENT_STATUS in policy.transient_status_codes:
                return ErrorDecision(ErrorClass.TRANSIENT, None,
                                     f"{label} (handled like HTTP 408)")
            return ErrorDecision(ErrorClass.RETRYABLE, None, label)

    return ErrorDecision(ErrorClass.RETRYABLE, None, type(exc).__name__)
