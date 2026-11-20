"""Gemini client: messages, payload restriction, configuration and offline SDK behaviour.

The ``TestRealSdkOffline`` cases run the genuine ChatGoogleGenerativeAI ->
google-genai path with a dummy key and ``httpx.MockTransport`` (no network).
"""
from __future__ import annotations

import os
from unittest import mock

import httpx

from week_07.config import ConfigurationError, GeminiModelConfig
from week_07.error_policy import ErrorClass, classify_error
from week_07.llm_client import (
    HUMAN_INSTRUCTION,
    NOT_PROVIDED,
    GeminiClassifier,
    PayloadError,
    build_human_content,
    build_messages,
    chat_model_kwargs,
    create_chat_model,
    response_text,
)
from week_07.prompts.prompt_loader import load_system_prompt
from week_07.response_validator import ResponseValidationError, validate_model_response
from week_07.tests.gemini_fakes import (
    DUMMY_KEY,
    VALID_RESPONSE,
    MockGemini,
    offline_chat_model,
    ok_body,
)
from week_07.tests.support import OfflineTestCase

PAYLOAD = {"findings": "Synthetic finding text.", "conclusions": "Synthetic conclusion.",
           "recommendations": ""}
KEY_ENV = {"GOOGLE_API_KEY": DUMMY_KEY}


class TestMessages(OfflineTestCase):
    def test_exact_human_text(self):
        self.assertEqual(
            build_human_content(PAYLOAD),
            "Classify the following canine thorax radiology report according to the system "
            "instructions.\n\nFINDINGS:\nSynthetic finding text.\n\nCONCLUSIONS:\nSynthetic "
            "conclusion.\n\nRECOMMENDATIONS:\n[Not provided]",
        )

    def test_empty_and_none_become_not_provided(self):
        text = build_human_content({"findings": None, "conclusions": "", "recommendations": "R"})
        self.assertIn(f"FINDINGS:\n{NOT_PROVIDED}\n", text)
        self.assertIn(f"CONCLUSIONS:\n{NOT_PROVIDED}\n", text)
        self.assertTrue(text.startswith(HUMAN_INSTRUCTION))

    def test_system_message_is_verified_prompt(self):
        system, human = build_messages(PAYLOAD)
        self.assertEqual(system.type, "system")
        self.assertEqual(system.content, load_system_prompt())
        self.assertEqual(human.type, "human")
        self.assertEqual(human.content, build_human_content(PAYLOAD))


class TestPayloadRestriction(OfflineTestCase):
    def test_reference_labels_and_case_id_rejected(self):
        for extra in ({"case_id": 1}, {"CaseID": 1}, {"pneumonia": "Positive"},
                      {"ai_findings": "x"}):
            with self.subTest(extra=extra), self.assertRaises(PayloadError):
                build_messages({**PAYLOAD, **extra})

    def test_missing_or_misspelled_fields_rejected(self):
        for payload in ({"findings": "a", "conclusions": "b"},
                        {"Findings": "a", "conclusions": "b", "recommendations": "c"}):
            with self.subTest(payload=payload), self.assertRaises(PayloadError):
                build_messages(payload)

    def test_non_mapping_rejected(self):
        with self.assertRaises(PayloadError):
            build_messages(["findings", "conclusions", "recommendations"])


class TestKwargsAndConfiguration(OfflineTestCase):
    def test_exact_constructor_arguments(self):
        self.assertEqual(chat_model_kwargs(GeminiModelConfig()), {
            "model": "gemini-3.8-flash",
            "temperature": 0.0,
            "timeout": 90.0,
            "max_retries": 1,            # = google-genai HttpRetryOptions.attempts (total)
            "response_mime_type": "application/json",
        })

    def test_no_credential_or_schema_in_kwargs(self):
        kwargs = chat_model_kwargs(GeminiModelConfig())
        for forbidden in ("google_api_key", "api_key", "response_schema",
                          "response_json_schema", "safety_settings"):
            self.assertNotIn(forbidden, kwargs)

    def test_missing_key_fails_before_client_construction(self):
        with mock.patch("langchain_google_genai.ChatGoogleGenerativeAI") as constructor:
            with self.assertRaises(ConfigurationError):
                create_chat_model(GeminiModelConfig(), environ={})
            with self.assertRaises(ConfigurationError):
                create_chat_model(None, environ={})
            constructor.assert_not_called()

    def test_no_private_langchain_function_is_used(self):
        import inspect

        import week_07.llm_client as module

        self.assertNotIn("_uses_fixed_sampling", inspect.getsource(module))
        self.assertNotIn("chat_models._", inspect.getsource(module))

    def test_settings_from_environment(self):
        with mock.patch.dict(os.environ, KEY_ENV), \
                mock.patch("langchain_google_genai.ChatGoogleGenerativeAI") as constructor:
            create_chat_model(None, environ={**KEY_ENV, "GEMINI_TIMEOUT_SECONDS": "30"})
        constructor.assert_called_once()
        self.assertEqual(constructor.call_args.kwargs["timeout"], 30.0)
        self.assertNotIn(DUMMY_KEY, repr(constructor.call_args))


class TestResponseText(OfflineTestCase):
    def test_string(self):
        self.assertEqual(response_text('  {"a": 1}\n'), '{"a": 1}')

    def test_thinking_and_text_blocks(self):
        content = [{"type": "thinking", "thinking": "reasoning..."},
                   {"type": "text", "text": VALID_RESPONSE}]
        self.assertEqual(response_text(content), VALID_RESPONSE)

    def test_text_block_with_signature_extras(self):
        content = [{"type": "text", "text": VALID_RESPONSE, "extras": {"signature": "c2ln"}}]
        self.assertEqual(response_text(content), VALID_RESPONSE)

    def test_list_of_plain_strings_is_concatenated(self):
        self.assertEqual(response_text(['{"a": ', '"b"}']), '{"a": "b"}')

    def test_non_text_blocks_ignored(self):
        content = [{"type": "image", "url": "x"}, {"type": "text", "text": 5},
                   {"type": "text", "text": "ok"}, 7]
        self.assertEqual(response_text(content), "ok")

    def test_fences_are_not_stripped(self):
        fenced = f"```json\n{VALID_RESPONSE}\n```"
        self.assertEqual(response_text(fenced), fenced)
        self.assertEqual(response_text([{"type": "text", "text": fenced}]), fenced)
        with self.assertRaises(ResponseValidationError):
            validate_model_response(response_text(fenced))

    def test_empty_content(self):
        self.assertEqual(response_text(""), "")
        self.assertEqual(response_text([]), "")
        self.assertEqual(response_text([{"type": "thinking", "thinking": "x"}]), "")

    def test_other_types_like_week5(self):
        self.assertEqual(response_text(None), "None")


class FakeChatModel:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return mock.Mock(content=self.content)


class TestClassifier(OfflineTestCase):
    def test_returns_text_and_sends_built_messages(self):
        fake = FakeChatModel([{"type": "text", "text": VALID_RESPONSE}])
        classifier = GeminiClassifier(chat_model=fake)
        self.assertEqual(classifier(PAYLOAD), VALID_RESPONSE)
        self.assertEqual([m.content for m in fake.calls[0]],
                         [m.content for m in build_messages(PAYLOAD)])

    def test_single_client_reused(self):
        fake = FakeChatModel(VALID_RESPONSE)
        with mock.patch("week_07.llm_client.create_chat_model", return_value=fake) as factory:
            classifier = GeminiClassifier()
            classifier(PAYLOAD)
            classifier(PAYLOAD)
        factory.assert_called_once()
        self.assertEqual(len(fake.calls), 2)

    def test_invalid_payload_rejected_before_client_creation(self):
        with mock.patch("week_07.llm_client.create_chat_model") as factory:
            with self.assertRaises(PayloadError):
                GeminiClassifier()({**PAYLOAD, "case_id": 3})
        factory.assert_not_called()


class TestRealSdkOffline(OfflineTestCase):
    """Real LangChain + google-genai request path on a mock transport."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ, KEY_ENV)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("GEMINI_API_KEY", None)

    def classifier(self, outcomes):
        gemini = MockGemini(outcomes)
        model = offline_chat_model(
            lambda: create_chat_model(GeminiModelConfig(), environ=KEY_ENV), gemini)
        return GeminiClassifier(chat_model=model), gemini

    def test_request_body(self):
        classifier, gemini = self.classifier([(200, ok_body([{"text": VALID_RESPONSE}]))])
        self.assertEqual(classifier(PAYLOAD), VALID_RESPONSE)
        self.assertEqual(len(gemini.requests), 1)
        body = gemini.bodies()[0]
        self.assertEqual(body["generationConfig"]["temperature"], 0.0)
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertNotIn("responseSchema", body["generationConfig"])
        self.assertNotIn("responseJsonSchema", body["generationConfig"])
        self.assertEqual(body["systemInstruction"]["parts"], [{"text": load_system_prompt()}])
        self.assertEqual(body["contents"],
                         [{"parts": [{"text": build_human_content(PAYLOAD)}], "role": "user"}])
        self.assertIn("gemini-3.8-flash", str(gemini.requests[0].url))
        self.assertEqual(gemini.requests[0].extensions["timeout"]["read"], 90.0)

    def test_temperature_and_mime_type_sent_without_warnings(self):
        import warnings

        classifier, gemini = self.classifier([(200, ok_body([{"text": VALID_RESPONSE}]))])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            classifier(PAYLOAD)
        self.assertEqual([w for w in caught if issubclass(w.category, UserWarning)], [])
        config_sent = gemini.bodies()[0]["generationConfig"]
        self.assertIn("temperature", config_sent)
        self.assertEqual(config_sent["temperature"], 0.0)
        self.assertIsInstance(config_sent["temperature"], float)
        self.assertEqual(config_sent["responseMimeType"], "application/json")
        self.assertIn("models/gemini-3.8-flash:generateContent", str(gemini.requests[0].url))

    def test_exactly_one_transport_attempt_per_call(self):
        for outcome, expected in (((503, None), ErrorClass.TRANSIENT),
                                  ((429, None), ErrorClass.TRANSIENT),
                                  ((500, None), ErrorClass.TRANSIENT),
                                  ((408, None), ErrorClass.TRANSIENT),
                                  ((400, None), ErrorClass.FATAL),
                                  ((401, None), ErrorClass.FATAL),
                                  ((403, None), ErrorClass.FATAL),
                                  ((404, None), ErrorClass.FATAL),
                                  (httpx.ReadTimeout, ErrorClass.TRANSIENT),
                                  (httpx.ConnectTimeout, ErrorClass.TRANSIENT),
                                  (httpx.ConnectError, ErrorClass.TRANSIENT),
                                  (httpx.ReadError, ErrorClass.TRANSIENT)):
            with self.subTest(outcome=outcome):
                classifier, gemini = self.classifier([outcome, outcome, outcome])
                with self.assertRaises(Exception) as ctx:
                    classifier(PAYLOAD)
                self.assertEqual(len(gemini.requests), 1, "SDK must not retry internally")
                self.assertIs(classify_error(ctx.exception).error_class, expected)

    def test_thinking_parts_are_excluded(self):
        parts = [{"text": "internal reasoning", "thought": True}, {"text": VALID_RESPONSE}]
        classifier, _ = self.classifier([(200, ok_body(parts))])
        self.assertEqual(classifier(PAYLOAD), VALID_RESPONSE)

    def test_split_text_parts_are_joined(self):
        half = len(VALID_RESPONSE) // 2
        parts = [{"text": VALID_RESPONSE[:half]}, {"text": VALID_RESPONSE[half:]}]
        classifier, _ = self.classifier([(200, ok_body(parts))])
        self.assertEqual(validate_model_response(classifier(PAYLOAD))["pneumonia"], "Negative")

    def test_fenced_response_reaches_validator_unchanged(self):
        fenced = f"```json\n{VALID_RESPONSE}\n```"
        classifier, _ = self.classifier([(200, ok_body([{"text": fenced}]))])
        text = classifier(PAYLOAD)
        self.assertEqual(text, fenced)
        with self.assertRaises(ResponseValidationError):
            validate_model_response(text)

    def test_safety_blocked_response_is_empty_and_invalid(self):
        for body in ({"promptFeedback": {"blockReason": "SAFETY"}},
                     {"candidates": [{"finishReason": "SAFETY", "content": {"role": "model"}}]}):
            with self.subTest(body=body):
                classifier, _ = self.classifier([(200, body)])
                text = classifier(PAYLOAD)
                self.assertEqual(text, "")
                with self.assertRaisesRegex(ResponseValidationError, "empty"):
                    validate_model_response(text)
