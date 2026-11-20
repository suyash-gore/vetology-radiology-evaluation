"""Gemini error classification (decision O3) using real SDK exception instances."""
from __future__ import annotations

import httpx

from week_07.config import ConfigurationError, RetryPolicy
from week_07.error_policy import (
    ErrorClass,
    FatalProviderError,
    classify_error,
    exception_chain,
    http_status_code,
)
from week_07.response_validator import ResponseValidationError
from week_07.tests.gemini_fakes import langchain_error, sdk_error, timeout_error
from week_07.tests.support import OfflineTestCase

TRANSIENT = (408, 429, 500, 502, 503, 504)
FATAL = (400, 401, 403, 404)


class TestHttpStatusClassification(OfflineTestCase):
    def test_transient_codes_raw_sdk_errors(self):
        for code in TRANSIENT:
            with self.subTest(code=code):
                decision = classify_error(sdk_error(code))
                self.assertIs(decision.error_class, ErrorClass.TRANSIENT)
                self.assertEqual(decision.status_code, code)
                self.assertTrue(decision.needs_backoff)

    def test_transient_codes_as_raised_by_langchain(self):
        for code in TRANSIENT:
            with self.subTest(code=code):
                exc = langchain_error(code)
                decision = classify_error(exc)
                self.assertIs(decision.error_class, ErrorClass.TRANSIENT)
                self.assertEqual(decision.status_code, code)

    def test_fatal_codes_raw_and_langchain(self):
        for code in FATAL:
            for exc in (sdk_error(code), langchain_error(code)):
                with self.subTest(code=code, type=type(exc).__name__):
                    decision = classify_error(exc)
                    self.assertIs(decision.error_class, ErrorClass.FATAL)
                    self.assertEqual(decision.status_code, code)
                    self.assertFalse(decision.needs_backoff)

    def test_langchain_4xx_wrappers_have_no_code_but_chain_to_client_error(self):
        from google.genai import errors as genai_errors

        for code in (400, 401, 403, 404, 408, 429):
            exc = langchain_error(code)
            with self.subTest(code=code):
                self.assertNotIsInstance(exc, genai_errors.APIError)
                self.assertIsInstance(exc.__cause__, genai_errors.ClientError)
                self.assertEqual(http_status_code(exc), code)

    def test_other_http_codes_keep_week5_retry(self):
        for code in (409, 422, 501, 599):
            with self.subTest(code=code):
                decision = classify_error(sdk_error(code))
                self.assertIs(decision.error_class, ErrorClass.RETRYABLE)
                self.assertEqual(decision.status_code, code)

    def test_policy_codes_are_used(self):
        policy = RetryPolicy(transient_status_codes=frozenset({503}),
                             fatal_status_codes=frozenset({401}))
        self.assertIs(classify_error(sdk_error(429), policy).error_class, ErrorClass.RETRYABLE)
        self.assertIs(classify_error(sdk_error(400), policy).error_class, ErrorClass.RETRYABLE)
        self.assertIs(classify_error(sdk_error(503), policy).error_class, ErrorClass.TRANSIENT)


class TestNonHttpErrors(OfflineTestCase):
    def test_network_timeouts_are_transient_like_408(self):
        import httpx2

        for cls in (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout,
                    httpx.PoolTimeout, httpx2.ReadTimeout, httpx2.ConnectTimeout):
            with self.subTest(cls=f"{cls.__module__}.{cls.__name__}"):
                decision = classify_error(timeout_error(cls))
                self.assertIs(decision.error_class, ErrorClass.TRANSIENT)
                self.assertIsNone(decision.status_code)
                self.assertIn("408", decision.reason)

    def test_wrapped_timeout_is_transient(self):
        try:
            try:
                raise httpx.ReadTimeout("synthetic")
            except httpx.ReadTimeout as inner:
                raise RuntimeError("wrapper") from inner
        except RuntimeError as outer:
            self.assertIs(classify_error(outer).error_class, ErrorClass.TRANSIENT)

    def test_timeout_without_408_in_policy_is_retryable(self):
        policy = RetryPolicy(transient_status_codes=frozenset({503}))
        self.assertIs(classify_error(timeout_error(), policy).error_class, ErrorClass.RETRYABLE)

    def test_network_errors_are_transient_like_408(self):
        import httpx2

        for cls in (httpx.ConnectError, httpx.ReadError, httpx.WriteError, httpx.CloseError,
                    httpx.NetworkError, httpx2.ConnectError, httpx2.ReadError,
                    httpx2.NetworkError):
            with self.subTest(cls=f"{cls.__module__}.{cls.__name__}"):
                decision = classify_error(cls("synthetic"))
                self.assertIs(decision.error_class, ErrorClass.TRANSIENT)
                self.assertIsNone(decision.status_code)
                self.assertIn("network error", decision.reason)
                self.assertIn("408", decision.reason)

    def test_wrapped_network_error_is_transient(self):
        try:
            try:
                raise httpx.ConnectError("synthetic")
            except httpx.ConnectError as inner:
                raise RuntimeError("wrapper") from inner
        except RuntimeError as outer:
            self.assertIs(classify_error(outer).error_class, ErrorClass.TRANSIENT)

    def test_network_error_without_408_in_policy_is_retryable(self):
        policy = RetryPolicy(transient_status_codes=frozenset({503}))
        self.assertIs(classify_error(httpx.ConnectError("x"), policy).error_class,
                      ErrorClass.RETRYABLE)

    def test_protocol_and_proxy_errors_are_not_network_errors(self):
        for exc in (httpx.RemoteProtocolError("x"), httpx.LocalProtocolError("x"),
                    httpx.ProxyError("x"), httpx.UnsupportedProtocol("x")):
            with self.subTest(exc=type(exc).__name__):
                self.assertIs(classify_error(exc).error_class, ErrorClass.RETRYABLE)

    def test_programming_errors_are_never_transient(self):
        for exc in (TypeError("x"), AttributeError("x"), NameError("x"), OSError("x"),
                    ConnectionError("x"), TimeoutError("x"), RuntimeError("connect failed")):
            with self.subTest(exc=type(exc).__name__):
                self.assertIs(classify_error(exc).error_class, ErrorClass.RETRYABLE)

    def test_configuration_error_wrapping_network_error_is_fatal(self):
        try:
            try:
                raise httpx.ConnectError("synthetic")
            except httpx.ConnectError as inner:
                raise ConfigurationError("bad settings") from inner
        except ConfigurationError as outer:
            self.assertTrue(classify_error(outer).is_fatal)

    def test_validation_failures_keep_week5_retry(self):
        for exc in (ResponseValidationError("Response is not valid JSON: x"),
                    ResponseValidationError("Model response is empty or is not text."),
                    ValueError("anything"), KeyError("x")):
            with self.subTest(exc=repr(exc)):
                decision = classify_error(exc)
                self.assertIs(decision.error_class, ErrorClass.RETRYABLE)
                self.assertFalse(decision.needs_backoff)

    def test_configuration_errors_are_fatal_even_when_wrapped(self):
        self.assertTrue(classify_error(ConfigurationError("no key")).is_fatal)
        try:
            try:
                raise ConfigurationError("no key")
            except ConfigurationError as inner:
                raise RuntimeError("wrapper") from inner
        except RuntimeError as outer:
            self.assertTrue(classify_error(outer).is_fatal)

    def test_messages_are_never_parsed(self):
        for text in ("429 RESOURCE_EXHAUSTED", "HTTP 503", "401 Unauthorized", "timeout"):
            with self.subTest(text=text):
                self.assertIs(classify_error(RuntimeError(text)).error_class,
                              ErrorClass.RETRYABLE)

    def test_non_integer_code_attribute_is_ignored(self):
        exc = sdk_error(503)
        exc.code = "503"
        self.assertIsNone(http_status_code(exc))
        exc.code = True
        self.assertIsNone(http_status_code(exc))


class TestChainWalking(OfflineTestCase):
    def test_cycle_safe(self):
        a, b = RuntimeError("a"), RuntimeError("b")
        a.__cause__, b.__cause__ = b, a
        self.assertEqual(len(list(exception_chain(a))), 2)
        self.assertIs(classify_error(a).error_class, ErrorClass.RETRYABLE)

    def test_context_is_followed(self):
        try:
            try:
                raise sdk_error(429)
            except Exception:
                raise RuntimeError("during handling")  # implicit __context__
        except RuntimeError as exc:
            self.assertEqual(http_status_code(exc), 429)

    def test_fatal_provider_error_carries_decision_and_counts(self):
        decision = classify_error(sdk_error(401))
        counts = {"succeeded": 1}
        error = FatalProviderError("stop", decision, counts)
        counts["succeeded"] = 99
        self.assertIs(error.decision, decision)
        self.assertEqual(error.counts, {"succeeded": 1})
