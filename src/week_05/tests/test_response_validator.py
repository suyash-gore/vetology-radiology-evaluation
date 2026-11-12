"""Offline tests for the V1.3 response validator. Synthetic responses only."""
from __future__ import annotations

import inspect
import json
import random
import unittest
from pathlib import Path

from week_05.conditions import CONDITION_KEYS
from week_05.config import REPO_ROOT
from week_05.response_validator import (
    ResponseValidationError,
    validate_model_response,
    validate_predictions,
)

WEEK4_FIXTURE = REPO_ROOT / "src" / "week_04" / "case1_raw_response.json"
SINGLE_CASE_ARTIFACT = REPO_ROOT / "outputs" / "week_04" / "matrix_1" / "single_case_test.json"


def labels(**overrides) -> dict:
    data = {key: "Negative" for key in CONDITION_KEYS}
    data.update(overrides)
    return data


def raw(**overrides) -> str:
    return json.dumps(labels(**overrides))


class ValidatorTestCase(unittest.TestCase):
    def assertRejected(self, response, message=None):
        with self.assertRaises(ResponseValidationError) as ctx:
            validate_model_response(response)
        if message is not None:
            self.assertEqual(str(ctx.exception), message)
        return str(ctx.exception)


class TestValidResponses(ValidatorTestCase):
    def test_week4_fixture_is_valid(self):
        result = validate_model_response(WEEK4_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(tuple(result), CONDITION_KEYS)
        positives = [k for k, v in result.items() if v == "Positive"]
        self.assertEqual(positives, ["bronchitis", "interstitial", "diseased_lungs"])

    def test_real_week4_single_case_raw_response_is_valid(self):
        record = json.loads(SINGLE_CASE_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(validate_model_response(record["raw_response"]), record["predictions"])

    def test_all_negative_all_positive_and_mixed(self):
        for data in (labels(), {k: "Positive" for k in CONDITION_KEYS},
                     labels(pneumonia="Positive", rtm="Positive", esophagitis="Positive")):
            with self.subTest(positives=sum(v == "Positive" for v in data.values())):
                self.assertEqual(validate_model_response(json.dumps(data)), data)

    def test_returns_exactly_twenty_keys_in_canonical_order(self):
        result = validate_model_response(raw(cardiomegaly="Positive"))
        self.assertEqual(len(result), 20)
        self.assertEqual(tuple(result), CONDITION_KEYS)
        self.assertEqual(set(result.values()), {"Positive", "Negative"})

    def test_formatting_whitespace_is_accepted(self):
        compact = json.dumps(labels(), separators=(",", ":"))
        variants = {
            "pretty": json.dumps(labels(), indent=2),
            "compact": compact,
            "surrounding whitespace": f"\n\t  {compact}  \r\n",
            "tabs between tokens": compact.replace(":", " :\t").replace(",", " ,\n"),
        }
        for name, response in variants.items():
            with self.subTest(variant=name):
                self.assertEqual(validate_model_response(response), labels())

    def test_unicode_escaped_key_is_the_same_key(self):
        response = raw().replace('"rtm"', '"\\u0072tm"')
        self.assertEqual(validate_model_response(response), labels())


class TestKeyOrder(ValidatorTestCase):
    """Week 4 accepts any key order and normalises to canonical order."""

    def test_non_canonical_orders_accepted_and_normalised(self):
        rng = random.Random(1300)
        orders = {"reversed": list(reversed(CONDITION_KEYS)),
                  "alphabetical": sorted(CONDITION_KEYS)}
        for i in range(5):
            shuffled = list(CONDITION_KEYS)
            rng.shuffle(shuffled)
            orders[f"shuffle {i}"] = shuffled
        expected = labels(pneumonia="Positive", esophagitis="Positive")
        for name, order in orders.items():
            with self.subTest(order=name):
                response = json.dumps({key: expected[key] for key in order})
                result = validate_model_response(response)
                self.assertEqual(result, expected)
                self.assertEqual(tuple(result), CONDITION_KEYS)


class TestMalformedResponses(ValidatorTestCase):
    def test_empty_or_non_text(self):
        message = "Model response is empty or is not text."
        for value in ("", " ", "\n\t ", None, 0, b"{}", {"rtm": "Negative"}, labels()):
            with self.subTest(value=type(value).__name__ + repr(value)[:20]):
                self.assertRejected(value, message)

    def test_invalid_json(self):
        cases = {
            "plain prose": "All conditions are negative.",
            "markdown fence": f"```json\n{raw()}\n```",
            "bare fence": f"```\n{raw()}\n```",
            "leading prose": f"Here is the JSON: {raw()}",
            "trailing prose": f"{raw()} Hope this helps.",
            "two objects": raw() + raw(),
            "truncated": raw()[:-5],
            "single quotes": raw().replace('"', "'"),
            "trailing comma": raw()[:-1] + ",}",
            "comment": raw()[:-1] + " // done\n}",
            "unquoted label": raw().replace('"Negative"', "Negative", 1),
            "BOM": "﻿" + raw(),
        }
        for name, response in cases.items():
            with self.subTest(case=name):
                message = self.assertRejected(response)
                self.assertTrue(message.startswith("Response is not valid JSON: "), message)
                self.assertRegex(message, r"at line \d+, column \d+\.$")

    def test_non_object_json(self):
        cases = {"list": ("[\"Positive\"]", "list"), "string": ('"Positive"', "str"),
                 "number": ("1", "int"), "null": ("null", "NoneType"), "true": ("true", "bool"),
                 "wrapped": (json.dumps([labels()]), "list")}
        for name, (response, type_name) in cases.items():
            with self.subTest(case=name):
                self.assertRejected(response, f"Expected a JSON object, received {type_name}.")

    def test_duplicate_keys(self):
        response = raw()[:-1] + ', "pneumonia": "Positive"}'
        self.assertRejected(response, "Duplicate JSON key: 'pneumonia'")

    def test_same_value_duplicate_still_rejected(self):
        response = raw()[:-1] + ', "rtm": "Negative"}'
        self.assertRejected(response, "Duplicate JSON key: 'rtm'")

    def test_nested_duplicate_key_rejected(self):
        response = raw()[:-1] + ', "note": {"a": 1, "a": 2}}'
        self.assertRejected(response, "Duplicate JSON key: 'a'")


class TestKeys(ValidatorTestCase):
    def test_missing_one_key(self):
        data = labels()
        del data["pneumonia"]
        self.assertRejected(json.dumps(data), "Missing keys (1): ['pneumonia']")

    def test_missing_keys_listed_in_canonical_order(self):
        data = labels()
        for key in ("esophagitis", "rtm", "perihilar_infiltrate"):
            del data[key]
        self.assertRejected(json.dumps(data),
                            "Missing keys (3): ['perihilar_infiltrate', 'rtm', 'esophagitis']")

    def test_empty_object_reports_all_twenty_missing(self):
        message = self.assertRejected("{}")
        self.assertTrue(message.startswith("Missing keys (20): "))
        self.assertEqual(message, f"Missing keys (20): {list(CONDITION_KEYS)}")

    def test_unexpected_keys_sorted(self):
        response = json.dumps({**labels(), "zeta": "Negative", "case_id": "1"})
        self.assertRejected(response, "Unexpected keys (2): ['case_id', 'zeta']")

    def test_missing_and_unexpected_reported_together(self):
        data = labels()
        del data["rtm"]
        data["RTM"] = "Negative"
        self.assertRejected(json.dumps(data),
                            "Missing keys (1): ['rtm']; Unexpected keys (1): ['RTM']")

    def test_near_miss_key_spellings_rejected(self):
        for wrong in ("Pneumonia", "pneumonia ", " pneumonia", "pneumonía", "pnuemonia",
                      "hypoplastic_trachea", "redundant_tracheal_membrane"):
            correct = {"Pneumonia": "pneumonia", "pneumonia ": "pneumonia",
                       " pneumonia": "pneumonia", "pneumonía": "pneumonia",
                       "pnuemonia": "pneumonia", "hypoplastic_trachea": "hypo_plastic_trachea",
                       "redundant_tracheal_membrane": "rtm"}[wrong]
            with self.subTest(wrong=wrong):
                data = {(wrong if k == correct else k): v for k, v in labels().items()}
                message = self.assertRejected(json.dumps(data))
                self.assertIn(f"Missing keys (1): [{correct!r}]", message)
                self.assertIn(f"Unexpected keys (1): [{wrong!r}]", message)

    def test_extra_metadata_keys_rejected(self):
        for extra in ("CaseID", "confidence", "explanation", "reasoning", "notes"):
            with self.subTest(extra=extra):
                self.assertRejected(json.dumps({**labels(), extra: "x"}),
                                    f"Unexpected keys (1): [{extra!r}]")

    def test_key_checks_take_precedence_over_label_checks(self):
        data = labels(pneumonia="maybe")
        del data["rtm"]
        self.assertRejected(json.dumps(data), "Missing keys (1): ['rtm']")


class TestLabels(ValidatorTestCase):
    def test_invalid_label_values(self):
        cases = {
            "lower case": "positive",
            "upper case": "NEGATIVE",
            "leading space": " Positive",
            "trailing space": "Negative ",
            "trailing newline": "Positive\n",
            "abbreviation": "Pos",
            "third class": "Uncertain",
            "not mentioned": "Not Mentioned",
            "unknown": "Unknown",
            "legacy": "Abnormal",
            "empty": "",
        }
        for name, value in cases.items():
            with self.subTest(case=name):
                self.assertRejected(
                    raw(rtm=value),
                    "Invalid labels. Values must be exactly 'Positive' or 'Negative': "
                    f"rtm={value!r}",
                )

    def test_non_string_values(self):
        for value in (True, False, 1, 0, 1.0, None, ["Positive"], {"value": "Positive"}):
            with self.subTest(value=value):
                message = self.assertRejected(raw(pneumonia=value))
                self.assertIn(f"pneumonia={value!r}", message)

    def test_all_invalid_labels_reported_in_response_order(self):
        data = {key: "Negative" for key in reversed(CONDITION_KEYS)}
        data["rtm"] = "yes"
        data["pneumonia"] = None
        self.assertRejected(
            json.dumps(data),
            "Invalid labels. Values must be exactly 'Positive' or 'Negative': "
            "rtm='yes', pneumonia=None",
        )


class TestIndependence(unittest.TestCase):
    def test_signature_takes_only_the_response(self):
        params = list(inspect.signature(validate_model_response).parameters)
        self.assertEqual(params, ["raw_response"])
        self.assertEqual(list(inspect.signature(validate_predictions).parameters),
                         ["predictions"])

    def test_module_does_not_reference_reference_labels_or_case_ids(self):
        import week_05.response_validator as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        code = source.split('"""', 2)[2]  # skip the module docstring
        for forbidden in ("dataset_loader", "reference_labels", "ground_truth", "gold"):
            self.assertNotIn(forbidden, code)

    def test_error_is_a_value_error(self):
        self.assertTrue(issubclass(ResponseValidationError, ValueError))


class TestValidatePredictions(unittest.TestCase):
    def test_valid_mapping_any_order(self):
        data = {k: "Negative" for k in reversed(CONDITION_KEYS)}
        self.assertEqual(tuple(validate_predictions(data)), CONDITION_KEYS)

    def test_invalid_mappings(self):
        missing = labels()
        del missing["rtm"]
        for value in (None, [], "text", missing, labels(rtm="positive"), {**labels(), "x": "y"}):
            with self.subTest(value=repr(value)[:30]):
                with self.assertRaises(ResponseValidationError):
                    validate_predictions(value)

    def test_unserialisable_mapping(self):
        with self.assertRaisesRegex(ResponseValidationError, "not JSON-serialisable"):
            validate_predictions({"rtm": object()})


class TestWeek4Parity(unittest.TestCase):
    """Every outcome — accepted result or exact error message — must match Week 4."""

    @classmethod
    def setUpClass(cls):
        from week_04.response_validator import ResponseValidationError as Week4Error
        from week_04.response_validator import validate_model_response as week4

        cls.week4 = staticmethod(week4)
        cls.week4_error = Week4Error

    def outcome(self, fn, error_type, response):
        try:
            result = fn(response)
            return ("ok", list(result.items()))
        except error_type as exc:
            return (type(exc).__name__, str(exc))

    def assert_same(self, response):
        self.assertEqual(
            self.outcome(validate_model_response, ResponseValidationError, response),
            self.outcome(self.week4, self.week4_error, response),
        )

    def test_curated_cases(self):
        base = raw()
        cases = [
            WEEK4_FIXTURE.read_text(encoding="utf-8"), base, "", "   ", None, 5, "null", "[]",
            "{}", base[:-3], f"```json\n{base}\n```", base + "x", base + base, "﻿" + base,
            base[:-1] + ', "rtm": "Positive"}', base[:-1] + ', "n": {"a": 1, "a": 1}}',
            raw(rtm="positive"), raw(rtm=" Negative"), raw(rtm=None), raw(rtm=1),
            json.dumps({k: "Negative" for k in reversed(CONDITION_KEYS)}),
            json.dumps({**labels(), "extra": "Negative"}),
            json.dumps({k: v for k, v in labels().items() if k != "bronchitis"}),
            "\n  " + base + "\n", '{"rtm": NaN}', '{"rtm": Infinity}',
        ]
        for response in cases:
            with self.subTest(response=repr(response)[:50]):
                self.assert_same(response)

    def test_randomised_mutations(self):
        rng = random.Random(20261110)
        bad_values = ["positive", " Positive", "Uncertain", "", None, 1, True, ["Negative"]]
        bad_keys = ["case_id", "Pneumonia", "rtm ", "extra"]
        for i in range(300):
            data = {k: rng.choice(("Positive", "Negative")) for k in CONDITION_KEYS}
            items = list(data.items())
            rng.shuffle(items)
            data = dict(items)
            for _ in range(rng.randint(0, 3)):
                action = rng.randrange(4)
                key = rng.choice(CONDITION_KEYS)
                if action == 0:
                    data.pop(key, None)
                elif action == 1:
                    data[rng.choice(bad_keys)] = rng.choice(("Positive", "Negative"))
                elif action == 2:
                    data[key] = rng.choice(bad_values)
            response = json.dumps(data, indent=rng.choice((None, 2)))
            if rng.random() < 0.1:
                response = response[: rng.randint(0, len(response))]
            if rng.random() < 0.05:
                response = f"```json\n{response}\n```"
            with self.subTest(i=i):
                self.assert_same(response)


if __name__ == "__main__":
    unittest.main(verbosity=2)
