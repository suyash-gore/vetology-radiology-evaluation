"""Offline tests for message construction and the OpenAI client wrapper.

No test sends a request to OpenAI: chat models are either fakes or real
``ChatOpenAI`` objects that are constructed (with a fake key) but never invoked.
"""
from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import HumanMessage, SystemMessage

from week_05 import llm_client
from week_05.config import ConfigurationError, ModelConfig
from week_05.llm_client import (
    NOT_PROVIDED,
    OpenAIClassifier,
    PayloadError,
    build_human_content,
    build_messages,
    chat_model_kwargs,
    create_chat_model,
    response_text,
)
from week_05.prompts.prompt_loader import load_system_prompt

FAKE_KEY = "sk-test-not-a-real-key-0123456789"

SAMPLE_PAYLOADS = {
    "all fields": {
        "findings": "Diffuse bronchial pattern.",
        "conclusions": "Bronchitis suspected.",
        "recommendations": "Recheck in 2 weeks.",
    },
    "all empty": {"findings": "", "conclusions": "", "recommendations": ""},
    "only findings": {"findings": "Mild cardiomegaly.", "conclusions": "", "recommendations": ""},
    "only recommendations": {"findings": "", "conclusions": "", "recommendations": "CT."},
    "None values": {"findings": None, "conclusions": "Normal thorax.", "recommendations": None},
    "multiline and unicode": {
        "findings": "Line 1\nLine 2 — “quoted” {braces} 5 mm",
        "conclusions": "Possible pneumonia.\n\nSecond paragraph.",
        "recommendations": "Whitespace kept as given:  ",
    },
}

EXPECTED_ALL_FIELDS = (
    "Classify the following canine thorax radiology report according to the "
    "system instructions.\n\n"
    "FINDINGS:\nDiffuse bronchial pattern.\n\n"
    "CONCLUSIONS:\nBronchitis suspected.\n\n"
    "RECOMMENDATIONS:\nRecheck in 2 weeks."
)


def week4_messages(payload):
    from week_04.llm_client import build_case_messages

    return build_case_messages(payload)


class TestHumanMessage(unittest.TestCase):
    def test_exact_text_for_known_payload(self):
        self.assertEqual(build_human_content(SAMPLE_PAYLOADS["all fields"]), EXPECTED_ALL_FIELDS)

    def test_empty_and_none_fields_become_not_provided(self):
        self.assertEqual(NOT_PROVIDED, "[Not provided]")
        content = build_human_content(SAMPLE_PAYLOADS["all empty"])
        self.assertEqual(
            content,
            "Classify the following canine thorax radiology report according to the "
            "system instructions.\n\nFINDINGS:\n[Not provided]\n\n"
            "CONCLUSIONS:\n[Not provided]\n\nRECOMMENDATIONS:\n[Not provided]",
        )
        content = build_human_content(SAMPLE_PAYLOADS["None values"])
        self.assertIn("FINDINGS:\n[Not provided]\n\n", content)
        self.assertIn("CONCLUSIONS:\nNormal thorax.\n\n", content)
        self.assertTrue(content.endswith("RECOMMENDATIONS:\n[Not provided]"))

    def test_text_is_not_altered(self):
        payload = SAMPLE_PAYLOADS["multiline and unicode"]
        content = build_human_content(payload)
        for value in payload.values():
            self.assertIn(value, content)


class TestWeek4Parity(unittest.TestCase):
    def test_messages_identical_to_week4(self):
        for label, payload in SAMPLE_PAYLOADS.items():
            with self.subTest(payload=label):
                expected = week4_messages(payload)
                actual = build_messages(payload)
                self.assertEqual([type(m) for m in actual], [SystemMessage, HumanMessage])
                self.assertEqual([type(m) for m in actual], [type(m) for m in expected])
                self.assertEqual(
                    [m.content.encode("utf-8") for m in actual],
                    [m.content.encode("utf-8") for m in expected],
                )
                self.assertEqual(actual, expected)

    def test_system_message_is_verified_prompt(self):
        messages = build_messages(SAMPLE_PAYLOADS["all fields"])
        self.assertEqual(messages[0].content, load_system_prompt())

    def test_week4_rejects_the_same_invalid_payloads(self):
        for payload in ({"findings": "x"},
                        {"findings": "", "conclusions": "", "recommendations": "", "case_id": 1}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    week4_messages(payload)
                with self.assertRaises(ValueError):
                    build_messages(payload)

    def test_client_constructor_arguments_match_week4(self):
        captured = {}

        def capture(name):
            def fake_chat_openai(**kwargs):
                captured[name] = kwargs
                return SimpleNamespace()
            return fake_chat_openai

        env = {"OPENAI_API_KEY": FAKE_KEY}
        with patch.dict(os.environ, env, clear=True), \
                patch("week_04.llm_client.load_dotenv"), \
                patch("week_05.config.load_dotenv"), \
                patch("week_04.llm_client.ChatOpenAI", side_effect=capture("week4")), \
                patch("langchain_openai.ChatOpenAI", side_effect=capture("week5")):
            from week_04.llm_client import create_chat_model as week4_create

            week4_create()
            create_chat_model()
        self.assertEqual(captured["week5"], captured["week4"])
        self.assertEqual(
            captured["week5"],
            {"model": "gpt-4.1-mini", "temperature": 0.0, "timeout": 90.0, "max_retries": 2},
        )

    def test_request_payload_identical_to_week4(self):
        """Compare the actual OpenAI request body LangChain would send (never sent)."""
        env = {"OPENAI_API_KEY": FAKE_KEY}
        with patch.dict(os.environ, env, clear=True), \
                patch("week_04.llm_client.load_dotenv"), \
                patch("week_05.config.load_dotenv"):
            from week_04.llm_client import create_chat_model as week4_create

            week4_model = week4_create()
            week5_model = create_chat_model()
            if not hasattr(week5_model, "_get_request_payload"):
                self.skipTest("langchain-openai does not expose _get_request_payload")
            for label, payload in SAMPLE_PAYLOADS.items():
                with self.subTest(payload=label):
                    expected = week4_model._get_request_payload(week4_messages(payload))
                    actual = week5_model._get_request_payload(build_messages(payload))
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual["model"], "gpt-4.1-mini")
                    self.assertEqual(actual["temperature"], 0.0)
                    self.assertEqual([m["role"] for m in actual["messages"]],
                                     ["system", "user"])
            self.assertEqual(week5_model.request_timeout, week4_model.request_timeout)
            self.assertEqual(week5_model.max_retries, week4_model.max_retries)


class TestPayloadRestriction(unittest.TestCase):
    BASE = {"findings": "f", "conclusions": "c", "recommendations": "r"}

    def test_missing_fields_rejected(self):
        for missing in ("findings", "conclusions", "recommendations"):
            payload = {k: v for k, v in self.BASE.items() if k != missing}
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(PayloadError, "exactly findings"):
                    build_messages(payload)
        with self.assertRaises(PayloadError):
            build_messages({})

    def test_forbidden_extra_fields_rejected(self):
        forbidden = [
            "case_id", "CaseID", "pneumonia", "labels", "gold_labels", "ground_truth",
            "Findings (AI report)", "ai_findings", "original_radiologist", "Abnormal/Normal",
        ]
        for key in forbidden:
            with self.subTest(key=key):
                with self.assertRaises(PayloadError):
                    build_messages({**self.BASE, key: "leak"})

    def test_wrong_key_spelling_rejected(self):
        with self.assertRaises(PayloadError):
            build_messages({"Findings": "f", "Conclusions": "c", "Recommendations": "r"})

    def test_non_mapping_rejected(self):
        for value in (None, "findings", ["findings", "conclusions", "recommendations"]):
            with self.subTest(value=value):
                with self.assertRaises(PayloadError):
                    build_messages(value)

    def test_payload_error_is_a_value_error(self):
        self.assertTrue(issubclass(PayloadError, ValueError))  # same type family as Week 4


class FakeChatModel:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.content)


class TestClassifier(unittest.TestCase):
    def test_returns_stripped_text_and_sends_built_messages(self):
        fake = FakeChatModel('  {"a": 1}\n')
        classifier = OpenAIClassifier(chat_model=fake)
        payload = SAMPLE_PAYLOADS["all fields"]
        self.assertEqual(classifier(payload), '{"a": 1}')
        self.assertEqual(fake.calls, [build_messages(payload)])

    def test_non_string_content_normalised_like_week4(self):
        self.assertEqual(response_text("  x  "), "x")
        self.assertEqual(response_text([{"type": "text", "text": "x"}]),
                         str([{"type": "text", "text": "x"}]))

    def test_single_client_reused_across_cases(self):
        constructed = []

        def factory(config=None):
            constructed.append(config)
            return FakeChatModel("{}")

        with patch.object(llm_client, "create_chat_model", side_effect=factory):
            classifier = OpenAIClassifier()
            for label in ("all fields", "only findings", "all empty"):
                classifier(SAMPLE_PAYLOADS[label])
        self.assertEqual(len(constructed), 1)
        self.assertEqual(len(classifier.chat_model.calls), 3)

    def test_explicit_config_is_passed_to_client_factory(self):
        cfg = ModelConfig(model="gpt-4.1-mini", temperature=0.0, timeout_seconds=90.0,
                          max_retries=2)
        with patch.object(llm_client, "create_chat_model",
                          return_value=FakeChatModel("{}")) as factory:
            OpenAIClassifier(config=cfg)(SAMPLE_PAYLOADS["all fields"])
        factory.assert_called_once_with(cfg)

    def test_invalid_payload_rejected_before_client_creation(self):
        with patch.object(llm_client, "create_chat_model") as factory:
            with self.assertRaises(PayloadError):
                OpenAIClassifier()({"findings": "f", "case_id": 1})
        factory.assert_not_called()


class TestClientConfigurationHandling(unittest.TestCase):
    def test_missing_key_fails_before_client_construction(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch("week_05.config.load_dotenv"), \
                patch("langchain_openai.ChatOpenAI") as chat_openai:
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
                create_chat_model()
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_API_KEY"):
                create_chat_model(ModelConfig())
            with self.assertRaises(ConfigurationError):
                OpenAIClassifier()(SAMPLE_PAYLOADS["all fields"])
        chat_openai.assert_not_called()

    def test_invalid_environment_setting_fails_before_client_construction(self):
        env = {"OPENAI_API_KEY": FAKE_KEY, "OPENAI_TIMEOUT_SECONDS": "-1"}
        with patch.dict(os.environ, env, clear=True), \
                patch("week_05.config.load_dotenv"), \
                patch("langchain_openai.ChatOpenAI") as chat_openai:
            with self.assertRaisesRegex(ConfigurationError, "OPENAI_TIMEOUT_SECONDS"):
                create_chat_model()
        chat_openai.assert_not_called()

    def test_kwargs_mapping(self):
        cfg = ModelConfig(model="m", temperature=0.5, timeout_seconds=30.0, max_retries=1)
        self.assertEqual(chat_model_kwargs(cfg),
                         {"model": "m", "temperature": 0.5, "timeout": 30.0, "max_retries": 1})

    def test_key_not_passed_explicitly_to_client(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": FAKE_KEY}, clear=True), \
                patch("week_05.config.load_dotenv"), \
                patch("langchain_openai.ChatOpenAI") as chat_openai:
            create_chat_model()
        kwargs = chat_openai.call_args.kwargs
        self.assertNotIn("api_key", kwargs)
        self.assertNotIn(FAKE_KEY, repr(kwargs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
