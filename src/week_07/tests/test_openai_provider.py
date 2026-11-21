"""OpenAI provider: configuration, credentials, client, messages and error policy (offline)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import httpx
import openai
from langchain_core.messages import HumanMessage, SystemMessage

from week_07 import config
from week_07.applications import CANINE_ABDOMEN, CANINE_THORAX, FELINE_THORAX
from week_07.config import ConfigurationError, OpenAIModelConfig
from week_07.error_policy import ErrorClass
from week_07.llm_client import PayloadError
from week_07.openai_client import (
    OpenAIClassifier,
    build_human_content,
    build_messages,
    chat_model_kwargs,
    create_chat_model,
)
from week_07.openai_error_policy import classify_openai_error, openai_status_code
from week_07.prompts.prompt_loader import PromptIntegrityError
from week_07.providers import PROVIDER_SPECS, provider_for
from week_07.tests.app_fixtures import STAND_IN_PROMPT, SyntheticAppRepo
from week_07.tests.support import OfflineTestCase

REPORT = {"findings": "Diffuse bronchial pattern.", "conclusions": "", "recommendations": "Recheck"}
FAKE_KEY = "sk-test-not-a-real-key-0000"
REQUEST = httpx.Request("POST", "https://api.openai.invalid/v1/chat/completions")


def status_error(cls, code):
    return cls("synthetic", response=httpx.Response(code, request=REQUEST), body=None)


class FakeChatModel:
    def __init__(self, content='{"a": "Negative"}'):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.content)


class TestOpenAIConfiguration(OfflineTestCase):
    def test_defaults(self):
        settings = config.load_openai_model_config({}, None)
        self.assertEqual(settings, OpenAIModelConfig("gpt-4.1-mini", 0.0, 90.0, 0))
        self.assertEqual(settings.transport_max_retries, 0)

    def test_environment_overrides_and_validation(self):
        settings = config.load_openai_model_config(
            {"OPENAI_MODEL": " gpt-x ", "OPENAI_TEMPERATURE": "0.5",
             "OPENAI_TIMEOUT_SECONDS": "30"}, None)
        self.assertEqual((settings.model, settings.temperature, settings.timeout_seconds),
                         ("gpt-x", 0.5, 30.0))
        for env in ({"OPENAI_MODEL": " "}, {"OPENAI_TEMPERATURE": "3"},
                    {"OPENAI_TEMPERATURE": "nan"}, {"OPENAI_TIMEOUT_SECONDS": "0"},
                    {"OPENAI_TIMEOUT_SECONDS": "x"}):
            with self.subTest(env=env), self.assertRaises(ConfigurationError):
                config.load_openai_model_config(env, None)

    def test_transport_retries_fixed_and_max_retries_variable_ignored(self):
        with self.assertRaises(ConfigurationError):
            OpenAIModelConfig(transport_max_retries=2)
        settings = config.load_openai_model_config({"OPENAI_MAX_RETRIES": "5"}, None)
        self.assertEqual(settings.transport_max_retries, 0)
        self.assertTrue(config.openai_retry_setting_ignored({"OPENAI_MAX_RETRIES": "5"}, None))
        self.assertFalse(config.openai_retry_setting_ignored({}, None))

    def test_settings_hold_no_credential(self):
        settings = config.validate_openai_runtime_configuration({"OPENAI_API_KEY": FAKE_KEY},
                                                                None)
        self.assertNotIn(FAKE_KEY, repr(settings))
        self.assertNotIn(FAKE_KEY, str(chat_model_kwargs(settings)))


class TestCredentialIndependence(OfflineTestCase):
    def test_openai_does_not_require_google_key(self):
        settings = config.validate_openai_runtime_configuration({"OPENAI_API_KEY": FAKE_KEY},
                                                                None)
        self.assertEqual(settings.model, "gpt-4.1-mini")
        provider_for(FELINE_THORAX).validate_runtime(FELINE_THORAX, {"OPENAI_API_KEY": "k"})

    def test_gemini_does_not_require_openai_key(self):
        settings = config.validate_runtime_configuration({"GOOGLE_API_KEY": "g"}, None)
        self.assertEqual(settings.model, config.DEFAULT_MODEL)
        provider_for(CANINE_THORAX).validate_runtime(CANINE_THORAX, {"GOOGLE_API_KEY": "g"})

    def test_each_provider_requires_only_its_own_key(self):
        with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
            config.validate_openai_runtime_configuration({"GOOGLE_API_KEY": "g"}, None)
        with self.assertRaisesRegex(ConfigurationError, "GOOGLE_API_KEY"):
            config.validate_runtime_configuration({"OPENAI_API_KEY": FAKE_KEY}, None)
        self.assertFalse(PROVIDER_SPECS["openai"].api_key_is_configured({"GOOGLE_API_KEY": "g"}))
        self.assertFalse(PROVIDER_SPECS["gemini"].api_key_is_configured({"OPENAI_API_KEY": "k"}))


class TestProviders(OfflineTestCase):
    def test_provider_per_application(self):
        self.assertEqual(provider_for(CANINE_THORAX).name, "gemini")
        self.assertEqual(provider_for(FELINE_THORAX).name, "openai")
        self.assertEqual(provider_for(CANINE_ABDOMEN, "openai").name, "openai")

    def test_mismatched_provider_refused(self):
        with self.assertRaises(ConfigurationError):
            provider_for(FELINE_THORAX, "gemini")
        with self.assertRaises(ConfigurationError):
            provider_for(CANINE_THORAX, "openai")

    def test_error_classifier_per_provider(self):
        from week_07.error_policy import classify_error

        self.assertIs(PROVIDER_SPECS["gemini"].error_classifier(), classify_error)
        self.assertIs(PROVIDER_SPECS["openai"].error_classifier(), classify_openai_error)

    def test_openai_packages_recorded(self):
        self.assertIn("langchain-openai", PROVIDER_SPECS["openai"].packages)
        self.assertNotIn("google-genai", PROVIDER_SPECS["openai"].packages)


class TestMessages(OfflineTestCase):
    def setUp(self):
        super().setUp()
        self.repo = SyntheticAppRepo("feline_thorax")
        self.addCleanup(self.repo.cleanup)
        self.app = self.repo.app

    def test_system_and_human_messages(self):
        messages = build_messages(self.app, REPORT)
        self.assertIsInstance(messages[0], SystemMessage)
        self.assertIsInstance(messages[1], HumanMessage)
        self.assertEqual(messages[0].content, STAND_IN_PROMPT.strip())
        self.assertEqual(messages[1].content, (
            "Classify the following feline thorax radiology report according to the system "
            "instructions.\n\nFINDINGS:\nDiffuse bronchial pattern.\n\nCONCLUSIONS:\n"
            "[Not provided]\n\nRECOMMENDATIONS:\nRecheck"))

    def test_abdomen_instruction(self):
        self.assertTrue(build_human_content(CANINE_ABDOMEN, REPORT).startswith(
            "Classify the following canine abdomen radiology report"))

    def test_payload_must_be_exactly_three_fields(self):
        for bad in ({**REPORT, "case_id": 1}, {**REPORT, "pneumonia": "Positive"},
                    {"findings": "x", "conclusions": "y"}, ["findings"]):
            with self.subTest(bad=bad), self.assertRaises(PayloadError):
                build_messages(self.app, bad)

    def test_pending_prompt_blocks_message_building(self):
        pending = SyntheticAppRepo("canine_abdomen", prompt="pending")
        self.addCleanup(pending.cleanup)
        with self.assertRaisesRegex(PromptIntegrityError, "pending approval"):
            build_messages(pending.app, REPORT)
        chat = FakeChatModel()
        with self.assertRaises(PromptIntegrityError):
            OpenAIClassifier(pending.app, chat_model=chat)(REPORT)
        self.assertEqual(chat.calls, [])

    def test_registered_applications_send_their_own_approved_prompt(self):
        from week_07.prompts.registry import load_prompt

        for app, region in ((FELINE_THORAX, "feline thorax"),
                            (CANINE_ABDOMEN, "canine abdomen")):
            chat = FakeChatModel()
            OpenAIClassifier(app, OpenAIModelConfig(), chat_model=chat)(REPORT)
            system, human = chat.calls[0]
            with self.subTest(app=app.key):
                self.assertEqual(system.content, load_prompt(app.prompt))
                self.assertEqual(len(system.content), app.prompt.text_length)
                self.assertTrue(human.content.startswith(
                    f"Classify the following {region} radiology report according to the "
                    "system instructions."))
        feline_system = FakeChatModel()
        OpenAIClassifier(FELINE_THORAX, chat_model=feline_system)(REPORT)
        abdomen_system = FakeChatModel()
        OpenAIClassifier(CANINE_ABDOMEN, chat_model=abdomen_system)(REPORT)
        self.assertNotEqual(feline_system.calls[0][0].content,
                            abdomen_system.calls[0][0].content)

    def test_canine_thorax_refused_by_openai_client(self):
        with self.assertRaises(ConfigurationError):
            OpenAIClassifier(CANINE_THORAX)

    def test_classifier_returns_text_and_reuses_model(self):
        chat = FakeChatModel(content='  {"x": 1}  ')
        classifier = OpenAIClassifier(self.app, chat_model=chat)
        self.assertEqual(classifier(REPORT), '{"x": 1}')
        classifier(REPORT)
        self.assertEqual(len(chat.calls), 2)
        sent = " ".join(m.content for m in chat.calls[0])
        self.assertNotIn("case_id", sent)

    def test_block_content_and_no_fence_stripping(self):
        chat = FakeChatModel(content=[{"type": "text", "text": "```json\n{}\n```"}])
        self.assertEqual(OpenAIClassifier(self.app, chat_model=chat)(REPORT), "```json\n{}\n```")


class TestChatOpenAIConstruction(OfflineTestCase):
    def test_kwargs(self):
        self.assertEqual(chat_model_kwargs(OpenAIModelConfig()), {
            "model": "gpt-4.1-mini", "temperature": 0.0, "timeout": 90.0, "max_retries": 0})

    def test_real_client_constructed_offline_with_zero_retries(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": FAKE_KEY}, clear=False):
            model = create_chat_model(FELINE_THORAX, OpenAIModelConfig(),
                                      environ={"OPENAI_API_KEY": FAKE_KEY})
        self.assertEqual(model.max_retries, 0)
        self.assertEqual(model.model_name, "gpt-4.1-mini")
        self.assertEqual(model.temperature, 0.0)
        self.assertNotIn(FAKE_KEY, repr(model))

    def test_missing_key_refused_before_construction(self):
        with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
            create_chat_model(FELINE_THORAX, OpenAIModelConfig(), environ={})
        with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
            create_chat_model(FELINE_THORAX, None, environ={"GOOGLE_API_KEY": "g"})


class TestOpenAIErrorPolicy(OfflineTestCase):
    def test_fatal_status_codes(self):
        for cls, code in ((openai.BadRequestError, 400), (openai.AuthenticationError, 401),
                          (openai.PermissionDeniedError, 403), (openai.NotFoundError, 404)):
            with self.subTest(code=code):
                decision = classify_openai_error(status_error(cls, code))
                self.assertEqual((decision.error_class, decision.status_code),
                                 (ErrorClass.FATAL, code))

    def test_transient_status_codes(self):
        for code in (408, 429, 500, 502, 503, 504):
            cls = openai.RateLimitError if code == 429 else openai.InternalServerError
            with self.subTest(code=code):
                decision = classify_openai_error(status_error(cls, code))
                self.assertEqual(decision.error_class, ErrorClass.TRANSIENT)
                self.assertTrue(decision.needs_backoff)

    def test_timeouts_and_connection_errors_transient(self):
        for exc in (openai.APITimeoutError(request=REQUEST),
                    openai.APIConnectionError(request=REQUEST),
                    httpx.ReadTimeout("t"), httpx.ConnectError("c")):
            with self.subTest(exc=type(exc).__name__):
                self.assertEqual(classify_openai_error(exc).error_class, ErrorClass.TRANSIENT)

    def test_other_errors_retryable(self):
        from week_07.response_validator import ResponseValidationError

        for exc in (status_error(openai.UnprocessableEntityError, 422),
                    ResponseValidationError("bad"), ValueError("x")):
            with self.subTest(exc=type(exc).__name__):
                self.assertEqual(classify_openai_error(exc).error_class, ErrorClass.RETRYABLE)

    def test_configuration_error_fatal_and_chain_walked(self):
        self.assertEqual(classify_openai_error(ConfigurationError("x")).error_class,
                         ErrorClass.FATAL)
        try:
            try:
                raise status_error(openai.AuthenticationError, 401)
            except openai.APIError as inner:
                raise RuntimeError("wrapped") from inner
        except RuntimeError as outer:
            self.assertEqual(openai_status_code(outer), 401)
            self.assertEqual(classify_openai_error(outer).error_class, ErrorClass.FATAL)

    def test_message_text_is_never_parsed(self):
        self.assertEqual(classify_openai_error(RuntimeError("HTTP 401 Unauthorized 429")).
                         error_class, ErrorClass.RETRYABLE)


class TestNoKeyLeakage(OfflineTestCase):
    def test_key_never_in_settings_kwargs_or_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text(f"OPENAI_API_KEY={FAKE_KEY}\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OPENAI_API_KEY", None)
                self.assertTrue(config.openai_api_key_is_configured(None, env))
                settings = config.load_openai_model_config(None, env)
                os.environ.pop("OPENAI_API_KEY", None)
        for text in (repr(settings), str(chat_model_kwargs(settings))):
            self.assertNotIn(FAKE_KEY, text)
