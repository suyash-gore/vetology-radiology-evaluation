"""Shared helpers for offline tests: quiet loggers, fixed clocks, fake classifiers."""
from __future__ import annotations

import json
import logging
import unittest
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

from week_05.conditions import CONDITION_KEYS

FIXED_START = datetime(2026, 11, 10, 9, 30, 0, 123456, tzinfo=timezone.utc)


def quiet(test: unittest.TestCase, *logger_names: str) -> None:
    """Silence the named loggers for one test (assertLogs still works)."""
    for name in logger_names:
        logger = logging.getLogger(name)
        handler = logging.NullHandler()
        previous = logger.propagate
        logger.addHandler(handler)
        logger.propagate = False
        test.addCleanup(logger.removeHandler, handler)
        test.addCleanup(setattr, logger, "propagate", previous)


class StepClock:
    """Deterministic UTC clock: each call advances by one millisecond."""

    def __init__(self, start: datetime = FIXED_START) -> None:
        self.current = start

    def __call__(self) -> datetime:
        value = self.current
        self.current += timedelta(milliseconds=1)
        return value


def labels_json(**overrides: str) -> str:
    data = {key: "Negative" for key in CONDITION_KEYS}
    data.update(overrides)
    return json.dumps(data)


VALID_RESPONSE = labels_json()


class ScriptedClassifier:
    """Fake classifier: returns/raises scripted outcomes and records every payload.

    ``script`` maps a findings string (or ``"*"`` as default) to a list of
    outcomes consumed per call; an outcome is a response string or an exception.
    """

    def __init__(self, script: dict[str, list[Any]] | None = None,
                 default: Any = VALID_RESPONSE) -> None:
        self.script = {key: list(value) for key, value in (script or {}).items()}
        self.default = default
        self.calls: list[dict[str, str]] = []

    def __call__(self, payload: dict[str, str]) -> str:
        self.calls.append(dict(payload))
        queue = self.script.get(payload["findings"])
        outcome = queue.pop(0) if queue else self.default
        if isinstance(outcome, BaseException):
            raise outcome
        if callable(outcome):
            return outcome(payload)
        return outcome


def make_cases(case_ids: Iterable[Any]) -> tuple[SimpleNamespace, ...]:
    """Minimal duck-typed cases (like the Week 4 offline tests)."""
    def case(case_id: Any) -> SimpleNamespace:
        payload = {"findings": f"findings {case_id}", "conclusions": "", "recommendations": ""}
        return SimpleNamespace(case_id=case_id, to_llm_payload=lambda p=payload: dict(p))

    return tuple(case(case_id) for case_id in case_ids)


def read_jsonl(path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


class FrozenDatetime:
    """Stand-in for ``datetime`` in Week 4's module, driven by a StepClock."""

    def __init__(self, clock: Callable[[], datetime]) -> None:
        self._clock = clock

    def now(self, tz=None):  # noqa: D401 - mimic datetime.now
        return self._clock()
