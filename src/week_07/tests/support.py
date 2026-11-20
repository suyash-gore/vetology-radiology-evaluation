"""Shared helpers for offline Week 7 tests.

``OfflineTestCase`` blocks outbound network connections for every test and
fails the test if any connection was attempted. Tests use synthetic data only;
no confidential dataset, prediction file or workbook is read.
"""
from __future__ import annotations

import ast
import logging
import unittest
from pathlib import Path
from unittest import mock


class NetworkAccessAttempted(AssertionError):
    """Raised when code under test tries to open a network connection."""


class OfflineTestCase(unittest.TestCase):
    """Blocks ``socket.connect``/``create_connection`` and asserts zero attempts."""

    def setUp(self) -> None:
        super().setUp()
        self.network_attempts: list[object] = []

        def refuse(*args, **kwargs):
            self.network_attempts.append(args[1:] if args else kwargs)
            raise NetworkAccessAttempted("Network access is blocked in Week 7 tests.")

        for target in ("socket.socket.connect", "socket.socket.connect_ex",
                       "socket.create_connection"):
            patcher = mock.patch(target, refuse)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self._assert_no_network)

    def _assert_no_network(self) -> None:
        self.assertEqual(self.network_attempts, [], "a network connection was attempted")


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


def code_without_docstrings(path: Path, *, rename: tuple[str, str] = ("week_05", "week_07")) -> str:
    """AST dump of a module with all docstrings removed and package names normalised.

    Used to prove that a Week 7 "verbatim copy" has exactly the same code as its
    Week 5 source; only docstrings (provenance notes) may differ.
    """
    source = path.read_text(encoding="utf-8").replace(*rename)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree, include_attributes=False)
