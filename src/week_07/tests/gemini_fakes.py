"""Offline Gemini test doubles: real SDK exception instances and a mock HTTP transport.

Nothing here opens a network connection. ``offline_chat_model`` builds a real
``ChatGoogleGenerativeAI`` with a dummy key string and replaces the SDK's httpx
client with ``httpx.MockTransport``, so the genuine LangChain -> google-genai
request/retry/error path runs against scripted synthetic HTTP responses.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import httpx
from google.genai import errors as genai_errors

from week_07.conditions import CONDITION_KEYS

DUMMY_KEY = "dummy-offline-test-key"  # never a real credential
FIXED_START = datetime(2026, 11, 20, 9, 30, 0, 123456, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Synthetic responses and cases
# ---------------------------------------------------------------------------

def labels_json(**overrides: str) -> str:
    data = {key: "Negative" for key in CONDITION_KEYS}
    data.update(overrides)
    return json.dumps(data)


VALID_RESPONSE = labels_json()


def make_cases(case_ids: Iterable[Any]) -> tuple[SimpleNamespace, ...]:
    """Minimal duck-typed cases with synthetic report text."""
    def case(case_id: Any) -> SimpleNamespace:
        payload = {"findings": f"synthetic findings {case_id}", "conclusions": "",
                   "recommendations": ""}
        return SimpleNamespace(case_id=case_id, to_llm_payload=lambda p=payload: dict(p))

    return tuple(case(case_id) for case_id in case_ids)


class StepClock:
    """Deterministic UTC clock: each call advances by one millisecond."""

    def __init__(self, start: datetime = FIXED_START) -> None:
        self.current = start

    def __call__(self) -> datetime:
        value = self.current
        self.current += timedelta(milliseconds=1)
        return value


class ScriptedClassifier:
    """Returns/raises scripted outcomes per findings text and records every payload.

    ``script`` maps a findings string (or ``"*"``) to a list of outcomes consumed
    per call; an outcome is a response string, an exception instance, or a
    zero-argument callable returning an exception to raise (for chained errors).
    """

    def __init__(self, script: dict[str, list[Any]] | None = None,
                 default: Any = VALID_RESPONSE) -> None:
        self.script = {key: list(value) for key, value in (script or {}).items()}
        self.default = default
        self.calls: list[dict[str, str]] = []

    def __call__(self, payload: dict[str, str]) -> str:
        self.calls.append(dict(payload))
        queue = self.script.get(payload["findings"]) or self.script.get("*")
        outcome = queue.pop(0) if queue else self.default
        if callable(outcome) and not isinstance(outcome, BaseException):
            outcome = outcome()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class RecordingSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def findings(case_id: Any) -> str:
    return f"synthetic findings {case_id}"


# ---------------------------------------------------------------------------
# Real SDK exception instances (constructed offline)
# ---------------------------------------------------------------------------

def _error_json(code: int, status: str = "SYNTHETIC") -> dict[str, Any]:
    return {"error": {"code": code, "message": "synthetic test error", "status": status}}


def sdk_error(code: int) -> genai_errors.APIError:
    """The google-genai error the SDK raises for an HTTP status (ClientError/ServerError)."""
    cls = genai_errors.ClientError if 400 <= code < 500 else genai_errors.ServerError
    return cls(code, _error_json(code))


def langchain_error(code: int) -> BaseException:
    """The exception ChatGoogleGenerativeAI actually raises for an HTTP status.

    4xx: a LangChain wrapper without ``code`` whose ``__cause__`` is the
    ``ClientError``; 5xx: ``GoogleAPIError`` (a ``ServerError`` with ``code``).
    Built by the installed LangChain conversion functions themselves.
    """
    from langchain_google_genai import chat_models

    original = sdk_error(code)
    try:
        if isinstance(original, genai_errors.ClientError):
            try:
                raise original
            except genai_errors.ClientError as exc:
                chat_models._handle_client_error(exc, {"model": "gemini-3.8-flash"})
        else:
            try:
                raise original
            except genai_errors.ServerError as exc:
                chat_models._handle_server_error(exc)
    except Exception as converted:  # noqa: BLE001
        return converted
    raise AssertionError("LangChain did not convert the SDK error")  # pragma: no cover


def timeout_error(cls: type[BaseException] = httpx.ReadTimeout) -> BaseException:
    return cls("synthetic timeout")


# ---------------------------------------------------------------------------
# Real ChatGoogleGenerativeAI on a mock transport
# ---------------------------------------------------------------------------

def ok_body(parts: list[dict[str, Any]]) -> dict[str, Any]:
    return {"candidates": [{"content": {"role": "model", "parts": parts},
                            "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1}}


class MockGemini:
    """Scripted HTTP outcomes for the SDK; records every request it receives.

    Each outcome is ``(status, json_body)`` or an ``httpx`` exception class.
    """

    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        outcome = self.outcomes.pop(0) if self.outcomes else (200, ok_body([{"text": "{}"}]))
        if isinstance(outcome, type) and issubclass(outcome, Exception):
            raise outcome("synthetic transport failure", request=request)
        status, body = outcome
        return httpx.Response(status, json=body if body is not None else _error_json(status))

    def bodies(self) -> list[dict[str, Any]]:
        return [json.loads(request.content) for request in self.requests]


def offline_chat_model(factory: Callable[[], Any], mock: MockGemini) -> Any:
    """Build the model via ``factory`` and route its SDK traffic to ``mock``."""
    model = factory()
    model.client._api_client._httpx_client = httpx.Client(
        transport=httpx.MockTransport(mock.handler)
    )
    return model
