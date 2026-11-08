"""Offline unit tests for the JSON prompt configuration loader."""
import json
import tempfile
import unittest
from pathlib import Path

from prompt_config_loader import load_prompt_config, load_system_prompt


class TestPromptConfigLoader(unittest.TestCase):
    def test_loads_v13_configuration(self):
        config = load_prompt_config()
        self.assertEqual(config["version"], "V1.3")
        self.assertEqual(len(config["condition_keys"]), 20)
        self.assertEqual(config["valid_labels"], ["Positive", "Negative"])
        self.assertTrue(config["system_prompt"].strip())

    def test_load_system_prompt_returns_prompt_text(self):
        prompt = load_system_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("V1.3", prompt)
        self.assertIn("Return only the final JSON object.", prompt)

    def test_missing_configuration_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_prompt_config("missing_prompt_config.json")

    def test_invalid_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_prompt_config(path)

    def test_missing_required_field_raises_value_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "incomplete.json"
            path.write_text(json.dumps({"version": "V1.3"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_prompt_config(path)


if __name__ == "__main__":
    unittest.main()
