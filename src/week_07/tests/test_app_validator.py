"""Application-aware response validation for all three applications."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from week_07 import response_validator
from week_07.app_validator import (
    ResponseValidationError,
    load_successful_case_ids_for,
    validate_model_response,
    validate_predictions,
    validator_for,
)
from week_07.applications import APPLICATIONS, CANINE_ABDOMEN, CANINE_THORAX, FELINE_THORAX
from week_07.jsonl_store import load_successful_case_ids
from week_07.tests.support import OfflineTestCase, quiet


def valid(app, label="Negative"):
    return {key: label for key in app.condition_keys}


def corpus(app):
    base = valid(app)
    text = json.dumps(base)
    first, last = app.condition_keys[0], app.condition_keys[-1]
    return [
        text, json.dumps(dict(reversed(list(base.items())))), f"  {text}\n",
        f"```json\n{text}\n```", f"Here: {text}", "﻿" + text, text + text,
        json.dumps({k: v for k, v in base.items() if k != last}),
        json.dumps({**base, "other": "Negative"}),
        json.dumps({**base, first: "positive"}), json.dumps({**base, first: " Positive"}),
        json.dumps({**base, first: True}), json.dumps({**base, first: "Normal"}),
        text[:-1] + f', "{last}": "Positive"}}', "", "   ", None, 5, "[]", '"x"', "{",
        "null", '{"a": {"a": 1, "a": 2}}',
    ]


def outcome(function, raw):
    try:
        return ("ok", function(raw))
    except ResponseValidationError as exc:
        return ("error", str(exc))


class TestEveryApplication(OfflineTestCase):
    def test_valid_response_returned_in_canonical_order(self):
        for app in APPLICATIONS.values():
            with self.subTest(app=app.key):
                shuffled = dict(reversed(list(valid(app, "Positive").items())))
                result = validate_model_response(json.dumps(shuffled), app.condition_keys)
                self.assertEqual(tuple(result), app.condition_keys)
                self.assertEqual(set(result.values()), {"Positive"})

    def test_missing_extra_duplicate_and_invalid_rejected(self):
        for app in APPLICATIONS.values():
            base = valid(app)
            last = app.condition_keys[-1]
            cases = {
                "missing": json.dumps({k: v for k, v in base.items() if k != last}),
                "extra": json.dumps({**base, "rtm_extra": "Negative"}),
                "duplicate": json.dumps(base)[:-1] + f', "{last}": "Positive"}}',
                "lowercase": json.dumps({**base, last: "negative"}),
                "padded": json.dumps({**base, last: "Negative "}),
                "abnormal": json.dumps({**base, last: "Abnormal"}),
                "null": json.dumps({**base, last: None}),
                "fenced": f"```json\n{json.dumps(base)}\n```",
                "prose": f"Answer: {json.dumps(base)}",
                "array": json.dumps([base]),
                "empty": "",
            }
            for name, raw in cases.items():
                with self.subTest(app=app.key, case=name):
                    with self.assertRaises(ResponseValidationError):
                        validate_model_response(raw, app.condition_keys)

    def test_keys_of_another_application_rejected(self):
        pairs = ((FELINE_THORAX, CANINE_THORAX), (CANINE_THORAX, FELINE_THORAX),
                 (CANINE_ABDOMEN, FELINE_THORAX), (FELINE_THORAX, CANINE_ABDOMEN))
        for expected, other in pairs:
            with self.subTest(expected=expected.key, given=other.key):
                with self.assertRaisesRegex(ResponseValidationError,
                                            "Missing keys|Unexpected keys"):
                    validate_model_response(json.dumps(valid(other)), expected.condition_keys)

    def test_canine_thorax_keys_are_a_strict_subset_of_feline(self):
        # Feline = the 20 Canine Thorax keys + Fe_Alveolar, in a different order.
        self.assertEqual(set(FELINE_THORAX.condition_keys) - set(CANINE_THORAX.condition_keys),
                         {"Fe_Alveolar"})
        self.assertLess(set(CANINE_THORAX.condition_keys), set(FELINE_THORAX.condition_keys))
        self.assertNotEqual(FELINE_THORAX.condition_keys[:20], CANINE_THORAX.condition_keys)
        with self.assertRaisesRegex(ResponseValidationError, r"Unexpected keys \(1\)"):
            validate_model_response(json.dumps(valid(FELINE_THORAX)),
                                    CANINE_THORAX.condition_keys)

    def test_feline_needs_fe_alveolar_case_sensitive(self):
        base = valid(FELINE_THORAX)
        del base["Fe_Alveolar"]
        base["fe_alveolar"] = "Negative"
        with self.assertRaisesRegex(ResponseValidationError, "Fe_Alveolar"):
            validate_model_response(json.dumps(base), FELINE_THORAX.condition_keys)

    def test_validate_predictions_and_bound_validator(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            self.assertEqual(validate_predictions(valid(app), app.condition_keys), valid(app))
            self.assertEqual(validator_for(app.condition_keys)(json.dumps(valid(app))),
                             valid(app))
            with self.assertRaises(ResponseValidationError):
                validate_predictions({"x": object()}, app.condition_keys)

    def test_invalid_key_sets_refused(self):
        for keys in ((), ("a", "a")):
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                validate_model_response("{}", keys)


class TestCanineThoraxParity(OfflineTestCase):
    def test_outcomes_and_messages_identical_to_verbatim_validator(self):
        for raw in corpus(CANINE_THORAX):
            with self.subTest(raw=repr(raw)[:60]):
                self.assertEqual(
                    outcome(lambda r: validate_model_response(r, CANINE_THORAX.condition_keys),
                            raw),
                    outcome(response_validator.validate_model_response, raw))

    def test_checkpoint_reader_identical_for_canine_keys(self):
        quiet(self, "week_07.jsonl_store")
        lines = [json.dumps({"case_id": 1, "status": "success",
                             "predictions": valid(CANINE_THORAX)}),
                 json.dumps({"case_id": 2, "status": "success",
                             "predictions": valid(FELINE_THORAX)}),
                 "{not json", "",
                 json.dumps({"case_id": 3, "status": "failed", "predictions": None}),
                 json.dumps({"case_id": None, "status": "success",
                             "predictions": valid(CANINE_THORAX)})]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.jsonl"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual(load_successful_case_ids_for(path, CANINE_THORAX.condition_keys),
                             load_successful_case_ids(path))
            self.assertEqual(load_successful_case_ids_for(path, FELINE_THORAX.condition_keys),
                             {"2"})
            self.assertEqual(load_successful_case_ids_for(Path(tmp) / "none.jsonl",
                                                          FELINE_THORAX.condition_keys), set())
