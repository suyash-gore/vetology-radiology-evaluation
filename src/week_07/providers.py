"""Provider registry: settings, credentials, classifier and error policy per provider.

* ``gemini`` — Canine Thorax: ``GeminiModelConfig``/``GOOGLE_API_KEY``,
  ``GeminiClassifier``, ``error_policy.classify_error`` (all unchanged). The
  Canine Thorax batch path (``run_workflow_batch``) keeps using those directly.
* ``openai`` — Feline Thorax and Canine Abdomen: ``OpenAIModelConfig``/
  ``OPENAI_API_KEY``, ``OpenAIClassifier``, ``classify_openai_error``.

Each provider only reads its own environment variables: an OpenAI application
never requires ``GOOGLE_API_KEY`` and Canine Thorax never requires
``OPENAI_API_KEY``. No provider stores a credential.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final

from week_07 import config
from week_07.applications import GEMINI, OPENAI, ApplicationSpec
from week_07.config import ConfigurationError, RetryPolicy


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    label: str                      # recorded in the run manifest identity
    short_label: str                # used in the evaluation workbook model record
    api_key_var: str
    packages: tuple[str, ...]       # versions recorded per run in the manifest

    def load_settings(self, app: ApplicationSpec,
                      environ: Mapping[str, str] | None = None) -> Any:
        if self.name == GEMINI:
            return config.load_model_config(environ, config.ENV_FILE)
        return config.load_openai_model_config(environ, config.ENV_FILE,
                                               default_model=app.default_model)

    def validate_runtime(self, app: ApplicationSpec,
                         environ: Mapping[str, str] | None = None) -> Any:
        if self.name == GEMINI:
            return config.validate_runtime_configuration(environ, config.ENV_FILE)
        return config.validate_openai_runtime_configuration(
            environ, config.ENV_FILE, default_model=app.default_model)

    def api_key_is_configured(self, environ: Mapping[str, str] | None = None) -> bool:
        if self.name == GEMINI:
            return config.api_key_is_configured(environ, config.ENV_FILE)
        return config.openai_api_key_is_configured(environ, config.ENV_FILE)

    def make_classifier(self, app: ApplicationSpec, settings: Any) -> Callable[[Any], str]:
        if self.name == GEMINI:
            from week_07.llm_client import GeminiClassifier

            return GeminiClassifier(settings)
        from week_07.openai_client import OpenAIClassifier

        return OpenAIClassifier(app, settings)

    def error_classifier(self) -> Callable[[BaseException, RetryPolicy], Any]:
        if self.name == GEMINI:
            from week_07.error_policy import classify_error

            return classify_error
        from week_07.openai_error_policy import classify_openai_error

        return classify_openai_error


PROVIDER_SPECS: Final[Mapping[str, ProviderSpec]] = MappingProxyType({
    GEMINI: ProviderSpec(
        name=GEMINI,
        label="Google Gemini via langchain-google-genai ChatGoogleGenerativeAI",
        short_label="Google Gemini",
        api_key_var=config.API_KEY_VAR,
        packages=("langchain-google-genai", "google-genai", "langchain-core", "httpx",
                  "openpyxl"),
    ),
    OPENAI: ProviderSpec(
        name=OPENAI,
        label="OpenAI via langchain-openai ChatOpenAI",
        short_label="OpenAI",
        api_key_var=config.OPENAI_API_KEY_VAR,
        packages=("langchain-openai", "openai", "langchain-core", "httpx", "openpyxl"),
    ),
})


def provider_for(app: ApplicationSpec, requested: str | None = None) -> ProviderSpec:
    """The application's provider; an explicitly requested different provider is refused."""
    if requested is not None and requested != app.provider:
        raise ConfigurationError(
            f"{app.key} uses provider {app.provider!r}; --provider {requested!r} is not "
            "supported for it."
        )
    try:
        return PROVIDER_SPECS[app.provider]
    except KeyError:  # pragma: no cover - ApplicationSpec validates the provider
        raise ConfigurationError(f"Unknown provider {app.provider!r}.") from None
