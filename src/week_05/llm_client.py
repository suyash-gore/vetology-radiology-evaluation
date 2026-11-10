"""LangChain/OpenAI client for classifying one canine thorax report.

Message construction reproduces Week 4 (``src/week_04/llm_client.py``) exactly:

* System message: the verified V1.3 prompt text (stripped).
* Human message: a fixed instruction followed by the three original radiologist
  report sections; an empty section is rendered as ``[Not provided]``.

Only ``findings``, ``conclusions`` and ``recommendations`` are accepted. CaseID,
reference labels and AI-generated report fields cannot reach the model because
any payload with other keys is rejected.

Difference from Week 4 (approved): one ``ChatOpenAI`` instance is created per
``OpenAIClassifier`` and reused for every case, with identical constructor
arguments, instead of constructing a new client for each case. The prompt is
also read once per process. Neither changes the request sent to OpenAI.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final, Protocol

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from week_05.config import ModelConfig, require_api_key, validate_runtime_configuration
from week_05.prompts.prompt_loader import load_system_prompt

REPORT_FIELDS: Final[tuple[str, ...]] = ("findings", "conclusions", "recommendations")
NOT_PROVIDED: Final[str] = "[Not provided]"
HUMAN_INSTRUCTION: Final[str] = (
    "Classify the following canine thorax radiology report according "
    "to the system instructions."
)


class PayloadError(ValueError):
    """Raised when an LLM payload is not exactly the three original report fields."""


class ChatModel(Protocol):
    """The subset of the LangChain chat-model interface used here."""

    def invoke(self, messages: list[BaseMessage]) -> Any: ...


def validate_payload(report: Mapping[str, Any]) -> None:
    """Require exactly the keys findings, conclusions and recommendations."""
    if not isinstance(report, Mapping):
        raise PayloadError(
            f"LLM report must be a mapping of report fields, not {type(report).__name__}."
        )
    if set(report) != set(REPORT_FIELDS):
        received = sorted(map(str, report))
        raise PayloadError(
            "LLM report must contain exactly findings, conclusions, and "
            f"recommendations; received {received}."
        )


def build_human_content(report: Mapping[str, Any]) -> str:
    """Return the human message text, byte-for-byte as in Week 4."""
    validate_payload(report)
    return (
        f"{HUMAN_INSTRUCTION}\n\n"
        f"FINDINGS:\n{report['findings'] or NOT_PROVIDED}\n\n"
        f"CONCLUSIONS:\n{report['conclusions'] or NOT_PROVIDED}\n\n"
        f"RECOMMENDATIONS:\n{report['recommendations'] or NOT_PROVIDED}"
    )


def build_messages(report: Mapping[str, Any]) -> list[BaseMessage]:
    """Build the [SystemMessage, HumanMessage] pair for one case."""
    human_content = build_human_content(report)
    return [
        SystemMessage(content=load_system_prompt()),
        HumanMessage(content=human_content),
    ]


def chat_model_kwargs(config: ModelConfig) -> dict[str, Any]:
    """Constructor arguments for ``ChatOpenAI`` (same keywords as Week 4)."""
    return {
        "model": config.model,
        "temperature": config.temperature,
        "timeout": config.timeout_seconds,
        "max_retries": config.max_retries,
    }


def create_chat_model(config: ModelConfig | None = None) -> ChatModel:
    """Create one ``ChatOpenAI`` client after validating credentials and settings.

    ``OPENAI_API_KEY`` is read by LangChain from the environment; it is never
    passed through or stored by this module.
    """
    if config is None:
        settings = validate_runtime_configuration()  # key + environment settings
    else:
        require_api_key()  # explicit settings supplied; still fail fast on the key
        settings = config

    from langchain_openai import ChatOpenAI  # imported only when a client is needed

    return ChatOpenAI(**chat_model_kwargs(settings))


def response_text(content: Any) -> str:
    """Normalise response content exactly as Week 4 does."""
    if isinstance(content, str):
        return content.strip()
    # Preserve readable text if a provider returns a list of content blocks.
    return str(content).strip()


class OpenAIClassifier:
    """Callable classifier: report payload -> raw model response text.

    The chat model is created on first use and then reused for every case.
    A pre-built ``chat_model`` may be injected (e.g. a fake in offline tests).
    Parsing and validation of the response belong to ``response_validator``.
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        chat_model: ChatModel | None = None,
    ) -> None:
        self._config = config
        self._chat_model = chat_model

    @property
    def chat_model(self) -> ChatModel:
        if self._chat_model is None:
            self._chat_model = create_chat_model(self._config)
        return self._chat_model

    def __call__(self, report: Mapping[str, Any]) -> str:
        messages = build_messages(report)  # validates the payload before any client use
        response = self.chat_model.invoke(messages)
        return response_text(response.content)
