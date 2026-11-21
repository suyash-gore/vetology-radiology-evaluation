"""Stage 2.1: application-qualified output isolation across all three applications.

Path evaluation only, against the real repository layout (``DEFAULT_POLICY``)
and against a synthetic copy of it in a temporary directory. Nothing is written
into the repository.
"""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from week_07 import config
from week_07.applications import CANINE_ABDOMEN, CANINE_THORAX, FELINE_THORAX
from week_07.evaluation.evaluate import check_prediction_source
from week_07.evaluation.reconcile import EvaluationInputError
from week_07.isolation import DEFAULT_POLICY, IsolationError, IsolationPolicy, OutputArea
from week_07.tests.support import OfflineTestCase

RUN, COMPARISON = OutputArea.RUN, OutputArea.COMPARISON
OUT = config.OUTPUT_ROOT
FILES = ("predictions.jsonl", "errors.jsonl", "run_manifest.json", "workbook.xlsx")

CANINE_TARGETS = (
    OUT / "matrix_1", OUT / "matrix_1" / "predictions.jsonl", OUT / "matrix_1" / "errors.jsonl",
    OUT / "matrix_1" / "run_manifest.json", OUT / "matrix_1" / "matrix1_evaluation_workbook.xlsx",
    OUT / "matrix_2", OUT / "matrix_2" / "predictions.jsonl",
    OUT / "matrix_2" / "Evaluation Workbook v2.xlsx",
    OUT / "comparison" / "matrix_1" / "matrix1_openai_vs_gemini_comparison.xlsx",
    OUT / "comparison" / "matrix_2" / "x.xlsx",
)


def _app_targets(key: str) -> tuple[Path, ...]:
    root = OUT / key
    return (
        root, root / "stray_file.jsonl", root / "other" / "predictions.jsonl",
        root / "predictions", *(root / "predictions" / name for name in FILES),
        root / "matrix_1", root / "matrix_1" / f"{key}_matrix1_evaluation_workbook.xlsx",
        root / "matrix_2", root / "matrix_2" / f"{key}_matrix2_evaluation_workbook.xlsx",
    )


class IsolationCase(OfflineTestCase):
    def assertRefused(self, spec, targets, area=RUN, policy=DEFAULT_POLICY):
        for target in targets:
            with self.subTest(writer=spec.qualified_name, area=area.value, target=str(target)):
                with self.assertRaises(IsolationError):
                    policy.assert_writable(target, spec, area)

    def assertAllowed(self, spec, targets, area=RUN, policy=DEFAULT_POLICY):
        for target in targets:
            with self.subTest(writer=spec.qualified_name, area=area.value, target=str(target)):
                self.assertEqual(policy.assert_writable(target, spec, area),
                                 Path(target).resolve())


class TestDefaultPolicyRegistration(OfflineTestCase):
    def test_all_six_workflows_are_registered_by_qualified_identity(self):
        self.assertEqual(set(DEFAULT_POLICY.workflows), {
            "canine_thorax/matrix1", "canine_thorax/matrix2",
            "feline_thorax/matrix1", "feline_thorax/matrix2",
            "canine_abdomen/matrix1", "canine_abdomen/matrix2",
        })
        for key, spec in DEFAULT_POLICY.workflows.items():
            self.assertEqual(key, spec.qualified_name)
        self.assertIs(DEFAULT_POLICY.workflows["canine_thorax/matrix1"], config.MATRIX1)
        self.assertIs(DEFAULT_POLICY.workflows["canine_thorax/matrix2"], config.MATRIX2)

    def test_application_roots(self):
        self.assertEqual(dict(DEFAULT_POLICY.application_roots), {
            "feline_thorax": OUT / "feline_thorax",
            "canine_abdomen": OUT / "canine_abdomen",
        })
        self.assertNotIn("canine_thorax", DEFAULT_POLICY.application_roots)

    def test_week5_parity_mapping_is_still_canine_only(self):
        self.assertEqual(set(config.WORKFLOWS), {"matrix1", "matrix2"})


class TestFelineThoraxCannotWriteIntoOtherApplications(IsolationCase):
    def test_canine_thorax_directories_refused(self):
        for spec in FELINE_THORAX.workflows.values():
            self.assertRefused(spec, CANINE_TARGETS)
            self.assertRefused(spec, CANINE_TARGETS, COMPARISON)

    def test_canine_abdomen_directories_refused(self):
        for spec in FELINE_THORAX.workflows.values():
            self.assertRefused(spec, _app_targets("canine_abdomen"))

    def test_stage2_review_probe_is_now_refused(self):
        with self.assertRaisesRegex(IsolationError, "feline_thorax/matrix1 run output"):
            DEFAULT_POLICY.assert_writable(config.MATRIX1.predictions_path,
                                           FELINE_THORAX.workflow("matrix1"))


class TestCanineThoraxCannotWriteIntoOtherApplications(IsolationCase):
    def test_feline_thorax_directories_refused(self):
        for spec in CANINE_THORAX.workflows.values():
            self.assertRefused(spec, _app_targets("feline_thorax"))
            self.assertRefused(spec, _app_targets("feline_thorax"), COMPARISON)

    def test_canine_abdomen_directories_refused(self):
        for spec in CANINE_THORAX.workflows.values():
            self.assertRefused(spec, _app_targets("canine_abdomen"))
            self.assertRefused(spec, _app_targets("canine_abdomen"), COMPARISON)

    def test_override_output_dir_into_another_application_refused(self):
        # resolve_outputs(spec, output_dir=...) passes the override through this guard.
        self.assertRefused(config.MATRIX1, (OUT / "feline_thorax" / "rerun",
                                            OUT / "canine_abdomen" / "rerun" / "predictions.jsonl"))

    def test_crafted_shared_directory_does_not_unlock_another_application(self):
        crafted = replace(config.MATRIX1,
                          shared_predictions_dir=FELINE_THORAX.workflow("matrix1").run_dir)
        self.assertRefused(crafted, (FELINE_THORAX.workflow("matrix1").predictions_path,))


class TestCanineAbdomenCannotWriteIntoOtherApplications(IsolationCase):
    def test_canine_thorax_directories_refused(self):
        for spec in CANINE_ABDOMEN.workflows.values():
            self.assertRefused(spec, CANINE_TARGETS)
            self.assertRefused(spec, CANINE_TARGETS, COMPARISON)

    def test_feline_thorax_directories_refused(self):
        for spec in CANINE_ABDOMEN.workflows.values():
            self.assertRefused(spec, _app_targets("feline_thorax"))


class TestValidWritesWithinOwnDirectories(IsolationCase):
    def test_canine_thorax_permissions_unchanged(self):
        m1, m2 = config.MATRIX1, config.MATRIX2
        self.assertAllowed(m1, [m1.predictions_path, m1.errors_path, m1.manifest_path,
                                m1.evaluation_workbook_path, OUT / "matrix_1_rerun" / "p.jsonl"])
        self.assertAllowed(m2, [m2.predictions_path, m2.errors_path, m2.manifest_path,
                                m2.evaluation_workbook_path])
        self.assertAllowed(m1, [m1.comparison_workbook_path], COMPARISON)
        self.assertAllowed(m2, [m2.comparison_workbook_path], COMPARISON)

    def test_canine_thorax_refusals_unchanged(self):
        m1, m2 = config.MATRIX1, config.MATRIX2
        self.assertRefused(m1, [m2.predictions_path, m1.comparison_workbook_path,
                                OUT / "comparison"])
        self.assertRefused(m2, [m1.evaluation_workbook_path])
        self.assertRefused(m1, [m1.output_dir / "cmp.xlsx", m2.comparison_workbook_path],
                           COMPARISON)

    def test_new_applications_own_directories(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            for spec in app.workflows.values():
                # Both workflows may write the application's ONE shared prediction run.
                self.assertAllowed(spec, [spec.predictions_path, spec.errors_path,
                                          spec.manifest_path, spec.evaluation_workbook_path])
            self.assertEqual(app.workflow("matrix1").predictions_path,
                             app.workflow("matrix2").predictions_path)

    def test_new_applications_keep_matrix_workbooks_separate(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            m1, m2 = app.workflow("matrix1"), app.workflow("matrix2")
            self.assertRefused(m1, [m2.evaluation_workbook_path, m2.output_dir])
            self.assertRefused(m2, [m1.evaluation_workbook_path, m1.output_dir])

    def test_new_applications_have_no_comparison_area_in_run_directories(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            spec = app.workflow("matrix1")
            self.assertRefused(spec, [spec.predictions_path, spec.evaluation_workbook_path],
                               COMPARISON)

    def test_protected_roots_still_refused_for_every_workflow(self):
        repo = config.REPO_ROOT
        for spec in config.ALL_WORKFLOWS.values():
            self.assertRefused(spec, [repo / "outputs" / "week_05" / "matrix_1" / "x.jsonl",
                                      repo / "outputs" / "week_04" / "x.json",
                                      repo / "data" / "week_07_inputs" / "x.xlsx",
                                      repo / "src" / "week_07" / "x.py", OUT])


class TestCanineMessagesUnchanged(IsolationCase):
    def test_canine_workflows_keep_bare_names_in_messages(self):
        with self.assertRaises(IsolationError) as ctx:
            DEFAULT_POLICY.assert_writable(config.MATRIX2.predictions_path, config.MATRIX1)
        message = str(ctx.exception)
        self.assertTrue(message.startswith(
            "matrix1 run output cannot be written to or around the matrix2 run output "
            "directory ("), message)


class TestSyntheticSixWorkflowPolicy(IsolationCase):
    """The same rules on a temporary copy of the layout (independent of the real repo)."""

    def setUp(self):
        super().setUp()
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        out = self.root / "outputs" / "week_07"

        def move(spec):
            def rebase(path):
                return None if path is None else out / path.relative_to(OUT)
            return replace(spec, output_dir=rebase(spec.output_dir),
                           comparison_dir=rebase(spec.comparison_dir),
                           shared_predictions_dir=rebase(spec.shared_predictions_dir),
                           week5_output_dir=None if spec.week5_output_dir is None
                           else self.root / "outputs" / "week_05" / spec.week5_output_dir.name)

        self.specs = {key: move(spec) for key, spec in config.ALL_WORKFLOWS.items()}
        self.policy = IsolationPolicy(
            output_root=out,
            protected_roots=(self.root / "outputs" / "week_05", self.root / "data"),
            workflows=self.specs,
            application_roots={key: out / key for key in ("feline_thorax", "canine_abdomen")},
        )

    def test_cross_application_matrix(self):
        for writer in self.specs.values():
            for owner in self.specs.values():
                own_tree = writer.application == owner.application
                for target in {owner.predictions_path, owner.evaluation_workbook_path}:
                    allowed = target in {writer.predictions_path, writer.errors_path,
                                         writer.manifest_path, writer.evaluation_workbook_path}
                    with self.subTest(writer=writer.qualified_name, target=str(target)):
                        if allowed:
                            self.assertTrue(own_tree)
                            self.policy.assert_writable(target, writer)
                        else:
                            with self.assertRaises(IsolationError):
                                self.policy.assert_writable(target, writer)


class TestPredictionSourceCheck(OfflineTestCase):
    """``evaluate.check_prediction_source`` with all six workflows registered."""

    def test_canine_thorax_refuses_predictions_from_other_applications(self):
        for spec in (config.MATRIX1, config.MATRIX2):
            for app in (FELINE_THORAX, CANINE_ABDOMEN):
                for source in (app.workflow("matrix1").predictions_path,
                               app.workflow("matrix1").evaluation_workbook_path.parent / "p.jsonl"):
                    with self.subTest(spec=spec.qualified_name, source=str(source)):
                        with self.assertRaises(EvaluationInputError):
                            check_prediction_source(spec, source)

    def test_canine_thorax_behaviour_unchanged(self):
        check_prediction_source(config.MATRIX1, config.MATRIX1.predictions_path)
        check_prediction_source(config.MATRIX2, config.MATRIX2.predictions_path)
        with self.assertRaises(EvaluationInputError):
            check_prediction_source(config.MATRIX1, config.MATRIX2.predictions_path)
        with self.assertRaises(EvaluationInputError):
            check_prediction_source(config.MATRIX1, config.MATRIX2.week5_predictions_path)

    def test_both_matrices_of_an_application_accept_its_shared_predictions(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            for spec in app.workflows.values():
                with self.subTest(spec=spec.qualified_name):
                    check_prediction_source(spec, spec.predictions_path)

    def test_new_applications_refuse_foreign_predictions(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            other = CANINE_ABDOMEN if app is FELINE_THORAX else FELINE_THORAX
            for spec in app.workflows.values():
                for source in (config.MATRIX1.predictions_path,
                               config.MATRIX2.week5_predictions_path,
                               other.workflow("matrix1").predictions_path):
                    with self.subTest(spec=spec.qualified_name, source=str(source)):
                        with self.assertRaises(EvaluationInputError):
                            check_prediction_source(spec, source)


# ---------------------------------------------------------------------------
# Stage 2.2: application-tree read isolation and confined output overrides
# ---------------------------------------------------------------------------

def _custom_paths(key: str) -> tuple[Path, ...]:
    """Unregistered locations inside one new application's tree."""
    root = OUT / key
    return (root / "custom" / "predictions.jsonl", root / "predictions.jsonl",
            root / "a" / "b" / "c" / "predictions.jsonl", root / "matrix_1_rerun" / "p.jsonl")


class TestReadIsolationAcrossApplicationTrees(OfflineTestCase):
    def assertReadRefused(self, spec, sources):
        for source in sources:
            with self.subTest(reader=spec.qualified_name, source=str(source)):
                with self.assertRaises(EvaluationInputError):
                    check_prediction_source(spec, source)

    def assertReadAllowed(self, spec, sources):
        for source in sources:
            with self.subTest(reader=spec.qualified_name, source=str(source)):
                check_prediction_source(spec, source)

    def test_canine_thorax_refuses_anything_inside_new_application_trees(self):
        for spec in (config.MATRIX1, config.MATRIX2):
            self.assertReadRefused(spec, _custom_paths("feline_thorax")
                                   + _custom_paths("canine_abdomen"))

    def test_feline_thorax_refuses_other_trees(self):
        for spec in FELINE_THORAX.workflows.values():
            self.assertReadRefused(spec, _custom_paths("canine_abdomen") + (
                config.MATRIX1.predictions_path, config.MATRIX2.predictions_path,
                OUT / "matrix_1_rerun" / "predictions.jsonl",       # Canine Thorax override
                OUT / "custom" / "predictions.jsonl",
                OUT / "comparison" / "matrix_1" / "p.jsonl"))

    def test_canine_abdomen_refuses_other_trees(self):
        for spec in CANINE_ABDOMEN.workflows.values():
            self.assertReadRefused(spec, _custom_paths("feline_thorax") + (
                config.MATRIX1.predictions_path, OUT / "matrix_1_rerun" / "predictions.jsonl",
                OUT / "custom" / "predictions.jsonl"))

    def test_shared_predictions_readable_by_both_own_workflows(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            shared = app.workflow("matrix1").predictions_path
            for spec in app.workflows.values():
                self.assertReadAllowed(spec, (shared,))

    def test_own_custom_paths_readable(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            for spec in app.workflows.values():
                self.assertReadAllowed(spec, (OUT / app.key / "custom" / "predictions.jsonl",))

    def test_matrix_workbook_dirs_of_the_other_workflow_still_refused(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            m1, m2 = app.workflow("matrix1"), app.workflow("matrix2")
            self.assertReadRefused(m1, (m2.output_dir / "predictions.jsonl",))
            self.assertReadRefused(m2, (m1.output_dir / "predictions.jsonl",))

    def test_canine_thorax_reads_unchanged_outside_new_trees(self):
        self.assertReadAllowed(config.MATRIX1, (
            config.MATRIX1.predictions_path, OUT / "matrix_1_rerun" / "predictions.jsonl",
            OUT / "custom" / "predictions.jsonl"))
        self.assertReadRefused(config.MATRIX1, (config.MATRIX2.predictions_path,
                                                config.MATRIX2.week5_predictions_path,
                                                config.MATRIX2.comparison_dir / "p.jsonl"))

    def test_application_root_message(self):
        with self.assertRaisesRegex(EvaluationInputError, "feline_thorax application output"):
            check_prediction_source(config.MATRIX1, _custom_paths("feline_thorax")[0])


class TestConfinedOutputOverrides(IsolationCase):
    def test_new_application_overrides_inside_own_tree_allowed(self):
        from week_07.batch_runner import resolve_outputs

        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            root = OUT / app.key
            for spec in app.workflows.values():
                for override in (root / "rerun", root / "experiments" / "run_2"):
                    with self.subTest(spec=spec.qualified_name, override=str(override)):
                        outputs = resolve_outputs(spec, override)
                        self.assertEqual(outputs.output_dir, override.resolve())
                        self.assertEqual(outputs.predictions_path.parent, override.resolve())
                self.assertAllowed(spec, [root / "rerun" / "evaluation.xlsx"])

    def test_new_application_overrides_outside_own_tree_refused(self):
        from week_07.batch_runner import resolve_outputs

        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            other = "canine_abdomen" if app is FELINE_THORAX else "feline_thorax"
            for spec in app.workflows.values():
                for override in (OUT / "rerun_elsewhere", OUT / f"{app.key}_rerun",
                                 OUT / "matrix_1_rerun", OUT / other / "rerun",
                                 OUT / app.key):          # the root itself, not inside it
                    with self.subTest(spec=spec.qualified_name, override=str(override)):
                        with self.assertRaises(IsolationError):
                            resolve_outputs(spec, override)
                self.assertRefused(spec, [OUT / "rerun_elsewhere" / "evaluation.xlsx"])
                self.assertRefused(spec, [OUT / "rerun_elsewhere" / "x.xlsx"], COMPARISON)

    def test_confinement_message(self):
        with self.assertRaisesRegex(IsolationError, "must stay inside its own application"):
            DEFAULT_POLICY.assert_writable(OUT / "rerun_elsewhere" / "p.jsonl",
                                           FELINE_THORAX.workflow("matrix1"))

    def test_canine_thorax_override_behaviour_unchanged(self):
        from week_07.batch_runner import resolve_outputs

        for override in (OUT / "matrix_1_rerun", OUT / "rerun_elsewhere", OUT / "matrix_1" / "sub"):
            with self.subTest(override=str(override)):
                self.assertEqual(resolve_outputs(config.MATRIX1, override).output_dir,
                                 override.resolve())
        for override in (OUT / "matrix_2", OUT / "comparison", OUT / "feline_thorax" / "rerun",
                         OUT / "canine_abdomen" / "rerun"):
            with self.subTest(override=str(override)), self.assertRaises(IsolationError):
                resolve_outputs(config.MATRIX1, override)

    def test_workflow_separation_and_shared_predictions_intact(self):
        for app in (FELINE_THORAX, CANINE_ABDOMEN):
            m1, m2 = app.workflow("matrix1"), app.workflow("matrix2")
            self.assertAllowed(m1, [m1.predictions_path, m1.evaluation_workbook_path])
            self.assertAllowed(m2, [m2.predictions_path, m2.evaluation_workbook_path])
            self.assertRefused(m1, [m2.evaluation_workbook_path])
            self.assertRefused(m2, [m1.evaluation_workbook_path])
            self.assertRefused(m1, [m1.predictions_path], COMPARISON)

    def test_no_spec_behaviour_deferred_to_stage5(self):
        # Documented, unchanged: without a workflow only the protected-root and
        # outputs/week_07 rules apply (generic run_batch compatibility contract).
        target = FELINE_THORAX.workflow("matrix1").predictions_path
        self.assertEqual(DEFAULT_POLICY.assert_writable(target), target.resolve())
