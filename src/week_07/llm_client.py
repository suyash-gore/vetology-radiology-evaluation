"""LangChain/Google Gemini client for classifying one canine thorax report.

Message construction is identical to Week 5 (``src/week_05/llm_client.py``),
which reproduces Week 4 exactly:

* System message: the verified V1.3 prompt text (stripped).
* Human message: a fixed instruction followed by the three original radiologist
  report sections; an empty section is rendered as ``[Not provided]``.

Only ``findings``, ``conclusions`` and ``recommendations`` are accepted. CaseID,
reference labels and AI-generated report fields cannot reach the model because
any payload with other keys is rejected.

Gemini-specific (approved decisions O2, O3, O7), verified offline against
langchain-google-genai 4.4.2 / google-genai 2.34.0:

* ``ChatGoogleGenerativeAI`` with ``response_mime_type="application/json"`` and
  no response schema. ``GOOGLE_API_KEY`` is read by the SDK from the process
  environment (it takes precedence over ``GEMINI_API_KEY``); it is never passed
  through or stored here.
* Transport attempts: LangChain passes ``max_retries`` straight to
  ``google.genai.types.HttpRetryOptions(attempts=...)``, i.e. it is the TOTAL
  number of transport attempts. ``max_retries=1`` therefore means exactly one
  attempt. (``0`` also gives one attempt in google-genai 2.34.0, but LangChain
  documents ``0`` as "use the Google default" for some SDK versions, so ``1`` is
  used.) LangChain's own default is 6 — it must always be set explicitly.
* Sampling: ``temperature`` is always passed to the constructor. Offline
  request-payload tests verify that the ``gemini-3.8-flash`` request carries
  ``temperature: 0.0`` and ``responseMimeType: application/json`` and that no
  warning is emitted (no private LangChain function is consulted).
* Response content may be a string or a list of content blocks (text blocks,
  thinking blocks, plain strings). ``response_text`` keeps only text, in order.
  Markdown fences are NOT stripped and invalid JSON is NOT repaired: the strict
  Week 5 validator decides.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final, Protocol

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from week_07 import config
from week_07.config import GeminiModelConfig
from week_07.prompts.prompt_loader import load_system_prompt

REPORT_FIELDS: Final[tuple[str, ...]] = ("findings", "conclusions", "recommendations")
NOT_PROVIDED: Final[str] = "[Not provided]"
HUMAN_INSTRUCTION: Final[str] = (
    "Classify the following canine thorax radiology report according "
    "to the system instructions."
)
# Value for LangChain's ``max_retries`` = google-genai ``HttpRetryOptions.attempts``.
LANGCHAIN_MAX_RETRIES_VALUE: Final[int] = config.TRANSPORT_ATTEMPTS


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
    """Return the human message text, byte-for-byte as in Weeks 4 and 5."""
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


def chat_model_kwargs(settings: GeminiModelConfig) -> dict[str, Any]:
    """Constructor arguments for ``ChatGoogleGenerativeAI`` (no credential, no schema)."""
    return {
        "model": settings.model,
        "temperature": settings.temperature,
        "timeout": settings.timeout_seconds,
        "max_retries": LANGCHAIN_MAX_RETRIES_VALUE,
        "response_mime_type": settings.response_mime_type,
    }


def create_chat_model(
    settings: GeminiModelConfig | None = None,
    environ: Mapping[str, str] | None = None,
) -> ChatModel:
    """Create one ``ChatGoogleGenerativeAI`` client after validating configuration.

    ``GOOGLE_API_KEY`` must be present; its value is read by the SDK from the
    process environment and is never handled here. ``environ`` is only used by
    tests to supply the variables for validation.
    """
    if settings is None:
        settings = config.validate_runtime_configuration(environ, config.ENV_FILE)
    else:
        config.require_api_key(environ, config.ENV_FILE)

    from langchain_google_genai import ChatGoogleGenerativeAI  # imported only when needed

    return ChatGoogleGenerativeAI(**chat_model_kwargs(settings))


def response_text(content: Any) -> str:
    """Return the model's text output; no fence stripping, no JSON repair.

    * ``str``: stripped (as in Week 5).
    * ``list``: concatenation, in order, of plain-string items and ``text`` of
      ``{"type": "text"}`` blocks; thinking and other non-text blocks are ignored.
      The result is stripped.
    * anything else: ``str(content).strip()`` (as in Week 5).
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        pieces: list[str] = []
        for block in content:
            if isinstance(block, str):
                pieces.append(block)
            elif (isinstance(block, Mapping) and block.get("type") == "text"
                  and isinstance(block.get("text"), str)):
                pieces.append(block["text"])
        return "".join(pieces).strip()
    return str(content).strip()


class GeminiClassifier:
    """Callable classifier: report payload -> raw model response text.

    The chat model is created on first use and then reused for every case.
    A pre-built ``chat_model`` may be injected (e.g. a fake in offline tests).
    Parsing and validation of the response belong to ``response_validator``;
    error classification belongs to ``error_policy``.
    """

    def __init__(
        self,
        settings: GeminiModelConfig | None = None,
        chat_model: ChatModel | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self._settings = settings
        self._chat_model = chat_model
        self._environ = environ

    @property
    def chat_model(self) -> ChatModel:
        if self._chat_model is None:
            self._chat_model = create_chat_model(self._settings, self._environ)
        return self._chat_model

    def __call__(self, report: Mapping[str, Any]) -> str:
        messages = build_messages(report)  # validates the payload before any client use
        response = self.chat_model.invoke(messages)
        return response_text(response.content)
