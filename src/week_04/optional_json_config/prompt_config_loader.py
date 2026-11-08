"""JSON prompt configuration loader for the Week 4 optional assignment.

This module only reads and validates a local JSON configuration.
It does not make API calls or execute an LLM.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "canine_thorax_v1_3.json"


def load_prompt_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and minimally validate the prompt configuration JSON."""
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Prompt configuration file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON configuration in {path}: {exc}") from exc

    required_fields = ("prompt_name", "version", "condition_keys", "valid_labels", "system_prompt")
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValueError(
            "Prompt configuration is missing required fields: "
            + ", ".join(missing_fields)
        )

    if not isinstance(config["system_prompt"], str) or not config["system_prompt"].strip():
        raise ValueError("'system_prompt' must be a non-empty string.")

    if config["version"] != "V1.3":
        raise ValueError(
            f"Expected prompt version 'V1.3', received {config['version']!r}."
        )

    if not isinstance(config["condition_keys"], list) or len(config["condition_keys"]) != 20:
        raise ValueError("'condition_keys' must be a list containing exactly 20 items.")

    if config["valid_labels"] != ["Positive", "Negative"]:
        raise ValueError("'valid_labels' must be ['Positive', 'Negative'].")

    return config


def load_system_prompt(config_path: str | Path = DEFAULT_CONFIG_PATH) -> str:
    """Return the system prompt text from the JSON configuration."""
    return load_prompt_config(config_path)["system_prompt"]
