"""Output isolation guard and read-only source protection.

Policy tests use a synthetic layout inside a temporary directory, so no file is
created in the repository. The DEFAULT_POLICY tests only evaluate paths; they
never write.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from week_07 import config
from week_07.config import ConfigurationError
from week_07.isolation import (
    DEFAULT_POLICY,
    IsolationError,
    IsolationPolicy,
    OutputArea,
    ProtectedFileModified,
    ReadOnlyGuard,
    assert_writable,
    sha256_file,
)
from week_07.tests.support import OfflineTestCase

RUN, COMPARISON = OutputArea.RUN, OutputArea.COMPARISON


class SyntheticLayout(OfflineTestCase):
    def setUp(self):
        super().setUp()
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.root)
        out = self.root / "outputs" / "week_07"
        self.m1 = replace(config.MATRIX1, output_dir=out / "matrix_1",
                          comparison_dir=out / "comparison" / "matrix_1",
                          week5_output_dir=self.root / "outputs" / "week_05" / "matrix_1")
        self.m2 = replace(config.MATRIX2, output_dir=out / "matrix_2",
                          comparison_dir=out / "comparison" / "matrix_2",
                          week5_output_dir=self.root / "outputs" / "week_05" / "matrix_2")
        self.protected = {
            "week4": self.root / "outputs" / "week_04",
            "week5": self.root / "outputs" / "week_05",
            "data": self.root / "data",
            "src": self.root / "src",
        }
        self.policy = IsolationPolicy(
            output_root=out,
            protected_roots=tuple(self.protected.values()),
            workflows={"matrix1": self.m1, "matrix2": self.m2},
        )
        self.out = out


class TestAllowedWrites(SyntheticLayout):
    def test_own_run_outputs(self):
        for name in ("predictions.jsonl", "errors.jsonl", "run_manifest.json",
                     "matrix1_evaluation_workbook.xlsx"):
            target = self.m1.output_dir / name
            self.assertEqual(self.policy.assert_writable(target, self.m1, RUN), target)

    def test_own_comparison_output(self):
        target = self.m2.comparison_workbook_path
        self.assertEqual(self.policy.assert_writable(target, self.m2, COMPARISON), target)

    def test_override_directory_inside_week7(self):
        target = self.out / "matrix_1_rerun" / "predictions.jsonl"
        self.assertEqual(self.policy.assert_writable(target, self.m1, RUN), target)

    def test_returns_resolved_path(self):
        messy = self.m1.output_dir / "sub" / ".." / "predictions.jsonl"
        self.assertEqual(self.policy.assert_writable(messy, self.m1),
                         self.m1.output_dir / "predictions.jsonl")


class TestRefusedWrites(SyntheticLayout):
    def test_protected_roots(self):
        for label, root in self.protected.items():
            for target in (root, root / "matrix_1" / "predictions.jsonl", root / "x.xlsx"):
                with self.subTest(label=label, target=target), self.assertRaises(IsolationError):
                    self.policy.assert_writable(target)

    def test_week5_prediction_file_is_never_writable(self):
        for spec in (self.m1, self.m2):
            with self.subTest(spec=spec.name), self.assertRaises(IsolationError):
                self.policy.assert_writable(spec.week5_predictions_path, spec)
            with self.assertRaises(IsolationError):
                self.policy.assert_writable(spec.week5_errors_path, spec)

    def test_outside_week7_root(self):
        for target in (self.root / "elsewhere.jsonl", self.root / "outputs" / "x.jsonl",
                       self.root / "outputs" / "week_06" / "x.jsonl", Path("/tmp/x.jsonl"),
                       self.out):
            with self.subTest(target=target), self.assertRaises(IsolationError):
                self.policy.assert_writable(target)

    def test_parent_traversal_escape(self):
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.m1.output_dir / ".." / ".." / "week_05" / "a.jsonl")

    def test_cross_workflow_run_dirs(self):
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.m2.predictions_path, self.m1, RUN)
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.m1.evaluation_workbook_path, self.m2, RUN)

    def test_cross_workflow_comparison_dirs(self):
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.m2.comparison_workbook_path, self.m1, COMPARISON)

    def test_run_and_comparison_areas_are_separate(self):
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.m1.comparison_dir / "predictions.jsonl", self.m1, RUN)
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.m1.output_dir / "cmp.xlsx", self.m1, COMPARISON)

    def test_directory_containing_another_workflow(self):
        # A run directory that would contain the other workflow's outputs.
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(self.out / "comparison", self.m1, RUN)

    @unittest.skipIf(os.name == "nt", "symlink creation needs privileges on Windows")
    def test_symlink_escape(self):
        self.protected["week5"].mkdir(parents=True)
        self.out.mkdir(parents=True)
        link = self.out / "matrix_1"
        link.symlink_to(self.protected["week5"], target_is_directory=True)
        with self.assertRaises(IsolationError):
            self.policy.assert_writable(link / "predictions.jsonl", self.m1)

    def test_isolation_error_is_a_configuration_error(self):
        self.assertTrue(issubclass(IsolationError, ConfigurationError))


class TestDefaultPolicy(OfflineTestCase):
    """Path evaluation against the real repository layout (nothing is written)."""

    def test_real_protected_locations_refused(self):
        repo = config.REPO_ROOT
        for target in (repo / "outputs" / "week_05" / "matrix_1" / "predictions.jsonl",
                       repo / "outputs" / "week_05" / "matrix_2" / "errors.jsonl",
                       repo / "outputs" / "week_04" / "matrix_1" / "single_case_test.json",
                       repo / "data" / "week_04_inputs" / "x.xlsx",
                       repo / "src" / "week_05" / "config.py",
                       repo / ".git" / "config",
                       repo / ".env",
                       repo / "requirements.txt"):
            with self.subTest(target=target), self.assertRaises(IsolationError):
                assert_writable(target)

    def test_real_week7_locations_allowed(self):
        self.assertEqual(assert_writable(config.MATRIX1.predictions_path, config.MATRIX1),
                         config.MATRIX1.predictions_path.resolve())
        self.assertEqual(
            assert_writable(config.MATRIX2.comparison_workbook_path, config.MATRIX2, COMPARISON),
            config.MATRIX2.comparison_workbook_path.resolve())

    def test_default_policy_protects_expected_roots(self):
        repo = config.REPO_ROOT
        self.assertEqual(set(DEFAULT_POLICY.protected_roots),
                         {repo / "outputs" / "week_04", repo / "outputs" / "week_05",
                          repo / "data", repo / "src", repo / ".git"})
        self.assertEqual(DEFAULT_POLICY.output_root, repo / "outputs" / "week_07")


class TestReadOnlyGuard(OfflineTestCase):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.source = self.tmp / "predictions.jsonl"
        self.source.write_bytes(b'{"case_id": 1}\n')

    def test_sha256_file(self):
        self.assertEqual(sha256_file(self.source),
                         hashlib.sha256(b'{"case_id": 1}\n').hexdigest())

    def test_unchanged_sources_pass_and_digests_are_recorded(self):
        with ReadOnlyGuard([self.source, self.source]) as guard:
            self.source.read_bytes()
        self.assertEqual(guard.digests, {self.source.resolve(): sha256_file(self.source)})

    def test_modification_is_detected(self):
        with self.assertRaises(ProtectedFileModified):
            with ReadOnlyGuard([self.source]):
                with self.source.open("ab") as handle:
                    handle.write(b"x")

    def test_deletion_is_detected(self):
        with self.assertRaises(ProtectedFileModified):
            with ReadOnlyGuard([self.source]):
                self.source.unlink()

    def test_detected_even_when_body_raises(self):
        with self.assertRaises(ProtectedFileModified):
            with ReadOnlyGuard([self.source]):
                self.source.write_bytes(b"changed")
                raise ValueError("body failure")

    def test_body_exception_propagates_when_unchanged(self):
        with self.assertRaises(ValueError):
            with ReadOnlyGuard([self.source]):
                raise ValueError("body failure")

    def test_missing_source_on_entry(self):
        with self.assertRaises(FileNotFoundError):
            with ReadOnlyGuard([self.tmp / "missing.jsonl"]):
                pass
