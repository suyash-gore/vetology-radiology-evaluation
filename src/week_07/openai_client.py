"""LangChain/OpenAI client for the Feline Thorax and Canine Abdomen applications.

Follows the Week 5 integration (``src/week_05/llm_client.py``: one
``ChatOpenAI`` per classifier, reused for every case, created lazily) with the
Week 7 rules:

* System message: the application's VERIFIED prompt (``prompts.registry``); a
  pending prompt cannot be loaded, so no request can be built for it.
* Human message: the Week 4/5 format with the application's region in the
  instruction ("Classify the following feline thorax radiology report ...");
  an empty section is rendered as ``[Not provided]``.
* Payload: exactly ``findings``, ``conclusions`` and ``recommendations``
  (``llm_client.validate_payload``); CaseID, reference labels and AI-generated
  report fields cannot reach the model.
* Transport: ``max_retries=0`` (one transport attempt per application attempt);
  the batch ``RetryPolicy`` is the only retry system.
* No response-format/JSON mode (as Week 5); the strict validator decides.
  Response text is extracted with ``llm_client.response_text`` (no fence
  stripping, no repair).

``OPENAI_API_KEY`` is read by the SDK from the process environment; it is never
passed through, stored, logged or written by this module.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from week_07 import config
from week_07.applications import OPENAI, ApplicationSpec
from week_07.config import ConfigurationError, OpenAIModelConfig
from week_07.llm_client import NOT_PROVIDED, ChatModel, response_text, validate_payload
from week_07.prompts.registry import load_prompt


def _require_openai_application(app: ApplicationSpec) -> ApplicationSpec:
    if not isinstance(app, ApplicationSpec):
        raise TypeError("app must be an ApplicationSpec.")
    if app.provider != OPENAI:
        raise ConfigurationError(
            f"{app.key} uses provider {app.provider!r}; the OpenAI client is not used for it."
        )
    return app


def build_human_content(app: ApplicationSpec, report: Mapping[str, Any]) -> str:
    """Human message text: Week 4/5 layout with the application's instruction."""
    validate_payload(report)
    return (
        f"{app.human_instruction}\n\n"
        f"FINDINGS:\n{report['findings'] or NOT_PROVIDED}\n\n"
        f"CONCLUSIONS:\n{report['conclusions'] or NOT_PROVIDED}\n\n"
        f"RECOMMENDATIONS:\n{report['recommendations'] or NOT_PROVIDED}"
    )


def build_messages(app: ApplicationSpec, report: Mapping[str, Any]) -> list[BaseMessage]:
    """[SystemMessage(verified prompt), HumanMessage(report)] for one case."""
    _require_openai_application(app)
    human_content = build_human_content(app, report)  # payload checked before the prompt
    return [SystemMessage(content=load_prompt(app.prompt)),
            HumanMessage(content=human_content)]


def chat_model_kwargs(settings: OpenAIModelConfig) -> dict[str, Any]:
    """Constructor arguments for ``ChatOpenAI`` (no credential)."""
    return {
        "model": settings.model,
        "temperature": settings.temperature,
        "timeout": settings.timeout_seconds,
        "max_retries": settings.transport_max_retries,
    }


def create_chat_model(
    app: ApplicationSpec,
    settings: OpenAIModelConfig | None = None,
    environ: Mapping[str, str] | None = None,
) -> ChatModel:
    """Create one ``ChatOpenAI`` after validating the key and settings."""
    _require_openai_application(app)
    if settings is None:
        settings = config.validate_openai_runtime_configuration(
            environ, config.ENV_FILE, default_model=app.default_model)
    else:
        config.require_openai_api_key(environ, config.ENV_FILE)

    from langchain_openai import ChatOpenAI  # imported only when a client is needed

    return ChatOpenAI(**chat_model_kwargs(settings))


class OpenAIClassifier:
    """Callable classifier for one OpenAI application: report payload -> raw text."""

    def __init__(
        self,
        app: ApplicationSpec,
        settings: OpenAIModelConfig | None = None,
        chat_model: ChatModel | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.app = _require_openai_application(app)
        self._settings = settings
        self._chat_model = chat_model
        self._environ = environ

    @property
    def chat_model(self) -> ChatModel:
        if self._chat_model is None:
            self._chat_model = create_chat_model(self.app, self._settings, self._environ)
        return self._chat_model

    def __call__(self, report: Mapping[str, Any]) -> str:
        messages = build_messages(self.app, report)  # payload + prompt checked first
        response = self.chat_model.invoke(messages)
        return response_text(response.content)
