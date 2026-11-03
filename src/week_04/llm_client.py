"""Vetology Week 4 — Block 3: LangChain/OpenAI client.

This module sends one original canine-thorax radiology report to OpenAI.
It deliberately returns raw model text; strict JSON/schema validation belongs
to Block 4. Gold Standard labels are never accepted by this module.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from week_04.prompts.canine_thorax_prompt import load_system_prompt


@dataclass(frozen=True)
class ModelConfig:
    model: str
    temperature: float = 0.0
    timeout_seconds: float = 90.0
    max_retries: int = 2


def load_model_config() -> ModelConfig:
    """Read model settings from environment; never hard-code credentials."""
    load_dotenv()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    if not model:
        raise ValueError("OPENAI_MODEL is empty. Set a valid model name in .env.")
    return ModelConfig(
        model=model,
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")),
        timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "90")),
        max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "2")),
    )


def create_chat_model(config: ModelConfig | None = None) -> ChatOpenAI:
    """Create the LangChain ChatOpenAI client using OPENAI_API_KEY from .env."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise EnvironmentError(
            "OPENAI_API_KEY was not found. Add it to the repository-root .env "
            "file. Do not paste the key into source code or commit the .env file."
        )

    settings = config or load_model_config()
    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
    )


def build_case_messages(report: dict[str, str]) -> list:
    """Build messages from ONLY original report fields.

    CaseID is retained by the data loader for tracking but is not sent to the
    model. Gold Standard labels and AI-generated reports are not accepted.
    """
    required = ("findings", "conclusions", "recommendations")
    if set(report) != set(required):
        raise ValueError(
            "LLM report must contain exactly findings, conclusions, "
            "and recommendations."
        )

    system_prompt = load_system_prompt()
    human_content = (
        "Classify the following canine thorax radiology report according "
        "to the system instructions.\n\n"
        f"FINDINGS:\n{report['findings'] or '[Not provided]'}\n\n"
        f"CONCLUSIONS:\n{report['conclusions'] or '[Not provided]'}\n\n"
        f"RECOMMENDATIONS:\n{report['recommendations'] or '[Not provided]'}"
    )
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_content),
    ]


def classify_one_case(report: dict[str, str], model: ChatOpenAI | None = None) -> str:
    """Invoke the model for one case and return its raw response text.

    Parsing, exact-key validation, retries for malformed JSON, and evaluation
    are intentionally deferred to later blocks.
    """
    llm = model or create_chat_model()
    response = llm.invoke(build_case_messages(report))
    content = response.content

    if isinstance(content, str):
        return content.strip()
    # Preserve readable text if a provider returns a list of content blocks.
    return str(content).strip()
