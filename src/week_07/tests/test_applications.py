"""Stage 2: application registry, condition definitions and application-aware workflow specs."""
from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType

from week_07 import applications, conditions, config
from week_07.applications import (
    APPLICATIONS,
    CANINE_ABDOMEN,
    CANINE_THORAX,
    FELINE_THORAX,
    ApplicationSpec,
    application_for,
    get_application,
)
from week_07.config import ConfigurationError
from week_07.tests.support import OfflineTestCase

FELINE_ORDER = (
    "pulmonary_nodules", "esophagitis", "pneumonia", "bronchitis", "interstitial",
    "diseased_lungs", "hypo_plastic_trachea", "cardiomegaly", "pleural_effusion",
    "perihilar_infiltrate", "rtm", "focal_caudodorsal_lung", "right_sided_cardiomegaly",
    "focal_perihilar", "left_sided_cardiomegaly", "bronchiectasis",
    "pulmonary_vessel_enlargement", "thoracic_lymphadenopathy", "pulmonary_hypoinflation",
    "pericardial_effusion", "Fe_Alveolar",
)
ABDOMEN_ORDER = (
    "gastritis", "ascites", "colitis", "liver_mass", "pancreatitis", "microhepatia",
    "small_intestinal_obstruction", "splenic_mass", "splenomegaly", "hepatomegaly",
)


class TestRegistry(OfflineTestCase):
    def test_three_applications_canine_thorax_default(self):
        self.assertEqual(tuple(APPLICATIONS),
                         ("canine_thorax", "feline_thorax", "canine_abdomen"))
        self.assertEqual(applications.DEFAULT_APPLICATION, "canine_thorax")
        self.assertIs(get_application(), CANINE_THORAX)
        for key, app in APPLICATIONS.items():
            self.assertIs(get_application(key), app)
            self.assertEqual(app.key, key)

    def test_unknown_application_rejected(self):
        for key in ("feline", "Canine_Thorax", "", "canine_thorax "):
            with self.subTest(key=key), self.assertRaises(ConfigurationError):
                get_application(key)

    def test_registry_is_read_only(self):
        with self.assertRaises(TypeError):
            APPLICATIONS["x"] = CANINE_THORAX  # type: ignore[index]

    def test_providers_and_default_models(self):
        self.assertEqual((CANINE_THORAX.provider, CANINE_THORAX.default_model),
                         ("gemini", "gemini-3.8-flash"))
        self.assertEqual(CANINE_THORAX.default_model, config.DEFAULT_MODEL)
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            self.assertEqual((app.provider, app.default_model), ("openai", "gpt-4.1-mini"))


class TestConditionDefinitions(OfflineTestCase):
    def test_canine_thorax_is_the_original_object(self):
        self.assertIs(CANINE_THORAX.condition_keys, conditions.CONDITION_KEYS)
        self.assertEqual(CANINE_THORAX.condition_count, 20)

    def test_feline_thorax_exact_21_in_order(self):
        self.assertEqual(FELINE_THORAX.condition_keys, FELINE_ORDER)
        self.assertEqual(FELINE_THORAX.condition_count, 21)
        self.assertEqual(len(set(FELINE_THORAX.condition_keys)), 21)
        self.assertIn("Fe_Alveolar", FELINE_THORAX.condition_keys)  # case-sensitive key

    def test_canine_abdomen_exact_10_in_order(self):
        self.assertEqual(CANINE_ABDOMEN.condition_keys, ABDOMEN_ORDER)
        self.assertEqual(CANINE_ABDOMEN.condition_count, 10)

    def test_keys_are_tuples(self):
        for app in APPLICATIONS.values():
            self.assertIsInstance(app.condition_keys, tuple)

    def test_counts_are_enforced(self):
        with self.assertRaises(ConfigurationError):
            replace(FELINE_THORAX, condition_keys=FELINE_ORDER[:-1])
        with self.assertRaises(ConfigurationError):
            replace(CANINE_ABDOMEN, condition_keys=ABDOMEN_ORDER[:-1] + ("gastritis",))
        with self.assertRaises(ConfigurationError):
            replace(CANINE_ABDOMEN, condition_keys=list(ABDOMEN_ORDER))


class TestHumanInstruction(OfflineTestCase):
    def test_canine_thorax_is_the_week4_5_sentence(self):
        from week_07.llm_client import HUMAN_INSTRUCTION

        self.assertEqual(CANINE_THORAX.human_instruction, HUMAN_INSTRUCTION)

    def test_region_swapped_for_new_applications(self):
        self.assertEqual(
            FELINE_THORAX.human_instruction,
            "Classify the following feline thorax radiology report according to the "
            "system instructions.")
        self.assertEqual(
            CANINE_ABDOMEN.human_instruction,
            "Classify the following canine abdomen radiology report according to the "
            "system instructions.")


class TestLabelNormalization(OfflineTestCase):
    def test_feline_matrix1_exactly_three_columns(self):
        mapping = FELINE_THORAX.label_normalization("matrix1")
        self.assertEqual(set(mapping), {"pulmonary_nodules", "esophagitis", "pneumonia"})
        for condition in mapping:
            self.assertEqual(dict(mapping[condition]),
                             {"Normal": "Negative", "Abnormal": "Positive"})

    def test_no_normalization_anywhere_else(self):
        self.assertEqual(dict(FELINE_THORAX.label_normalization("matrix2")), {})
        for app in (CANINE_THORAX, CANINE_ABDOMEN):
            for workflow in ("matrix1", "matrix2"):
                with self.subTest(app=app.key, workflow=workflow):
                    self.assertEqual(dict(app.label_normalization(workflow)), {})

    def test_normalization_is_read_only(self):
        mapping = FELINE_THORAX.label_normalization("matrix1")
        with self.assertRaises(TypeError):
            mapping["rtm"] = {}  # type: ignore[index]
        with self.assertRaises(TypeError):
            mapping["pneumonia"]["normal"] = "Negative"  # type: ignore[index]

    def test_unknown_workflow_rejected(self):
        with self.assertRaises(ConfigurationError):
            FELINE_THORAX.label_normalization("matrix3")

    def test_invalid_normalization_rejected(self):
        def bad(by_condition):
            return MappingProxyType({"matrix1": MappingProxyType(by_condition)})

        for case in ({"not_a_condition": {"Normal": "Negative"}},
                     {"rtm": {"Normal": "negative"}},
                     {"rtm": {"Positive": "Negative"}}):
            with self.subTest(case=case), self.assertRaises(ConfigurationError):
                replace(FELINE_THORAX, reference_label_normalization=bad(case))
        with self.assertRaises(ConfigurationError):
            replace(FELINE_THORAX, reference_label_normalization=MappingProxyType(
                {"matrix3": MappingProxyType({})}))


class TestWorkflows(OfflineTestCase):
    def test_canine_thorax_uses_the_original_workflow_objects(self):
        self.assertIs(CANINE_THORAX.workflow("matrix1"), config.MATRIX1)
        self.assertIs(CANINE_THORAX.workflow("matrix2"), config.MATRIX2)
        self.assertEqual(config.WORKFLOWS, {"matrix1": config.MATRIX1,
                                            "matrix2": config.MATRIX2})
        self.assertFalse(CANINE_THORAX.shared_predictions)
        self.assertIsNone(CANINE_THORAX.prediction_source_workflow)

    def test_canine_thorax_paths_unchanged(self):
        root = config.REPO_ROOT / "outputs" / "week_07"
        for spec, folder in ((config.MATRIX1, "matrix_1"), (config.MATRIX2, "matrix_2")):
            self.assertEqual(spec.application, "canine_thorax")
            self.assertIsNone(spec.shared_predictions_dir)
            self.assertEqual(spec.run_dir, root / folder)
            self.assertEqual(spec.predictions_path, root / folder / "predictions.jsonl")
            self.assertEqual(spec.errors_path, root / folder / "errors.jsonl")
            self.assertEqual(spec.manifest_path, root / folder / "run_manifest.json")
            self.assertEqual(spec.comparison_dir, root / "comparison" / folder)
            self.assertEqual(spec.input_dir, config.DATA_DIR / "week_04_inputs")

    def test_new_application_layout(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            root = config.OUTPUT_ROOT / app.key
            self.assertTrue(app.shared_predictions)
            self.assertEqual(app.prediction_source_workflow, "matrix1")
            for name, folder in (("matrix1", "matrix_1"), ("matrix2", "matrix_2")):
                spec = app.workflow(name)
                with self.subTest(app=app.key, workflow=name):
                    self.assertEqual(spec.name, name)
                    self.assertEqual(spec.application, app.key)
                    self.assertEqual(spec.qualified_name, f"{app.key}/{name}")
                    self.assertIs(application_for(spec), app)
                    self.assertEqual(spec.output_dir, root / folder)
                    self.assertEqual(spec.run_dir, root / "predictions")
                    self.assertEqual(spec.predictions_path,
                                     root / "predictions" / "predictions.jsonl")
                    self.assertEqual(spec.manifest_path,
                                     root / "predictions" / "run_manifest.json")
                    self.assertEqual(spec.evaluation_workbook_path.parent, root / folder)
                    self.assertTrue(spec.evaluation_workbook_filename.startswith(app.key))
                    self.assertIsNone(spec.comparison_dir)
                    self.assertIsNone(spec.week5_output_dir)
                    self.assertEqual(spec.input_dir, config.WEEK7_INPUT_DIR)
                    self.assertEqual(spec.case_limit, 100)
                    with self.assertRaises(ConfigurationError):
                        spec.comparison_workbook_path
                    with self.assertRaises(ConfigurationError):
                        spec.week5_predictions_path

    def test_case_rules_follow_matrix1_and_matrix2(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            m1, m2 = app.workflow("matrix1"), app.workflow("matrix2")
            for field in ("require_exact_case_count", "max_case_limit", "configurable_limit",
                          "worksheet_name", "case_limit", "title", "reference_description"):
                with self.subTest(app=app.key, field=field):
                    self.assertEqual(getattr(m1, field), getattr(config.MATRIX1, field))
                    self.assertEqual(getattr(m2, field), getattr(config.MATRIX2, field))

    def test_input_filenames(self):
        self.assertEqual(
            (FELINE_THORAX.workflow("matrix1").input_filename,
             FELINE_THORAX.workflow("matrix2").input_filename),
            ("2_feline_thorax_raw_data_encoded.xlsx",
             "2_feline_thorax_gold_standard_score_draft.xlsx"))
        self.assertEqual(
            (CANINE_ABDOMEN.workflow("matrix1").input_filename,
             CANINE_ABDOMEN.workflow("matrix2").input_filename),
            ("3_canine_abdomen_raw_data_encoded.xlsx",
             "3_canine_abdomen_gold_standard_score_draft.xlsx"))

    def test_all_workflows_unique_and_disjoint(self):
        self.assertEqual(len(config.ALL_WORKFLOWS), 6)
        for key, spec in config.ALL_WORKFLOWS.items():
            self.assertEqual(key, spec.qualified_name)
        dirs = []
        for spec in config.ALL_WORKFLOWS.values():
            dirs.append(spec.output_dir.resolve())
            if spec.shared_predictions_dir is not None:
                dirs.append(spec.shared_predictions_dir.resolve())
            if spec.comparison_dir is not None:
                dirs.append(spec.comparison_dir.resolve())
        unique = list(dict.fromkeys(dirs))
        for i, a in enumerate(unique):
            for b in unique[i + 1:]:
                self.assertFalse(a.is_relative_to(b) or b.is_relative_to(a), (a, b))

    def test_unknown_workflow_rejected(self):
        with self.assertRaises(ConfigurationError):
            FELINE_THORAX.workflow("matrix3")

    def test_application_rejects_foreign_or_inconsistent_workflows(self):
        with self.assertRaises(ConfigurationError):
            replace(FELINE_THORAX, workflows=CANINE_ABDOMEN.workflows)
        with self.assertRaises(ConfigurationError):
            replace(FELINE_THORAX, shared_predictions=False)
        with self.assertRaises(ConfigurationError):
            replace(CANINE_THORAX, prediction_source_workflow="matrix1")

    def test_repr_is_short(self):
        self.assertIsInstance(ApplicationSpec.__repr__(FELINE_THORAX), str)
        self.assertNotIn("pulmonary_nodules", repr(FELINE_THORAX))
